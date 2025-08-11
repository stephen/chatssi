import os
from datetime import datetime, timedelta
from typing import Optional
import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Depends, Request
from jose import JWTError, jwt
from models import get_db, User
from models.bigtable_user import BigtableUserService

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request, db_service: BigtableUserService = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    authorization = request.headers.get("Authorization")
    if authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise credentials_exception
        except ValueError:
            raise credentials_exception
    else:
        token = request.cookies.get("access_token")
        if not token:
            raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db_service.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user


async def get_or_create_user(user_info: dict, db_service: BigtableUserService) -> User:
    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name") or user_info.get("given_name", "")
    picture = user_info.get("picture")

    # Validate required fields
    if not google_id:
        raise ValueError("google_id is required but not found in user_info")
    if not email:
        raise ValueError("email is required but not found in user_info")
    if not name:
        name = email.split("@")[0]

    user = db_service.get_user_by_google_id(google_id)

    if not user:
        user = db_service.create_user(
            name=name, email=email, google_id=google_id, picture=picture
        )
    else:
        if user.name != name or user.picture != picture:
            user = db_service.update_user(user.id, name=name, picture=picture)

    return user
