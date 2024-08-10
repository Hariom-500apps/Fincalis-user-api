"""Base jwt classes"""

from fastapi import HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import jwt
from pydantic import BaseModel
from datetime import timedelta, datetime
from typing import Union
from os import environ
from dotenv import load_dotenv


load_dotenv()


class TokenData(BaseModel):
    """JWT token class"""

    full_name: str
    mobile: str
    token_type: str = "access"
    user_type: str = "user"
    user_id: int
    email: str

    def asdict(self):
        """create dict"""
        return {
            "full_name": self.full_name,
            "mobile": self.mobile,
            "token_type": self.token_type,
            "user_type": self.user_type,
            "user_id": self.user_id,
            "email": self.email,
        }


class JWTBearer(HTTPBearer):
    """Check jwt bearer"""

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        if request.query_params.get("_token"):
            token_data = verify_jwt(request.query_params.get("_token"))
            return token_data

        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=403, detail="Invalid authentication scheme."
            )

        token_data = verify_jwt(credentials.credentials)

        return token_data


def create_access_token(data: dict, expires_delta: Union[timedelta, None]):
    """create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    # Use specific jwt secret to sign the jwt token
    encoded_jwt = jwt.encode(
        to_encode, environ.get("SECRET_HS512_KEY"), algorithm=environ.get("SIGNING_KEY")
    )
    return encoded_jwt


def create_service_token(
    full_name: str,
    mobile: str,
    user_id: str = None,
    email: str = None,
    expiry_days: int = 7,
):
    """Generate token"""
    tokendata = TokenData(
        full_name=full_name,
        mobile=mobile,
        user_id=user_id,
        email=email,
        token_type="access",
        user_type="user",
    )

    jwt_token = create_access_token(
        tokendata.asdict(), expires_delta=timedelta(days=expiry_days)
    )

    return jwt_token


def verify_jwt(token: str) -> TokenData:
    """Token validation"""
    try:
        # Passing the token inside credentials.credentials to set env details
        payload = jwt.decode(
            token=token, key=environ.get("SECRET_HS512_KEY"), algorithms=["HS512"]
        )
        token_data = TokenData(**payload)
        return token_data

    except Exception as ex:
        raise HTTPException(
            status_code=403, detail="Invalid authorization code."
        ) from ex
