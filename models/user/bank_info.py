"""User's Bank details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import TIMESTAMP, text

from sqlmodel import SQLModel, Field, Column


class BankIn(SQLModel):

    # Name of the bank
    bank_name: str = Field(default=None, max_length=200, nullable=False)

    # Account number
    account_number: str = Field(default=None, max_length=50, nullable=False)

    # Bank account holder name
    account_holder_name: str = Field(default=None, max_items=100, nullable=False)

    # Bank IFSC code
    ifsc_code: str = Field(default=None, max_length=50, nullable=False)

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class BankOut(BankIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    # Status
    is_active: bool = Field(default=True)


class UserBankInfo(BankOut, SQLModel, table=True):

    __tablename__ = "bank_infos"

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
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )
