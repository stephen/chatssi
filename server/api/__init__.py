from fastapi import APIRouter

api = APIRouter()

# Import auth routes to register them
from . import auth
