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
    Relationship,
    UniqueConstraint,
)


class Company(SQLModel):

    # Company name
    company_name: str = Field(default=None, max_length=200, nullable=False)

    # Designation
    designation: str = Field(default=None, max_length=50, nullable=False)

    # Official email
    office_email: EmailStr = Field(default=None, max_length=100, nullable=False)

    # Office id
    office_id: str = Field(default=None, max_length=50, nullable=False)

    # Work experience
    work_exp: float = Field(default=None, nullable=False)

    # Industry type
    industry_type_id: int = Field(default=None, foreign_key="business_natures.id")

    # Company address
    company_address: str = Field(default=None, max_length=200, nullable=False)

    # Pin code
    pincode: str = Field(default=None, max_length=10, nullable=False)


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


class UserCompanyInfo(CompanyOut, table=True):

    # Table name
    __tablename__ = "company_details"

    # Id
    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    # Creation date of company details
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )

    # Modified date of company details
    modified_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)

    users: "Users" = Relationship(back_populates="company_info")
    nature: "BusinessNature" = Relationship(back_populates="company_nature_info")
