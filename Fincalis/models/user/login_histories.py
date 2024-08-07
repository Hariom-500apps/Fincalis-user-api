"""User login history model"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import Field, TIMESTAMP, text, Column, SQLModel


class LoginHistoryIN(SQLModel):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")

    # Loan status
    latitude: float = Field(default=None, nullable=False)

    # Limit
    longitude: float = Field(default=None, nullable=False)

    # Return on investment
    address: str = Field(default=None, max_length=1000)


class LoginHistoryOut(LoginHistoryIN):
    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    is_active: bool = Field(default=True)


class LoginHistory(LoginHistoryOut, table=True):
    # Table name
    __tablename__ = "user_login_histories"

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
