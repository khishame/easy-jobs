import streamlit as st
import psycopg2
import bcrypt
import io
import base64
from datetime import date, timedelta
from dp import claim_job
import os

# ── DB helpers ────────────────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_jobs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    job_id INTEGER NOT NULL,
                    UNIQUE(user_id, job_id)
                )
            """)
        conn.commit()

init_db()

# ── Job queries ───────────────────────────────────────────────────────────────

def get_all_jobs():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT j.id, j.job_name, j.description, j.price, j.image,
               j.date_posted, u.username, u.email, j.status
                FROM jobs j
                JOIN users u ON j.user_id = u.id
                WHERE j.status = 'open'
                ORDER BY j.date_posted DESC
            """)
            return cursor.fetchall()

def save_job(user_id, job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO saved_jobs (user_id, job_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, job_id))
        conn.commit()

def unsave_job(user_id, job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM saved_jobs WHERE user_id = %s AND job_id = %s", (user_id, job_id))
        conn.commit()

def is_saved(user_id, job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM saved_jobs WHERE user_id = %s AND job_id = %s", (user_id, job_id))
            return cursor.fetchone() is not None

# ── Profile queries ───────────────────────────────────────────────────────────

def get_user_profile(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, surname, username, email, cellphone1, cellphone2, address, profile_picture
                FROM users WHERE id = %s
            """, (user_id,))
            return cursor.fetchone()

def update_user_profile(user_id, name, surname, username, email, cellphone1, cellphone2, address, profile_picture=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET name=%s, surname=%s, username=%s, email=%s,
                    cellphone1=%s, cellphone2=%s, address=%s, profile_picture=%s
                WHERE id=%s
            """, (name, surname, username, email, cellphone1, cellphone2, address, profile_picture, user_id))
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
            cursor.execute("DELETE FROM saved_jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM jobs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Easy Jobs", layout="wide")

# Hide sidebar completely
st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebar']{display:none!important;}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0d1117; }

.block-container {
    max-width: 1000px;
    margin: auto;
    padding: 1.2rem 1.5rem 4rem 1.5rem;
}

.stButton > button {
    background: #161b22;
    border: 1px solid #30363d;
    color: #c9d1d9;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.4rem 0.8rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #21262d;
    border-color: #58a6ff;
    color: #58a6ff;
}

input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
}
input:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.1) !important;
}

