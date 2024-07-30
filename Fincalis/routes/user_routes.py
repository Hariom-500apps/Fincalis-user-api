"""User routes"""

import os
import requests
import json
import math
import mimetypes
import shutil
import logging
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    Form,
)


from Fincalis.models.user.personal_info import Basic, BasicIn, UserPersonalInfo
from Fincalis.models.user.company_info import Company, CompanyIn, UserCompanyInfo
from Fincalis.models.user.business_info import Business, BusinessIn, UserBusinessInfo
from Fincalis.models.user.school_info import School, SchoolIn, UserSchoolInfo
from Fincalis.models.user.business_types import BusinessType
from Fincalis.models.user.business_natures import BusinessNature
from Fincalis.models.user.loan_type import LoanType
from Fincalis.models.user.user_loan import UserLoanInfo
from Fincalis.models.user.loan_application import LoanInfo, Loan
from Fincalis.models.user.user_reference import UserReferenceIfo, UserReferenceIN
from Fincalis.models.user.ticket import TicketIfo, TicketIN, Status as ticket_Status
from Fincalis.models.user.signup_level import SignupLevelInfo, SignupLevelIn
from Fincalis.models.user.user_consent import UserConsentIN, UserConsentIfo
from Fincalis.models.user.user_contact import UserContactIN, UserContactIfo
from Fincalis.models.user.bank_info import UserBankInfo
from Fincalis.models.user.users import Users, User

from Fincalis.util import response, ALLOWED_IMAGE_TYPES, sort_emi_dates
from Fincalis.base_jwt import JWTBearer
from Fincalis.db import get_db
from Fincalis.api_crud import get_all, create_new, get_single, update_single
from os import environ
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# Define the directory where files will be saved
UPLOAD_DIRECTORY = "Upload"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

background_tasks = BackgroundTasks()

username = environ.get("TRUTH_SCREEN_USERNAME")

CASE_FREE_CLIENT_ID_PROD = environ.get("CASE_FREE_CLIENT_ID_PROD")
CASE_FREE_CLIENT_SECRET_PROD = environ.get("CASE_FREE_CLIENT_SECRET_PROD")
CASE_FREE_SIGNATURE_PROD = environ.get("CASE_FREE_SIGNATURE_PROD")
tenure = 9

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


def kyc_background_signup_level(user_id, background_tasks, db, input_field):
    try:
        background_tasks.add_task(update_signup_level, user_id, input_field, db)
    except Exception as exc:
        msg = f"kyc_background_signup_level exception {str(exc)}"
        logger.exception(msg)


def encrypt_decrypt_api(headers, endpoint, payload):
    try:
        url = "https://www.truthscreen.com/v1/apicall"
        url = f"{url}/{endpoint}"
        result = requests.request("POST", url, headers=headers, data=payload)
        return result.text
    except Exception as exc:
        msg = f"kyc_background_signup_level exception {str(exc)}"
        logger.exception(msg)


async def get_loan_details(user_id: str, db: Session):
    loan_obj = await get_single(LoanInfo, db, user_id, level=True, columns=["loan_id", "loan_approved"])
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


