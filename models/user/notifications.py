"""User notifications model"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import Field, TIMESTAMP, text, Column, SQLModel


class Notification(SQLModel):

    # Notification content
    content: str = Field(default=None, nullable=False)

    # Read status
    is_read: bool = Field(default=False, nullable=False)

    # Return on investment
    address: str = Field(default=None, max_length=1000)


class NotificationOut(Notification):
    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class Notifications(NotificationOut, table=True):
    # Table name
    __tablename__ = "notifications"

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
