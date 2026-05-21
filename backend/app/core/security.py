"""
Mock authentication + role-based access control (RBAC).

The spec allows mock auth. We do it the simplest secure way:
- The frontend sends a header `X-User-Id: <id>` on every request.
- `get_current_user` looks up that user in the database.
- `require_roles(...)` is a dependency factory that blocks users not in the allowed roles.

Why this is still real RBAC:
  Even though login is fake, every API route uses `require_roles(...)` so a CADET
  hitting /sorties/{id}/release with curl will get HTTP 403 Forbidden. The rules
  live on the backend, not the frontend.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, UserRole


def get_current_user(
    x_user_id: int = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    """Read X-User-Id header, fetch the matching user, or 401 if not found."""
    user = db.query(User).filter(User.id == x_user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-User-Id header",
        )
    return user


def require_roles(*allowed_roles: UserRole):
    """
    Returns a FastAPI dependency that allows only users with one of `allowed_roles`.

    Usage in a route:
        @router.patch("/{id}/release",
                      dependencies=[Depends(require_roles(UserRole.DISPATCHER, UserRole.ADMIN))])
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        # ADMIN is allowed everywhere by default.
        if current_user.role == UserRole.ADMIN or current_user.role in allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role {current_user.role.value} is not allowed for this action",
        )

    return checker
