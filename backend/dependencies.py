
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from database import users_col
from security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Please log in."
        )

    payload = decode_access_token(credentials.credentials)

    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login."
        )

    if not ObjectId.is_valid(payload["sub"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid user."
        )

    user = users_col.find_one({
        "_id": ObjectId(payload["sub"])
    })

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found."
        )

    user["id"] = str(user.pop("_id"))
    user.pop("password_hash", None)

    return user


def require_roles(*roles):

    def checker(user=Depends(get_current_user)):

        if user.get("role") not in roles:
            raise HTTPException(
                status_code=403,
                detail="Permission denied."
            )

        return user

    return checker
