import streamlit as st
import psycopg2
import bcrypt
import base64
import io
import pandas as pd
import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ── Page history ──────────────────────────────────────────────────────────────

if "page_history" not in st.session_state:
    st.session_state.page_history = []

CURRENT_PAGE = "Dashboard"
if not st.session_state.page_history or st.session_state.page_history[-1] != CURRENT_PAGE:
    st.session_state.page_history.append(CURRENT_PAGE)

# ── Dashboard queries ─────────────────────────────────────────────────────────

def get_stats():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM jobs")
            jobs = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users")
            users = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(price) FROM jobs")
            avg_price = cursor.fetchone()[0] or 0
    return jobs, users, avg_price

def get_price_distribution():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT 
                CASE
                    WHEN price < 500 THEN 'Under R500'
                    WHEN price BETWEEN 500 AND 1000 THEN 'R500 - R1000'
                    WHEN price BETWEEN 1000 AND 5000 THEN 'R1000 - R5000'
                    ELSE 'Above R5000'
                END as range,
                COUNT(*) as total
            FROM jobs WHERE price IS NOT NULL
            GROUP BY range
        """, conn)
    return df

def get_users_over_time():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT DATE(created_at) as date, COUNT(*) as total
            FROM users
            GROUP BY DATE(created_at)
            ORDER BY date
        """, conn)
    return df

def get_recent_jobs():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT job_name, price, DATE(date_posted) as date
            FROM jobs ORDER BY date_posted DESC LIMIT 5
        """, conn)
    return df

# ── Profile queries ───────────────────────────────────────────────────────────

def get_user_profile(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, surname, username, email, cellphone1, cellphone2, address, profile_picture
                FROM users WHERE id = %s
            """, (user_id,))
            return cursor.fetchone()

