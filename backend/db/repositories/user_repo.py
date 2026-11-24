from db.mongo import get_db
from core.auth.auth_handler import hash_password, verify_password
import datetime


async def create_user(username: str, email: str, password: str) -> dict:
    db = get_db()

    # Check if user exists
    if await db.users.find_one({"email": email}):
        return {"error": "Email already registered"}

    if await db.users.find_one({"username": username}):
        return {"error": "Username already taken"}

    user = {
        "username": username,
        "email": email,
        "password": hash_password(password),  # ✅ now safe
        "created_at": datetime.datetime.utcnow(),
        "query_count": 0,
    }

    result = await db.users.insert_one(user)

    return {
        "id": str(result.inserted_id),
        "username": username,
        "email": email,
    }


async def login_user(email: str, password: str) -> dict:
    db = get_db()

    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User not found"}

    if not verify_password(password, user["password"]):
        return {"error": "Incorrect password"}

    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
    }


async def get_user_by_id(user_id: str) -> dict:
    from bson import ObjectId

    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if user:
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "query_count": user.get("query_count", 0),
        }

    return {}