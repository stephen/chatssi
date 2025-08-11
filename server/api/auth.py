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

HOST = os.getenv("HOST", "http://localhost:5173")


@api.get("/auth/login")
async def login(request: Request):
    # Use frontend URL for OAuth callback
    redirect_uri = f"{HOST}/auth/callback"
    print(f"Redirect URI: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)  # type: ignore


@api.post("/auth/callback")
async def auth_callback(
    request: Request, db_service: BigtableUserService = Depends(get_db)
):
    """Handle OAuth callback - expects auth code from frontend"""
    try:
        body = await request.json()
        auth_code = body.get("code")

        if not auth_code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Exchange code for token manually
        import httpx

        token_url = "https://oauth2.googleapis.com/token"

        token_data = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{HOST}/auth/callback",
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()

        # Get user info
        userinfo_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={tokens['access_token']}"
        async with httpx.AsyncClient() as client:
            user_response = await client.get(userinfo_url)
            user_response.raise_for_status()
            user_info = user_response.json()

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user = await get_or_create_user(user_info, db_service)
        access_token = create_access_token(data={"sub": str(user.id)})

        return {"access_token": access_token, "user": user}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@api.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}


@api.get("/auth/me", response_model=UserSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
