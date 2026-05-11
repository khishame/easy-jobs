import streamlit as st
import psycopg2
import os
from dp import (
    get_connection,
    send_broadcast_message,
    send_admin_direct_message,
    get_all_admin_messages,
    delete_admin_message,
)
 
# ── Config ─────────────────────────────────────────────────────────────────────
ADMIN_USERNAMES = {"AmandaU"}  # must match EasyJobsWebApp.py
 
# ── DB helpers ─────────────────────────────────────────────────────────────────
 
def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, surname, username, email, cellphone1, address
                FROM users ORDER BY id ASC
            """)
            return cur.fetchall()
 
def delete_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE jobs SET claimed_by = NULL WHERE claimed_by = %s", (user_id,))
            cur.execute("DELETE FROM saved_jobs WHERE user_id = %s",      (user_id,))
            cur.execute("DELETE FROM notifications WHERE user_id = %s",   (user_id,))
            cur.execute("DELETE FROM admin_messages WHERE user_id = %s",  (user_id,))
            cur.execute("DELETE FROM jobs WHERE user_id = %s",            (user_id,))
            cur.execute("DELETE FROM users WHERE id = %s",                (user_id,))
        conn.commit()
 
def get_all_jobs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # FIXED: Using job_name instead of title
            cur.execute("""
                SELECT j.id, j.job_name, j.description, j.location, j.price,
                       j.status, u.username AS owner,
                       c.username AS claimed_by_user
                FROM jobs j
                LEFT JOIN users u ON j.user_id = u.id
                LEFT JOIN users c ON j.claimed_by = c.id
                ORDER BY j.id DESC
            """)
            return cur.fetchall()
 
def delete_job(job_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM saved_jobs WHERE job_id = %s",      (job_id,))
            cur.execute("DELETE FROM notifications WHERE job_id = %s",   (job_id,))
            cur.execute("DELETE FROM jobs WHERE id = %s",                (job_id,))
        conn.commit()
 
def get_stats():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users");          total_users  = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM jobs");           total_jobs   = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open'"); open_jobs = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM jobs WHERE claimed_by IS NOT NULL"); claimed_jobs = cur.fetchone()[0]
    return total_users, total_jobs, open_jobs, claimed_jobs
 
# ── Page setup ─────────────────────────────────────────────────────────────────
 
st.set_page_config(page_title="Admin - Easy Jobs", page_icon="🛡️", layout="wide")
st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebar']{display:none!important;}</style>", unsafe_allow_html=True)
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }
 
[data-testid="stAppViewContainer"] { background: #0b1220; }
.block-container { max-width: 1150px; margin: auto; padding: 2rem 2rem 3rem 2rem; }
 
h1, h2, h3 { color: #38bdf8; }
p, li { color: #94a3b8; }
 
.stat-card {
    background: #131c2e;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 20px 24px; text-align: center;
}
.stat-number { font-size: 2rem; font-weight: 800; color: #38bdf8; margin: 0; }
.stat-label  { font-size: 0.85rem; color: #64748b; margin: 4px 0 0 0; }
 
.admin-badge {
    display: inline-block;
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    color: white; font-size: 0.72rem; font-weight: 700;
    padding: 2px 10px; border-radius: 20px;
    margin-left: 8px; vertical-align: middle;
}
 
.msg-broadcast {
    background: #0f2233;
    border-left: 4px solid #38bdf8;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.msg-direct {
    background: #1a1f2e;
    border-left: 4px solid #818cf8;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.msg-meta { font-size: 0.75rem; color: #475569; margin-top: 4px; }
 
.stButton > button {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10); color: #e5e7eb;
    border-radius: 8px; padding: 0.35rem 0.7rem;
    font-size: 0.82rem; font-weight: 600; transition: all 0.2s ease;
}
.stButton > button:hover {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.4);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    border: none; color: white;
}
 
hr { border-color: rgba(255,255,255,0.06); }
footer { visibility: hidden; }
 
.stTabs [data-baseweb="tab-list"] {
    background: #0f172a; border-radius: 10px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] { color: #64748b; border-radius: 8px; padding: 6px 18px; }
.stTabs [aria-selected="true"] { background: #1e3a5f !important; color: #38bdf8 !important; }
</style>
""", unsafe_allow_html=True)
 
