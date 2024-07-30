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
    Relationship,
    UniqueConstraint,
)


class MaritalStatus(str, enum.Enum):
    """Marital Status"""

    Single = "Single"
    Married = "Married"


class Gender(str, enum.Enum):
    """Gender Status"""

    Male = "Male"
    Female = "Female"


class LoanPurpose(str, enum.Enum):
    """Loan purpose"""

    Personal = "Personal Loan"
    Home = "Home Loan"
    Education = "Education Loan"
    Business = "Business Loan"


class Profession(str, enum.Enum):
    """Profession"""

    Employee = "Employee"
    Student = "Student"
    Business = "Business"


class Basic(SQLModel):

    # Full name
    full_name: str = Field(default=None, max_length=50, nullable=False)

    # Father's name
    fathers_name: str = Field(default=None, max_length=50, nullable=False)

    # Mother's name
    mothers_name: str = Field(default=None, max_length=50, nullable=False)

    # Date of birth
    dob: date = Field(default=None, nullable=False)

    # Marital status
    marital_status: MaritalStatus = Field(
        default=MaritalStatus.Single, sa_column=Column(Enum(MaritalStatus))
    )

    # Address
    address: str = Field(default=None, max_length=500, nullable=False)

    # Pin code
    pincode: str = Field(default=None, max_length=10, nullable=False)

    # Gender
    gender: Gender = Field(default=None, sa_column=Column(Enum(Gender)))

    # Loan purpose
    loan_purpose: LoanPurpose = Field(default=None, sa_column=Column(Enum(LoanPurpose)))

    # Profession
    profession: Profession = Field(default=None, sa_column=Column(Enum(Profession)))

    # user_id: int = Field(foreign_key="users.id")

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
        return self.dob.strftime('%d-%m-%Y')


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


class UserPersonalInfo(BasicOut, table=True):

    __tablename__ = "user_personal_details"

    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    # Aadhaar number
    aadhaar: str = Field(default=None, max_length=12, nullable=True)

    # PAN number
    pan: str = Field(default=None, max_length=11, nullable=True)

    # Pan image
    pan_image: str = Field(default=None, nullable=True)

    @field_validator("aadhaar")
    def check_aadhar(cls, v):
        if not v.isdigit() or len(v) != 12:
            raise ValueError("Aadhaar number must be a 12-digit numeric string")
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
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)

    users: "Users" = Relationship(back_populates="personal_info")
