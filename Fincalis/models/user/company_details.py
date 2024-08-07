"""User's company details"""

from typing import Optional
import uuid as uuid_pkg
from datetime import datetime
from pydantic import EmailStr
from sqlmodel import (
    SQLModel,
    TIMESTAMP,
    Column,
    Field,
    text,
    UniqueConstraint,
)


class Company(SQLModel):

    # Company name
    company_name: str = Field(default=None, max_length=200, nullable=False)

    # Designation
    designation: str = Field(default=None, max_length=50, nullable=False)

    # Official email
    office_email: EmailStr = Field(default=None, max_length=100, nullable=False)

    # Salary
    salary: float = Field(default=None, nullable=False)

    # Work experience
    work_exp: float = Field(default=None, nullable=False)

    # Industry type
    industry_type_id: int = Field(default=None, foreign_key="business_natures.id")

    # Company address
    company_address: str = Field(default=None, max_length=200, nullable=False)

    # Pin code
    pincode: int = Field(default=None, nullable=False)


class CompanyIn(Company):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class CompanyOut(CompanyIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    # User status
    is_active: bool = Field(default=True)


class UserCompanyInfo(CompanyOut, table=True):

    # Table name
    __tablename__ = "company_details"

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
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)
