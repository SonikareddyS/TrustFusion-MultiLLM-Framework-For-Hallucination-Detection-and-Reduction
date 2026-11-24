from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.auth.auth_handler import decode_token


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403,
                    detail="Invalid or expired token"
                )
            return credentials.credentials
        raise HTTPException(status_code=403, detail="Invalid authorization")

    def verify_jwt(self, token: str) -> bool:
        payload = decode_token(token)
        return bool(payload)


jwt_bearer = JWTBearer()