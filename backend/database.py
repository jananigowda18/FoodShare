
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://localhost:27017"
)

DATABASE_NAME = os.getenv("DATABASE_NAME", "foodshare")

client = MongoClient(
    MONGODB_URL,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]

users_col = db["users"]
donations_col = db["donations"]
requests_col = db["requests"]

users_col.create_index("email", unique=True)
donations_col.create_index("created_at")
requests_col.create_index("donation_id")
