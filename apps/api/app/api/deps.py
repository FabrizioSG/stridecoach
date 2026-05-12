import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.request import urlopen

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.training import User

JWKS_CACHE_TTL_SECONDS = 600
_jwks_cache: dict[str, object] = {"expires_at": 0.0, "keys": []}


@dataclass(frozen=True)
class SupabaseIdentity:
    supabase_user_id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None


def decode_supabase_token(token: str) -> Mapping[str, object]:
    settings = get_settings()
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")

    if algorithm == "HS256":
        if (
            not settings.supabase_jwt_secret
            or settings.supabase_jwt_secret == "replace-with-supabase-jwt-secret"
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET is required for legacy HS256 tokens",
            )

        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

    if algorithm not in {"ES256", "RS256"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported Supabase token algorithm: {algorithm}",
        )

    key_id = header.get("kid")
    if not key_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase token is missing key id",
        )

    signing_key = get_jwks_key(str(key_id))
    if signing_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase signing key was not found",
        )

    return jwt.decode(
        token,
        signing_key,
        algorithms=[algorithm],
        options={"verify_aud": False},
    )


def get_jwks_key(key_id: str) -> dict | None:
    keys = get_jwks_keys()
    return next((key for key in keys if key.get("kid") == key_id), None)


def get_jwks_keys() -> list[dict]:
    now = time.time()
    cached_keys = _jwks_cache["keys"]
    if isinstance(cached_keys, list) and now < float(_jwks_cache["expires_at"]):
        return cached_keys

    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is required for JWKS token verification",
        )

    jwks_url = f"{str(settings.supabase_url).rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        with urlopen(jwks_url, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Supabase JWKS",
        ) from exc

    keys = body.get("keys", [])
    if not isinstance(keys, list):
        keys = []

    _jwks_cache["keys"] = keys
    _jwks_cache["expires_at"] = now + JWKS_CACHE_TTL_SECONDS
    return keys


def get_supabase_identity(request: Request) -> SupabaseIdentity:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    try:
        payload = decode_supabase_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase token",
        ) from exc

    supabase_user_id = payload.get("sub")
    if not supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase token is missing subject",
        )

    metadata = payload.get("user_metadata") or {}
    return SupabaseIdentity(
        supabase_user_id=supabase_user_id,
        email=payload.get("email"),
        display_name=metadata.get("full_name") or metadata.get("name"),
        avatar_url=metadata.get("avatar_url") or metadata.get("picture"),
    )


def get_current_user(
    identity: SupabaseIdentity = Depends(get_supabase_identity),
    db: Session = Depends(get_db),
) -> User:
    user = db.scalar(select(User).where(User.supabase_user_id == identity.supabase_user_id))
    if user is None:
        user = User(supabase_user_id=identity.supabase_user_id)

    user.email = identity.email
    user.display_name = identity.display_name
    user.avatar_url = identity.avatar_url

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


DbSession = Depends(get_db)
CurrentUser = Depends(get_current_user)
