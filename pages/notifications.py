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
st.title("🔔 Notifications")

# =========================
# AUTH CHECK
# =========================
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