# ── Auth check ─────────────────────────────────────────────────────────────────
 
username = st.session_state.get("username")
 
if not username:
    st.warning("⚠️ Please log in first.")
    if st.button("🔑 Go to Login"):
        st.switch_page("EasyJobsWebApp.py")
    st.stop()
 
if username.lower() not in {u.lower() for u in ADMIN_USERNAMES}:
    st.error("⛔ Access denied. You do not have admin privileges.")
    st.stop()
 
# ── Header ─────────────────────────────────────────────────────────────────────
 
col_h1, col_h2 = st.columns([7, 1])
with col_h1:
    st.markdown(
        f'<h1 style="margin-bottom:0;">🛡️ Admin Panel <span class="admin-badge">ADMIN</span></h1>'
        f'<p style="margin-top:4px;">Logged in as <strong style="color:#38bdf8;">@{username}</strong></p>',
        unsafe_allow_html=True
    )
with col_h2:
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.switch_page("EasyJobsWebApp.py")
 
st.divider()
 
# ── Stats ──────────────────────────────────────────────────────────────────────
 
try:
    total_users, total_jobs, open_jobs, claimed_jobs = get_stats()
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.markdown(f'<div class="stat-card"><p class="stat-number">{total_users}</p><p class="stat-label">Total Users</p></div>', unsafe_allow_html=True)
    with s2: st.markdown(f'<div class="stat-card"><p class="stat-number">{total_jobs}</p><p class="stat-label">Total Jobs</p></div>', unsafe_allow_html=True)
    with s3: st.markdown(f'<div class="stat-card"><p class="stat-number">{open_jobs}</p><p class="stat-label">Open Jobs</p></div>', unsafe_allow_html=True)
    with s4: st.markdown(f'<div class="stat-card"><p class="stat-number">{claimed_jobs}</p><p class="stat-label">Claimed Jobs</p></div>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Could not load stats: {e}")
 
st.write("")
 
# ── Tabs ───────────────────────────────────────────────────────────────────────
 
tab_users, tab_jobs, tab_broadcast, tab_board = st.tabs([
    "👥 Users", "💼 Jobs", "📢 Broadcast & Message", "📋 Message Board"
])
 
# ══ USERS TAB ══════════════════════════════════════════════════════════════════
 
with tab_users:
    st.markdown("### All Users")
    try:
        users = get_all_users()
    except Exception as e:
        st.error(f"Could not load users: {e}")
        users = []
 
    if not users:
        st.info("No users found.")
    else:
        search = st.text_input("🔍 Search users", placeholder="Filter by name, username or email...", key="user_search")
        filtered = [u for u in users if not search or any(search.lower() in str(v).lower() for v in u)]
        st.caption(f"Showing {len(filtered)} of {len(users)} users")
        st.write("")
 
        h0, h1, h2, h3, h4, h5, h6 = st.columns([1, 2, 2, 3, 2, 2, 1.5])
        for col, label in zip([h0,h1,h2,h3,h4,h5,h6], ["ID","Name","Username","Email","Phone","Address","Action"]):
            col.markdown(f"<small style='color:#475569;font-weight:700;'>{label}</small>", unsafe_allow_html=True)
        st.divider()
 
        for u in filtered:
            uid, name, surname, uname, email, cell, address = u
            c0,c1,c2,c3,c4,c5,c6 = st.columns([1,2,2,3,2,2,1.5])
            c0.markdown(f"<small style='color:#64748b;'>#{uid}</small>", unsafe_allow_html=True)
            c1.markdown(f"<span style='color:#e2e8f0;'>{name or ''} {surname or ''}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='color:#38bdf8;'>@{uname or ''}</span>", unsafe_allow_html=True)
            c3.markdown(f"<small style='color:#94a3b8;'>{email or ''}</small>", unsafe_allow_html=True)
            c4.markdown(f"<small style='color:#94a3b8;'>{cell or '—'}</small>", unsafe_allow_html=True)
            c5.markdown(f"<small style='color:#94a3b8;'>{address or '—'}</small>", unsafe_allow_html=True)
 
            if uname and uname.lower() in {u.lower() for u in ADMIN_USERNAMES}:
                c6.markdown("<small style='color:#475569;'>Protected</small>", unsafe_allow_html=True)
            else:
                if c6.button("🗑️ Delete", key=f"del_user_{uid}"):
                    st.session_state[f"confirm_user_{uid}"] = True
 
            if st.session_state.get(f"confirm_user_{uid}"):
                st.warning(f"⚠️ Delete user **@{uname}**? This removes all their jobs and data.")
                yes, no = st.columns(2)
                if yes.button("✅ Yes, delete", key=f"yes_user_{uid}", type="primary"):
                    try:
                        delete_user(uid)
                        st.success(f"User @{uname} deleted.")
                        st.session_state.pop(f"confirm_user_{uid}", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                if no.button("❌ Cancel", key=f"no_user_{uid}"):
                    st.session_state.pop(f"confirm_user_{uid}", None)
                    st.rerun()
 
            st.divider()
 
# ══ JOBS TAB ═══════════════════════════════════════════════════════════════════
 
with tab_jobs:
    st.markdown("### All Jobs")
    try:
        jobs = get_all_jobs()
    except Exception as e:
        st.error(f"Could not load jobs: {e}")
        jobs = []
 
    if not jobs:
        st.info("No jobs found.")
    else:
        search_j = st.text_input("🔍 Search jobs", placeholder="Filter by job name, location or owner...", key="job_search")
        filtered_j = [j for j in jobs if not search_j or any(search_j.lower() in str(v).lower() for v in j)]
        st.caption(f"Showing {len(filtered_j)} of {len(jobs)} jobs")
        st.write("")
 
        h0,h1,h2,h3,h4,h5,h6 = st.columns([1,3,2,2,1.5,2,1.5])
        for col, label in zip([h0,h1,h2,h3,h4,h5,h6], ["ID","Job Name","Location","Owner","Price","Claimed By","Action"]):
            col.markdown(f"<small style='color:#475569;font-weight:700;'>{label}</small>", unsafe_allow_html=True)
        st.divider()
 
        for j in filtered_j:
            # Updated to match the new column order (job_name instead of title)
            jid, job_name, desc, location, price, status, owner, claimed_by = j
            c0,c1,c2,c3,c4,c5,c6 = st.columns([1,3,2,2,1.5,2,1.5])
            c0.markdown(f"<small style='color:#64748b;'>#{jid}</small>", unsafe_allow_html=True)
            c1.markdown(f"<span style='color:#e2e8f0;font-weight:600;'>{job_name or ''}</span>", unsafe_allow_html=True)
            c2.markdown(f"<small style='color:#94a3b8;'>📍 {location or '—'}</small>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color:#38bdf8;'>@{owner or '—'}</span>", unsafe_allow_html=True)
            c4.markdown(f"<span style='color:#4ade80;font-weight:600;'>R{price or 0}</span>", unsafe_allow_html=True)
            c5.markdown(f"<small style='color:#94a3b8;'>{claimed_by or '—'}</small>", unsafe_allow_html=True)
 
            # Show status badge
            status_color = "#22c55e" if status == "open" else "#ef4444"
            status_text = "Open" if status == "open" else "Taken"
            
            with c6:
                st.markdown(f"<small style='color:{status_color};'>{status_text}</small>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_job_{jid}", help="Delete this job"):
                    st.session_state[f"confirm_job_{jid}"] = True
 
            if st.session_state.get(f"confirm_job_{jid}"):
                st.warning(f"⚠️ Delete job **{job_name}**?")
                yes, no = st.columns(2)
                if yes.button("✅ Yes, delete", key=f"yes_job_{jid}", type="primary"):
                    try:
                        delete_job(jid)
                        st.success(f"Job '{job_name}' deleted.")
                        st.session_state.pop(f"confirm_job_{jid}", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                if no.button("❌ Cancel", key=f"no_job_{jid}"):
                    st.session_state.pop(f"confirm_job_{jid}", None)
                    st.rerun()
 
            st.divider()
 
# ══ BROADCAST & MESSAGE TAB ════════════════════════════════════════════════════
 
with tab_broadcast:
    st.markdown("### 📢 Broadcast to All Users")
    st.markdown("<p style='color:#64748b;font-size:0.9rem;'>This message will be sent to every user on the platform and will appear in their notifications/messages.</p>", unsafe_allow_html=True)
 
    broadcast_msg = st.text_area(
        "Broadcast Message", height=120,
        placeholder="e.g. We are performing maintenance on Saturday 10 May from 2–4 PM...",
        key="broadcast_input"
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📤 Send to All Users", type="primary", key="send_broadcast", use_container_width=True):
            if not broadcast_msg.strip():
                st.error("Please enter a message before sending.")
            else:
                ok = send_broadcast_message(username, broadcast_msg.strip())
                if ok:
                    st.success("✅ Broadcast sent to all users!")
                    st.balloons()
                else:
                    st.error("❌ Failed to send broadcast. Check your database connection.")
 
    st.divider()
 
    st.markdown("### 💬 Send Direct Message to a User")
    st.markdown("<p style='color:#64748b;font-size:0.9rem;'>Send a private message to a specific user. They will see it in their message board.</p>", unsafe_allow_html=True)
 
    try:
        all_users_raw = get_all_users()
        # Exclude admin accounts from recipient list
        recipient_options = {
            f"@{u[3]} — {u[1]} {u[2]}": u[0]
            for u in all_users_raw
            if u[3] and u[3].lower() not in {a.lower() for a in ADMIN_USERNAMES}
        }
    except Exception as e:
        st.error(f"Could not load users: {e}")
        recipient_options = {}
 
    if not recipient_options:
        st.info("No users available to message.")
    else:
        selected_label = st.selectbox("Select User", options=list(recipient_options.keys()), key="dm_target")
        direct_msg = st.text_area(
            "Message", height=100,
            placeholder="Type your message to this user...",
            key="direct_msg_input"
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📨 Send Direct Message", type="primary", key="send_direct", use_container_width=True):
                if not direct_msg.strip():
                    st.error("Please enter a message.")
                else:
                    target_id = recipient_options[selected_label]
                    ok = send_admin_direct_message(username, target_id, direct_msg.strip())
                    if ok:
                        st.success(f"✅ Message sent to {selected_label}!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to send message.")
 
# ══ MESSAGE BOARD TAB ══════════════════════════════════════════════════════════
 
with tab_board:
    st.markdown("### 📋 Message Board")
    st.markdown("<p style='color:#64748b;font-size:0.9rem;'>All messages sent by admin — broadcasts and direct messages.</p>", unsafe_allow_html=True)
 
    if st.button("🔄 Refresh", key="refresh_board", use_container_width=False):
        st.rerun()
 
    try:
        all_msgs = get_all_admin_messages()
    except Exception as e:
        st.error(f"Could not load messages: {e}")
        all_msgs = []
 
    if not all_msgs:
        st.info("No messages sent yet.")
    else:
        filter_type = st.radio("Filter", ["All", "Broadcasts only", "Direct only"], horizontal=True, key="msg_filter")
        
        # Add delete all button
        col_filter, col_delete_all = st.columns([3, 1])
        with col_delete_all:
            if st.button("🗑️ Delete All", type="secondary"):
                for msg in all_msgs:
                    delete_admin_message(msg[0])
                st.rerun()
        
        st.write("")
 
        for msg in all_msgs:
            mid, to_user, from_admin, content, is_broadcast, is_read, created_at = msg
 
            if filter_type == "Broadcasts only" and not is_broadcast:
                continue
            if filter_type == "Direct only" and is_broadcast:
                continue
 
            css_class = "msg-broadcast" if is_broadcast else "msg-direct"
            kind_label = "📢 Broadcast" if is_broadcast else "💬 Direct"
            read_label = "✅ Read" if is_read else "🔵 Unread"
            time_str   = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "—"
 
            col_msg, col_del = st.columns([9, 1])
            with col_msg:
                st.markdown(f"""
                <div class="{css_class}">
                    <strong style="color:#e2e8f0;">{content}</strong>
                    <div class="msg-meta">
                        {kind_label} &nbsp;→&nbsp; <span style="color:#38bdf8;">@{to_user}</span>
                        &nbsp;|&nbsp; {read_label} &nbsp;|&nbsp; 📅 {time_str}
                        &nbsp;|&nbsp; <span style="color:#64748b;">From: {from_admin}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                st.write("")
                if st.button("🗑️", key=f"del_msg_{mid}", help="Delete this message"):
                    delete_admin_message(mid)
                    st.rerun()
            
            st.markdown("---")
 
st.caption("Easy Jobs Admin Panel © 2026")
