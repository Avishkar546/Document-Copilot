from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ValidationError

from app.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


class _SupabaseAuthUser(BaseModel):
    id: UUID


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="A valid bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    headers = {
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {credentials.credentials}",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail="Authentication service is unavailable"
        ) from exc

    if response.status_code in {401, 403}:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if response.is_error:
        raise HTTPException(status_code=502, detail="Authentication service failed")

    try:
        user = _SupabaseAuthUser.model_validate(response.json())
    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail="Authentication service returned an invalid user"
        ) from exc

    return user.id
