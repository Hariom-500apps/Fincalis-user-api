"""User's personal details"""

import enum
import re
import uuid as uuid_pkg
from typing import Optional
from datetime import date, datetime


from pydantic import field_validator, validator
from sqlmodel import (
    Enum,
    Column,
    Field,
    SQLModel,
    TIMESTAMP,
    text,
    UniqueConstraint,
)


class MaritalStatus(str, enum.Enum):
    """Marital Status"""

    single = "single"
    married = "married"


class Gender(str, enum.Enum):
    """Gender Status"""

    male = "male"
    female = "female"
    other = "other"


class LoanPurpose(str, enum.Enum):
    """Loan purpose"""

    Personal = "Personal Loan"
    Home = "Home Loan"
    Education = "Education Loan"
    Business = "Business Loan"


class Profession(str, enum.Enum):
    """Profession"""

    employee = "employee"
    student = "student"
    business = "business"


class Basic(SQLModel):

    # Father's name
    father_name: str = Field(default=None, max_length=50, nullable=False)

    # Mother's name
    mother_name: str = Field(default=None, max_length=50, nullable=False)

    # Date of birth
    dob: date = Field(default=None, nullable=False)

    # Marital status
    marital_status: MaritalStatus = Field(
        default=MaritalStatus.single, sa_column=Column(Enum(MaritalStatus))
    )

    # Address
    address: str = Field(default=None, max_length=500, nullable=False)

    # Pin code
    pincode: int = Field(default=None, nullable=False)

    # Gender
    gender: Gender = Field(default=None, sa_column=Column(Enum(Gender)))

    # Loan purpose
    # loan_purpose: LoanPurpose = Field(default=None, sa_column=Column(Enum(LoanPurpose)))

    # Profession
    profession: Profession = Field(default=None, sa_column=Column(Enum(Profession)))

    # verified_status:bool=Field(default=False)

    @validator("dob", pre=True)
    def parse_date(cls, value):
        if isinstance(value, str):
            for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    pass
            raise ValueError("Date format should be either DD-MM-YYYY or DD/MM/YYYY")
        return value

    @property
    def formatted_dob(self) -> str:
        return self.dob.strftime("%d-%m-%Y")


class BasicIn(Basic):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class BasicOut(BasicIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )

    # User status
    is_active: bool = Field(default=True)


class UserPersonalInfo(BasicOut, table=True):

    __tablename__ = "user_details"

    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    # Aadhar number
    aadhar: str = Field(default=None, max_length=12, nullable=True)

    # PAN number
    pan: str = Field(default=None, max_length=11, nullable=True)

    # Pan image
    pan_image: str = Field(default=None, nullable=True)

    # Aadhar image
    aadhar_image: str = Field(default=None, nullable=True)
    

    @field_validator("aadhar")
    def check_aadhar(cls, v):
        if not v.isdigit() or len(v) != 12:
            raise ValueError("Aadhar number must be a 12-digit numeric string")
        return v

    @field_validator("pan")
    def validate_pan(cls, value):
        pan_regex = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
        if not pan_regex.match(value):
            raise ValueError("Invalid PAN number format")
        return value

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
