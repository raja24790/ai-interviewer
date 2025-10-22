from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..deps import SettingsType, get_settings
from ..schemas import TokenPayload

http_bearer = HTTPBearer(auto_error=False)


def create_access_token(session_id: str, settings: SettingsType | None = None) -> str:
    settings = settings or get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    to_encode = {"sub": session_id, "exp": int(expire.timestamp())}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: SettingsType | None = None) -> TokenPayload:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - simple exception branch
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if "sub" not in payload or "exp" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return TokenPayload(sub=str(payload["sub"]), exp=int(payload["exp"]))


async def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    settings: Annotated[SettingsType, Depends(get_settings)],
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    payload = decode_token(credentials.credentials, settings=settings)
    if payload.exp < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload.sub
