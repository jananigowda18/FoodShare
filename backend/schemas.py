
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    role: str
    password: str = Field(min_length=8, max_length=128)

    # Optional location details
    location: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class DonationInput(BaseModel):
    food_name: str = Field(min_length=2, max_length=120)
    category: str
    quantity: float = Field(gt=0)
    unit: str
    expiry_date: str

    # Pickup address and coordinates
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    description: Optional[str] = ""


class RequestInput(BaseModel):
    donation_id: str
    message: Optional[str] = ""


class RequestStatusInput(BaseModel):
    status: str
