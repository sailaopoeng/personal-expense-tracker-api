from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # minutes

class TokenData(BaseModel):
    username: Optional[str] = None
