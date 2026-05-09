import streamlit as st
import psycopg2
import io


import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def get_user_id(username):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE username = %s OR email = %s
                """, (username, username))
                row = cursor.fetchone()
                return row[0] if row else None
    except Exception as e:
        st.error(f"Error getting user: {e}")
        return None


def get_saved_jobs(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        j.id,
                        j.job_name,
                        j.description,
                        j.price,
                        j.image,
                        j.date_posted,
                        u.username,
                        u.email
                    FROM saved_jobs sj
                    JOIN jobs j ON sj.job_id = j.id
                    JOIN users u ON j.user_id = u.id
                    WHERE sj.user_id = %s
                    ORDER BY j.date_posted DESC
                """, (user_id,))
                return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading saved jobs: {e}")
        return []


def unsave_job(user_id, job_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM saved_jobs
                    WHERE user_id = %s AND job_id = %s
                """, (user_id, job_id))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error removing saved job: {e}")
        return False


def show_image(image):
    if not image:
        return
    try:
        st.image(io.BytesIO(image), width=250)
    except:
        st.warning("⚠️ Image could not be displayed")
st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #0f172a, #0b1220 60%, #070b14);
}
.block-container {
    padding: 2rem 2.5rem;
    max-width: 1200px;
}
html, body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: #e5e7eb;
}

h1, h2, h3 {
    color: #38bdf8;
    font-weight: 700;
    letter-spacing: 0.3px;
}
div[data-testid="stContainer"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    backdrop-filter: blur(10px);
    transition: 0.2s ease;
}

div[data-testid="stContainer"]:hover {
    transform: translateY(-3px);
    border: 1px solid rgba(56,189,248,0.4);
    box-shadow: 0 10px 30px rgba(56,189,248,0.12);
}


.stButton > button {
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 0.45rem 1rem;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton > button:hover {
    filter: brightness(1.15);
    transform: translateY(-1px);
}

.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.08);
    color: #e5e7eb;
}

section[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid rgba(255,255,255,0.06);
}

input, textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: white !important;
    border-radius: 10px !important;
}

input:focus, textarea:focus {
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56,189,248,0.2);
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 10px;
}
hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
}

.stCaption {
    color: #9ca3af;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Saved Jobs - Easy Jobs", page_icon="⭐", layout="centered")
st.title("⭐ Saved Jobs")


username = st.session_state.get("username")

if not username:
    st.warning("Please log in first.")
    st.switch_page("EasyJobsWebApp.py")

else:
    user_id = get_user_id(username)

    if not user_id:
        st.error("Could not find your account. Please log in again.")
        st.stop()

    saved_jobs = get_saved_jobs(user_id)

    
    if st.button("← Back to Marketplace"):
        st.switch_page("pages/home.py")

    st.divider()

    if not saved_jobs:
        st.info("You haven't saved any jobs yet.")
        if st.button("Browse Jobs"):
            st.switch_page("pages/home.py")

    else:
        st.subheader(f"Your Saved Jobs ({len(saved_jobs)})")

        for job in saved_jobs:
            job_id, job_name, description, price, image, date_posted, username_poster, email = job

            with st.container(border=True):

                
                show_image(image)

                
                st.markdown(f"### {job_name}")
                st.markdown(f"**💰 R{price if price else 0}**")

                
                desc = description or "_No description provided_"
                st.write(desc[:150] + "..." if len(desc) > 150 else desc)

                st.divider()

                
                st.caption(f"👤 Posted by: {username_poster}")
                if date_posted:
                    try:
                        st.caption(f"📅 {date_posted.strftime('%Y-%m-%d')}")
                    except:
                        st.caption(f"📅 {date_posted}")
                else:
                    st.caption("📅 Unknown date")

                
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📧 Contact", key=f"contact_{job_id}", use_container_width=True):
                        st.toast(f"📧 {email}")

                with col2:
                    if st.button("ℹ️ Details", key=f"details_{job_id}", use_container_width=True):
                        with st.expander("Full Job Details", expanded=True):
                            st.write(f"**Full Description:** {description or 'N/A'}")
                            st.write(f"**Contact Email:** {email}")
                            st.write(f"**Posted by:** {username_poster}")

                with col3:
                    if st.button("❌ Unsave", key=f"unsave_{job_id}", use_container_width=True):
                        if unsave_job(user_id, job_id):
                            st.success(f"'{job_name}' removed from saved jobs.")
                            st.rerun()

        st.divider()
        st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
