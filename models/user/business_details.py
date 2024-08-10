"""User's business details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from pydantic import EmailStr
from sqlmodel import (
    TIMESTAMP,
    Column,
    Field,
    text,
    SQLModel,
    UniqueConstraint,
)
from sqlalchemy import Column


class Business(SQLModel):

    # Business name
    business_name: str = Field(default=None, max_length=200, nullable=False)

    # Registered address
    registered_address: str = Field(default=None, max_length=200, nullable=False)

    # Official email
    official_email: EmailStr = Field(default=None, max_length=200, nullable=False)

    # Annual income
    annual_income: float = Field(default=None, nullable=False)

    # Pin code
    pincode: int = Field(default=None, nullable=False)

    # Registration type
    registration_type_id: int = Field(default=None, foreign_key="business_types.id")

    # Nature of business
    nature_of_business_id: int = Field(default=None, foreign_key="business_natures.id")


class BusinessIn(Business):
    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class BusinessInOut(BusinessIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    # User status
    is_active: bool = Field(default=True)


class UserBusinessInfo(BusinessInOut, table=True):

    __tablename__ = "business_details"

    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    # Creation date of User
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )

    modified_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )

    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)
