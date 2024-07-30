"""Business type model"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, TIMESTAMP, text, Column, SQLModel
import uuid as uuid_pkg


class BusinessTypeIn(SQLModel):

    # Business type name
    name: str = Field(default=None, nullable=False)

    # Business status
    is_active: bool = Field(default=True)


class BusinessTypeOut(BusinessTypeIn):
    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )


class BusinessType(BusinessTypeOut, table=True):
    # Table name
    __tablename__ = "business_types"

    # Id
    id: Optional[int] = Field(default=None, index=True, primary_key=True)

    # Creation date of company details
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default_factory=datetime.utcnow,
    )

    # Modified date of company details
    modified_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
