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
)


class UserType(str, enum.Enum):
    """User type"""

    user = "user"
    staff = "staff"
    admin = "admin"


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

    user_type: UserType = Field(default=UserType.user, sa_column=Column(Enum(UserType)))

    email_verified: bool = Field(default=False)


class UserOut(UserIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )

    # User status
    is_active: bool = Field(default=True)


class Users(UserOut, table=True):

    # Table name
    __tablename__ = "users"

    # Id
    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    is_superuser: bool = Field(default=False)

    is_admin: bool = Field(default=False)

    is_blocked: bool = Field(default=False)

    is_staff: bool = Field(default=False)

    password: str = Field(default=None, max_length=255, nullable=True)

    fcm_token: str = Field(default=None, max_length=255, nullable=True)

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

    __table_args__ = (
        Index("idx_user_uid", "uid"),
        UniqueConstraint("email", name="uq_email"),
        UniqueConstraint("mobile", name="uq_mobile"),
    )
