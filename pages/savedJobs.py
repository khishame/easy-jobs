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
