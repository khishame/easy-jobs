import streamlit as st
import bcrypt
from dp import get_connection, get_notifications, mark_notification_read, mark_all_read, count_unread

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

st.set_page_config(page_title="Notifications - Easy Jobs", page_icon="🔔", layout="centered")

st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0b1220; }

.block-container {
    max-width: 850px;
    margin: auto;
    padding: 2rem 2rem 3rem 2rem;
}

h1 { text-align: center; font-size: 2rem; font-weight: 800; color: #38bdf8; }

div[data-testid="stContainer"] { margin-bottom: 10px; }

div[style*="background-color: #f0fdf4"] {
    background: #111827 !important;
    border-left: 4px solid #22c55e !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: none;
    color: #e5e7eb !important;
}
div[style*="background-color: #f9f9f9"] {
    background: #0f172a !important;
    border-left: 4px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    padding: 14px !important;
    color: #94a3b8 !important;
}

html, body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color: #e5e7eb; }
strong { color: #e5e7eb; }
small { color: #64748b !important; }

.stButton > button {
    width: 100%;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10);
    color: #e5e7eb;
    border-radius: 10px;
    padding: 0.45rem;
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

hr { border-color: rgba(255,255,255,0.06); }
.stAlert { border-radius: 12px; background: #0f172a; color: #cbd5e1; }
.element-container { margin-bottom: 0.6rem; }
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

st.title("🔔 Notifications")

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

            if not is_read:
                bg_style = "background-color: #f0fdf4; border-left: 4px solid #2d6a4f; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;"
                badge = "🟢"
            else:
                bg_style = "background-color: #f9f9f9; border-left: 4px solid #ccc; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;"
                badge = "⚪"

            with st.container():
                st.markdown(
                    f"""<div style="{bg_style}">
                        <strong>{badge} {message}</strong><br>
                        <small style="color: #888;">📅 {created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'Unknown time'}</small>
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