h1 { color: #e6edf3; font-size: 1.6rem; font-weight: 700; }
p, .stMarkdown p { color: #8b949e; }
hr { border-color: #21262d; margin: 0.8rem 0; }
footer { visibility: hidden; }

[data-testid="stExpander"] {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
}

.profile-panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    margin-bottom: 20px;
    overflow: hidden;
}
.profile-panel-header {
    background: linear-gradient(135deg, #1a2d4a, #0d1117);
    border-bottom: 1px solid #30363d;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.panel-avatar {
    width: 72px; height: 72px;
    border-radius: 50%;
    background: #1f6feb;
    border: 3px solid #388bfd;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 700; color: #fff;
    overflow: hidden; flex-shrink: 0;
}
.panel-avatar img { width:100%; height:100%; object-fit:cover; border-radius:50%; }
.panel-name    { color: #e6edf3; font-size: 1.1rem; font-weight: 700; margin: 0 0 2px 0; }
.panel-uname   { color: #58a6ff; font-size: 0.82rem; margin: 0 0 2px 0; }
.panel-email   { color: #8b949e; font-size: 0.78rem; margin: 0; }
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

# ── Top navbar ────────────────────────────────────────────────────────────────

nav_l, nav_r = st.columns([9, 1])

with nav_l:
    st.markdown(
        '<p style="color:#e6edf3;font-size:1.15rem;font-weight:700;margin:6px 0 0 0;">💼 Easy Jobs Marketplace</p>',
        unsafe_allow_html=True
    )

with nav_r:
    if user_id:
        if avatar_src:
            avatar_display = f'<img src="{avatar_src}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;vertical-align:middle;border:2px solid #388bfd;" />'
        else:
            avatar_display = f'<span style="display:inline-flex;width:32px;height:32px;border-radius:50%;background:#1f6feb;border:2px solid #388bfd;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;">{initials}</span>'

        toggle_label = "✕ Close" if st.session_state.show_profile_panel else "👤 Profile"
        if st.button(toggle_label, key="avatar_toggle", use_container_width=True):
            st.session_state.show_profile_panel = not st.session_state.show_profile_panel
            st.session_state.confirm_delete = False
            st.rerun()
    else:
        if st.button("Login", use_container_width=True, key="login_btn"):
            st.switch_page("EasyJobsWebApp.py")

# ── Inline profile panel ──────────────────────────────────────────────────────

if st.session_state.show_profile_panel and user_id and profile:
    p_name, p_surname, p_username, p_email, p_cell1, p_cell2, p_address, p_pic = profile

    avatar_inner = (
        f'<img src="{avatar_src}" />'
        if avatar_src
        else f'<span>{initials}</span>'
    )

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

    # ── Profile picture upload ──
    st.markdown("#####  Change Profile Picture")
    new_pic = st.file_uploader("Upload a photo (JPG or PNG)", type=["jpg", "jpeg", "png"], key="pic_upload")
    if new_pic:
        st.image(io.BytesIO(new_pic.read()), width=72)
        new_pic.seek(0)

    # ── Edit fields ──
    st.markdown("###  Edit Profile")
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

    # ── Password ──
    st.markdown("####  Change Password")
    pw1, pw2 = st.columns(2)
    with pw1:
        new_pw  = st.text_input("New Password",     type="password", key="pf_pw",  placeholder="Leave blank to keep current")
    with pw2:
        conf_pw = st.text_input("Confirm Password", type="password", key="pf_cpw", placeholder="Repeat new password")

    # ── Action buttons ──
    st.markdown("")
    ba, bb, bc = st.columns([2, 1, 1])
    with ba:
        if st.button("Save Changes", use_container_width=True, type="primary", key="pf_save"):
            if new_pw and new_pw != conf_pw:
                st.error("❌ Passwords do not match.")
            else:
                # Use new pic if uploaded, else keep existing
                if new_pic:
                    pic_to_save = psycopg2.Binary(new_pic.read())
                else:
                    pic_to_save = p_pic
                update_user_profile(user_id, new_name, new_surname, new_username,
                                    new_email, new_cell1, new_cell2, new_address, pic_to_save)
                if new_pw:
                    update_user_password(user_id, new_pw)
                st.success("✅ Profile updated!")
                st.session_state.show_profile_panel = False
                st.rerun()
    with bb:
        if st.button("Log Out", use_container_width=True, key="pf_logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("EasyJobsWebApp.py")
    with bc:
        if st.button("Delete Account", use_container_width=True, key="pf_del_open"):
            st.session_state.confirm_delete = True

    # ── Delete confirmation ──
    if st.session_state.confirm_delete:
        st.warning(" This will **permanently delete** your account and all your data.")
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

# ── Nav buttons ───────────────────────────────────────────────────────────────

st.title(" Easy Jobs Marketplace")
st.write("Connect with skilled workers or find your next opportunity")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("📝 Post a Job", use_container_width=True, type="primary"):
        st.switch_page("pages/postJob.py")
with col2:
    if st.button("👤 My Jobs", use_container_width=True):
        st.switch_page("pages/myJobs.py")
with col3:
    if st.button("⭐ Saved Jobs", use_container_width=True):
        st.switch_page("pages/savedJobs.py")
with col4:
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/dashboard.py")
with col5:
    if st.button("🔔 Notifications", use_container_width=True):
        st.switch_page("pages/notifications.py")

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────

with st.expander("Filters & Sort", expanded=False):
    f1, f2, f3 = st.columns(3)
    with f1:
        price_filter = st.radio("Price Range", ["All", "Under R500", "R500 - R1000", "R1000 - R5000", "Above R5000"], key="pf_filter")
    with f2:
        date_filter  = st.radio("Posted Date", ["All Time", "Today", "This Week", "This Month"], key="df_filter")
    with f3:
        sort_by      = st.selectbox("Sort By", ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"], key="sb_filter")
    if st.button("Clear Filters", key="clear_filters"):
        st.rerun()

search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    search_job = st.text_input("Search", placeholder="🔍 Search for plumber, electrician, gardener...", label_visibility="collapsed")
with search_col2:
    st.button("Search", use_container_width=True)

st.divider()

# ── Job listing ───────────────────────────────────────────────────────────────

try:
    jobs = get_all_jobs()

    if not jobs:
        st.info(" No jobs posted yet. Be the first to post a job!")
        if st.button("Post Your First Job "):
            st.switch_page("pages/postJob.py")
    else:
        job_list = []
        for job in jobs:
            job_id_val, job_name, description, price, image, date_posted, username, email, status = job
            job_list.append({
                "id": job_id_val, "job_name": job_name, "description": description,
                "price": price, "image": image, "date_posted": date_posted,
                "username": username, "email": email, "status": status or "open"
            })

        if search_job:
            job_list = [j for j in job_list if
                search_job.lower() in str(j["job_name"]).lower() or
                search_job.lower() in str(j["description"]).lower()]

        if price_filter != "All":
            filtered = []
            for j in job_list:
                try:
                    p = float(str(j["price"]).replace("R","").replace(",","").strip() or 0)
                    if   price_filter == "Under R500"    and p < 500:           filtered.append(j)
                    elif price_filter == "R500 - R1000"  and 500  <= p <= 1000: filtered.append(j)
                    elif price_filter == "R1000 - R5000" and 1000 <= p <= 5000: filtered.append(j)
                    elif price_filter == "Above R5000"   and p > 5000:          filtered.append(j)
                except: continue
            job_list = filtered

        if date_filter != "All Time":
            today = date.today()
            filtered = []
            for j in job_list:
                try:
                    dp = j["date_posted"].date() if hasattr(j["date_posted"], "date") else j["date_posted"]
                    if   date_filter == "Today"      and dp == today:                      filtered.append(j)
                    elif date_filter == "This Week"  and dp >= today - timedelta(days=7):  filtered.append(j)
                    elif date_filter == "This Month" and dp >= today - timedelta(days=30): filtered.append(j)
                except: continue
            job_list = filtered

        try:
            if sort_by == "Newest First":
                job_list = sorted(job_list, key=lambda x: x["date_posted"] or "", reverse=True)
            elif sort_by == "Oldest First":
                job_list = sorted(job_list, key=lambda x: x["date_posted"] or "")
            elif sort_by == "Price: Low to High":
                job_list = sorted(job_list, key=lambda x: float(str(x["price"] or 0).replace("R","").replace(",","").strip() or 0))
            elif sort_by == "Price: High to Low":
                job_list = sorted(job_list, key=lambda x: float(str(x["price"] or 0).replace("R","").replace(",","").strip() or 0), reverse=True)
        except: pass

        if search_job:
            st.success(f"✅ Found {len(job_list)} job(s) matching '{search_job}'")
        else:
            st.subheader(f"📋 All Jobs ({len(job_list)} available)")

        if not job_list:
            st.warning("No jobs found matching your criteria.")
        else:
            for j in job_list:
                img_col, content_col, claim_col = st.columns([2, 5, 1.2])

                with img_col:
                    if j["image"]:
                        try:
                            st.image(io.BytesIO(bytes(j["image"])), use_container_width=True)
                        except:
                            st.markdown('<div style="height:180px;background:#21262d;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2rem;">🖼️</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="height:180px;background:#21262d;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2.5rem;">💼</div>', unsafe_allow_html=True)

                with content_col:
                    status = j["status"]
                    badge_color = "#3fb950" if status == "open" else "#f85149"
                    badge_bg    = "#1a3a2a" if status == "open" else "#2d1b1b"
                    st.markdown(
                        f'<p style="font-size:1.1rem;font-weight:700;color:#e6edf3;margin:0">{j["job_name"]} '
                        f'<span style="background:{badge_bg};color:{badge_color};border:1px solid {badge_color};border-radius:12px;padding:1px 8px;font-size:0.72rem;font-weight:600;">{status.upper()}</span></p>',
                        unsafe_allow_html=True)
                    st.markdown(f'<p style="font-size:1.05rem;font-weight:700;color:#3fb950;margin:4px 0">💰 R{j["price"] if j["price"] else 0}</p>', unsafe_allow_html=True)
                    desc = j["description"] or "No description"
                    short_desc = desc[:120] + "..." if len(desc) > 120 else desc
                    st.markdown(f'<p style="color:#8b949e;font-size:0.88rem;margin:0 0 8px 0">{short_desc}</p>', unsafe_allow_html=True)
                    date_str = j["date_posted"].strftime('%Y-%m-%d') if j["date_posted"] else "Unknown"
                    st.markdown(f'<p style="color:#6e7681;font-size:0.78rem;margin:0">👤 {j["username"]} &nbsp;·&nbsp; 📅 {date_str}</p>', unsafe_allow_html=True)

                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("📧 Contact", key=f"contact_{j['id']}", use_container_width=True):
                            st.toast(f"📧 {j['email']}")
                    with b2:
                        details_key = f"show_details_{j['id']}"
                        if details_key not in st.session_state:
                            st.session_state[details_key] = False
                        if st.button("ℹ️ Details", key=f"details_{j['id']}", use_container_width=True):
                            st.session_state[details_key] = not st.session_state[details_key]
                    with b3:
                        if user_id:
                            if is_saved(user_id, j["id"]):
                                if st.button("❌ Unsave", key=f"unsave_{j['id']}", use_container_width=True):
                                    unsave_job(user_id, j["id"])
                                    st.rerun()
                            else:
                                if st.button("⭐ Save", key=f"save_{j['id']}", use_container_width=True):
                                    save_job(user_id, j["id"])
                                    st.rerun()
                        else:
                            st.caption("Login")

                    if st.session_state.get(f"show_details_{j['id']}", False):
                        with st.container():
                            st.markdown("---")
                            st.markdown(f"**📄 Full Description:**\n\n{j['description']}")
                            st.markdown(f"**📧 Contact Email:** {j['email']}")
                            st.markdown(f"**👤 Posted by:** {j['username']}")

                with claim_col:
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                    if user_id:
                        if status == "taken":
                            st.markdown('<div style="background:#2d1b1b;border:1px solid #da3633;border-radius:8px;padding:10px 6px;text-align:center;color:#f85149;font-size:0.8rem;font-weight:600;">🔒 TAKEN</div>', unsafe_allow_html=True)
                        else:
                            if st.button("🛠️ Claim", key=f"claim_{j['id']}", use_container_width=True):
                                result = claim_job(j["id"], user_id)
                                if result == "success":
                                    st.success("✅ Claimed!")
                                    st.rerun()
                                elif result == "already_taken":
                                    st.warning("⚠️ Already taken")
                                elif result == "own_job":
                                    st.warning("⚠️ Your job")
                                else:
                                    st.error("❌ Error")
                    else:
                        st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 6px;text-align:center;color:#6e7681;font-size:0.78rem;">🔒 Login<br>to claim</div>', unsafe_allow_html=True)

                st.divider()

except Exception as e:
    st.error(f"❌ Error loading jobs: {e}")
    with st.expander("Debug"):
        st.code(str(e))

st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
