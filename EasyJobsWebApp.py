import streamlit as st
import psycopg2
import bcrypt
import os
 
def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))
 
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
 
def verify_user(username_or_email: str, password: str):
    try:
        result = get_user(username_or_email)
 
        if not result:
            return False, None, None
 
        user_id, username, stored_hash = result
 
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()
 
        if bcrypt.checkpw(password.encode(), stored_hash):
            return True, user_id, username
 
        return False, None, None
 
    except Exception as e:
        st.error(f"Database error: {e}")
        return False, None, None
 
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
 
if "username" not in st.session_state:
    st.session_state["username"] = None
 
st.set_page_config(page_title="Easy Jobs", page_icon=":briefcase:", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
 
 
[data-testid="stAppViewContainer"] {
    background: #0b1220;
}
 
.block-container {
    max-width: 850px;
    margin: auto;
    padding-top: 3rem;
    padding-bottom: 3rem;
}
 
 
h1 {
    text-align: center;
    font-size: 2rem;
    font-weight: 800;
    color: #38bdf8;
}
 
h3, h2, p {
    text-align: center;
    color: #94a3b8;
}
 
input {
    background-color: #0f172a !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    padding: 0.6rem !important;
    color: #e5e7eb !important;
}
 
input:focus {
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 12px rgba(56,189,248,0.25) !important;
}
 
 
.stButton > button {
    width: 100%;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.12);
    color: #e5e7eb;
    border-radius: 10px;
    padding: 0.55rem;
    font-weight: 600;
    transition: all 0.2s ease;
}
 
.stButton > button:hover {
    background: rgba(56,189,248,0.12);
    border: 1px solid rgba(56,189,248,0.5);
    transform: translateY(-2px);
}
 
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    border: none;
    color: white;
}
 
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.1);
}
 
 
div[data-testid="column"] {
    padding: 0.5rem;
}
 
 
.stAlert {
    border-radius: 10px;
}
 
 
footer {
    visibility: hidden;
}
 
.element-container {
    margin-bottom: 0.8rem;
}
 
.block-container {
    gap: 0.6rem;
}
 
</style>
""", unsafe_allow_html=True)
 
st.subheader("Welcome to Easy Jobs 👋")
st.title("Sell your skills or hire a skilled worker 🔍")
st.write("Easy Jobs is a platform where skilled workers can offer services and clients can hire them.")
 
col1, col2 = st.columns(2)
 
with col1:
    user_input = st.text_input("Username or Email", placeholder="Enter here...")
 
with col2:
    password_input = st.text_input("Password", type="password")
 
# =========================
# LOGIN & SIGN UP BUTTONS SIDE BY SIDE
# =========================
btn_col1, btn_col2 = st.columns(2)
 
login_clicked = btn_col1.button("Login", use_container_width=True)
signup_clicked = btn_col2.button("Sign Up", use_container_width=True)
 
if login_clicked:
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
 
if signup_clicked:
    st.switch_page("pages/signUp.py")
