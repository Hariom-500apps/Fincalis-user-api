"""Util file"""

from pydantic import BaseModel
from collections import OrderedDict
from datetime import datetime


class Response(BaseModel):
    data: dict
    settings: dict


ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
    "image/tiff",
]


def response(message, success, status_code, data=None):
    return Response(
        data={"result": data},
        settings={
            "message": message,
            "status": status_code,
            "success": success,
        },
    )


def sort_emi_dates(emi_dates):
    return OrderedDict(
        sorted(emi_dates.items(), key=lambda x: datetime.strptime(x[0], "%d-%b-%Y"))
    )
