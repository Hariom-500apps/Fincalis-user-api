"""Subscription Authorization"""

import requests
from pydantic import BaseModel

from fastapi import APIRouter, Depends, BackgroundTasks
import json
from os import environ
from dotenv import load_dotenv

from models.user.loan_types import LoanType
from util import response
from sqlmodel import select


from datetime import date
from api_crud import  create_new, get_single, update_single
from models.user.bank_info import  UserBankInfo
from models.user.users import Users
from sqlalchemy.orm import Session
from base_jwt import JWTBearer
from db import get_db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


from models.user.loan_applications import LoanApplicationInfo
from models.user.loans import UserLoanInfo
from models.user.loan_repayments import  LoanRepaymentInfo


sub_client_id = environ.get("SUB_TEST_CLIENT_ID")
sub_client_secret = environ.get("SUB_TEST_CLIENT_SECRET")
maxCycles = environ.get("TENURE")


router = APIRouter()
load_dotenv()

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

@router.get("/pre/subscription/info")
async def get_pre_subscription_info(user_id: str, db: Session = Depends(get_db)):
    try:
        user_account = await get_single(UserBankInfo, db, user_id, level=True)
        user_profile = await get_single(Users, db, user_id)
        print("user_account", user_account)
        user_profile_obj = dict(user_profile.data["result"])
        user_account_obj = dict(user_account.data["result"])
        result = {
            "Name": user_profile_obj["full_name"],
            "Phone": user_profile_obj["mobile"],
            "Email": user_profile_obj["email"],
            "accountNumber": user_account_obj["account_no"],
            "bankName": user_account_obj["bank_name"],
            "accountHolderName": user_account_obj["account_holder_name"],
            "ifsc": user_account_obj["ifsc_code"],
        }
        return response("Found details", 1, 200, result)
    except Exception as exc:
        return str(exc)


@router.post("/plan/subscription")
async def create_subscription_with_plan(
    background_task: BackgroundTasks,
    user_id: str,
    name: str,
    mobile: str,
    email: str,
    account_number: str,
    account_holder_name: str,
    ifsc_code: str,
    db: Session = Depends(get_db),
    token_data: BaseModel = Depends(JWTBearer()),
):
    try:
        statement = (
            select(LoanType.name, LoanApplicationInfo.loan_required, UserLoanInfo.repayment_months, UserLoanInfo.id, UserLoanInfo.loan_no)
            .join(LoanApplicationInfo, LoanType.id == LoanApplicationInfo.loan_id)
            .join(UserLoanInfo, UserLoanInfo.loan_application_id == LoanApplicationInfo.id)
            .where(LoanApplicationInfo.user_id == user_id)
        )
        loan_type = db.execute(statement).first()
        print("loan_type--------------", loan_type)
        print("statement[2]", type(loan_type[2]))
        repayment_months = loan_type[2]
        recurringAmount = next(iter(repayment_months.values()))

        payload = {
            "subscriptionId": loan_type[4],
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
        print("response_obj", response_obj)
        print(response_obj)
        if response_obj["status"] == 200:
            update_input = {"sub_ref_id": response_obj["data"]["subReferenceId"]}
            # print("----------------------------",{"loan_id": loan_type[3], "amount":int(loan_type[1]),"sub_ref_id": response_obj["data"]["subReferenceId"]})
            create_input = {"loan_id": loan_type[3], "loan_amount":int(loan_type[1])}
            background_task.add_task(
                update_single,
                user_id,
                update_input,
                UserLoanInfo,
                db,
                "message",
                level=True,
            )
            "LoanRepaymentInfoLoanRepaymentInfo {'loan_id': 1, 'amount': 50300}"
            # resss = await create_new(create_input,LoanRepaymentInfo,db,"message")
            background_task.add_task(
                create_new,
                create_input,
                LoanRepaymentInfo,
                db,
                "message"
            )
            return  [create_input]
            return response(response_obj["message"], 1, 201, response_obj["data"])

        return response(response_obj["message"], 0, 400)

    except Exception as exc:
        return str(exc)