@router.post("/basic", tags=["user"])
async def basic_user_details(
    user: BasicIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "Basic user's details added successfully"
    basic_info = await create_new(user, UserPersonalInfo, db, message)

    if basic_info.data["result"]:
        input_field = {
            "is_basic_completed": True,
            "provision_status": basic_info.data["result"].profession,
        }
        background_signup_level(
            basic_info.data["result"], background_tasks, db, input_field, "create"
        )

    return basic_info


@router.put("/basic", tags=["user"])
async def update_basic_user_details(
    user_id: str,
    update_input: Basic,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Basic details updated successful"

    return await update_single(
        user_id, update_input, UserPersonalInfo, db, message, level=True
    )


@router.post("/company", tags=["user"])
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

    return company_response


@router.put("/company", tags=["user"])
async def update_user_company_details(
    user_id: str,
    update_input: Company,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Company details updated successful"

    return await update_single(
        user_id, update_input, UserCompanyInfo, db, message, level=True
    )


@router.post("/business", tags=["user"])
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
    return business_response


@router.put("/business", tags=["user"])
async def update_user_business_details(
    user_id: str,
    update_input: Business,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Business details updated successful"

    return await update_single(
        user_id, update_input, UserBusinessInfo, db, message, level=True
    )


@router.post("/consent", tags=["user"])
async def user_consent(
    business_input: UserConsentIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User consent added successfully"

    return await create_new(business_input, UserConsentIfo, db, message)


# @router.post("/signup/level")
async def create_signup_level(
    signup_level_input: SignupLevelIn, db: Session = Depends(get_db)
):

    return await create_new(signup_level_input, SignupLevelInfo, db, "message")


@router.get("/signup/level", tags=["user"])
async def get_signup_level(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(SignupLevelInfo, db, user_id, level=True)


@router.put("/profile/image")
async def upload_profile_image(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:

        if file.content_type not in ALLOWED_IMAGE_TYPES:
            message = "Invalid file type. Only image files are allowed."
            return response(message, 0, 400)

        new_filename = f"{user_id}_profile_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_input = {"image": file_path}
        message = "Profile image updated successful"

        return await update_single(user_id, update_input, Users, db, message)
    
    except Exception as exc:

        msg = f"user loan status exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 404)


@router.get("/profile")
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    return await get_single(Users, db, user_id)


@router.put("/profile")
async def update_user_profile(
    user_id: str,
    user_input: User,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "Users details updated successful"

    return await update_single(user_id, user_input, Users, db, message)

@router.post("/contact", tags=["user"])
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

        return await create_new(contact_input, UserContactIfo, db, message)
    except Exception as exc:
        msg = f"user loan status exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.get("/basic", tags=["user"])
async def get_user_basic_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(UserPersonalInfo, db, user_id, level=True)


@router.get("/company", tags=["user"])
async def get_user_company_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(UserCompanyInfo, db, user_id, level=True)


@router.get("/business", tags=["user"])
async def get_user_business_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    return await get_single(UserBusinessInfo, db, user_id, level=True)


@router.get("/reference", tags=["user"])
async def get_user_reference_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    filters = {"user_id": user_id}
    return await get_all(UserReferenceIfo, db, user_id, filters=filters)


@router.get("/tickets", tags=["user"])
async def get_user_ticket_info(
    user_id: str,
    status: ticket_Status,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    filters = {"user_id": user_id, "status": status}
    return await get_all(TicketIfo, db, user_id, filters=filters)


@router.get("/school", tags=["user"])
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
    return await update_single(
        user_id, signup_level_input, SignupLevelInfo, db, "message", level=True
    )


@router.get("/registration/type", tags=["user"])
async def registration_type(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    columns = ["name", "id"]
    message = "Loan type retried successfully"

    return await get_all(BusinessType, db, message, columns)


@router.get("/business/nature", tags=["user"])
async def business_nature(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    columns = ["name", "id"]
    message = "Loan type retried successfully"

    return await get_all(BusinessNature, db, message, columns)


@router.get("/loan/type", tags=["user"])
async def loan_type(
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    columns = ["name"]
    message = "Loan type retried successfully"

    return await get_all(LoanType, db, message, columns)


@router.get("/loan/status", tags=["user"])
async def user_loan_status(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
    loan_info_id: bool = False,
):
    try:
        field = UserLoanInfo.id if loan_info_id else UserLoanInfo.loan_status
        result = (
            db.query(field)
            .join(LoanInfo, LoanInfo.id == UserLoanInfo.loan_application)
            .filter(LoanInfo.user_id == user_id)
            .first()
        )
        if result is None:
            message = "Loan information not found"
            return response(message, 0, 404)
        data = {"loan_status": result[0]}
        message = "Loan status fetch successful"
        return response(message, 1, 200, data=data)
    except Exception as exc:
        msg = f"user loan status exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/select/loan/type", tags=["user"])
async def select_loan_type(
    loan_input: Loan,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        response_obj = await get_single(LoanInfo, db, loan_input.user_id, level=True)
        if response_obj.data["result"]:
            message = "Loan type updated successfully"
            response_obj = await update_single(
                response_obj.data["result"].user_id,
                loan_input,
                LoanInfo,
                db,
                message,
                level=True,
            )
        else:

            message = "Loan type added successfully"

            response_obj = await create_new(loan_input, LoanInfo, db, message)
            if response_obj.data["result"]:
                input_user_loan = {"loan_application": response_obj.data["result"].id}
                background_tasks.add_task(
                    create_new, input_user_loan, UserLoanInfo, db, "message"
                )
        return response_obj
    except Exception as exc:
        msg = f"select loan type exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 404)


@router.post("/school", tags=["user"])
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
    return school_response


@router.put("/school", tags=["user"])
async def update_user_school_details(
    user_id: str,
    update_input: School,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    message = "School details updated successful"
    return await update_single(
        user_id, update_input, UserSchoolInfo, db, message, level=True
    )


@router.post("/reference", tags=["user"])
async def user_reference(
    reference_input: UserReferenceIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User reference added successfully"

    return await create_new(reference_input, UserReferenceIfo, db, message)


@router.post("/ticket", tags=["user"])
async def user_reference(
    ticket_input: TicketIN,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):

    message = "User ticket raised successfully"

    return await create_new(ticket_input, TicketIfo, db, message)


@router.get("/loan/overview", tags=["user"])
async def get_loan_overview(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        columns = ["id", "loan_required"]
        response_obj = await get_single(
            LoanInfo, db, user_id, level=True, columns=columns
        )

        user_loan_info_id = await user_loan_status(
            user_id, db, token_data, loan_info_id=True
        )

        lon_info_id = user_loan_info_id.data["result"]["loan_status"]

        columns = ["repayment_months"]
        loan_info_response = await get_single(
            UserLoanInfo, db, lon_info_id, columns=columns
        )

        emi_dict = loan_info_response.data["result"].repayment_months
        emi_value = next(iter(emi_dict.values()))

        output_response = dict(response_obj.data["result"])
        output_response["emi_value"] = emi_value
        output_response["emi_date"] = "2nd Every Month"

        response_obj.data["result"] = output_response
        return response_obj
    except Exception as exc:
        msg = f"loan overview exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


@router.get("/loan/application/info", tags=["user"])
async def get_loan_application_info(
    user_id: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_details = await get_loan_details(user_id, db)
        message = "Loan application details"

        return response(message, 1, 200, loan_details)
    except Exception as exc:
        msg = f"loan application info exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 400)


@router.post("/loan/application", tags=["user"])
async def user_loan_application(
    loan_amount: int,
    user_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        loan_details = await get_loan_details(user_id, db)
    
        total_loan_amount = loan_amount + loan_details["processing_fee"] + loan_details["gateway_fee"] + loan_details["additional_fee"]
        loan_input = {
            "loan_required": total_loan_amount,
        }

        background_tasks.add_task(
            update_single, user_id, loan_input, LoanInfo, db, "message", level=True
        )

        monthly_emi = math.ceil((total_loan_amount) / tenure)
        current_date = datetime.now()

        if current_date.day > 2:
            # Move to the next month first
            start_date = (
                current_date.replace(day=1) + relativedelta(months=1)
            ).replace(day=2)
        else:
            start_date = current_date.replace(day=2)

        emi_dates = {}
        for i in range(tenure):
            emi_date = start_date + relativedelta(months=i)
            emi_dates[emi_date.strftime("%d-%b-%Y")] = monthly_emi

        sorted_emi_dates = sort_emi_dates(emi_dates)
        
        update_loan_info = {"repayment_months": sorted_emi_dates}
        user_loan_info_id = await user_loan_status(
            user_id, db, token_data, loan_info_id=True
        )
        lon_info_id = user_loan_info_id.data["result"]["loan_status"]
        background_tasks.add_task(
            update_single, lon_info_id, update_loan_info, UserLoanInfo, db, "message"
        )
        message = "EMI calculated successfully"
        data = {
            "tenure": f"{tenure} Months",
            "total_loan_amount":total_loan_amount,
            "loan_approved": loan_details["loan_approved"],
            "processing_fee": loan_details["processing_fee"],
            "gateway_fee": loan_details["gateway_fee"],
            "additional_fee": loan_details["additional_fee"],
            "monthly emi": monthly_emi,
            "emi_dates": sorted_emi_dates,
        }

        return response(message, 1, 200, data)
    except Exception as exc:
        msg = f"loan application info exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 400)


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
        file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_input = {"statement": file_path}
        message = "Bank statement added successfully"
        response_obj = await update_single(
            user_id, update_input, LoanInfo, db, "message", level=True
        )

        if response_obj.data["result"]:
            input_field = {"is_document_completed": True}
            kyc_background_signup_level(user_id, background_tasks, db, input_field)

        return response_obj
    except Exception as exc:
        msg = f"loan application info exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 400)


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
                    "account_no": account_number,
                    "ifsc_code": ifsc_code,
                    "user_id": user_id,
                    "account_holder_name": bank_obj["name_at_bank"],
                }

                background_tasks.add_task(
                    create_new, bank_input, UserBankInfo, db, "message"
                )

                message = "Bank verification successful"

                return response(message, 1, 200, data=bank_obj)

            return response(bank_obj["account_status_code"], 0, 400)

        return response(
            f'{bank_obj["code"]} {bank_obj["message"]}', 0, bank_response.status_code
        )

    except Exception as exc:

        msg = f"loan application info exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


@router.get("/bank/statement", tags=["verification"])
async def get_bank_statement(
    user_id: int,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        columns = ["statement"]
        statement_response = await get_single(
            LoanInfo, db, user_id, level=True, columns=columns
        )

        if statement_response.data["result"]:
            file_path = statement_response.data["result"].statement
            if os.path.exists(file_path):
                message = "Statement found"
                data = {"bank_statement": file_path}
                return response(message, 1, 200, data)

        message = "Bank statement not found"
        return response(message, 0, 400)

    except Exception as exc:

        msg = f"bank statement exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


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
        file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_input = {"pan_image": file_path}
        await update_single(
            user_id, update_input, UserPersonalInfo, db, "message", level=True
        )

        message = "Image uploaded successfully"
        response_obj = response(message, 1, 201, file.filename)

        if response_obj.data["result"]:
            input_field = {"is_pan_image_uploaded": True}
            kyc_background_signup_level(user_id, background_tasks, db, input_field)

        return response_obj
    except Exception as exc:
        msg = f"pan image exception {str(exc)}"
        logger.exception(msg)
        return response(str(exc), 0, 400)


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
            columns=["pan_image", "pan", "aadhaar"],
        )
        if kyc_result.data["result"]:
            file_path = kyc_result.data["result"].pan_image
            if os.path.exists(file_path):
                message = "PAN image found"
                data = {
                    "pan_img_path": file_path,
                    "pan": kyc_result.data["result"].pan,
                    "adhaar": kyc_result.data["result"].aadhaar,
                }
                return response(message, 1, 200, data)

        message = "No KYC details found for the given user id"
        return response(message, 0, 404)

    except Exception as exc:
        msg = f"pan image exception {str(exc)}"
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

            pan_response = response(message, 1, 200, decrypt_response)

            if pan_response.data["result"]:
                update_input = {"pan": pan_number}
                await update_single(
                    user_id, update_input, UserPersonalInfo, db, "message", level=True
                )

                input_field = {"is_pan_verified": True}
                kyc_background_signup_level(user_id, background_tasks, db, input_field)

            return pan_response
        return response(
            decrypt_response["msg"], 0, decrypt_response["status"], decrypt_response
        )

    except Exception as exc:

        msg = f"verify pan number exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


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
        msg = f"verify pan number exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


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
            update_input = {"aadhaar": aadhaar_number}
            await update_single(
                user_id, update_input, UserPersonalInfo, db, "message", level=True
            )
            # return json.loads(decrypt_response)
            return response(message, 1, 200, decrypt_response)
        return response(
            decrypt_response["msg"], 0, decrypt_response["status"], decrypt_response
        )
    except Exception as exc:
        msg = f"verify pan number exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


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

        print("decrypt token response->", decrypt_response)
        decrypt_response = json.loads(decrypt_response)
        if decrypt_response["status"] != 1:
            print("Error:", decrypt_response["msg"])
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

        msg = f"verify pan number exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


@router.post("/credit", tags=["verification"])
async def credit_otp(
    email: str,
    pan: str,
    mobile: str,
    first_name: str,
    last_name: str,
    dob: str,
    address: str,
    city: str,
    state: str,
    pincode: str,
    gender: str = "Male",
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        headers = {"username": username, "content-type": "application/json"}

        otp_generation_payload = json.dumps(
            {
                "transID": "123",
                "docType": 45,
                "email": email,
                "mobileNumber": mobile,
                "firstName": first_name,
                "lastName": last_name,
                "dob": dob,
                "gender": gender,
                "address": address,
                "city": city,
                "state": state,
                "pinCode": pincode,
                "pan": pan,
            }
        )

        encrypt_payload = encrypt_decrypt_api(
            headers, "encrypt", otp_generation_payload
        )
        otp_generation_url = (
            "https://www.truthscreen.com/CreditReportVerificationApi/requestSend"
        )
        payload = json.dumps({"requestData": encrypt_payload})

        response = requests.post(otp_generation_url, data=payload, headers=headers)
        decrypt_payload = encrypt_decrypt_api(headers, "decrypt", response.text)

        return json.loads(decrypt_payload)

    except Exception as exc:

        msg = f"verify pan number exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)


@router.post("/credit/otp/verification", tags=["verification"])
async def credit_otp_verification(
    otp: str,
    tsTransID: str,
    verifyotp: int = 1,
    resendotp: int = 0,
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
                "verifyotp": verifyotp,
                "resendotp": resendotp,
            }
        )

        encrypt_payload = encrypt_decrypt_api(headers, "encrypt", otp_payload)
        payload = json.dumps({"requestData": encrypt_payload})

        result = requests.post(verify_otp_url, data=payload, headers=headers)
        decrypt_response = encrypt_decrypt_api(headers, "decrypt", result.text)

        decrypt_response = json.loads(decrypt_response)

        if decrypt_response["status"] == 1:
            return response(decrypt_response["result"], 1, 200, decrypt_response)

        return response(
            decrypt_response["msg"], 0, decrypt_response["status"], decrypt_response
        )

    except Exception as exc:
        msg = f"verify pan number exception {str(exc)}"
        logger.exception(msg)

        return response(str(exc), 0, 400)
