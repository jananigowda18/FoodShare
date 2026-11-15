
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends

from database import users_col
from schemas import RegisterInput, LoginInput
from security import (
    hash_password,
    verify_password,
    create_access_token
)
from dependencies import get_current_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


def public_user(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "role": user.get("role", ""),
        "location": user.get("location", ""),
        "latitude": user.get("latitude"),
        "longitude": user.get("longitude")
    }


@router.post("/register")
def register(data: RegisterInput):

    role = data.role.lower().strip()

    if role not in ["donor", "ngo"]:
        raise HTTPException(
            status_code=400,
            detail="Select donor or NGO."
        )

    email = data.email.lower()

    if users_col.find_one({"email": email}):
        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )

    user = {
        "name": data.name.strip(),
        "email": email,
        "phone": data.phone.strip(),
        "role": role,
        "location": data.location or "",
        "latitude": data.latitude,
        "longitude": data.longitude,
        "password_hash": hash_password(data.password),
        "created_at": datetime.now(timezone.utc)
    }

    result = users_col.insert_one(user)
    user["_id"] = result.inserted_id

    return {
        "message": "Registration successful.",
        "user": public_user(user)
    }


@router.post("/login")
def login(data: LoginInput):

    user = users_col.find_one({
        "email": data.email.lower()
    })

    if not user or not verify_password(
        data.password,
        user.get("password_hash", "")
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    token = create_access_token(
        str(user["_id"]),
        user["role"]
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": public_user(user)
    }


@router.get("/me")
def get_profile(user=Depends(get_current_user)):
    return {"user": user}
