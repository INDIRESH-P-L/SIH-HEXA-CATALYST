import asyncio
from pydantic import ValidationError
from app.schemas.auth import RegisterRequest

try:
    req = RegisterRequest(
        email="keshav@mospi.gov.in",
        password="test", # < 8 chars
        full_name="Keshav K",
        job_role_code="DATA_SCIENTIST"
    )
    print("Success")
except ValidationError as e:
    print(e.json())
