
from fastapi import FastAPI
api = FastAPI()

# Import auth routes to register them
from . import auth
