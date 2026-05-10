import streamlit as st
import psycopg2
import bcrypt
import base64
import io
from dp import get_connection, get_notifications, mark_notification_read, mark_all_read, count_unread
 
def get_user_id(username):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, username))
                row = cursor.fetchone()
                return row[0] if row else None
    except Exception as e:
        st.error(f"Error getting user: {e}")
        return None
 
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
            cursor.execute("DELETE FROM saved_jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
 
st.set_page_config(page_title="Notifications - Easy Jobs", page_icon="🔔", layout="centered")
 
st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebar']{display:none!important;}</style>", unsafe_allow_html=True)
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }
 
[data-testid="stAppViewContainer"] { background: #0b1220; }
 
.block-container {
    max-width: 850px;
    margin: auto;
    padding: 1.2rem 2rem 3rem 2rem;
}
 
h1 { text-align: center; font-size: 2rem; font-weight: 800; color: #38bdf8; }
 
div[data-testid="stContainer"] { margin-bottom: 10px; }
 
html, body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color: #e5e7eb; }
strong { color: #e5e7eb; }
small { color: #64748b !important; }
 
.stButton > button {
    width: 100%; background: transparent;
    border: 1px solid rgba(255,255,255,0.10); color: #e5e7eb;
    border-radius: 10px; padding: 0.45rem; font-weight: 600; transition: all 0.2s ease;
}
.stButton > button:hover {
    background: rgba(56,189,248,0.12);
    border: 1px solid rgba(56,189,248,0.4); transform: translateY(-2px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2563eb, #06b6d4); border: none; color: white;
}
 
hr { border-color: rgba(255,255,255,0.06); }
.stAlert { border-radius: 12px; background: #0f172a; color: #cbd5e1; }
.element-container { margin-bottom: 0.6rem; }
footer { visibility: hidden; }
 
/* ── Notification cards ── */
.notif-unread {
    background: #0f2a1e;
    border-left: 4px solid #22c55e;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.notif-unread strong { color: #bbf7d0; }
.notif-unread small  { color: #4ade80 !important; }
 
.notif-read {
    background: #131c2e;
    border-left: 4px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.notif-read strong { color: #94a3b8; }
.notif-read small  { color: #475569 !important; }
 
/* ── Profile panel ── */
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
 
user_id = st.session_state.get("user_id")
 
if "show_profile_panel" not in st.session_state:
    st.session_state.show_profile_panel = False
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False
 
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
 
nav_l, nav_r = st.columns([9, 1])
 
with nav_l:
    st.markdown(
        '<p style="color:#38bdf8;font-size:1.15rem;font-weight:700;margin:6px 0 0 0;">🔔 Notifications</p>',
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
 
    if st.button("← Back to Marketplace"):
        st.switch_page("pages/home.py")
 
    st.divider()
 
    notifications = get_notifications(user_id)
    unread_count  = count_unread(user_id)
 
    if not notifications:
        st.info("🔕 No notifications yet. You'll be notified when someone claims your job.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            if unread_count > 0:
                st.subheader(f"You have {unread_count} unread notification(s)")
            else:
                st.subheader(f"All notifications ({len(notifications)})")
        with col2:
            if unread_count > 0:
                if st.button("✅ Mark all as read", use_container_width=True):
                    mark_all_read(user_id)
                    st.rerun()
 
        st.divider()
 
        for notif in notifications:
            notif_id, job_id, message, is_read, created_at = notif
            time_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'Unknown time'
 
            if not is_read:
                css_class = "notif-unread"
                badge = "🟢"
            else:
                css_class = "notif-read"
                badge = "⚪"
 
            with st.container():
                st.markdown(
                    f"""<div class="{css_class}">
                        <strong>{badge} {message}</strong><br>
                        <small>📅 {time_str}</small>
                    </div>""",
                    unsafe_allow_html=True
                )
                if not is_read:
                    if st.button("Mark as read", key=f"read_{notif_id}"):
                        mark_notification_read(notif_id)
                        st.rerun()
                st.write("")
 
    st.divider()
    st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
