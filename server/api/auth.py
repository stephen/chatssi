from . import api
from starlette.middleware.sessions import SessionMiddleware
import os
from datetime import timedelta
from auth import oauth, get_current_user, get_or_create_user, create_access_token
from fastapi import HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse

from models import get_db, User, UserSchema
from models.bigtable_user import BigtableUserService
import httpx

HOST = os.getenv("HOST", "http://localhost:5173")


@api.get("/auth/login", operation_id="auth_login")
async def login(request: Request):
    # Use frontend URL for OAuth callback
    redirect_uri = f"{HOST}/auth/callback"
    try:
        return await oauth.google.authorize_redirect(request, redirect_uri)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth setup error: {str(e)}")


@api.post("/auth/callback", operation_id="auth_callback")
async def auth_callback(
    request: Request,
    response: Response,
    db_service: BigtableUserService = Depends(get_db),
):
    """Handle OAuth callback - expects auth code from frontend"""
    try:
        body = await request.json()
        auth_code = body.get("code")

        if not auth_code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

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

        # Validate required fields from Google
        google_id = user_info.get("sub") or user_info.get(
            "id"
        )  # Try 'sub' first, fallback to 'id'
        if not google_id:
            raise HTTPException(
                status_code=400, detail="No user ID found in Google response"
            )

        if not user_info.get("email"):
            raise HTTPException(
                status_code=400, detail="No email found in Google response"
            )

        # Ensure we have the google_id in the user_info for get_or_create_user
        user_info["sub"] = google_id

        user = await get_or_create_user(user_info, db_service)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=24)
        )

        # Set httpOnly cookie instead of returning token
        is_production = os.getenv("ENVIRONMENT") == "production"
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_production,  # Only secure in production (HTTPS)
            max_age=30 * 24 * 60 * 60,  # 30 days
        )

        return {"user": user, "success": True}

    except httpx.HTTPStatusError as e:
        print(f"HTTP error during token exchange: {e.response.text}")
        raise HTTPException(
            status_code=400, detail=f"Token exchange failed: {e.response.text}"
        )
    except Exception as e:
        print(f"General error in auth callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@api.get("/auth/logout", operation_id="auth_logout")
async def logout(request: Request, response: Response):
    # Clear the httpOnly cookie
    is_production = os.getenv("ENVIRONMENT") == "production"
    response.delete_cookie(key="access_token", httponly=True, secure=is_production)
    return {"message": "Logged out"}


@api.get("/auth/me", response_model=UserSchema, operation_id="auth_get_me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
