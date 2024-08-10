"""User routes"""

import os
import requests
import json
import math
import mimetypes
import os
from io import BytesIO
import logging
from datetime import date, datetime, timedelta
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    Form,
)
from sqlalchemy import func
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
from starlette.responses import StreamingResponse

from base_jwt import JWTBearer
from bunny_net import upload_file, get_file

from db import get_db

from models.user.basic_details import Basic, BasicIn, UserPersonalInfo
from models.user.company_details import Company, CompanyIn, UserCompanyInfo
from models.user.business_details import Business, BusinessIn, UserBusinessInfo
from models.user.school_details import School, SchoolIn, UserSchoolInfo
from models.user.business_types import BusinessType, BusinessTypeIn
from models.user.business_natures import BusinessNature
from models.user.loan_types import LoanType
from models.user.loans import UserLoanInfo
from models.user.loan_applications import LoanApplicationInfo, LoanApplication
from models.user.user_references import UserReferenceIfo, UserReferenceIN
from models.user.tickets import TicketIfo, TicketIN, Status as ticket_Status
from models.user.signup_levels import SignupLevelInfo, SignupLevelIn
from models.user.user_consents import UserConsentIN, UserConsentIfo
from models.user.user_contacts import UserContactIN, UserContactIfo
from models.user.users import Users
from models.user.bank_info import UserBankInfo
from models.user.login_histories import LoginHistory, LoginHistoryIN
from models.user.bank_npci import NPCIBank
from models.user.schools import SchoolName
from models.user.loan_repayments import LoanRepaymentInfo

from util import response, ALLOWED_IMAGE_TYPES, sort_emi_dates
from api_crud import get_all, create_new, get_single, update_single, bulk_create_items
from os import environ
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

background_tasks = BackgroundTasks()

username = environ.get("TRUTH_SCREEN_USERNAME")
CASE_FREE_CLIENT_ID_PROD = environ.get("CASE_FREE_CLIENT_ID_PROD")
CASE_FREE_CLIENT_SECRET_PROD = environ.get("CASE_FREE_CLIENT_SECRET_PROD")
CASE_FREE_SIGNATURE_PROD = environ.get("CASE_FREE_SIGNATURE_PROD")
tenure = environ.get("TENURE")
LOAN_NO = environ.get("LOAN_NO")


def background_signup_level(
    response_data, background_tasks, db, input_field, operation
):
    try:
        response_dict = dict(response_data)

        user_id = response_dict["user_id"]
        if operation == "update":
            background_tasks.add_task(update_signup_level, user_id, input_field, db)
        else:
            input_field["user_id"] = user_id
            background_tasks.add_task(create_signup_level, input_field, db)
    except Exception as exc:
        msg = f"background_signup_level exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


def kyc_background_signup_level(user_id, background_tasks, db, input_field):
    try:
        background_tasks.add_task(update_signup_level, user_id, input_field, db)
    except Exception as exc:
        msg = f"kyc_background_signup_level exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


def encrypt_decrypt_api(headers, endpoint, payload):

    url = "https://www.truthscreen.com/v1/apicall"
    url = f"{url}/{endpoint}"
    result = requests.request("POST", url, headers=headers, data=payload)
    return result.text


async def get_loan_details(user_id: str, db: Session):
    loan_obj = await get_single(
        LoanApplicationInfo,
        db,
        user_id,
        level=True,
        columns=["loan_id", "loan_approved"],
    )
    loan_type = loan_obj.data["result"].loan_id
    loan_approved = loan_obj.data["result"].loan_approved

    loan_type_info = await get_single(LoanType, db, loan_type)
    loan_type_info = dict(loan_type_info.data["result"])
    gateway_fee = loan_type_info["gateway_fee"]
    additional_fee = loan_type_info["additional_fee"]
    processing_fee = loan_type_info["processing_fee"]

    return {
        "tenure": tenure,
        "loan_approved": loan_approved,
        "processing_fee": processing_fee,
        "gateway_fee": gateway_fee,
        "additional_fee": additional_fee,
    }


