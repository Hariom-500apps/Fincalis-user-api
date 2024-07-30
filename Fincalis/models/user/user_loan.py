"""User's loan details"""

import enum
import uuid as uuid_pkg
from typing import Optional
from datetime import datetime

from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text, Enum, JSON


class RiskStatus(str, enum.Enum):
    """Risk status"""

    low = "low"
    medium = "medium"
    high = "high"


class LoanStatus(str, enum.Enum):
    """Loan status"""

    under_review = "under_review"
    verified = "verified"
    rejected = "rejected"
    disbursed = "disbursed"


class UserLoanIn(SQLModel):

    # Loan application
    loan_application: int = Field(default=None, foreign_key="loan_applications.id")

    # Risk status
    risk_status: RiskStatus = Field(
        default=RiskStatus.low, sa_column=Column(Enum(RiskStatus))
    )

    # Loan status
    loan_status: LoanStatus = Field(
        default=LoanStatus.under_review, sa_column=Column(Enum(LoanStatus))
    )

    # Repayment month
    repayment_months: dict = Field(default=None, sa_column=Column(JSON))

    # Loan status
    is_active: bool = Field(default=True)


class UserLoanOut(UserLoanIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class UserLoanInfo(UserLoanOut, table=True):

    __tablename__ = "user_loan_info"

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
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
