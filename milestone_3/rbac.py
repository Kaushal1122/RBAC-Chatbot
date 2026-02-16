from fastapi import Depends, HTTPException
from milestone_3.auth import get_current_user

# RBAC rules
RBAC_RULES = {
    "finance": ["finance", "general"],
    "hr": ["hr", "general"],
    "engineering": ["engineering", "general"],
    "marketing": ["marketing", "general"],
    "employees": ["general"],
    "c-level": ["finance", "hr", "engineering", "marketing", "general"]
}

def rbac_required(department: str = None):
    """
    If department is None → allow based on role only
    If department is set → enforce department access
    """

    def checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user["role"].lower()

        if user_role not in RBAC_RULES:
            raise HTTPException(status_code=403, detail="Role not recognized")

        # If no department specified, just allow authenticated users
        if department is None:
            return current_user

        allowed_departments = RBAC_RULES[user_role]

        if department.lower() not in allowed_departments:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied for role: {user_role}"
            )

        return current_user

    return checker
