"""User's signup level """

import enum
import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import TIMESTAMP, Column, Field, text, SQLModel, UniqueConstraint, Enum
from sqlalchemy import Column


class Provision(str, enum.Enum):

    employee = "employee"
    student = "student"
    business = "business"


class SignupLevelIn(SQLModel):

    # Basic info status
    is_basic_completed: bool = Field(default=False)

    provision_status: Provision = Field(default=None, sa_column=Column(Enum(Provision)))

    # Work info status
    is_work_completed: bool = Field(default=False, nullable=True)

    # Pan verified status
    is_pan_verified: bool = Field(default=False, nullable=True)

    # Adhaar verified status
    is_adhaar_verified: bool = Field(default=False, nullable=True)

    # Aadhar image uploaded status
    is_aadhar_image_uploaded: bool = Field(default=False, nullable=True)

    # Pan image uploaded status
    is_pan_image_uploaded: bool = Field(default=False, nullable=True)

    # Document info status
    is_document_completed: bool = Field(default=False, nullable=True)

    # bank verification status
    is_bank_verified:bool  = Field(default=False, nullable=True)

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class SignupLevelInOut(SignupLevelIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    # status
    is_active: bool = Field(default=True)


class SignupLevelInfo(SignupLevelInOut, table=True):

    __tablename__ = "signup_levels"

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

    modified_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)
