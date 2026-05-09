import streamlit as st
import psycopg2

# =========================
# DATABASE CONFIG
# =========================
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
# INIT DB
# =========================
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

# =========================
# VALIDATION
# =========================
def is_valid_price(value):
    try:
        float(value)
        return True
    except:
        return False

# =========================
# AUTH CHECK
# =========================
st.set_page_config(page_title="Post Jobs", page_icon="📌", layout="centered")
st.title("Post a Job")

user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("Session expired. Please log in again.")
    st.switch_page("EasyJobsWebApp.py")

# =========================
# INIT STATE SAFELY
# =========================
def reset_form():
    st.session_state["job_name"] = ""
    st.session_state["job_description"] = ""
    st.session_state["pay"] = ""

for key in ["job_name", "job_description", "pay"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# =========================
# UI
# =========================
job_name = st.text_input("Job Name", key="job_name")
job_description = st.text_area("Description", key="job_description")
pay = st.text_input("Price Offer (numbers only)", key="pay")

upload_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])

# =========================
# SUBMIT
# =========================
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