import streamlit as st
import psycopg2
import bcrypt

DB_CONFIG = {
    "dbname": "easy_jobs",
    "user": "postgres",
    "password": "Mulweli123?",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# =========================
# GET USER (ID + LOGIN DATA)
# =========================
def get_user(username_or_email):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, username, password
                    FROM users
                    WHERE LOWER(username) = LOWER(%s)
                       OR LOWER(email) = LOWER(%s)
                """, (username_or_email, username_or_email))
                
                return cursor.fetchone()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# =========================
# VERIFY USER
# =========================
def verify_user(username_or_email: str, password: str):
    try:
        result = get_user(username_or_email)

        if not result:
            return False, None, None

        user_id, username, stored_hash = result

        # 🔥 CRITICAL FIX: handle both TEXT and BYTEA
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()

        if bcrypt.checkpw(password.encode(), stored_hash):
            return True, user_id, username

        return False, None, None

    except Exception as e:
        st.error(f"Database error: {e}")
        return False, None, None

# =========================
# SESSION STATE INIT
# =========================
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

if "username" not in st.session_state:
    st.session_state["username"] = None

# =========================
# UI
# =========================
st.set_page_config(page_title="Easy Jobs", page_icon=":briefcase:", layout="centered")

st.subheader("Welcome to Easy Jobs 👋")
st.title("Sell your skills or hire a skilled worker 🔍")
st.write("Easy Jobs is a platform where skilled workers can offer services and clients can hire them.")

col1, col2 = st.columns(2)

with col1:
    user_input = st.text_input("Username or Email", placeholder="Enter here...")

with col2:
    password_input = st.text_input("Password", type="password")

# =========================
# LOGIN BUTTON
# =========================
if st.button("Login"):
    user_input = user_input.strip()
    password_input = password_input.strip()

    if not user_input or not password_input:
        st.error("Please fill in all fields")
    else:
        success, user_id, username = verify_user(user_input, password_input)

        if success:
            st.success("Login successful")

            st.session_state["user_id"] = user_id
            st.session_state["username"] = username

            # ✅ redirect to home page
            st.switch_page("pages/home.py")

        else:
            st.error("Invalid username/email or password")

# =========================
# SIGN UP BUTTON
# =========================
if st.button("Sign Up"):
    st.switch_page("pages/signUp.py")
    
