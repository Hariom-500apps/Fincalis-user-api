"""User's model"""

import enum
import uuid as uuid_pkg
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field
from sqlmodel import (
    SQLModel,
    Index,
    TIMESTAMP,
    Column,
    Field,
    text,
    UniqueConstraint,
    Enum,
    Relationship,
)


class UserType(str, enum.Enum):
    """User type"""

    User = "user"
    Staff = "staff"
    Admin = "admin"


class User(SQLModel):

    # User's full name
    full_name: str = Field(default=None, max_length=50, nullable=False)

    # Email of the user
    email: EmailStr = Field(default=None, max_length=50, nullable=True)


class UserIn(User):

    # User image
    image: str = Field(default=None, max_length=1024, nullable=True)

    # Mobile number of the user
    mobile: str = Field(default=None, max_length=10, min_length=10, nullable=False)

    user_type: UserType = Field(default=None, sa_column=Column(Enum(UserType)))

    # User status
    is_active: bool = Field(default=True)

    email_verified: bool = Field(default=False)


class UserOut(UserIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class Users(UserOut, table=True):

    # Table name
    __tablename__ = "users"

    # Id
    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    is_superuser: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    is_blocked: bool = Field(default=False)

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

    __table_args__ = (
        Index("idx_user_uid", "uid"),
        UniqueConstraint("email", name="uq_email"),
        UniqueConstraint("mobile", name="uq_mobile"),
    )
    personal_info: "UserPersonalInfo" = Relationship(back_populates="users")
    company_info: "UserCompanyInfo" = Relationship(back_populates="users")
    business_info: "UserBusinessInfo" = Relationship(back_populates="users")
    school_info: "UserSchoolInfo" = Relationship(back_populates="users")
