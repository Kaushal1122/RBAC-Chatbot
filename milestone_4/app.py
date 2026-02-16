import streamlit as st
import requests
import os

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Company Internal Chatbot",
    layout="wide"
)

# ---------------- Session State ----------------
if "token" not in st.session_state:
    st.session_state.token = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ---------------- Helper: Get Accessible Files ----------------
def get_accessible_files(role):
    base_path = os.path.join(os.getcwd(), "data", "raw")

    if not os.path.exists(base_path):
        return {}

    role = role.lower()

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


# ================= LOGIN UI =================
if st.session_state.token is None:
    st.title("🔐 Company Internal Chatbot")
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            with st.spinner("Connecting to backend..."):
                response = requests.post(
                    f"{API_URL}/login",
                    data={"username": username, "password": password},
                    timeout=25
                )
        except requests.exceptions.ConnectionError:
            st.error("❌ Backend server is not running.")
            st.stop()
        except requests.exceptions.ReadTimeout:
            st.error("⏳ Backend is still starting.")
            st.stop()

        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.session_state.chat_history = []
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")


# ================= LOGGED-IN STATE =================
else:
    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    # Fetch user info
    try:
        response = requests.get(
            f"{API_URL}/me",
            headers=headers,
            timeout=25
        )
    except:
        st.error("❌ Backend not responding.")
        st.stop()

    if response.status_code != 200:
        st.error("Authentication failed. Please login again.")
        st.session_state.token = None
        st.stop()

    user = response.json()

    # ---------------- Sidebar ----------------
    st.sidebar.title("👤 User Info")
    st.sidebar.write(f"**Username:** {user['username']}")
    st.sidebar.write(f"**Role:** {user['role']}")

    # 📁 Accessible Documents
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Accessible Documents")

    accessible_files = get_accessible_files(user["role"])

    if accessible_files:
        for department, files in accessible_files.items():
            with st.sidebar.expander(f"📂 {department}", expanded=False):
                for file in files:
                    st.markdown(f"📄 {file}")
    else:
        st.sidebar.write("No accessible files.")

    # 🕒 Chat History
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕒 Chat History (Session)")

    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            st.sidebar.write(f"• {chat['query']}")
    else:
        st.sidebar.write("No queries yet.")

    # ---------------- ADMIN PANEL (C-Level Only) ----------------
    if user["role"].lower() == "c-level":

        st.sidebar.markdown("---")
        st.sidebar.subheader("👑 Admin Panel")

        admin_tab = st.sidebar.radio(
            "Admin Actions",
            ["View Users", "Add User", "Delete User"]
        )

        if admin_tab == "View Users":
            response = requests.get(f"{API_URL}/admin/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                for u in users:
                    st.sidebar.write(f"👤 {u['username']} ({u['role']})")
            else:
                st.sidebar.error("Access denied.")

        elif admin_tab == "Add User":
            new_username = st.sidebar.text_input("New Username")
            new_password = st.sidebar.text_input("New Password", type="password")
            new_role = st.sidebar.selectbox(
                "Role",
                ["engineering", "finance", "hr", "marketing", "employees", "c-level"]
            )

            if st.sidebar.button("Add User"):
                response = requests.post(
                    f"{API_URL}/admin/add-user",
                    params={
                        "username": new_username,
                        "password": new_password,
                        "role": new_role
                    },
                    headers=headers
                )

                if response.status_code == 200:
                    st.sidebar.success("User added successfully")
                else:
                    st.sidebar.error(response.json().get("detail", "Error"))

        elif admin_tab == "Delete User":
            del_username = st.sidebar.text_input("Username to Delete")

            if st.sidebar.button("Delete User"):
                response = requests.delete(
                    f"{API_URL}/admin/delete-user",
                    params={"username": del_username},
                    headers=headers
                )

                if response.status_code == 200:
                    st.sidebar.success("User deleted successfully")
                else:
                    st.sidebar.error(response.json().get("detail", "Error"))

    # ---------------- Logout (For All Users) ----------------
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.chat_history = []
        st.success("Logged out successfully")
        st.stop()

    # ---------------- Chat UI (For All Users) ----------------
    st.title("💬 Company Internal Chatbot")

    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["query"])

        with st.chat_message("assistant"):
            st.write(chat["answer"])
            st.markdown(f"**Confidence:** {chat['confidence']}")
            if chat["sources"]:
                st.markdown("**Sources:**")
                for src in chat["sources"]:
                    st.write(f"- {src}")

    query = st.chat_input("Ask something about company documents...")

    if query:
        with st.chat_message("user"):
            st.write(query)

        chat_response = requests.post(
            f"{API_URL}/chat",
            json={"query": query},
            headers=headers,
            timeout=35
        )

        if chat_response.status_code == 200:
            data = chat_response.json()

            with st.chat_message("assistant"):
                st.write(data.get("answer", "No answer generated."))
                st.markdown(f"**Confidence:** {data.get('confidence', 0.0)}")
                if data.get("sources"):
                    st.markdown("**Sources:**")
                    for src in data["sources"]:
                        st.write(f"- {src}")

            st.session_state.chat_history.append({
                "query": query,
                "answer": data.get("answer"),
                "confidence": data.get("confidence"),
                "sources": data.get("sources", [])
            })

        elif chat_response.status_code == 403:
            st.error("🚫 Not authorized.")
        else:
            st.error("Something went wrong.")








# uvicorn milestone_3.main:app --workers 2
# streamlit run milestone_4/app.py

# ---------------- SAMPLE QUERIES ----------------
# Marketing:
#   Summarize key highlights of Q4 2024 marketing report
#   Describe the Q4 Projections & Targets
#   Describe the Q3 Strategic Objectives
#
# Finance:
#   Summarize the key financial highlights of Q4 2024
#   Explain 2024 Annual Summary
#   Quarterly Expense Breakdown
#
# Engineering:
#   Describe the backend system architecture
#   Explain company overview
#   What is Horizontal Scaling?

# HR
#   Give me some full names



#  General:
#  How do I apply for maternity leave?
#  Give me the details of Statutory Benefits
#  How is overtime calculated?
#  