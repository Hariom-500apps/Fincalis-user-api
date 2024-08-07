"""Business nature model"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, TIMESTAMP, text, Column, SQLModel
import uuid as uuid_pkg


class BusinessNatureIn(SQLModel):

    # Business nature name
    name: str = Field(default=None, nullable=False)

    # Business status
    is_active: bool = Field(default=True)


class BusinessNatureOut(BusinessNatureIn):
    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class BusinessNature(BusinessNatureOut, table=True):
    # Table name
    __tablename__ = "business_natures"

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
