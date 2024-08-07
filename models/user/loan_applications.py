"""Loan application details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime

from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text, UniqueConstraint


class LoanApplication(SQLModel):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")

    # Loan type id
    loan_id: int = Field(default=None, foreign_key="loan_types.id")


class LoanApplicationIn(LoanApplication):

    # Loan amount
    loan_required: float = Field(default=None, nullable=True)

    # Cibil score
    cibil: Optional[int] = Field(default=None, nullable=True)


class LoanApplicationOut(LoanApplicationIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )

    # Loan status
    is_active: bool = Field(default=True)

    # Loan approved
    loan_approved: float = Field(default=None, nullable=True)

    # Statement
    statement: str = Field(default=None, nullable=True)


class LoanApplicationInfo(LoanApplicationOut, table=True):

    __tablename__ = "loan_applications"

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
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)
