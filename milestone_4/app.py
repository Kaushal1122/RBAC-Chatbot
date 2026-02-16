import streamlit as st
import requests

# ===============================
# 🔥 BACKEND SPACE URL
# ===============================
API_URL = "https://kaushal1528-chatbot.hf.space"

st.set_page_config(
    page_title="Company Internal Chatbot",
    layout="wide"
)

# ---------------- Session State ----------------
if "token" not in st.session_state:
    st.session_state.token = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


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
                    timeout=30
                )

        except requests.exceptions.ConnectionError:
            st.error("❌ Backend server is not reachable.")
            st.stop()

        except requests.exceptions.ReadTimeout:
            st.error("⏳ Backend is still starting. Please wait.")
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

    # -------- Fetch User Info --------
    try:
        response = requests.get(
            f"{API_URL}/me",
            headers=headers,
            timeout=30
        )
    except:
        st.error("❌ Backend not responding.")
        st.stop()

    if response.status_code != 200:
        st.error("Authentication failed. Please login again.")
        st.session_state.token = None
        st.stop()

    user = response.json()

    # ================= Sidebar =================
    st.sidebar.title("👤 User Info")
    st.sidebar.write(f"**Username:** {user['username']}")
    st.sidebar.write(f"**Role:** {user['role']}")

    # ================= Accessible Documents =================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Accessible Documents")

    try:
        doc_response = requests.get(
            f"{API_URL}/accessible-documents",
            headers=headers,
            timeout=30
        )

        if doc_response.status_code == 200:
            accessible_files = doc_response.json()

            if accessible_files:
                for department, files in accessible_files.items():
                    with st.sidebar.expander(f"📂 {department}", expanded=False):
                        for file in files:
                            st.markdown(f"📄 {file}")
            else:
                st.sidebar.write("No accessible files.")

        else:
            st.sidebar.error("Could not fetch documents.")

    except:
        st.sidebar.error("Backend not responding.")

    # ================= Admin Panel =================
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

    # ================= Logout =================
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.chat_history = []
        st.success("Logged out successfully")
        st.stop()

    # ================= Chat UI =================
    st.title("💬 Company Internal Chatbot")

    # Display chat history
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

    # Chat input
    query = st.chat_input("Ask something about company documents...")

    if query:

        with st.chat_message("user"):
            st.write(query)

        try:
            chat_response = requests.post(
                f"{API_URL}/chat",
                json={"query": query},
                headers=headers,
                timeout=40
            )
        except:
            st.error("Backend not responding.")
            st.stop()

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