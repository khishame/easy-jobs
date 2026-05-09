import streamlit as st
import psycopg2

import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    job_name TEXT NOT NULL,
                    description TEXT,
                    price NUMERIC,
                    image BYTEA,
                    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()

init_db()

def is_valid_price(value):
    try:
        float(value)
        return True
    except:
        return False

st.set_page_config(page_title="Post Jobs", page_icon="📌", layout="centered")

st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #0b1220 0%, #0f172a 45%, #070b14 100%);
}

.block-container {
    max-width: 1150px;
    padding: 2rem 1.5rem;
    margin: auto;
}

html, body {
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
    color: #e5e7eb;
}

h1 {
    text-align: center;
    font-size: 2.2rem;
    font-weight: 700;
    color: #e5e7eb;
    letter-spacing: 0.3px;
    margin-bottom: 1.2rem;
}

h2, h3 {
    color: #93c5fd;
    font-weight: 600;
}

[data-testid="stHeader"] {
    background: rgba(10, 15, 25, 0.85);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

div[data-testid="stContainer"] {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    backdrop-filter: blur(8px);
    transition: all 0.25s ease;
}

div[data-testid="stContainer"]:hover {
    transform: translateY(-4px);
    border: 1px solid rgba(59,130,246,0.5);
    box-shadow: 0 12px 30px rgba(59,130,246,0.12);
}
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 0.5rem 0.9rem;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.1);
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    color: #e5e7eb;
}
input, textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
}

input:focus, textarea:focus {
    border: 1px solid #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
}

section[data-testid="stSidebar"] {
    background: rgba(10, 15, 25, 0.95);
    border-right: 1px solid rgba(255,255,255,0.08);
}

hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
}
.stCaption {
    color: #9ca3af;
    font-size: 0.85rem;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 12px;
    border-radius: 12px;
}
.block-container {
    text-align: left;
}

a {
    color: #38bdf8;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

</style>
""", unsafe_allow_html=True)

st.title("Post a Job")

user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("Session expired. Please log in again.")
    st.switch_page("EasyJobsWebApp.py")

def reset_form():
    st.session_state["job_name"] = ""
    st.session_state["job_description"] = ""
    st.session_state["pay"] = ""

for key in ["job_name", "job_description", "pay"]:
    if key not in st.session_state:
        st.session_state[key] = ""

job_name = st.text_input("Job Name", key="job_name")
job_description = st.text_area("Description", key="job_description")
pay = st.text_input("Price Offer (numbers only)", key="pay")

upload_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])

if st.button("Post Job"):

    job_name = job_name.strip()
    job_description = job_description.strip()
    pay = pay.strip()

    if not job_name:
        st.error("Job name is required")

    elif pay and not is_valid_price(pay):
        st.error("Price must be a valid number")

    else:
        try:
            image_bytes = upload_file.read() if upload_file else None

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO jobs (user_id, job_name, description, price, image)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        job_name,
                        job_description,
                        float(pay) if pay else None,
                        psycopg2.Binary(image_bytes) if image_bytes else None
                    ))
                conn.commit()

            st.success("Job posted successfully!")
            st.switch_page("pages/home.py")

        
            reset_form()

            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
