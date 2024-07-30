"""User's ticket details"""

import enum
import uuid as uuid_pkg
from typing import Optional
from datetime import datetime

from sqlmodel import Column, Field, SQLModel, TIMESTAMP, text, Enum, TEXT


class Status(str, enum.Enum):
    """Ticket status"""

    open = "open"
    closed = "closed"


class TicketIN(SQLModel):

    # User id
    user_id: int = Field(default=None, foreign_key="users.id")

    # Ticket title
    title: str = Field(default=None, max_length=50, nullable=False)

    # Ticket description
    description: str = Field(default=None, sa_column=Column(TEXT))

    # Ticket status
    status: Status = Field(default=None, sa_column=(Enum(Status)))


class TicketOut(TicketIN):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class TicketIfo(TicketOut, table=True):

    __tablename__ = "ticket_info"

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
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
