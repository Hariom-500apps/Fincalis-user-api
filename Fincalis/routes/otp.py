"""OTP Authorization"""

from fastapi import APIRouter, Depends
import logging
import json
import http.client
from ..util import response
from ..base_jwt import create_service_token
from sqlalchemy.orm import Session
from ..models.user.users import Users
from ..models.user.user_consents import UserConsentIfo
from ..util import response
from ..db import get_db
from ..api_crud import create_new
from os import environ
from dotenv import load_dotenv


load_dotenv()

conn = http.client.HTTPSConnection("control.msg91.com")
logger = logging.getLogger(__name__)


OTP_TEMPLATE_ID = environ.get("OTP_TEMPLATE_ID")
OTP_AUTH_KEY = environ.get("OTP_AUTH_KEY")
headers = {"Content-Type": "application/JSON"}

router = APIRouter()


@router.post("/send")
async def send(name: str, mobile: int):
    try:
        if len(str(mobile)) != 10:
            return response("Invalid mobile number", 0, 422)

        payload = json.dumps({"name": name})
        conn.request(
            "POST",
            f"/api/v5/otp?template_id={OTP_TEMPLATE_ID}&otp_length=6&mobile=91{mobile}&authkey={OTP_AUTH_KEY}&realTimeResponse=1",
            payload,
            headers,
        )

        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    except Exception as exc:
        msg = f"send otp exception {str(exc)}"
        logger.exception(msg)
        return str(exc)


@router.post("/verify")
async def verify(
    full_name: str, otp: int, mobile: int, fcm_token: str, db: Session = Depends(get_db)
):
    try:
        if len(str(mobile)) != 10:
            return response("Invalid mobile number", 0, 422)
        headers = {"authkey": OTP_AUTH_KEY}

        conn.request(
            "GET", f"/api/v5/otp/verify?otp={otp}&mobile=91{mobile}", headers=headers
        )

        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))
        if "error" == result["type"]:
            return response(result["message"], 0, 400)
        user_exist = db.query(Users).filter(Users.mobile == mobile).first()
        user_consent_status = None
        if user_exist:
            if user_exist.email == None:
                email = "dummy@gmail.com"
            else:
                email = user_exist.email
            jwt_token = create_service_token(
                user_exist.full_name, user_exist.mobile, user_exist.id, email
            )
            user_id = user_exist.id
            user_consent_status = (
                db.query(UserConsentIfo.status)
                .filter(UserConsentIfo.user_id == user_id)
                .first()
            )
        else:
            payload = {
                "full_name": full_name,
                "mobile": str(mobile),
                "fcm_token": fcm_token,
            }
            response_obj = await create_new(payload, Users, db, message="")
            user_id = dict(response_obj.data["result"])["id"]
            jwt_token = create_service_token(
                full_name, str(mobile), user_id, "dummy@gmail.com"
            )
        data = {
            "jwt_token": jwt_token,
            "user_id": user_id,
            "user_consent_status": (
                user_consent_status[0] if user_consent_status else False
            ),
        }
        return response(result["message"], 1, 200, data)

    except Exception as exc:
        msg = f"verify otp exception {str(exc)}"
        logger.exception(msg)
        return str(exc)


@router.post("/resend")
async def resend(mobile: int):
    try:
        if len(str(mobile)) != 10:
            return response("Invalid mobile number", 0, 422)
        conn = http.client.HTTPSConnection("control.msg91.com")

        conn.request(
            "GET",
            f"/api/v5/otp/retry?authkey={OTP_AUTH_KEY}&retrytype=1&mobile=91{mobile}",
        )

        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        msg = f"resend otp exception {str(exc)}"
        logger.exception(msg)
        return str(exc)
