import streamlit as st
import psycopg2


DB_CONFIG = {
    "dbname": "easy_jobs",
    "user": "postgres",
    "password": "Mulweli123?",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


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


def get_my_jobs(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, job_name, description, price, date_posted
                    FROM jobs
                    WHERE user_id = %s
                    ORDER BY date_posted DESC
                """, (user_id,))
                return cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        return []

def update_job(job_id, job_name, description, price):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE jobs
                    SET job_name = %s, description = %s, price = %s
                    WHERE id = %s
                """, (job_name, description, price, job_id))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating job: {e}")
        return False

def delete_job(job_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting job: {e}")
        return False


st.set_page_config(page_title="My Jobs - Easy Jobs", page_icon="📁", layout="centered")
st.title("📁 My Posted Jobs")


conflicting_keys = ["job_name", "description", "price"]
for key in conflicting_keys:
    if key in st.session_state:
        del st.session_state[key]


username = st.session_state.get("username")

if not username:
    st.warning("Please log in first.")
    st.switch_page("EasyJobsWebApp.py")

else:
    user_id = get_user_id(username)

    if not user_id:
        st.error("Could not find your account. Please log in again.")
        st.stop()

    jobs = get_my_jobs(user_id)

    if not jobs:
        st.info("You haven't posted any jobs yet.")
        if st.button("Post a Job"):
            st.switch_page("pages/postJob.py")

    else:
        st.subheader(f"Your Jobs ({len(jobs)})")

        for job in jobs:
            job_id, job_name, description, price, date_posted = job

            with st.expander(f"📌 {job_name} — R{price if price else 'N/A'}"):

                # View info
                st.caption(f"📅 Posted: {date_posted}")

                
                edit_key = f"editing_{job_id}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✏️ Edit", key=f"edit_btn_{job_id}"):
                        st.session_state[edit_key] = not st.session_state[edit_key]

                with col2:
                    if st.button("🗑 Delete", key=f"del_{job_id}"):
                        if delete_job(job_id):
                            st.success("Job deleted successfully!")
                            st.rerun()

                
                if st.session_state[edit_key]:
                    st.divider()
                    st.markdown("**Edit Job Details**")

                    new_name = st.text_input(
                        "Job Name",
                        value=job_name,
                        key=f"edit_name_{job_id}"        
                    )
                    new_desc = st.text_area(
                        "Description",
                        value=description or "",
                        key=f"edit_desc_{job_id}"       
                    )
                    new_price = st.number_input(
                        "Price (R)",
                        value=float(price) if price else 0.0,
                        min_value=0.0,
                        key=f"edit_price_{job_id}"      
                    )

                    if st.button("💾 Save Changes", key=f"save_{job_id}"):
                        if update_job(job_id, new_name, new_desc, new_price):
                            st.success("Job updated successfully!")
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    # Display mode
                    st.write(f"**Description:** {description or '_No description_'}")
                    st.write(f"**Price:** R{price if price else '0'}")

    if st.button("Go Home"):
        st.switch_page("pages/home.py")

st.divider()
st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")