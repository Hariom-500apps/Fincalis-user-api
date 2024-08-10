"""Subscription Authorization"""

import requests
import json
import logging

from os import environ
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, BackgroundTasks



from dotenv import load_dotenv
from util import response
from api_crud import get_single,update_single
from base_jwt import JWTBearer
from db import get_db
from models.user.loan_types import LoanType
from models.user.bank_info import UserBankInfo
from models.user.users import Users
from models.user.loan_applications import LoanApplicationInfo
from models.user.loans import UserLoanInfo
from models.user.loan_repayments import LoanRepaymentInfo



sub_client_id = environ.get("SUB_TEST_CLIENT_ID")
sub_client_secret = environ.get("SUB_TEST_CLIENT_SECRET")
maxCycles = environ.get("TENURE")


router = APIRouter()

load_dotenv()

logger = logging.getLogger(__name__)
background_tasks = BackgroundTasks()



def default_expires_on():
    return (datetime.now() + timedelta(days=10 * 30)).strftime("%Y-%m-%d %H:%M:%S")


def set_first_charge_date():
    today = date.today()
    if today.day < 2:
        v = date(today.year, today.month, 4)
    else:
        next_month = today + relativedelta(months=1)
        v = date(next_month.year, next_month.month, 2)
    return v


@router.get("/pre/info")
async def get_pre_subscription_info(user_id: str, db: Session = Depends(get_db),token_data: BaseModel = Depends(JWTBearer()),):
    try:
        user_account = await get_single(UserBankInfo, db, user_id, level=True)
        user_profile = await get_single(Users, db, user_id)
        user_profile_obj = dict(user_profile.data["result"])
        user_account_obj = dict(user_account.data["result"])
        result = {
            "Name": user_profile_obj["full_name"],
            "Phone": user_profile_obj["mobile"],
            "Email": user_profile_obj["email"],
            "accountNumber": user_account_obj["account_number"],
            "bankName": user_account_obj["bank_name"],
            "accountHolderName": user_account_obj["account_holder_name"],
            "ifsc": user_account_obj["ifsc_code"],
        }
        return response("Found details", 1, 200, result)
    except Exception as exc:
        msg = f"get pre subscription info exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/plan/subscription")
async def create_subscription_with_plan(
    user_id: str,
    name: str,
    mobile: str,
    email: str,
    account_number: str,
    account_holder_name: str,
    ifsc_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:

        statement = (
            select(
                LoanType.name,
                LoanApplicationInfo.loan_required,
                UserLoanInfo.id,
                UserLoanInfo.loan_no,
            )
            .join(LoanApplicationInfo, LoanType.id == LoanApplicationInfo.loan_id)
            .join(
                UserLoanInfo, UserLoanInfo.loan_application_id == LoanApplicationInfo.id
            )
            .where(LoanApplicationInfo.user_id == user_id)
        )

        loan_type = db.execute(statement).first()
        query = select(
            LoanRepaymentInfo.amount,
        ).where(LoanRepaymentInfo.loan_id == loan_type[2])
        result = db.execute(query)
        emi_amount = result.fetchone()

        recurringAmount = int(emi_amount[0])

        payload = {
            "subscriptionId": loan_type[3],
            "planInfo": {
                "planName": f"plan_{loan_type[0]}_{user_id}",
                "type": "PERIODIC",
                "maxCycles": maxCycles,
                "maxAmount": loan_type[1],
                "recurringAmount": recurringAmount,
                "intervalType": "month",
                "intervals": 1,
            },
            "customerName": name,
            "customerPhone": mobile,
            "customerEmail": email,
            "tpvEnabled": True,
            "payerAccountDetails": {
                "accountNumber": account_number,
                "accountHolderName": account_holder_name,
                "accountType": "SAVINGS",
                "ifsc": ifsc_code,
            },
            "returnUrl": "www.google.com",
            "authAmount": 1,
            "expiresOn": str(default_expires_on()),
            "firstChargeDate": str(set_first_charge_date()),
            "linkExpiry": 15,
            "notificationChannels": [
                "EMAIL",
                "SMS",
            ],
        }

        url = "https://test.cashfree.com/api/v2/subscriptions/nonSeamless/subscription"

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-Client-Id": sub_client_id,
            "X-Client-Secret": sub_client_secret,
        }
        response_data = requests.post(url, data=json.dumps(payload), headers=headers)
        response_obj = json.loads(response_data.text)
        if response_obj["status"] == 200:
            update_input = {
                    "loan_status" :"disbursed_pending"
                }
            background_tasks.add_task(update_single, user_id,update_input,UserLoanInfo,db,"message", level=True)
            return response(response_obj["message"], 1, 201, response_obj["data"])

        return response(response_obj["message"], 0, 400)

    except Exception as exc:
        msg = f"create subscription plan exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)
