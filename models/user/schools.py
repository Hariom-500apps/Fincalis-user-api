"""School names details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import TIMESTAMP, text

from sqlmodel import SQLModel, Field, Column


class SchoolNameIn(SQLModel):

    # Name of the school
    name: str = Field(default=None, max_length=500, nullable=False)


class SchoolNameOut(SchoolNameIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    is_active: bool = Field(default=True)


class SchoolName(SchoolNameOut, table=True):

    __tablename__ = "schools"

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
