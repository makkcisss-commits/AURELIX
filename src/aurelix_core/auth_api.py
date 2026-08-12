from __future__ import annotations

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from .session import SessionStore

router = APIRouter()
sessions = SessionStore()

# V1 uses an already-authenticated upstream owner identity. The login secret
# must be supplied by deployment configuration; never hard-code credentials.


def issue_owner_session(owner_id: str, response: Response) -> dict[str, str]:
    session = sessions.create(owner_id)
    response.set_cookie(
        "aurelix_session",
        session.token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 60,
        path="/",
    )
    return {"status": "authenticated"}


def require_session(token: str | None) -> str:
    session = sessions.validate(token)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
    return session.owner_id


@router.get("/v1/auth/me")
def auth_me(aurelix_session: str | None = Cookie(default=None)):
    return {"authenticated": sessions.validate(aurelix_session) is not None}


@router.post("/v1/auth/logout")
def logout(response: Response, aurelix_session: str | None = Cookie(default=None)):
    if aurelix_session:
        sessions.revoke(aurelix_session)
    response.delete_cookie("aurelix_session", path="/")
    return {"status": "signed_out"}
