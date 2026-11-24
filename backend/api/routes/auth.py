from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from core.auth.auth_handler import create_access_token
from db.repositories.user_repo import create_user, login_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(request: RegisterRequest):
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    result = await create_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    token = create_access_token({
        "sub": result["id"],
        "username": result["username"]
    })

    return {"token": token, "user": result}


@router.post("/login")
async def login(request: LoginRequest):
    result = await login_user(
        email=request.email,
        password=request.password,
    )

    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])

    token = create_access_token({
        "sub": result["id"],
        "username": result["username"]
    })

    return {"token": token, "user": result}