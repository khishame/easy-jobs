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
    """
    Marks a job as taken by a worker.
    Returns: 'success' | 'already_taken' | 'own_job' | 'error'
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:

                # Fetch job details + poster info
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

                # Can't claim your own job
                if poster_user_id == worker_user_id:
                    return "own_job"

                # Already taken
                if status == "taken":
                    return "already_taken"

                # Get worker's username
                cursor.execute("SELECT username FROM users WHERE id = %s", (worker_user_id,))
                worker_row = cursor.fetchone()
                worker_username = worker_row[0] if worker_row else "Someone"

                # Mark job as taken
                cursor.execute("""
                    UPDATE jobs
                    SET status = 'taken',
                        claimed_by = %s,
                        claimed_at = NOW()
                    WHERE id = %s
                """, (worker_user_id, job_id))

                # Create in-app notification for the poster
                message = f"🎉 Your job '{job_name}' has been claimed by {worker_username}!"
                cursor.execute("""
                    INSERT INTO notifications (user_id, job_id, message)
                    VALUES (%s, %s, %s)
                """, (poster_user_id, job_id, message))

            conn.commit()

        # Send email notification to poster
        send_email_notification(
            to_email=poster_email,
            to_name=poster_username,
            job_name=job_name,
            worker_username=worker_username
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
        msg["From"] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg["To"] = to_email

        # Plain text fallback
        text_body = f"""
Hi {to_name},

Great news! Your job posting "{job_name}" has been claimed by {worker_username}.

Log in to Easy Jobs to view details and get in touch with the worker.

— The Easy Jobs Team
        """.strip()

        # HTML email body
        html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
  <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <h2 style="color: #2d6a4f;">🎉 Your job has been claimed!</h2>
    <p>Hi <strong>{to_name}</strong>,</p>
    <p>Great news! Your job posting:</p>
    <div style="background: #f0fdf4; border-left: 4px solid #2d6a4f; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
      <strong style="font-size: 16px;">📌 {job_name}</strong>
    </div>
    <p>has been claimed by <strong>{worker_username}</strong>.</p>
    <p>Log in to <strong>Easy Jobs</strong> to view the details and get in touch with the worker.</p>
    <br>
    <p style="color: #888; font-size: 12px;">— The Easy Jobs Team</p>
  </div>
</body>
</html>
        """.strip()

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.sendmail(EMAIL_CONFIG["sender_email"], to_email, msg.as_string())

    except Exception as e:
        print(f"Email send error: {e}")  # Non-blocking — don't crash the app

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
                cursor.execute("""
                    UPDATE notifications SET is_read = TRUE WHERE id = %s
                """, (notification_id,))
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
                cursor.execute("""
                    UPDATE notifications SET is_read = TRUE WHERE user_id = %s
                """, (user_id,))
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
