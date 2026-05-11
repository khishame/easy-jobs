import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
 
load_dotenv()
 
EMAIL_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": os.getenv("EMAIL"),
    "sender_password": os.getenv("EMAIL_PASS"),
    "sender_name": "Easy Jobs"
}
 
def get_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(database_url)
 
# =========================
# CLAIM A JOB
# =========================
def claim_job(job_id, worker_user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT j.status, j.user_id, j.job_name, u.email, u.username
                    FROM jobs j
                    JOIN users u ON j.user_id = u.id
                    WHERE j.id = %s
                """, (job_id,))
                row = cursor.fetchone()
                if not row:
                    return "error"
                status, poster_user_id, job_name, poster_email, poster_username = row
                if poster_user_id == worker_user_id:
                    return "own_job"
                if status == "taken":
                    return "already_taken"
                cursor.execute("SELECT username FROM users WHERE id = %s", (worker_user_id,))
                worker_row = cursor.fetchone()
                worker_username = worker_row[0] if worker_row else "Someone"
                cursor.execute("""
                    UPDATE jobs SET status = 'taken', claimed_by = %s, claimed_at = NOW()
                    WHERE id = %s
                """, (worker_user_id, job_id))
                message = f"🎉 Your job '{job_name}' has been claimed by {worker_username}!"
                cursor.execute("""
                    INSERT INTO notifications (user_id, job_id, message)
                    VALUES (%s, %s, %s)
                """, (poster_user_id, job_id, message))
            conn.commit()
        send_email_notification(
            to_email=poster_email, to_name=poster_username,
            job_name=job_name, worker_username=worker_username
        )
        return "success"
    except Exception as e:
        print(f"claim_job error: {e}")
        return "error"
 
# =========================
# SEND EMAIL NOTIFICATION
# =========================
def send_email_notification(to_email, to_name, job_name, worker_username):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your job '{job_name}' has been claimed!"
        msg["From"]    = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg["To"]      = to_email
        text_body = f"Hi {to_name},\n\nYour job \"{job_name}\" has been claimed by {worker_username}.\n\n— The Easy Jobs Team"
        html_body = f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:30px;">
  <div style="max-width:500px;margin:auto;background:white;border-radius:10px;padding:30px;">
    <h2 style="color:#2d6a4f;">🎉 Your job has been claimed!</h2>
    <p>Hi <strong>{to_name}</strong>,</p>
    <p>Your job <strong>{job_name}</strong> has been claimed by <strong>{worker_username}</strong>.</p>
    <p>Log in to Easy Jobs to view details.</p>
    <p style="color:#888;font-size:12px;">— The Easy Jobs Team</p>
  </div></body></html>"""
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.sendmail(EMAIL_CONFIG["sender_email"], to_email, msg.as_string())
    except Exception as e:
        print(f"Email send error: {e}")
 
# =========================
# GET NOTIFICATIONS
# =========================
def get_notifications(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, job_id, message, is_read, created_at
                    FROM notifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                return cursor.fetchall()
    except Exception as e:
        print(f"get_notifications error: {e}")
        return []
 
# =========================
# MARK NOTIFICATION AS READ
# =========================
def mark_notification_read(notification_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notification_id,))
            conn.commit()
    except Exception as e:
        print(f"mark_read error: {e}")
 
# =========================
# MARK ALL NOTIFICATIONS AS READ
# =========================
def mark_all_read(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,))
            conn.commit()
    except Exception as e:
        print(f"mark_all_read error: {e}")
 
