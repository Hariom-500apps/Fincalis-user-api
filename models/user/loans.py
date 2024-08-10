"""User's loan details"""

import enum
import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from os import environ

from dotenv import load_dotenv
from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text, Enum


load_dotenv()
TENURE = environ.get("TENURE")


class RiskStatus(str, enum.Enum):
    """Risk status"""

    low = "low"
    medium = "medium"
    high = "high"


class LoanStatus(str, enum.Enum):
    """Loan status"""

    initiated = "initiated"
    under_review = "under review"
    verified = "verified"
    rejected = "rejected"
    disbursed_pending = "disbursed pending"
    disbursed = "disbursed"
    active = "active"
    on_hold = "on hold"
    completed = "completed"
    customer_cancelled = "customer cancelled"
    customer_paused = "customer paused"
    expired = "expired"
    link_expired = "link expired"
    bank_verified = "bank verified"
    subscription_created = "subscription created"


class UserLoanIn(SQLModel):

    # Loan application
    loan_application_id: int = Field(default=None, foreign_key="loan_applications.id")

    # Risk status
    risk_status: RiskStatus = Field(
        default=RiskStatus.low, sa_column=Column(Enum(RiskStatus))
    )

    # Loan status
    loan_status: LoanStatus = Field(
        default=LoanStatus.initiated, sa_column=Column(Enum(LoanStatus))
    )

    # Repayment month
    repayment_months: int = Field(default=TENURE, nullable=True)

    # Loan amount
    loan_amount: float = Field(default=None, nullable=True)

    # Repayment month
    paid_months: int = Field(default=0, nullable=True)

    # Paid status
    is_paid: bool = Field(default=False)

    # Loan no
    loan_no: str = Field(default=None, max_length=100, nullable=True)

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class UserLoanOut(UserLoanIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )

    # Loan status
    is_active: bool = Field(default=True)


class UserLoanInfo(UserLoanOut, table=True):

    __tablename__ = "loans"

    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    # Creation date
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )
    # Last modification date
    modified_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )
