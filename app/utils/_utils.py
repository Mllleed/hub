import asyncio
import uuid
import datetime as dt

from datetime import datetime, timedelta
from datetime import timezone as tz

from pytz import timezone

from app.types._types import Numeric

RESERVED_CLAIMS = {
    "fresh",
    "csrf",
    "iat",
    "exp",
    "iss",
    "aud",
    "type",
    "jti",
    "nbf",
    "sub",
}

utc = timezone("UTC")

def get_now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)

def get_now_ts() -> Numeric:
    return get_now().timestamp()

def get_uuid() -> str:
    return str(uuid.uuid4())