# =========================
# COUNT UNREAD NOTIFICATIONS
# =========================
def count_unread(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM notifications
                    WHERE user_id = %s AND is_read = FALSE
                """, (user_id,))
                return cursor.fetchone()[0]
    except:
        return 0
 
# =========================
# ADMIN: SEND BROADCAST MESSAGE (to all users)
# =========================
def send_broadcast_message(admin_username, message):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users")
                all_users = cursor.fetchall()
                for (uid,) in all_users:
                    cursor.execute("""
                        INSERT INTO admin_messages (user_id, admin_username, message, is_broadcast)
                        VALUES (%s, %s, %s, TRUE)
                    """, (uid, admin_username, message))
            conn.commit()
        return True
    except Exception as e:
        print(f"send_broadcast error: {e}")
        return False
 
# =========================
# ADMIN: SEND DIRECT MESSAGE to a specific user
# =========================
def send_admin_direct_message(admin_username, user_id, message):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO admin_messages (user_id, admin_username, message, is_broadcast)
                    VALUES (%s, %s, %s, FALSE)
                """, (user_id, admin_username, message))
            conn.commit()
        return True
    except Exception as e:
        print(f"send_direct_message error: {e}")
        return False
 
# =========================
# USER: GET ADMIN MESSAGES for a user
# =========================
def get_admin_messages(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, admin_username, message, is_broadcast, is_read, created_at
                    FROM admin_messages
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                return cursor.fetchall()
    except Exception as e:
        print(f"get_admin_messages error: {e}")
        return []
 
# =========================
# USER: MARK ADMIN MESSAGE AS READ
# =========================
def mark_admin_message_read(message_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE admin_messages SET is_read = TRUE WHERE id = %s", (message_id,))
            conn.commit()
    except Exception as e:
        print(f"mark_admin_message_read error: {e}")
 
# =========================
# USER: COUNT UNREAD ADMIN MESSAGES
# =========================
def count_unread_admin_messages(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_messages
                    WHERE user_id = %s AND is_read = FALSE
                """, (user_id,))
                return cursor.fetchone()[0]
    except:
        return 0
 
# =========================
# ADMIN: GET ALL ADMIN MESSAGES (for message board view)
# =========================
def get_all_admin_messages():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT am.id, u.username, am.admin_username, am.message,
                           am.is_broadcast, am.is_read, am.created_at
                    FROM admin_messages am
                    JOIN users u ON am.user_id = u.id
                    ORDER BY am.created_at DESC
                """)
                return cursor.fetchall()
    except Exception as e:
        print(f"get_all_admin_messages error: {e}")
        return []
 
# =========================
# ADMIN: DELETE AN ADMIN MESSAGE
# =========================
def delete_admin_message(message_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM admin_messages WHERE id = %s", (message_id,))
            conn.commit()
        return True
    except Exception as e:
        print(f"delete_admin_message error: {e}")
        return False

def get_admin_messages(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, admin_username, message, is_broadcast, is_read, created_at
                    FROM admin_messages
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                return cursor.fetchall()
    except Exception as e:
        print(f"get_admin_messages error: {e}")
        return []

# =========================
# USER: MARK ADMIN MESSAGE READ
# =========================
def mark_admin_message_read(message_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE admin_messages SET is_read = TRUE WHERE id = %s", (message_id,))
            conn.commit()
    except Exception as e:
        print(f"mark_admin_message_read error: {e}")

# =========================
# USER: COUNT UNREAD ADMIN MESSAGES
# =========================
def count_unread_admin_messages(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_messages
                    WHERE user_id = %s AND is_read = FALSE
                """, (user_id,))
                return cursor.fetchone()[0]
    except:
        return 0

# =========================
# USER: SEND MESSAGE TO ADMIN
# =========================
def send_user_message_to_admin(user_id, message):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Find admin ID
                cursor.execute("SELECT id FROM users WHERE username = 'AmandaU' LIMIT 1")
                admin_row = cursor.fetchone()
                if admin_row:
                    admin_id = admin_row[0]
                    cursor.execute("""
                        INSERT INTO notifications (user_id, message, type)
                        VALUES (%s, %s, 'user_to_admin')
                    """, (admin_id, f"💬 Message from user {user_id}: {message}"))
                    conn.commit()
                    return True
        return False
    except:
        return False
