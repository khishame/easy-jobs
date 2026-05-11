import streamlit as st
import psycopg2
import bcrypt
import base64
import io
from dp import (
    get_connection, 
    get_notifications, 
    mark_notification_read, 
    mark_all_read, 
    count_unread,
    get_admin_messages, 
    mark_admin_message_read, 
    count_unread_admin_messages, 
    send_user_message_to_admin,
    get_user_own_messages
)

# =========================
# USER PROFILE FUNCTIONS (these need to be defined here or imported from dp)
# =========================

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

# =========================
# PAGE CONFIGURATION
# =========================

st.set_page_config(page_title="Notifications - Easy Jobs", page_icon="🔔", layout="centered")

# Hide sidebar
st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebar']{display:none!important;}</style>", unsafe_allow_html=True)

# Custom CSS
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

.admin-direct { border-left: 4px solid #ef4444 !important; }
.admin-broadcast { border-left: 4px solid #8b5cf6 !important; }

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

# =========================
# SESSION STATE INITIALIZATION
# =========================

if "user_id" not in st.session_state:
    st.session_state.user_id = None

user_id = st.session_state.get("user_id")

if "show_profile_panel" not in st.session_state:
    st.session_state.show_profile_panel = False
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False

# =========================
# CHECK LOGIN STATUS
# =========================

if not user_id:
    st.warning("⚠️ Please login to view notifications")
    if st.button("🔑 Go to Login"):
        st.switch_page("EasyJobsWebApp.py")
    st.stop()

# =========================
# GET USER PROFILE
# =========================

profile = get_user_profile(user_id)
if not profile:
    st.error("User profile not found")
    st.stop()

p_name, p_surname, p_username, p_email, p_cell1, p_cell2, p_address, p_pic = profile
initials = ((p_name[0].upper() if p_name else "") + (p_surname[0].upper() if p_surname else "")) or "U"
avatar_src = "data:image/jpeg;base64," + base64.b64encode(bytes(p_pic)).decode() if p_pic else None

# =========================
# HEADER WITH PROFILE TOGGLE
# =========================

nav_l, nav_r = st.columns([9, 1])

with nav_l:
    st.markdown('<p style="color:#38bdf8;font-size:1.15rem;font-weight:700;margin:6px 0 0 0;">🔔 Notifications</p>', unsafe_allow_html=True)

with nav_r:
    toggle_label = "✕ Close" if st.session_state.show_profile_panel else "👤 Profile"
    if st.button(toggle_label, key="avatar_toggle", use_container_width=True):
        st.session_state.show_profile_panel = not st.session_state.show_profile_panel
        st.session_state.confirm_delete = False
        st.rerun()

# =========================
# PROFILE PANEL
# =========================

if st.session_state.show_profile_panel:
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
        new_name = st.text_input("First Name", value=p_name or "", key="pf_name")
        new_username = st.text_input("Username", value=p_username or "", key="pf_username")
        new_cell1 = st.text_input("Cell Number 1", value=p_cell1 or "", key="pf_cell1")
        new_address = st.text_input("Address", value=p_address or "", key="pf_address")
    with c2:
        new_surname = st.text_input("Last Name", value=p_surname or "", key="pf_surname")
        new_email = st.text_input("Email", value=p_email or "", key="pf_email")
        new_cell2 = st.text_input("Cell Number 2", value=p_cell2 or "", key="pf_cell2")

    st.markdown("#### 🔒 Change Password")
    pw1, pw2 = st.columns(2)
    with pw1:
        new_password = st.text_input("New Password", type="password", key="new_pw")
    with pw2:
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pw")
    
    if st.button("🔄 Update Password", key="update_pw"):
        if new_password and new_password == confirm_password:
            if len(new_password) >= 6:
                update_user_password(user_id, new_password)
                st.success("✅ Password updated successfully!")
                st.rerun()
            else:
                st.error("❌ Password must be at least 6 characters")
        elif new_password or confirm_password:
            st.error("❌ Passwords do not match")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Profile Changes", key="save_profile"):
            update_user_profile(user_id, new_name, new_surname, new_username, new_email, new_cell1, new_cell2, new_address)
            st.success("✅ Profile updated!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Delete Account", key="delete_acc_btn"):
            st.session_state.confirm_delete = True

    if st.session_state.confirm_delete:
        st.warning("⚠️ **WARNING**: This action is permanent and cannot be undone!")
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("✅ Yes, Delete My Account", key="confirm_delete"):
                delete_user_account(user_id)
                st.session_state.clear()
                st.success("Account deleted successfully")
                st.switch_page("EasyJobsWebApp.py")
        with confirm_col2:
            if st.button("❌ Cancel", key="cancel_delete"):
                st.session_state.confirm_delete = False
                st.rerun()

# =========================
# NOTIFICATIONS SECTION
# =========================

st.markdown("---")

unread_job_notifications = count_unread(user_id)
unread_admin_messages = count_unread_admin_messages(user_id)

tab1, tab2, tab3 = st.tabs([
    f"📋 Job Updates ({unread_job_notifications})",
    f"📨 Admin Messages ({unread_admin_messages})",
    f"💬 My Messages"
])

# TAB 1: JOB NOTIFICATIONS
with tab1:
    notifications = get_notifications(user_id)
    
    if not notifications:
        st.info("📭 No job notifications yet")
    else:
        if unread_job_notifications > 0:
            if st.button("✅ Mark All Job Notifications as Read", key="mark_all_job"):
                mark_all_read(user_id)
                st.rerun()
        
        for notif in notifications:
            notif_id, message, created_at, is_read, related_job_id = notif
            
            card_class = "notif-unread" if not is_read else "notif-read"
            
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <strong>{message}</strong><br>
                        <small>{created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'Just now'}</small>
                    </div>
                    <div>
                        {'🔴 UNREAD' if not is_read else '✓ READ'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not is_read:
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button("✓ Mark Read", key=f"mark_{notif_id}"):
                        mark_notification_read(notif_id)
                        st.rerun()


with tab2:
    admin_messages = get_admin_messages(user_id)
    
    if not admin_messages:
        st.info("📭 No admin messages yet")
    else:
        for msg in admin_messages:
            msg_id, admin_username, message_content, is_broadcast, is_read, created_at = msg
            
            # Get first 50 chars as subject
            subject = message_content[:50] + ("..." if len(message_content) > 50 else "")
            type_class = "admin-direct" if not is_broadcast else "admin-broadcast"
            type_icon = "🔒" if not is_broadcast else "📢"
            type_label = "Personal" if not is_broadcast else "Announcement"
            
            st.markdown(f"""
            <div class="notif-{'unread' if not is_read else 'read'} {type_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <strong>{type_icon} {subject}</strong><br>
                        <span style="font-size: 0.9em;">{message_content[:200]}{'...' if len(message_content) > 200 else ''}</span><br>
                        <small>From: {admin_username} • {created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'Just now'} • {type_label}</small>
                    </div>
                    <div>
                        {'🔴 UNREAD' if not is_read else '✓ READ'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not is_read:
                if st.button(f"✓ Mark as Read", key=f"mark_admin_{msg_id}"):
                    mark_admin_message_read(msg_id, user_id)
                    st.rerun()
            st.markdown("---")

# TAB 3: SEND AND VIEW MESSAGES
with tab3:
    st.markdown("### 📝 Send Message to Admin")
    
    with st.form("send_admin_message"):
        message_subject = st.text_input("Subject", placeholder="e.g., Question about job posting", key="msg_subject")
        message_content = st.text_area("Message", placeholder="Type your message here...", height=100, key="msg_content")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("📤 Send", use_container_width=True)
        
        if submitted:
            if message_subject and message_content:
                success = send_user_message_to_admin(user_id, message_subject, message_content)
                if success:
                    st.success("✅ Message sent to admin successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to send message. Please try again.")
            else:
                st.warning("⚠️ Please fill in both subject and message")
    
    st.markdown("---")
    st.markdown("### 📂 My Sent Messages")
    
    user_messages = get_user_own_messages(user_id)
    
    if not user_messages:
        st.info("📭 You haven't sent any messages yet")
    else:
        for msg in user_messages:
            msg_id, subject, message, admin_response, responded_at, created_at = msg
            
            with st.expander(f"📧 {subject} - {created_at.strftime('%Y-%m-%d %H:%M') if created_at else 'Just now'}"):
                st.markdown(f"**Your Message:**\n{message}")
                if admin_response:
                    st.markdown(f"**Admin Response:**\n{admin_response}")
                    st.markdown(f"*Responded on: {responded_at.strftime('%Y-%m-%d %H:%M') if responded_at else 'N/A'}*")
                else:
                    st.info("⏳ Waiting for admin response...")

# =========================
# FOOTER
# =========================

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #64748b; font-size: 0.8rem;">'
    '🔔 Stay updated with your job notifications and admin messages</p>',
    unsafe_allow_html=True
)
