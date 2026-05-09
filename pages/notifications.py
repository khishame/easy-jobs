import streamlit as st
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


st.set_page_config(page_title="Notifications - Easy Jobs", page_icon="🔔", layout="centered")

st.markdown("""
<style>



[data-testid="stAppViewContainer"] {
    background: #0b1220;
}



.block-container {
    max-width: 850px;
    margin: auto;
    padding: 2rem 2rem 3rem 2rem;
}


h1 {
    text-align: center;
    font-size: 2rem;
    font-weight: 800;
    color: #38bdf8;
}



div[data-testid="stContainer"] {
    margin-bottom: 10px;
}
div[style*="background-color: #f0fdf4"] {
    background: #111827 !important;
    border-left: 4px solid #22c55e !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: none;
    color: #e5e7eb !important;
}

/* read notification */
div[style*="background-color: #f9f9f9"] {
    background: #0f172a !important;
    border-left: 4px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    padding: 14px !important;
    color: #94a3b8 !important;
}

html, body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: #e5e7eb;
}

strong {
    color: #e5e7eb;
}

/* timestamp */
small {
    color: #64748b !important;
}


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
    border: none;
    color: white;
}


.stButton > button:contains("Back") {
    border: 1px solid rgba(148,163,184,0.3);
}


hr {
    border-color: rgba(255,255,255,0.06);
}


.stAlert {
    border-radius: 12px;
    background: #0f172a;
    color: #cbd5e1;
}


.element-container {
    margin-bottom: 0.6rem;
}

.block-container {
    gap: 0.6rem;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


st.title("🔔 Notifications")

username = st.session_state.get("username")

if not username:
    st.warning("Please log in first.")
    st.switch_page("EasyJobsWebApp.py")

else:
    user_id = get_user_id(username)

    if not user_id:
        st.error("Could not find your account. Please log in again.")
        st.stop()

    # Back button
    if st.button("← Back to Marketplace"):
        st.switch_page("pages/home.py")

    st.divider()

    notifications = get_notifications(user_id)
    unread_count = count_unread(user_id)

    if not notifications:
        st.info("🔕 No notifications yet. You'll be notified when someone claims your job.")
    else:
        # Header row
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

            # Style unread vs read
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

                st.write("")  # Spacer

    st.divider()
    st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
