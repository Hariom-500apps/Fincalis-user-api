"""Main file"""


import time
import logging
import ipaddress

from routes import user_routes ,otp, subscription

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


logger = logging.getLogger(__name__)
app = FastAPI()


DESCRIPTION = """
Your Service 🚀

## Fincalis user

"""


app = FastAPI(
    description=DESCRIPTION,
    title="Fincalis user services",
    contact={
        "name": "Pixl.in",
        "url": "https://pixl.in/contact-us",
        "email": "connect@pixl.in",
    },
    license_info={
        "name": "All rights reserved © pixl.in",
        "url": "https://pixl.in",
    },
    swagger_ui_parameters={"persistAuthorization": True},
    redoc_url="/redoc",
)

logging.basicConfig(
    level=logging.ERROR,  # Set the log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
    filename='app.log',  # Log file name
    filemode='w'  # Write mode, use 'a' for append mode
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    msg = f"exception_handler exception {str(exc.errors)}"
    logger.exception(msg)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "data": {"exc_error": str(exc.errors)},
            "settings": {
                " status": 422,
                "message": "Validation error: one or more fields are missing or invalid.",
                "success": 0,
            },
        },
    )
allowed_ips = ["34.168.253.122"]

@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = request.client.host
    if ipaddress.ip_address(client_ip) not in allowed_ips:
        return JSONResponse({"message": "IP is not whitelisted", "type": "error"}, status_code=403)
    response = await call_next(request)
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time"""

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/hello")
def read_root():
    try:
        logger.exception(str("Hello"))
        return {"Hello": "World"}
    except Exception as exc:
        logger.exception(str(exc))


# Routes
app.include_router(prefix="/user", router=user_routes.router)
app.include_router(prefix="/otp", router=otp.router, tags=["OTP"])
app.include_router(prefix="/subscription", router=subscription.router, tags=["Subscription"])