@router.post("/basic")
async def basic_user_details(
    email: EmailStr,
    full_name: str,
    user: BasicIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        message = "Basic user's details added successfully"
        basic_info = await create_new(user, UserPersonalInfo, db, message)
        if basic_info.data["result"]:
            user_id = basic_info.data["result"].user_id
            update_input = {"email": email, "full_name": full_name}
            background_tasks.add_task(
                update_single, int(user_id), update_input, Users, db, "message"
            )
            input_field = {
                "is_basic_completed": True,
                "provision_status": basic_info.data["result"].profession,
            }
            background_signup_level(
                basic_info.data["result"], background_tasks, db, input_field, "create"
            )

        return basic_info.settings
    except Exception as exc:
        msg = f"get bank name {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.put("/basic")
async def update_basic_user_details(
    user_id: str,
    update_input: Basic,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Basic details updated successful"
    response_obj = await update_single(
        user_id, update_input, UserPersonalInfo, db, message, level=True
    )
    return response_obj.settings


@router.post("/company")
async def user_company_details(
    company_input: CompanyIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User's company details added successfully"

    company_response = await create_new(company_input, UserCompanyInfo, db, message)

    if company_response.data["result"]:
        input_field = {"is_work_completed": True}

        background_signup_level(
            company_response.data["result"], background_tasks, db, input_field, "update"
        )

    return company_response.settings


@router.put("/company")
async def update_user_company_details(
    user_id: str,
    update_input: Company,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Company details updated successful"
    response_obj = await update_single(
        user_id, update_input, UserCompanyInfo, db, message, level=True
    )
    return response_obj.settings


@router.post("/business")
async def user_business_details(
    business_input: BusinessIn,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User's business details added successfully"

    business_response = await create_new(business_input, UserBusinessInfo, db, message)
    if business_response.data["result"]:
        input_field = {"is_work_completed": True}

        background_signup_level(
            business_response.data["result"],
            background_tasks,
            db,
            input_field,
            "update",
        )
    return business_response.settings


@router.put("/business")
async def update_user_business_details(
    user_id: str,
    update_input: Business,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Business details updated successful"
    response_obj = await update_single(
        user_id, update_input, UserBusinessInfo, db, message, level=True
    )
    return response_obj.settings


@router.post("/consent")
async def user_consent(
    business_input: UserConsentIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User consent added successfully"

    response_obj = await create_new(business_input, UserConsentIfo, db, message)
    return response_obj.settings


# @router.post("/signup/level")
async def create_signup_level(
    signup_level_input: SignupLevelIn, db: Session = Depends(get_db)
):

    response_obj = await create_new(signup_level_input, SignupLevelInfo, db, "message")
    return response_obj.settings


@router.get("/signup/level")
async def get_signup_level(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(SignupLevelInfo, db, user_id, level=True)


@router.get("/bank/name")
async def get_bank_name(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    return await get_all(NPCIBank, db, "Bank list", columns=["bank_name"])


@router.get("/school/name")
async def get_school_name(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    return await get_all(SchoolName, db, "School list", columns=["name"])


@router.put("/profile")
async def update_profile(
    user_id: str,
    email: str = None,
    full_name: str = None,
    profile_img: UploadFile = File(None),
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        update_input = {}
        if profile_img:
            if profile_img.content_type not in ALLOWED_IMAGE_TYPES:
                message = "Invalid file type. Only image files are allowed."
                return response(message, 0, 400)

            new_filename = f"{user_id}_profile_{profile_img.filename}"

            temp_file_path = f"/tmp/{new_filename}"

            with open(temp_file_path, "wb") as f:
                content = await profile_img.read()
                f.write(content)

            response_obj = upload_file(temp_file_path, new_filename, m="p_image")
            if response_obj.status_code == 201:
                update_input["image"] = new_filename
        if email:
            update_input["email"] = email
        if full_name:
            update_input["full_name"] = full_name

        message = "Profile updated successful"

        response_obj = await update_single(user_id, update_input, Users, db, message)
        return response_obj.settings
    except Exception as exc:
        msg = f"user loan status exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/profile/image")
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        response_obj = await get_single(Users, db, user_id, columns=["image"])
        profile_image_url = getattr(response_obj.data["result"], "image", None)
        if profile_image_url:
            response_date = get_file(response_obj.data["result"].image, m="p_image")
            if response_date.status_code == 200:
                image_stream = BytesIO(response_date.content)
                return StreamingResponse(image_stream, media_type="image/jpeg")

        return response("Image not found", 0, 400)
    except Exception as exc:
        msg = f"get profile image exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/aadhar/image", tags=["verification"])
async def upload_aadhar_image(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            message = "Invalid file type. Only image files are allowed."
            return response(message, 0, 400)

        new_filename = f"{user_id}_aadhar_{file.filename}"
        temp_file_path = f"/tmp/{new_filename}"

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        response_obj = upload_file(temp_file_path, new_filename, m="aadhar_image")
        if response_obj.status_code == 201:
            update_input = {"aadhar_image": new_filename}
            await update_single(
                user_id, update_input, UserPersonalInfo, db, "message", level=True
            )
            message = "Image uploaded successfully"
            response_obj = response(message, 1, 201, file.filename)
            if response_obj.data["result"]:
                input_field = {"is_aadhar_image_uploaded": True}
                kyc_background_signup_level(user_id, background_tasks, db, input_field)

            return response_obj.settings
        return response("Failed to upload file", 0, response_obj.status_code)
    except Exception as exc:
        msg = f"upload aadhar image exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/aadhar/image", tags=["verification"])
async def get_user_aadhar(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    response_obj = await get_single(
        UserPersonalInfo, db, user_id, level=True, columns=["aadhar_image"]
    )

    aadhar_image_url = getattr(response_obj.data["result"], "aadhar_image", None)
    if aadhar_image_url:
        response_date = get_file(aadhar_image_url, m="aadhar_image")

        if response_date.status_code == 200:
            image_stream = BytesIO(response_date.content)
            return StreamingResponse(image_stream, media_type="image/jpeg")

    return response("Aadhar Image not found", 0, 400)


@router.get("/pan/image", tags=["verification"])
async def get_user_pan(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        response_obj = await get_single(
            UserPersonalInfo, db, user_id, level=True, columns=["pan_image"]
        )

        pan_image_url = getattr(response_obj.data["result"], "pan_image", None)
        if pan_image_url:
            response_date = get_file(pan_image_url, m="pan_image")

            if response_date.status_code == 200:
                image_stream = BytesIO(response_date.content)
                return StreamingResponse(image_stream, media_type="image/jpeg")

        return response("PAN Image not found", 0, 400)
    except Exception as exc:
        msg = f"get pan image exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/profile")
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    return await get_single(Users, db, user_id)


@router.post("/contact")
async def upload_contact(
    user_id: str,
    contact_json: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        if contact_json.content_type != "application/json":
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JSON files are accepted.",
            )
        contact_json_content = await contact_json.read()

        contact_input = UserContactIN(
            user_id=user_id, contact_json=contact_json_content
        )
        message = "User contacts added successfully"

        response_obj = await create_new(contact_input, UserContactIfo, db, message)
        return response_obj.settings
    except Exception as exc:
        msg = f"upload contact exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/basic")
async def get_user_basic_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    response_obj = await get_single(UserPersonalInfo, db, user_id, level=True)
    if response_obj.data["result"]:
        profile_response = await get_single(
            Users, db, user_id, columns=["email", "full_name"]
        )
        user_response = dict(profile_response.data["result"])
        user_response.pop("id", None)

        result = {**dict(response_obj.data["result"]), **user_response}
        response_obj.data["result"] = result
        return response_obj
    return response("Data not found", 0, 400)


@router.get("/company")
async def get_user_company_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(UserCompanyInfo, db, user_id, level=True)


@router.get("/business")
async def get_user_business_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(UserBusinessInfo, db, user_id, level=True)


@router.get("/reference")
async def get_user_reference_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    filters = {"user_id": user_id}
    return await get_all(UserReferenceIfo, db, user_id, filters=filters)


@router.get("/tickets")
async def get_user_ticket_info(
    user_id: str,
    status: ticket_Status,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    filters = {"user_id": user_id, "status": status}
    return await get_all(TicketIfo, db, user_id, filters=filters)


@router.get("/school")
async def get_user_school_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(UserSchoolInfo, db, user_id, level=True)


# @router.put("/signup/level")
async def update_signup_level(
    user_id: str, signup_level_input: SignupLevelIn, db: Session = Depends(get_db)
):
    response_obj = await update_single(
        user_id, signup_level_input, SignupLevelInfo, db, "message", level=True
    )
    return response_obj.settings


@router.get("/registration/type")
async def registration_type(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        columns = ["name", "id"]
        message = "Loan type retried successfully"

        response_obj = await get_all(BusinessType, db, message, columns)
        result = {item["id"]: item["name"] for item in response_obj.data["result"]}
        response_obj.data["result"] = result
        return response_obj
    except Exception as exc:
        msg = f"get registration type exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/business/nature")
async def business_nature(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        columns = ["name", "id"]
        message = "Loan type retried successfully"

        response_obj = await get_all(BusinessNature, db, message, columns)
        result = {item["id"]: item["name"] for item in response_obj.data["result"]}
        response_obj.data["result"] = result
        return response_obj
    except Exception as exc:
        msg = f"kyc_background_signup_level exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/loan/type")
async def loan_type(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Loan type retried successfully"
    return await get_all(LoanType, db, message)


@router.get("/loan/status")
async def user_loan_status(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    return await get_single(
        UserLoanInfo, db, user_id, level=True, columns=["loan_status"]
    )


@router.post("/select/loan/type")
async def select_loan_type(
    loan_id: int,
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_input = {"user_id": user_id, "loan_id": loan_id}
        response_obj = await get_single(LoanApplicationInfo, db, user_id, level=True)
        if response_obj.data["result"]:
            message = "Loan type updated successfully"
            response_obj = await update_single(
                response_obj.data["result"].user_id,
                loan_input,
                LoanApplicationInfo,
                db,
                message,
                level=True,
            )

        else:
            message = "Loan type added successfully"

            response_obj = await create_new(
                loan_input, LoanApplicationInfo, db, message
            )
            if response_obj.data["result"]:
                input_user_loan = {
                    "loan_application_id": response_obj.data["result"].id,
                    "user_id": user_id,
                }
                background_tasks.add_task(
                    create_new, input_user_loan, UserLoanInfo, db, "message"
                )
        return response_obj.settings
    except Exception as exc:
        msg = f"select loan type exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/school")
async def user_school_details(
    user: SchoolIn,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "School details added successfully"

    school_response = await create_new(user, UserSchoolInfo, db, message)
    if school_response.data["result"]:
        input_field = {"is_work_completed": True}

        background_signup_level(
            school_response.data["result"], background_tasks, db, input_field, "update"
        )
    return school_response.settings


@router.put("/school")
async def update_user_school_details(
    user_id: str,
    update_input: School,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "School details updated successful"
    response_obj = await update_single(
        user_id, update_input, UserSchoolInfo, db, message, level=True
    )
    return response_obj.settings


@router.post("/reference")
async def user_reference(
    reference_input: UserReferenceIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User reference added successfully"

    response_obj = await create_new(reference_input, UserReferenceIfo, db, message)
    return response_obj.settings


@router.post("/ticket")
async def raise_ticket(
    ticket_input: TicketIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User ticket raised successfully"

    response_obj = await create_new(ticket_input, TicketIfo, db, message)
    return response_obj.settings


@router.post("/login/history")
async def user_login_history(
    login_history: LoginHistoryIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User login history added successfully"

    response_obj = await create_new(login_history, LoginHistory, db, message)
    return response_obj.settings


@router.get("/transaction/history")
async def user_transaction_history(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_response = await get_single(
            UserLoanInfo, db, user_id, level=True, columns=["id"]
        )
        filters = {"is_paid": 1, "loan_id": loan_response.data["result"].id}
        response_obj = await get_all(
            LoanRepaymentInfo, db, "Transaction histories", filters=filters
        )
        return response_obj

    except Exception as exc:
        msg = f"user emi breakup exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/emi/breakup")
async def get_emi_breakup(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_id_info = await get_single(
            UserLoanInfo, db, user_id, level=True, columns=["id"]
        )
        loan_id = loan_id_info.data["result"].id
        filters = {"is_paid": 0, "loan_id": loan_id}
        emi_response = await get_all(
            LoanRepaymentInfo, db, "Found data", ["date", "amount"], filters=filters
        )

        if emi_response.data["result"]:

            return emi_response
        else:
            message = "User loan not found"
            return response(message, 0, 404)

    except Exception as exc:
        msg = f"user emi breakup exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/loan/overview")
async def get_loan_overview(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:

        loan_application_info = await get_single(
            LoanApplicationInfo, db, user_id, level=True, columns=["loan_required"]
        )

        loans_info = await get_single(
            UserLoanInfo, db, user_id, level=True, columns=["loan_no"]
        )
        loan_app_info = dict(loan_application_info.data["result"])

        query = select(
            LoanRepaymentInfo.date,
            LoanRepaymentInfo.amount,
        ).where(LoanRepaymentInfo.loan_id == loans_info.data["result"].id)
        result = db.execute(query)
        results = result.fetchone()

        message = "No loan information found"
        if results is None:
            return response(message, 0, 404)
        if results:
            # Extract the required information
            emi_value = results[1]
            loan_id = loans_info.data["result"].loan_no
            loan_required = loan_app_info["loan_required"]

            # Construct the response object
            response_obj = {
                "loan_required": loan_required,
                "loan_id": loan_id,
                "emi_date": "2nd Every Month",
                "emi_value": emi_value,
            }

            return response("Found loan data", 1, 200, data=response_obj)
        return response(message, 0, 404)

    except Exception as exc:
        msg = f"loan overview exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/loan/application/info")
async def get_loan_application_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    loan_details = await get_loan_details(user_id, db)
    message = "Loan application details"

    return response(message, 1, 200, loan_details)


@router.post("/loan/application")
async def user_loan_application(
    loan_amount: int,
    user_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_details = await get_loan_details(user_id, db)

        total_loan_amount = (
            loan_amount
            + loan_details["processing_fee"]
            + loan_details["gateway_fee"]
            + loan_details["additional_fee"]
        )
        loan_input = {
            "loan_required": total_loan_amount,
        }
        background_tasks.add_task(
            update_single,
            user_id,
            loan_input,
            LoanApplicationInfo,
            db,
            "message",
            level=True,
        )

        monthly_emi = math.ceil(total_loan_amount / float(tenure))
        current_date = datetime.now()

        if current_date.day > 2:
            # Move to the next month first
            start_date = (
                current_date.replace(day=1) + relativedelta(months=1)
            ).replace(day=2)
        else:
            start_date = current_date.replace(day=2)

        emi_dates = {}
        for i in range(int(tenure)):
            emi_date = start_date + relativedelta(months=i)
            emi_dates[emi_date.strftime("%d-%b-%Y")] = monthly_emi

        sorted_emi_dates = sort_emi_dates(emi_dates)

        emi_dates_list = []
        for i in range(int(9)):
            emi_date = start_date + relativedelta(months=i)
            emi_dates_list.append(emi_date.strftime("%Y-%m-%d"))
            emi_date = emi_date + relativedelta(months=1)

        user_loan_info_id = await get_single(
            UserLoanInfo, db, user_id, level=True, columns=["id"]
        )
        lon_info_id = dict(user_loan_info_id)["data"]["result"].id

        max_loan_no = (
            db.query(func.max(UserLoanInfo.loan_no))
            .filter(UserLoanInfo.loan_no.like(f"{LOAN_NO[:4]}%"))
            .scalar()
        )
        if max_loan_no:
            loan_no = max_loan_no
            new_loan_no = loan_no[:-5] + f"{int(loan_no[-5:]) + 1:05}"
        else:
            new_loan_no = LOAN_NO
        update_input = {"loan_no": new_loan_no}
        background_tasks.add_task(
            update_single,
            user_id,
            update_input,
            UserLoanInfo,
            db,
            "message",
            level=True,
        )

        input_model = {
            "loan_id": lon_info_id,
            "amount": monthly_emi,
            "date": emi_dates_list,
        }
        background_tasks.add_task(bulk_create_items, input_model, LoanRepaymentInfo, db)

        message = "EMI calculated successfully"
        data = {
            "tenure": f"{tenure} Months",
            "total_loan_amount": total_loan_amount,
            "loan_approved": loan_details["loan_approved"],
            "processing_fee": loan_details["processing_fee"],
            "gateway_fee": loan_details["gateway_fee"],
            "additional_fee": loan_details["additional_fee"],
            "monthly emi": monthly_emi,
            "emi_dates": sorted_emi_dates,
            "emi_repay_date": list(sorted_emi_dates.keys()),
        }

        response_obj = response(message, 1, 200, data)
        return response_obj
    except Exception as exc:
        msg = f"select loan type exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/bank/statement", tags=["verification"])
async def get_bank_statement(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        pdf_response = await get_single(
            LoanApplicationInfo, db, user_id, level=True, columns=["statement"]
        )

        pdf_response_url = getattr(pdf_response.data["result"], "statement", None)
        if pdf_response_url:
            response_date = get_file(pdf_response_url, m="bank_st")

            if response_date.status_code == 200:
                image_stream = BytesIO(response_date.content)
                return StreamingResponse(image_stream, media_type="application/pdf")

        return response("Bank statement not found", 0, 400)
    except Exception as exc:
        msg = f"get bank statement exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/upload/bank/statement", tags=["verification"])
async def upload_bank_statement(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        if file.content_type != "application/pdf":
            message = "Invalid file type. Only PDF files are allowed."
            return response(message, 0, 400)

        new_filename = f"{user_id}_bank_statement_{file.filename}"
        temp_file_path = f"/tmp/{new_filename}"

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        response_obj = upload_file(temp_file_path, new_filename, m="bank_st")
        if response_obj.status_code == 201:

            update_input = {"statement": new_filename}
            message = "Bank statement added successfully"
            response_obj = await update_single(
                user_id, update_input, LoanApplicationInfo, db, message, level=True
            )

            if response_obj.data["result"]:
                input_field = {"is_document_completed": True}
                kyc_background_signup_level(user_id, background_tasks, db, input_field)

            return response_obj.settings
        return response("Failed to upload file", 0, response_obj.status_code)
    except Exception as exc:
        msg = f"upload bank statement exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/upcoming/emi")
def get_upcoming_and_bounced_emi(
    user_id: int,
    session: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_application = session.execute(
            select(UserLoanInfo.id).where(UserLoanInfo.user_id == user_id)
        ).first()
        if not loan_application:
            raise HTTPException(status_code=404, detail="Loan application not found")

        # Get the upcoming EMI
        upcoming_repayment = session.execute(
            select(LoanRepaymentInfo.date, LoanRepaymentInfo.amount)
            .where(
                LoanRepaymentInfo.loan_id == loan_application.id,
                LoanRepaymentInfo.status == "pending",
                LoanRepaymentInfo.is_paid == False,
                LoanRepaymentInfo.date > date.today(),
            )
            .order_by(LoanRepaymentInfo.date)
        ).first()
        last_40_days_start = upcoming_repayment.date - timedelta(days=40)

        bounced_emis = session.execute(
            select(LoanRepaymentInfo.date, LoanRepaymentInfo.amount)
            .where(
                LoanRepaymentInfo.loan_id == loan_application.id,
                LoanRepaymentInfo.status == "pending",
                LoanRepaymentInfo.is_paid == False,
                LoanRepaymentInfo.date.between(
                    last_40_days_start, upcoming_repayment.date
                ),
            )
            .order_by(LoanRepaymentInfo.date)
        ).first()
        emi = {
            "upcoming": {
                "date": upcoming_repayment.date,
                "amount": upcoming_repayment.amount,
            }
        }
        if bounced_emis:
            if upcoming_repayment.date != bounced_emis.date:
                emi["bounce"] = {
                    "date": bounced_emis.date,
                    "amount": bounced_emis.amount,
                }

        return response("Found upcoming emi", 1, 200, emi)
    except Exception as exc:
        msg = f"get upcoming emis exception {str(exc)}"
        logger.exception(msg)
        response(str(exc), 0, 404)


@router.post("/verify/bank", tags=["verification"])
async def verify_Bank(
    user_id: str,
    account_number: str,
    ifsc_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        url = "https://api.cashfree.com/verification/bank-account/sync"

        payload = {"bank_account": account_number, "ifsc": ifsc_code}

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-client-id": CASE_FREE_CLIENT_ID_PROD,
            "x-client-secret": CASE_FREE_CLIENT_SECRET_PROD,
            "X-Cf-Signature": CASE_FREE_SIGNATURE_PROD,
        }

        bank_response = requests.post(url, json=payload, headers=headers)
        bank_obj = json.loads(bank_response.text)
        if bank_response.status_code == 200:
            if bank_obj["account_status"] == "VALID":
                bank_input = {
                    "bank_name": bank_obj["bank_name"],
                    "account_number": account_number,
                    "ifsc_code": ifsc_code,
                    "user_id": user_id,
                    "account_holder_name": bank_obj["name_at_bank"],
                }
                input_field = {"is_bank_verified": True}
                kyc_background_signup_level(user_id, background_tasks, db, input_field)
                background_tasks.add_task(
                    create_new, bank_input, UserBankInfo, db, "message"
                )
                message = "Bank verification successful"
                response_obj = response(message, 1, 200, data=bank_obj)
                return response_obj.settings
            return response(bank_obj["account_status_code"], 0, 400)

        return response(
            f'{bank_obj["code"]} {bank_obj["message"]}', 0, bank_response.status_code
        )

    except Exception as exc:
        msg = f"verify bank exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/bank/statement", tags=["verification"])
async def get_bank_statement(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    # Fetch the pdf record
    try:
        columns = ["statement"]
        pdf_response = await get_single(
            LoanApplicationInfo, db, user_id, level=True, columns=columns
        )

        if pdf_response.data["result"]:
            # Decode Base64 to binary data
            file_path = pdf_response.data["result"].statement
            if os.path.exists(file_path):
                return response("Found bank statement", 1, 200, pdf_response)

        return response("Bank statement not found", 0, 404)
    except Exception as exc:
        msg = f"get bank statement exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/pan/image", tags=["verification"])
async def upload_pan_image(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            message = "Invalid file type. Only image files are allowed."
            return response(message, 0, 400)

        new_filename = f"{user_id}_pan_{file.filename}"
        temp_file_path = f"/tmp/{new_filename}"

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        response_obj = upload_file(temp_file_path, new_filename, m="pan_image")
        if response_obj.status_code == 201:

            update_input = {"pan_image": new_filename}
            await update_single(
                user_id, update_input, UserPersonalInfo, db, "message", level=True
            )
            message = "Image uploaded successfully"
            response_obj = response(message, 1, 201, file.filename)
            if response_obj.data["result"]:
                input_field = {"is_pan_image_uploaded": True}
                kyc_background_signup_level(user_id, background_tasks, db, input_field)

            return response_obj.settings
        return response("Failed to upload file", 0, response_obj.status_code)
    except Exception as exc:
        msg = f"upload pan image exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/kyc/details", tags=["verification"])
async def get_kyc_details(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        kyc_result = await get_single(
            UserPersonalInfo,
            db,
            user_id,
            level=True,
            columns=["pan_image", "pan", "aadhar"],
        )
        if kyc_result.data["result"].pan or kyc_result.data["result"].aadhar:
            data = {
                "pan": kyc_result.data["result"].pan,
                "adhaar": kyc_result.data["result"].aadhar,
            }
            file_path = kyc_result.data["result"].pan_image
            if file_path and os.path.exists(file_path):
                data["pan_img_path"] = file_path
            message = "Kyc details found"

            return response(message, 1, 200, data)

        message = "No KYC details found for the given user id"
        return response(message, 0, 404)
    except Exception as exc:
        msg = f"get kyc details exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/verify/pan/number", tags=["verification"])
async def verify_pan_number(
    background_tasks: BackgroundTasks,
    pan_number: str,
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    try:
        url = "https://www.truthscreen.com/v1/apicall/nid/panComprehensive"

        headers = {"username": username, "content-type": "application/json"}

        payload = json.dumps(
            {"PanNumber": pan_number, "docType": 523, "transId": "Alpha-123"}
        )

        encrypt_payload = encrypt_decrypt_api(headers, "encrypt", payload)
        payload = json.dumps({"requestData": encrypt_payload})

        message = "PAN verification successful"
        result = requests.post(url, data=payload, headers=headers)
        decrypt_response = encrypt_decrypt_api(headers, "decrypt", result.text)

        decrypt_response = json.loads(decrypt_response)
        if decrypt_response["status"] == 1:
            # return json.loads(decrypt_response)

            pan_response = response(message, 1, 200, decrypt_response)
            if pan_response.data["result"]:
                update_input = {"pan": pan_number}
                await update_single(
                    user_id, update_input, UserPersonalInfo, db, "message", level=True
                )

                input_field = {"is_pan_verified": True}
                kyc_background_signup_level(user_id, background_tasks, db, input_field)
            return pan_response.settings
        return response(
            decrypt_response["msg"], 0, decrypt_response["status"], decrypt_response
        )

    except Exception as exc:
        msg = f"pan verify exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/verify/aadhaar/number", tags=["verification"])
async def verify_aadhaar_number(
    aadhaar_number: str, token_data: BaseModel = Depends(JWTBearer())
):
    try:
        aadhaar_number = aadhaar_number.replace(" ", "")

        url = "https://www.truthscreen.com/v1/apicall/nid/aadhar_get_otp"

        headers = {"username": username, "content-type": "application/json"}

        payload = json.dumps(
            {"aadharNo": aadhaar_number, "docType": 211, "transId": "beta-12321"}
        )

        encrypt_payload = encrypt_decrypt_api(headers, "encrypt", payload)
        payload = json.dumps({"requestData": encrypt_payload})

        result = requests.post(url, data=payload, headers=headers)
        decrypt_response = encrypt_decrypt_api(headers, "decrypt", result.text)
        message = "Otp send to linked mobile number"
        decrypt_response = json.loads(decrypt_response)

        if decrypt_response["status"] == 1:
            return response(message, 1, 200, decrypt_response)
        return response(
            decrypt_response["msg"], 0, decrypt_response["status"], decrypt_response
        )
    except Exception as exc:
        msg = f"send aadhar otp exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/verify/aadhaar/otp", tags=["verification"])
async def verify_aadhaar_otp(
    otp: int,
    TransID: str,
    user_id: str,
    aadhaar_number: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        url = "https://www.truthscreen.com/v1/apicall/nid/aadhar_submit_otp"

        headers = {"username": username, "content-type": "application/json"}

        payload = json.dumps(
            {
                "transId": TransID,
                "otp": otp,
            }
        )
        encrypt_payload = encrypt_decrypt_api(headers, "encrypt", payload)
        payload = json.dumps({"requestData": encrypt_payload})

        result = requests.post(url, data=payload, headers=headers)
        decrypt_response = encrypt_decrypt_api(headers, "decrypt", result.text)
        decrypt_response = json.loads(decrypt_response)
        if decrypt_response["status"] == 1:

            message = "Adhaar verified successful"

            # if decrypt_response:
            input_field = {"is_adhaar_verified": True}

            kyc_background_signup_level(user_id, background_tasks, db, input_field)
            update_input = {"aadhar": aadhaar_number}
            await update_single(
                user_id, update_input, UserPersonalInfo, db, "message", level=True
            )

            return response(message, 1, 200, decrypt_response)

        return response(
            decrypt_response["msg"], 0, decrypt_response["status"], decrypt_response
        )
    except Exception as exc:
        msg = f"verify aadhar otp exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/liveness", tags=["verification"])
async def verify_liveness(
    file_img: UploadFile = File(...),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        liveness_token_url = "https://www.truthscreen.com/liveness/token"
        boundary = ""
        transID = "12345"
        docType = "366"
        payload = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="transID"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{transID}\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="docType"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{docType}\r\n"
            f"--{boundary}--\r\n"
        )

        headers_liveness = {
            "username": username,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        file = []
        result = requests.post(
            liveness_token_url,
            headers=headers_liveness,
            data=payload.encode("utf-8"),
            files=file,
        )
        headers_encrypt = {"username": username, "content-type": "application/json"}
        decrypt_response = encrypt_decrypt_api(headers_encrypt, "decrypt", result.text)

        decrypt_response = json.loads(decrypt_response)
        if decrypt_response["status"] != 1:
            return decrypt_response["msg"]

        secretToken = decrypt_response["msg"]["secretToken"]
        tsTransID = decrypt_response["msg"]["tsTransID"]

        boundary = ""
        url = "https://www.truthscreen.com/liveness/request"

        boundary = ""
        file_name = file_img.filename

        file_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        payload = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="tsTransID"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{tsTransID}\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="secretToken"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{secretToken}\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="docType"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{docType}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
            f"Content-Type: {file_type}\r\n\r\n"
        )

        # Read the file content and append it to the payload
        file_content = await file_img.read()

        payload += file_content.decode("latin-1") + f"\r\n--{boundary}\r\n"
        payload += (
            'Content-Disposition: form-data; name="username"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            f"{username}\r\n"
            f"--{boundary}--\r\n"
        )

        result = requests.post(
            url, headers=headers_liveness, data=payload.encode("latin-1")
        )

        decrypt_response = encrypt_decrypt_api(headers_encrypt, "decrypt", result.text)

        decrypt_response = json.loads(decrypt_response)
        if decrypt_response["result"] != "Real":
            return response(decrypt_response["result"], 0, 400, decrypt_response)

        return response(decrypt_response["result"], 1, 200, decrypt_response)
    except Exception as exc:
        msg = f"liveness verification exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/credit", tags=["verification"])
async def credit_otp(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        basic_info = await get_single(UserPersonalInfo, db, user_id, level=True)
        user_info = await get_single(Users, db, user_id)
        basic_details = dict(basic_info.data["result"])
        user_details = dict(user_info.data["result"])
        headers = {"username": username, "content-type": "application/json"}

        full_name = user_details["full_name"].split(" ")
        otp_generation_payload = json.dumps(
            {
                "transID": "123",
                "docType": 45,
                "email": user_details["email"],
                "mobileNumber": user_details["mobile"],
                "firstName": full_name[0],
                "lastName": full_name[1],
                "dob": str(basic_details["dob"]),
                "gender": str(basic_details["gender"])[7:],
                "address": "Hyderabad",
                "city": "Hyderabad",
                "state": "Telangana",
                "pinCode": "500016",
                "pan": basic_details["pan"],
            }
        )

        encrypt_payload = encrypt_decrypt_api(
            headers, "encrypt", otp_generation_payload
        )
        otp_generation_url = (
            "https://www.truthscreen.com/CreditReportVerificationApi/requestSend"
        )
        payload = json.dumps({"requestData": encrypt_payload})

        response_obj = requests.post(otp_generation_url, data=payload, headers=headers)
        decrypt_payload = encrypt_decrypt_api(headers, "decrypt", response_obj.text)
        return json.loads(decrypt_payload)
    except Exception as exc:
        msg = f"create otp for credit report exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/credit/otp/verification", tags=["verification"])
async def credit_otp_verification(
    user_id: int,
    otp: str,
    tsTransID: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        verify_otp_url = (
            "https://www.truthscreen.com/CreditReportVerificationApi/verifyOtp"
        )

        headers = {"username": username, "content-type": "application/json"}

        otp_payload = json.dumps(
            {
                "transID": "Beta-123",
                "docType": 45,
                "tsTransID": tsTransID,
                "otp": otp,
                "verifyotp": 1,
                "resendotp": 0,
            }
        )

        encrypt_payload = encrypt_decrypt_api(headers, "encrypt", otp_payload)
        payload = json.dumps({"requestData": encrypt_payload})

        result = requests.post(verify_otp_url, data=payload, headers=headers)
        decrypt_response = encrypt_decrypt_api(headers, "decrypt", result.text)

        decrypt_response = json.loads(decrypt_response)
        if decrypt_response["status"] == 1:
            update_input = {"loan_status": "under_review"}
            background_tasks.add_task(
                update_single,
                user_id,
                update_input,
                UserLoanInfo,
                db,
                "message",
                level=True,
            )
            return response(
                "Credit score report generated", 1, 200, decrypt_response["msg"]["data"]
            )
        return response("No Record Found!.", 0, decrypt_response["status"])

    except Exception as exc:
        msg = f"verify credit otp exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)
