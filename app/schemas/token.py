# app/schemas/token.py
from typing import Optional, Union
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[Union[int, str]] = None
    exp: Optional[int] = None
