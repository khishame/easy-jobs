import streamlit as st
import psycopg2
import bcrypt
import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ── Job queries ───────────────────────────────────────────────────────────────

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
                cursor.execute("DELETE FROM saved_jobs WHERE job_id = %s", (job_id,))
                cursor.execute("UPDATE jobs SET claimed_by = NULL WHERE id = %s", (job_id,))
                cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting job: {e}")
        return False

# ── Profile queries ───────────────────────────────────────────────────────────

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

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="My Jobs - Easy Jobs", page_icon="📁", layout="centered")

st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0b1220; }

.block-container {
    max-width: 1000px;
    margin: auto;
    padding: 2rem 2rem 3rem 2rem;
}

h1 { text-align: center; font-size: 2rem; font-weight: 800; color: #38bdf8; }

details, div[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    padding: 10px !important;
    margin-bottom: 10px !important;
}
summary { font-weight: 600; color: #e5e7eb; }

html, body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color: #e5e7eb; }
p, span, label { color: #94a3b8; }

input, textarea {
    background-color: #0f172a !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #e5e7eb !important;
}
input:focus, textarea:focus {
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 12px rgba(56,189,248,0.25) !important;
}

.stButton > button {
    width: 100%;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10);
    color: #e5e7eb;
    border-radius: 10px;
    padding: 0.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: rgba(56,189,248,0.12);
    border: 1px solid rgba(56,189,248,0.4);
    transform: translateY(-2px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    border: none; color: white;
}
.stButton > button:has(span:contains("🗑")) {
    border: 1px solid rgba(239,68,68,0.5);
    color: #f87171;
}
.stButton > button:has(span:contains("🗑")):hover {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.8);
}

div[data-testid="stVerticalBlock"] { gap: 0.6rem; }
.stCaption { color: #94a3b8; font-size: 0.8rem; }
hr { border-color: rgba(255,255,255,0.06); }
footer { visibility: hidden; }

.profile-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 16px;
    margin-bottom: 16px; text-align: center;
}
.avatar-circle {
    width: 64px; height: 64px; border-radius: 50%;
    background: #1f6feb; border: 3px solid #388bfd;
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
    if not user_id:
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
                    new_name  = st.text_input("Job Name",    value=job_name,            key=f"edit_name_{job_id}")
                    new_desc  = st.text_area("Description",  value=description or "",   key=f"edit_desc_{job_id}")
                    new_price = st.number_input("Price (R)", value=float(price) if price else 0.0,
                                                min_value=0.0, key=f"edit_price_{job_id}")
                    if st.button("💾 Save Changes", key=f"save_{job_id}"):
                        if update_job(job_id, new_name, new_desc, new_price):
                            st.success("Job updated successfully!")
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    st.write(f"**Description:** {description or '_No description_'}")
                    st.write(f"**Price:** R{price if price else '0'}")

    if st.button("Go Home"):
        st.switch_page("pages/home.py")

st.divider()
st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
