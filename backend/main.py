
import os

from datetime import datetime, timezone
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import client, users_col
from security import hash_password

from routes import auth, donations, requests, admin

load_dotenv()

app = FastAPI(
    title="FoodShare API",
    description="Smart Food Waste Management System",
    version="1.0.0"
)

origins = [
    x.strip()
    for x in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500"
    ).split(",")
    if x.strip()
]
print("FoodShare allowed CORS origins:", origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(donations.router)
app.include_router(requests.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup():

    client.admin.command("ping")

    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")

    if email and password and not users_col.find_one({
        "email": email
    }):

        users_col.insert_one({
            "name": os.getenv(
                "ADMIN_NAME",
                "FoodShare Administrator"
            ),
            "email": email,
            "phone": "",
            "role": "admin",
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc)
        })


@app.get("/")
def home():
    return {
        "message": "FoodShare API is running"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
