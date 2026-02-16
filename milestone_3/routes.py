from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
import sqlite3
from milestone_3.database import DB_PATH
from milestone_3.models import verify_password, hash_password
from milestone_3.auth import create_access_token, get_current_user
from milestone_3.rbac import rbac_required
from milestone_3.logs import log_access
from milestone_3.rag import rag_pipeline
from pydantic import BaseModel

router = APIRouter()


# ================= LOGIN =================
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, password, role FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db_username, db_password, role = user

    if not verify_password(password, db_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": db_username,
        "role": role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ================= GET CURRENT USER =================
@router.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ================= RBAC SECURE SEARCH =================
@router.get("/secure-search")
def secure_search(
    department: str = Query(..., description="finance, hr, engineering, marketing, general"),
    current_user: dict = Depends(get_current_user)
):
    role = current_user["role"]
    username = current_user["username"]

    # RBAC CHECK
    rbac_required(department)(current_user)

    # LOG ACCESS
    log_access(username, role, f"/secure-search?department={department}", confidence=1.0)

    return {
        "requested_department": department,
        "access_granted_for_role": role,
        "data": f"Confidential {department} data"
    }


# ================= ADMIN PANEL ROUTES =================

# ---- VIEW ALL USERS ----
@router.get("/admin/users")
def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"].lower() != "c-level":
        raise HTTPException(status_code=403, detail="Access denied")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()

    conn.close()

    return [{"username": u[0], "role": u[1]} for u in users]


# ---- ADD NEW USER ----
@router.post("/admin/add-user")
def add_user(
    username: str,
    password: str,
    role: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"].lower() != "c-level":
        raise HTTPException(status_code=403, detail="Access denied")

    role = role.lower()

    allowed_roles = ["engineering", "finance", "hr", "marketing", "employees", "c-level"]

    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check duplicate user
    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(password)

    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hashed_password, role)
    )

    conn.commit()
    conn.close()

    return {"message": "User added successfully"}


# ---- DELETE USER ----
@router.delete("/admin/delete-user")
def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"].lower() != "c-level":
        raise HTTPException(status_code=403, detail="Access denied")

    # Prevent deleting yourself
    if username == current_user["username"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT role FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting last C-Level
    if user[0].lower() == "c-level":
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='c-level'")
        count = cursor.fetchone()[0]
        if count <= 1:
            conn.close()
            raise HTTPException(status_code=400, detail="Cannot delete last C-Level user")

    cursor.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

    return {"message": "User deleted successfully"}

@router.get("/accessible-documents")
def get_accessible_documents(current_user: dict = Depends(get_current_user)):

    import os

    base_path = os.path.join(os.getcwd(), "data", "raw")

    if not os.path.exists(base_path):
        return {}

    role = current_user["role"].lower()

    role_folder_map = {
        "engineering": ["engineering", "general"],
        "finance": ["finance", "general"],
        "hr": ["hr", "general"],
        "marketing": ["marketing", "general"],
        "employees": ["general"],
        "c-level": ["engineering", "finance", "hr", "marketing", "general"]
    }

    requested_folders = role_folder_map.get(role, [])
    result = {}

    actual_folders = os.listdir(base_path)

    for req_folder in requested_folders:
        for actual in actual_folders:
            if actual.lower() == req_folder.lower():
                folder_path = os.path.join(base_path, actual)

                if os.path.isdir(folder_path):
                    clean_files = []

                    for file in os.listdir(folder_path):
                        if file.endswith(".md") or file.endswith(".csv"):
                            clean_files.append(file)

                    if clean_files:
                        result[actual.capitalize()] = clean_files

    return result



# class ChatRequest(BaseModel):
#     query: str

# @router.post("/chat")
# def chat(
#     request: ChatRequest,
#     current_user: dict = Depends(get_current_user)
# ):
#     role = current_user["role"]
#     result = rag_pipeline(request.query, role)
#     return result






















# @router.post("/chat")
# def chat(
#     query: str,
#     current_user: dict = Depends(get_current_user)
# ):
#     role = current_user["role"]
#     username = current_user["username"]

#     result = rag_pipeline(query, role)

#     log_access(username, role, f"/chat → {query}")

#     return result












# no parameter in secure_search
# from fastapi import APIRouter, HTTPException, Depends, Query
# from fastapi.security import OAuth2PasswordRequestForm
# import sqlite3
# from milestone_3.database import DB_PATH
# from milestone_3.models import verify_password
# from milestone_3.auth import create_access_token, get_current_user
# from milestone_3.rbac import rbac_required
# from milestone_3.logs import log_access

# router = APIRouter()

# @router.post("/login")
# def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     username = form_data.username
#     password = form_data.password

#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute(
#         "SELECT username, password, role FROM users WHERE username=?",
#         (username,)
#     )
#     user = cursor.fetchone()
#     conn.close()

#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     db_username, db_password, role = user

#     if not verify_password(password, db_password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     token = create_access_token({
#         "sub": db_username,
#         "role": role
#     })

#     return {
#         "access_token": token,
#         "token_type": "bearer"
#     }

# @router.get("/me")
# def read_me(current_user: dict = Depends(get_current_user)):
#     return current_user


# # --------- PROTECTED ENDPOINT (FIXED) ---------

# @router.get("/secure-search")
# def secure_search(current_user: dict = Depends(rbac_required())):
#     username = current_user["username"]
#     role = current_user["role"]

#     # LOG HERE (Step 9)
#     log_access(username, role, "/secure-search")

#     role_lower = role.lower()

#     if role_lower == "finance":
#         return {"data": "Finance confidential data"}

#     elif role_lower == "hr":
#         return {"data": "HR confidential data"}

#     elif role_lower == "engineering":
#         return {"data": "Engineering confidential data"}

#     elif role_lower == "marketing":
#         return {"data": "Marketing confidential data"}

#     elif role_lower == "employees":
#         return {"data": "General company data"}

#     elif role_lower == "c-level":
#         return {"data": "All company data"}

#     return {"data": "No data"}
