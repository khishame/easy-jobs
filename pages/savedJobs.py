import streamlit as st
import psycopg2
import bcrypt
import io
import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ── User / profile queries ────────────────────────────────────────────────────

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

def get_user_profile(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, surname, username, email, cellphone1, cellphone2, address
                FROM users WHERE id = %s
            """, (user_id,))
            return cursor.fetchone()

def update_user_profile(user_id, name, surname, username, email, cellphone1, cellphone2, address):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET name=%s, surname=%s, username=%s, email=%s,
                    cellphone1=%s, cellphone2=%s, address=%s
                WHERE id=%s
            """, (name, surname, username, email, cellphone1, cellphone2, address, user_id))
        conn.commit()

def update_user_password(user_id, new_password):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
        conn.commit()

def delete_user_account(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE jobs SET claimed_by = NULL WHERE claimed_by = %s", (user_id,))
            cursor.execute("DELETE FROM saved_jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

# ── Saved jobs queries ────────────────────────────────────────────────────────

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

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Saved Jobs - Easy Jobs", page_icon="⭐", layout="centered")

st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0d1117; }

.block-container {
    max-width: 1000px;
    margin: auto;
    padding: 2rem 1.5rem 4rem 1.5rem;
}

.stButton > button {
    background: #161b22;
    border: 1px solid #30363d;
    color: #c9d1d9;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.4rem 0.8rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #21262d;
    border-color: #58a6ff;
    color: #58a6ff;
}

input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
}
input:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.1) !important;
}

h1 { color: #e6edf3; font-size: 1.6rem; font-weight: 700; }
p, .stMarkdown p { color: #8b949e; }
hr { border-color: #21262d; margin: 0.8rem 0; }
footer { visibility: hidden; }

[data-testid="stExpander"] {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
}

.profile-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
    text-align: center;
}
.avatar-circle {
    width: 64px; height: 64px;
    border-radius: 50%;
    background: #1f6feb;
    border: 3px solid #388bfd;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 700; color: #fff;
    margin: 0 auto 10px auto;
}
.profile-username { color: #e6edf3; font-size: 1rem; font-weight: 700; margin: 0; }
.profile-email { color: #8b949e; font-size: 0.78rem; margin: 2px 0 0 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

user_id = st.session_state.get("user_id")

if "show_profile_panel" not in st.session_state:
    st.session_state.show_profile_panel = False
if "profile_saved" not in st.session_state:
    st.session_state.profile_saved = False

# ── Sidebar profile panel ─────────────────────────────────────────────────────

with st.sidebar:
    if user_id:
        profile = get_user_profile(user_id)
        if profile:
            p_name, p_surname, p_username, p_email, p_cell1, p_cell2, p_address = profile
            initials = (
                (p_name[0].upper() if p_name else "") +
                (p_surname[0].upper() if p_surname else "")
            ) or "U"

            st.markdown(f"""
            <div class="profile-card">
                <div class="avatar-circle">{initials}</div>
                <p class="profile-username">{p_name or ""} {p_surname or ""}</p>
                <p class="profile-email">{p_email or ""}</p>
            </div>
            """, unsafe_allow_html=True)

            panel_label = "✕ Close Profile" if st.session_state.show_profile_panel else "👤 Edit Profile"
            if st.button(panel_label, use_container_width=True, key="toggle_profile"):
                st.session_state.show_profile_panel = not st.session_state.show_profile_panel
                st.rerun()

        if st.session_state.show_profile_panel and profile:
            st.divider()
            st.markdown("### ✏️ Edit Profile")

            new_name     = st.text_input("First Name",    value=p_name     or "", key="pf_name")
            new_surname  = st.text_input("Last Name",     value=p_surname  or "", key="pf_surname")
            new_username = st.text_input("Username",      value=p_username or "", key="pf_username")
            new_email    = st.text_input("Email",         value=p_email    or "", key="pf_email")
            new_cell1    = st.text_input("Cell Number 1", value=p_cell1    or "", key="pf_cell1")
            new_cell2    = st.text_input("Cell Number 2", value=p_cell2    or "", key="pf_cell2")
            new_address  = st.text_input("Address",       value=p_address  or "", key="pf_address")

            st.markdown("#### 🔒 Change Password")
            new_pw  = st.text_input("New Password",     type="password", key="pf_pw",  placeholder="Leave blank to keep current")
            conf_pw = st.text_input("Confirm Password", type="password", key="pf_cpw", placeholder="Repeat new password")

            st.divider()

            if st.button("💾 Save Changes", use_container_width=True, type="primary", key="pf_save"):
                if new_pw and new_pw != conf_pw:
                    st.error("❌ Passwords do not match.")
                else:
                    update_user_profile(user_id, new_name, new_surname, new_username,
                                        new_email, new_cell1, new_cell2, new_address)
                    if new_pw:
                        update_user_password(user_id, new_pw)
                    st.session_state.profile_saved = True
                    st.success("✅ Profile updated!")
                    st.rerun()

            if st.button("🚪 Log Out", use_container_width=True, key="pf_logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.switch_page("EasyJobsWebApp.py")

            st.divider()
            with st.expander("⚠️ Danger Zone", expanded=False):
                st.warning("This will **permanently delete** your account and all your data. This cannot be undone.")
                confirm_del = st.text_input("Type DELETE to confirm", key="pf_del_confirm")
                if st.button("🗑️ Delete My Account", use_container_width=True, key="pf_delete"):
                    if confirm_del.strip() == "DELETE":
                        delete_user_account(user_id)
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.success("Account deleted.")
                        st.switch_page("EasyJobsWebApp.py")
                    else:
                        st.error("Type DELETE (all caps) to confirm.")
    else:
        st.info("🔒 Log in to access your profile.")
        if st.button("🔑 Login / Register", use_container_width=True):
            st.switch_page("EasyJobsWebApp.py")

# ── Main page ─────────────────────────────────────────────────────────────────

st.title("⭐ Saved Jobs")

username = st.session_state.get("username")

if not username:
    st.warning("Please log in first.")
    st.switch_page("EasyJobsWebApp.py")
else:
    if not user_id:
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
