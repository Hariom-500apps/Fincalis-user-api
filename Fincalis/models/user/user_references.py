"""User's reference details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text


class UserReferenceIN(SQLModel):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")

    # Reference name
    name: str = Field(default=None, max_length=50, nullable=False)

    # Relation with user
    relation: str = Field(default=None, max_length=50, nullable=False)

    # Reference mobile
    mobile: str = Field(default=None, min_length=10, max_length=10, nullable=False)


class UserReferenceOut(UserReferenceIN):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )

    # Reference status
    is_active: bool = Field(default=True)


class UserReferenceIfo(UserReferenceOut, table=True):

    __tablename__ = "user_references"

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
