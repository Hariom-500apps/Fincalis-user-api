"""NPCI sported bank  details"""

import uuid as uuid_pkg
from typing import Optional
from datetime import datetime
from sqlmodel import TIMESTAMP, text

from sqlmodel import SQLModel, Field, Column


class NPCIBankIn(SQLModel):

    # Name of the bank
    bank_name: str = Field(default=None, max_length=500, nullable=False)


class NPCIBankOut(NPCIBankIn):

    # UUID
    uid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        index=True,
        nullable=False,
    )
    
    is_active: bool = Field(default=True)


class NPCIBank(NPCIBankOut, table=True):

    __tablename__ = "bank_npcis"

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
