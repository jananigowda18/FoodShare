
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from database import requests_col, donations_col, users_col
from schemas import RequestInput, RequestStatusInput
from dependencies import get_current_user, require_roles

router = APIRouter(
    prefix="/api/requests",
    tags=["Food Requests"]
)


def serialize(doc):
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.post("")
def create_request(
    data: RequestInput,
    user=Depends(require_roles("ngo"))
):
    if not ObjectId.is_valid(data.donation_id):
        raise HTTPException(status_code=400, detail="Invalid donation ID.")

    donation = donations_col.find_one({
        "_id": ObjectId(data.donation_id),
        "status": "available"
    })

    if not donation:
        raise HTTPException(
            status_code=404,
            detail="Donation is not available."
        )

    existing = requests_col.find_one({
        "donation_id": data.donation_id,
        "ngo_id": user["id"],
        "status": {"$in": ["pending", "approved"]}
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You already requested this donation."
        )

    doc = {
        "donation_id": data.donation_id,
        "food_name": donation.get("food_name", ""),
        "category": donation.get("category", ""),
        "quantity": donation.get("quantity", 0),
        "unit": donation.get("unit", ""),
        "description": donation.get("description", ""),
        "location": donation.get("location", ""),
        "donor_id": donation["donor_id"],
        "donor_name": donation.get("donor_name", ""),
        "ngo_id": user["id"],
        "ngo_name": user["name"],
        "message": data.message or "",
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }

    result = requests_col.insert_one(doc)
    doc["_id"] = result.inserted_id

    return {
        "message": "Request submitted.",
        "request": serialize(doc)
    }


@router.get("")
def list_requests(user=Depends(get_current_user)):

    if user["role"] == "admin":
        query = {}
    elif user["role"] == "donor":
        query = {"donor_id": user["id"]}
    else:
        query = {"ngo_id": user["id"]}

    records = list(
        requests_col.find(query).sort("created_at", -1)
    )

    response = []

    for req in records:
        item = serialize(req)

        # Get latest donation details
        donation = None

        if ObjectId.is_valid(req.get("donation_id", "")):
            donation = donations_col.find_one({
                "_id": ObjectId(req["donation_id"])
            })

        if donation:
            item["food_name"] = donation.get("food_name", item.get("food_name", ""))
            item["category"] = donation.get("category", "")
            item["quantity"] = donation.get("quantity", 0)
            item["unit"] = donation.get("unit", "")
            item["description"] = donation.get("description", "")
            item["location"] = donation.get("location", "")

        # Only the NGO that requested the donation gets
        # donor contact information after approval.
        if (
            user["role"] == "ngo"
            and item.get("status") in ["approved", "collected"]
        ):
            donor = None

            if ObjectId.is_valid(req.get("donor_id", "")):
                donor = users_col.find_one({
                    "_id": ObjectId(req["donor_id"])
                })

            item["donor_phone"] = donor.get("phone", "") if donor else ""
            item["donor_email"] = donor.get("email", "") if donor else ""

        response.append(item)

    return response


@router.patch("/{request_id}")
def update_request(
    request_id: str,
    data: RequestStatusInput,
    user=Depends(require_roles("donor"))
):
    status = data.status.lower()

    if status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid request status."
        )

    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid request ID."
        )

    req = requests_col.find_one({
        "_id": ObjectId(request_id),
        "donor_id": user["id"],
        "status": "pending"
    })

    if not req:
        raise HTTPException(
            status_code=404,
            detail="Pending request not found."
        )

    if status == "approved":
        result = donations_col.update_one(
            {
                "_id": ObjectId(req["donation_id"]),
                "status": "available"
            },
            {
                "$set": {"status": "reserved"}
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=409,
                detail="This donation is no longer available."
            )

    requests_col.update_one(
        {"_id": req["_id"]},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return {
        "message": f"Request {status} successfully."
    }


@router.patch("/{request_id}/collect")
def mark_as_collected(
    request_id: str,
    user=Depends(require_roles("ngo"))
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid request ID."
        )

    req = requests_col.find_one({
        "_id": ObjectId(request_id),
        "ngo_id": user["id"],
        "status": "approved"
    })

    if not req:
        raise HTTPException(
            status_code=404,
            detail="Approved request not found."
        )

    result = donations_col.update_one(
        {
            "_id": ObjectId(req["donation_id"]),
            "status": "reserved"
        },
        {
            "$set": {"status": "collected"}
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=409,
            detail="Donation is not in reserved status."
        )

    requests_col.update_one(
        {"_id": req["_id"]},
        {
            "$set": {
                "status": "collected",
                "collected_at": datetime.now(timezone.utc)
            }
        }
    )

    return {
        "message": "Donation marked as collected successfully."
    }
