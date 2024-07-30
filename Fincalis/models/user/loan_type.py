"""Loan type model"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, TIMESTAMP, text, Column, SQLModel
import uuid as uuid_pkg


class LoanTypeIn(SQLModel):

    # Loan type name
    name: str = Field(default=None, nullable=False)

    # Loan status
    is_active: bool = Field(default=True)

    # Limit
    limit: float = Field(default=None, nullable=False)

    # Return on investment
    roi: float = Field(default=None, nullable=False)

    # Processing fee
    processing_fee: float = Field(default=None, nullable=False)

    # Gateway fee
    gateway_fee: float = Field(default=None, nullable=False)

    # Additional fee
    additional_fee: float = Field(default=None, nullable=False)

    # Late fee
    late_fee: float = Field(default=None, nullable=False)


class LoanTypeOut(LoanTypeIn):
    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class LoanType(LoanTypeOut, table=True):
    # Table name
    __tablename__ = "loan_types"

    # Id
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

    # Modified date
    modified_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
