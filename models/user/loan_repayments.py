"""Loan repayments details"""

import enum
import uuid as uuid_pkg
from typing import Optional
from datetime import datetime, date as date_field


from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text, Enum


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    credited = "credited"
    debited = "debited"


class LoanRepaymentIn(SQLModel):

    amount: int = Field(default=None, nullable=False)

    date: date_field = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )

    # Loan type id
    loan_id: int = Field(default=None, foreign_key="loans.id")

    # Loan status
    is_active: bool = Field(default=True)

    # Loan status
    is_paid: bool = Field(default=False)

    status: PaymentStatus = Field(
        default=PaymentStatus.pending,
        sa_column=Column(Enum(PaymentStatus), nullable=True),
    )


class LoanRepaymentOut(LoanRepaymentIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class LoanRepaymentInfo(LoanRepaymentOut, table=True):

    __tablename__ = "loan_repayments"

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
