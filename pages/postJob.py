import streamlit as st
import psycopg2
import bcrypt
import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ── DB init ───────────────────────────────────────────────────────────────────

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

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_valid_price(value):
    try:
        float(value)
        return True
    except:
        return False

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Post Jobs", page_icon="📌", layout="centered")

st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #0b1220 0%, #0f172a 45%, #070b14 100%);
}
.block-container {
    max-width: 1150px;
    padding: 2rem 1.5rem;
    margin: auto;
}
html, body { font-family: "Segoe UI", Roboto, Arial, sans-serif; color: #e5e7eb; }
h1 {
    text-align: center; font-size: 2.2rem; font-weight: 700;
    color: #e5e7eb; letter-spacing: 0.3px; margin-bottom: 1.2rem;
}
h2, h3 { color: #93c5fd; font-weight: 600; }
div[data-testid="stContainer"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    backdrop-filter: blur(8px); transition: all 0.25s ease;
}
div[data-testid="stContainer"]:hover {
    transform: translateY(-4px);
    border: 1px solid rgba(59,130,246,0.5);
    box-shadow: 0 12px 30px rgba(59,130,246,0.12);
}
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white; border-radius: 10px; border: none;
    font-weight: 600; padding: 0.5rem 0.9rem; transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-2px); filter: brightness(1.1); }
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12); color: #e5e7eb;
}
input, textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e5e7eb !important; border-radius: 10px !important;
}
input:focus, textarea:focus {
    border: 1px solid #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
}
hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); }
.stCaption { color: #9ca3af; font-size: 0.85rem; }
a { color: #38bdf8; text-decoration: none; }
a:hover { text-decoration: underline; }
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

st.title("Post a Job")

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

job_name        = st.text_input("Job Name",                      key="job_name")
job_description = st.text_area("Description",                    key="job_description")
pay             = st.text_input("Price Offer (numbers only)",    key="pay")
upload_file     = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])

if st.button("Post Job"):
    job_name        = job_name.strip()
    job_description = job_description.strip()
    pay             = pay.strip()

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
            reset_form()
            st.switch_page("pages/home.py")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
