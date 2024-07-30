"""User's school details"""

from typing import Optional
from datetime import datetime
from sqlmodel import TIMESTAMP, text
import uuid as uuid_pkg
from sqlmodel import SQLModel, Field, Column, Relationship, UniqueConstraint


class School(SQLModel):

    # Name of the school
    school_name: str = Field(default=None, max_length=200, nullable=False)

    # Branch
    branch: str = Field(default=None, max_length=50, nullable=False)

    # Student class
    student_class: str = Field(default=None, max_length=5, nullable=False)

    # Student name
    student_name: str = Field(default=None, max_length=50, nullable=False)

    # School fee
    fee: float = Field(default=None, nullable=False)

    # Guardian name like father's name
    guardian_name: str = Field(default=None, max_length=50, nullable=False)

    # Guardian name like father's name
    guardian_mobile: str = Field(
        default=None, max_length=10, min_length=10, nullable=False
    )

    # User status
    is_active: bool = Field(default=True)


class SchoolIn(School):
    # User id
    user_id: int = Field(default=None, foreign_key="users.id")


class SchoolOut(SchoolIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class UserSchoolInfo(SchoolOut, table=True):

    __tablename__ = "user_school_info"

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
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)

    users: "Users" = Relationship(back_populates="school_info")
