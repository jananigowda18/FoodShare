
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

from fastapi import APIRouter, Depends, Query

from database import donations_col, users_col
from schemas import DonationInput
from dependencies import get_current_user, require_roles

router = APIRouter(
    prefix="/api/donations",
    tags=["Food Donations"]
)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate approximate straight-line distance in kilometres."""

    if None in (lat1, lon1, lat2, lon2):
        return None

    try:
        lat1, lon1, lat2, lon2 = map(
            float, (lat1, lon1, lat2, lon2)
        )

        earth_radius = 6371

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = (
            sin(dlat / 2) ** 2
            + cos(radians(lat1))
            * cos(radians(lat2))
            * sin(dlon / 2) ** 2
        )

        return round(
            earth_radius * 2 * atan2(sqrt(a), sqrt(1 - a)),
            2
        )

    except (TypeError, ValueError):
        return None


def serialize(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.post("")
def create_donation(
    data: DonationInput,
    user=Depends(require_roles("donor"))
):
    doc = data.model_dump()

    doc.update({
        "donor_id": user["id"],
        "donor_name": user["name"],
        "status": "available",
        "created_at": datetime.now(timezone.utc)
    })

    result = donations_col.insert_one(doc)
    doc["_id"] = result.inserted_id

    return {
        "message": "Donation created successfully.",
        "donation": serialize(doc)
    }


@router.get("")
def list_donations(
    mine: bool = Query(default=False),
    user=Depends(get_current_user)
):
    query = {}

    if user["role"] == "donor":

        if mine:
            query["donor_id"] = user["id"]
        else:
            query["donor_id"] = {"$ne": user["id"]}
            query["status"] = "available"

    elif user["role"] == "ngo":
        query["status"] = "available"

    donations = list(
        donations_col.find(query).sort("created_at", -1)
    )

    # Add distance for NGO users
    if user["role"] == "ngo":

        ngo = users_col.find_one({
            "email": user.get("email")
        })

        if ngo:
            ngo_lat = ngo.get("latitude")
            ngo_lon = ngo.get("longitude")

            for donation in donations:
                donation["distance_km"] = calculate_distance(
                    ngo_lat,
                    ngo_lon,
                    donation.get("latitude"),
                    donation.get("longitude")
                )

            # Nearest donations first.
            # Donations without coordinates appear afterwards.
            donations.sort(
                key=lambda d: (
                    d.get("distance_km") is None,
                    d.get("distance_km")
                    if d.get("distance_km") is not None
                    else 0
                )
            )

    return [serialize(d) for d in donations]