def update_user_profile(user_id, name, surname, username, email, cellphone1, cellphone2, address):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET name=%s, surname=%s, username=%s, email=%s,
                    cellphone1=%s, cellphone2=%s, address=%s WHERE id=%s
            """, (name, surname, username, email, cellphone1, cellphone2, address, user_id))
        conn.commit()

def update_profile_picture(user_id, image_bytes):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET profile_picture=%s WHERE id=%s",
                           (psycopg2.Binary(image_bytes), user_id))
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
            cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM admin_messages WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM user_messages WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM saved_jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Dashboard", layout="wide")

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebar']{display:none!important;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0b1220; }

.block-container {
    max-width: 1100px;
    margin: auto;
    padding: 1.2rem 2rem 3rem 2rem;
}

h1 { font-size: 1.8rem; font-weight: 700; color: #38bdf8; text-align: left; }

div[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 12px; box-shadow: none;
}
div[data-testid="metric-container"] > div { color: #e5e7eb; }

div[data-testid="stPlotlyChart"], div[data-testid="stChart"] {
    background: #111827; border-radius: 12px;
    padding: 10px; border: 1px solid rgba(255,255,255,0.06);
}

table { background: #111827 !important; border-radius: 12px !important; overflow: hidden; }
thead tr th { background: #0f172a !important; color: #e5e7eb !important; }
tbody tr td { color: #cbd5e1 !important; }

.stButton > button {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.08);
    color: #e5e7eb; border-radius: 8px; padding: 0.4rem; font-weight: 500;
}
.stButton > button:hover {
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.4);
}

html, body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color: #e5e7eb; }
p, span, label { color: #94a3b8; }
hr { border-color: rgba(255,255,255,0.06); }
footer { visibility: hidden; }

.profile-panel {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 14px; margin-bottom: 20px; overflow: hidden;
}
.profile-panel-header {
    background: linear-gradient(135deg, #1a2d4a, #0d1117);
    border-bottom: 1px solid #30363d; padding: 20px;
    display: flex; align-items: center; gap: 16px;
}
.panel-avatar {
    width: 72px; height: 72px; border-radius: 50%;
    background: #1f6feb; border: 3px solid #388bfd;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 700; color: #fff;
    overflow: hidden; flex-shrink: 0;
}
.panel-avatar img { width:100%; height:100%; object-fit:cover; border-radius:50%; }
.panel-name  { color: #e6edf3; font-size: 1.1rem; font-weight: 700; margin: 0 0 2px 0; }
.panel-uname { color: #58a6ff; font-size: 0.82rem; margin: 0 0 2px 0; }
.panel-email { color: #8b949e; font-size: 0.78rem; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

user_id = st.session_state.get("user_id")

if "show_profile_panel" not in st.session_state:
    st.session_state.show_profile_panel = False
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False

# ── Load profile ──────────────────────────────────────────────────────────────

profile    = None
initials   = "U"
avatar_src = None

if user_id:
    profile = get_user_profile(user_id)
    if profile:
        p_name, p_surname, p_username, p_email, p_cell1, p_cell2, p_address, p_pic = profile
        initials = (
            (p_name[0].upper() if p_name else "") +
            (p_surname[0].upper() if p_surname else "")
        ) or "U"
        if p_pic:
            avatar_src = "data:image/jpeg;base64," + base64.b64encode(bytes(p_pic)).decode()

# ── Top navbar ────────────────────────────────────────────────────────────────

nav_l, nav_r = st.columns([9, 1])

with nav_l:
    st.markdown(
        '<p style="color:#38bdf8;font-size:1.15rem;font-weight:700;margin:6px 0 0 0;">📊 Dashboard</p>',
        unsafe_allow_html=True
    )

with nav_r:
    if user_id:
        toggle_label = "✕ Close" if st.session_state.show_profile_panel else "👤 Profile"
        if st.button(toggle_label, key="avatar_toggle", use_container_width=True):
            st.session_state.show_profile_panel = not st.session_state.show_profile_panel
            st.session_state.confirm_delete = False
            st.rerun()
    else:
        if st.button("🔑 Login", use_container_width=True):
            st.switch_page("EasyJobsWebApp.py")

# ── Inline profile panel ──────────────────────────────────────────────────────

if st.session_state.show_profile_panel and user_id and profile:
    p_name, p_surname, p_username, p_email, p_cell1, p_cell2, p_address, p_pic = profile

    avatar_inner = f'<img src="{avatar_src}" />' if avatar_src else f'<span>{initials}</span>'

    st.markdown(f"""
    <div class="profile-panel">
        <div class="profile-panel-header">
            <div class="panel-avatar">{avatar_inner}</div>
            <div>
                <p class="panel-name">{p_name or ""} {p_surname or ""}</p>
                <p class="panel-uname">@{p_username or ""}</p>
                <p class="panel-email">{p_email or ""}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📷 Change Profile Picture", expanded=False):
        new_pic = st.file_uploader("Upload a photo (JPG or PNG)", type=["jpg", "jpeg", "png"], key="pic_upload")
        if new_pic:
            pic_bytes = new_pic.read()
            prev_col, btn_col = st.columns([1, 3])
            with prev_col:
                st.image(io.BytesIO(pic_bytes), width=72)
            with btn_col:
                st.write("")
                if st.button("💾 Save Photo", key="save_pic"):
                    update_profile_picture(user_id, pic_bytes)
                    st.success("✅ Profile picture updated!")
                    st.rerun()

    st.markdown("### ✏️ Edit Profile")
    c1, c2 = st.columns(2)
    with c1:
        new_name     = st.text_input("First Name",    value=p_name     or "", key="pf_name")
        new_username = st.text_input("Username",      value=p_username or "", key="pf_username")
        new_cell1    = st.text_input("Cell Number 1", value=p_cell1    or "", key="pf_cell1")
        new_address  = st.text_input("Address",       value=p_address  or "", key="pf_address")
    with c2:
        new_surname  = st.text_input("Last Name",     value=p_surname  or "", key="pf_surname")
        new_email    = st.text_input("Email",         value=p_email    or "", key="pf_email")
        new_cell2    = st.text_input("Cell Number 2", value=p_cell2    or "", key="pf_cell2")

    st.markdown("#### 🔒 Change Password")
    pw1, pw2 = st.columns(2)
    with pw1:
        new_pw  = st.text_input("New Password",     type="password", key="pf_pw",  placeholder="Leave blank to keep current")
    with pw2:
        conf_pw = st.text_input("Confirm Password", type="password", key="pf_cpw", placeholder="Repeat new password")

    st.markdown("")
    ba, bb, bc = st.columns([2, 1, 1])
    with ba:
        if st.button("💾 Save Changes", use_container_width=True, type="primary", key="pf_save"):
            if new_pw and new_pw != conf_pw:
                st.error("❌ Passwords do not match.")
            else:
                update_user_profile(user_id, new_name, new_surname, new_username,
                                    new_email, new_cell1, new_cell2, new_address)
                if new_pw:
                    update_user_password(user_id, new_pw)
                st.success("✅ Profile updated!")
                st.session_state.show_profile_panel = False
                st.rerun()
    with bb:
        if st.button("🚪 Log Out", use_container_width=True, key="pf_logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("EasyJobsWebApp.py")
    with bc:
        if st.button("🗑️ Delete Account", use_container_width=True, key="pf_del_open"):
            st.session_state.confirm_delete = True

    if st.session_state.confirm_delete:
        st.warning("⚠️ This will **permanently delete** your account and all your data.")
        confirm_del = st.text_input("Type DELETE to confirm", key="pf_del_confirm")
        if st.button("Confirm Delete", key="pf_delete_final", type="primary"):
            if confirm_del.strip() == "DELETE":
                delete_user_account(user_id)
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Account deleted.")
                st.switch_page("EasyJobsWebApp.py")
            else:
                st.error("Type DELETE (all caps) to confirm.")

    st.divider()

# ── Main page ─────────────────────────────────────────────────────────────────

st.title("📊 Dashboard")

if not user_id:
    st.warning("Please log in first.")
    st.switch_page("EasyJobsWebApp.py")

jobs, users, avg_price = get_stats()

col1, col2, col3 = st.columns(3)
col1.metric("📋 Total Jobs", jobs)
col2.metric("👤 Users", users)
col3.metric("💰 Avg Price", f"R{round(avg_price, 2)}")

st.divider()

st.subheader("📊 Analytics")

col1, col2 = st.columns(2)

with col1:
    st.write("💰 Price Distribution")
    price_data = get_price_distribution()
    if not price_data.empty:
        st.bar_chart(price_data.set_index("range"))
    else:
        st.info("No price data available")

with col2:
    st.write("👤 Users Over Time")
    users_data = get_users_over_time()
    if not users_data.empty:
        users_data["date"] = pd.to_datetime(users_data["date"])
        users_data = users_data.sort_values("date")
        users_data = users_data.set_index("date")
        st.line_chart(users_data["total"])
    else:
        st.info("No user data available")

st.divider()

st.subheader("🆕 Recent Jobs")
recent = get_recent_jobs()
if not recent.empty:
    st.dataframe(recent, use_container_width=True)
else:
    st.info("No recent jobs")

st.divider()

if st.button("⬅️ Back"):
    st.switch_page("pages/home.py")
