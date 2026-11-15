
from fastapi import APIRouter, Depends

from database import users_col, donations_col, requests_col
from dependencies import require_roles

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


@router.get("/summary")
def summary(user=Depends(require_roles("admin"))):

    return {
        "total_users": users_col.count_documents({}),
        "total_donations": donations_col.count_documents({}),
        "total_requests": requests_col.count_documents({}),
        "available_donations": donations_col.count_documents({
            "status": "available"
        }),
        "pending_requests": requests_col.count_documents({
            "status": "pending"
        })
    }


@router.get("/users")
def users(user=Depends(require_roles("admin"))):

    result = []

    for u in users_col.find(
        {},
        {"password_hash": 0}
    ).sort("created_at", -1):

        result.append({
            "id": str(u["_id"]),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "role": u.get("role", "")
        })

    return result
