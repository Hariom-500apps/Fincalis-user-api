"""User's contact details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime

from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text, UniqueConstraint


class UserContactIN(SQLModel):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")

    # Contacts
    contact_json: bytes = Field(default=None)


class UserContactOut(UserContactIN):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )

    is_active: bool = True


class UserContactIfo(UserContactOut, table=True):

    __tablename__ = "user_contacts"

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
    # Last modification date
    modified_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_id"),)
