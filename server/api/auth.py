from . import api
from starlette.middleware.sessions import SessionMiddleware
import os
from auth import oauth, get_current_user, get_or_create_user, create_access_token
from fastapi import HTTPException, Request, Depends
from fastapi.responses import RedirectResponse

from models import get_db, User, UserSchema
from models.bigtable_user import BigtableUserService

api.add_middleware(
    SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-this")
)


@api.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    print(f"Redirect URI: {redirect_uri}")  # Debug: check what URI is being used
    return await oauth.google.authorize_redirect(request, redirect_uri)  # type: ignore


@api.get("/oauth/google")
async def auth_callback(
    request: Request, db_service: BigtableUserService = Depends(get_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)  # type: ignore
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user = await get_or_create_user(user_info, db_service)

        access_token = create_access_token(data={"sub": str(user.id)})

        request.session["access_token"] = access_token

        return RedirectResponse(url="/")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@api.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}


@api.get("/auth/me", response_model=UserSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
