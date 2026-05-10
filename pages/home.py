import streamlit as st
import psycopg2
import bcrypt
import io
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
                SELECT
                    j.id,
                    j.job_name,
                    j.description,
                    j.price,
                    j.image,
                    j.date_posted,
                    u.username,
                    u.email,
                    j.status
                FROM jobs j
                JOIN users u ON j.user_id = u.id
                ORDER BY j.date_posted DESC
            """)
            return cursor.fetchall()

def save_job(user_id, job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO saved_jobs (user_id, job_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (user_id, job_id))
        conn.commit()

def unsave_job(user_id, job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM saved_jobs
                WHERE user_id = %s AND job_id = %s
            """, (user_id, job_id))
        conn.commit()

def is_saved(user_id, job_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM saved_jobs
                WHERE user_id = %s AND job_id = %s
            """, (user_id, job_id))
            return cursor.fetchone() is not None

# ── Profile queries ───────────────────────────────────────────────────────────

def get_user_profile(user_id):
    """Returns (name, surname, username, email, cellphone1, cellphone2, address)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, surname, username, email, cellphone1, cellphone2, address
                FROM users
                WHERE id = %s
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
            cursor.execute("DELETE FROM saved_jobs WHERE user_id=%s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Easy Jobs", page_icon="💼", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] { background: #0d1117; }

.block-container {
    max-width: 1000px;
    margin: auto;
    padding: 2rem 1.5rem 4rem 1.5rem;
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

section[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
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

/* Sidebar profile card */
.profile-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
    text-align: center;
}
.avatar-circle {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #1f6feb;
    border: 3px solid #388bfd;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    margin: 0 auto 10px auto;
}
.profile-username {
    color: #e6edf3;
    font-size: 1rem;
    font-weight: 700;
    margin: 0;
}
.profile-email {
    color: #8b949e;
    font-size: 0.78rem;
    margin: 2px 0 0 0;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────

user_id = st.session_state.get("user_id")

if "show_profile_panel" not in st.session_state:
    st.session_state.show_profile_panel = False
if "profile_saved" not in st.session_state:
    st.session_state.profile_saved = False

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:

    # ── Profile card ──
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

        # ── Profile edit panel (slides open inside sidebar) ──
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

            # Save
            if st.button("💾 Save Changes", use_container_width=True, type="primary", key="pf_save"):
                if new_pw and new_pw != conf_pw:
                    st.error("❌ Passwords do not match.")
                else:
                    update_user_profile(
                        user_id,
                        new_name, new_surname, new_username,
                        new_email, new_cell1, new_cell2, new_address
                    )
                    if new_pw:
                        update_user_password(user_id, new_pw)
                    st.session_state.profile_saved = True
                    st.success("✅ Profile updated!")
                    st.rerun()

            # Logout
            if st.button("🚪 Log Out", use_container_width=True, key="pf_logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.switch_page("pages/login.py")

            # Delete account
            st.divider()
            with st.expander("⚠️ Danger Zone", expanded=False):
                st.warning("This will **permanently delete** your account and all your data. This cannot be undone.")
                confirm_del = st.text_input("Type **DELETE** to confirm", key="pf_del_confirm")
                if st.button("🗑️ Delete My Account", use_container_width=True, key="pf_delete"):
                    if confirm_del.strip() == "DELETE":
                        delete_user_account(user_id)
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.success("Account deleted.")
                        st.switch_page("pages/login.py")
                    else:
                        st.error("Type DELETE (all caps) to confirm.")
    else:
        st.info("🔒 Log in to access your profile.")
        if st.button("🔑 Login / Register", use_container_width=True):
            st.switch_page("pages/login.py")

    st.divider()

    # ── Filters ──
    st.header("🔍 Filters")
    st.subheader("Price Range")
    price_filter = st.radio(
        "Price", ["All", "Under R500", "R500 - R1000", "R1000 - R5000", "Above R5000"],
        label_visibility="collapsed"
    )
    st.subheader("Posted Date")
    date_filter = st.radio(
        "Date", ["All Time", "Today", "This Week", "This Month"],
        label_visibility="collapsed"
    )
    st.subheader("Sort By")
    sort_by = st.selectbox(
        "Sort", ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"],
        label_visibility="collapsed"
    )
    if st.button("Clear Filters", use_container_width=True):
        st.rerun()

# ── Main page ─────────────────────────────────────────────────────────────────

st.title("💼 Easy Jobs Marketplace")
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

search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    search_job = st.text_input(
        "Search",
        placeholder="🔍 Search for plumber, electrician, gardener...",
        label_visibility="collapsed"
    )
with search_col2:
    st.button("Search", use_container_width=True)

st.divider()

# ── Job listing ───────────────────────────────────────────────────────────────

try:
    jobs = get_all_jobs()

    if not jobs:
        st.info("📭 No jobs posted yet. Be the first to post a job!")
        if st.button("Post Your First Job 🚀"):
            st.switch_page("pages/postJob.py")
    else:
        job_list = []
        for job in jobs:
            job_id_val, job_name, description, price, image, date_posted, username, email, status = job
            job_list.append({
                "id":          job_id_val,
                "job_name":    job_name,
                "description": description,
                "price":       price,
                "image":       image,
                "date_posted": date_posted,
                "username":    username,
                "email":       email,
                "status":      status or "open"
            })

        # Search filter
        if search_job:
            job_list = [j for j in job_list if
                search_job.lower() in str(j["job_name"]).lower() or
                search_job.lower() in str(j["description"]).lower()]

        # Price filter
        if price_filter != "All":
            filtered = []
            for j in job_list:
                try:
                    p = float(str(j["price"]).replace("R", "").replace(",", "").strip() or 0)
                    if   price_filter == "Under R500"       and p < 500:             filtered.append(j)
                    elif price_filter == "R500 - R1000"     and 500  <= p <= 1000:   filtered.append(j)
                    elif price_filter == "R1000 - R5000"    and 1000 <= p <= 5000:   filtered.append(j)
                    elif price_filter == "Above R5000"      and p > 5000:            filtered.append(j)
                except:
                    continue
            job_list = filtered

        # Date filter
        if date_filter != "All Time":
            today = date.today()
            filtered = []
            for j in job_list:
                try:
                    dp = j["date_posted"].date() if hasattr(j["date_posted"], "date") else j["date_posted"]
                    if   date_filter == "Today"      and dp == today:                         filtered.append(j)
                    elif date_filter == "This Week"  and dp >= today - timedelta(days=7):     filtered.append(j)
                    elif date_filter == "This Month" and dp >= today - timedelta(days=30):    filtered.append(j)
                except:
                    continue
            job_list = filtered

        # Sort
        try:
            if sort_by == "Newest First":
                job_list = sorted(job_list, key=lambda x: x["date_posted"] or "", reverse=True)
            elif sort_by == "Oldest First":
                job_list = sorted(job_list, key=lambda x: x["date_posted"] or "")
            elif sort_by == "Price: Low to High":
                job_list = sorted(job_list, key=lambda x: float(str(x["price"] or 0).replace("R","").replace(",","").strip() or 0))
            elif sort_by == "Price: High to Low":
                job_list = sorted(job_list, key=lambda x: float(str(x["price"] or 0).replace("R","").replace(",","").strip() or 0), reverse=True)
        except:
            pass

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
                            st.markdown(
                                '<div style="height:180px;background:#21262d;border-radius:8px;'
                                'display:flex;align-items:center;justify-content:center;font-size:2rem;">🖼️</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            '<div style="height:180px;background:#21262d;border-radius:8px;'
                            'display:flex;align-items:center;justify-content:center;font-size:2.5rem;">💼</div>',
                            unsafe_allow_html=True
                        )

                with content_col:
                    status = j["status"]
                    badge_color = "#3fb950" if status == "open" else "#f85149"
                    badge_bg    = "#1a3a2a" if status == "open" else "#2d1b1b"
                    st.markdown(
                        f'<p style="font-size:1.1rem;font-weight:700;color:#e6edf3;margin:0">'
                        f'{j["job_name"]} '
                        f'<span style="background:{badge_bg};color:{badge_color};border:1px solid {badge_color};'
                        f'border-radius:12px;padding:1px 8px;font-size:0.72rem;font-weight:600;">'
                        f'{status.upper()}</span></p>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<p style="font-size:1.05rem;font-weight:700;color:#3fb950;margin:4px 0">'
                        f'💰 R{j["price"] if j["price"] else 0}</p>',
                        unsafe_allow_html=True
                    )
                    desc       = j["description"] or "No description"
                    short_desc = desc[:120] + "..." if len(desc) > 120 else desc
                    st.markdown(
                        f'<p style="color:#8b949e;font-size:0.88rem;margin:0 0 8px 0">{short_desc}</p>',
                        unsafe_allow_html=True
                    )
                    date_str = j["date_posted"].strftime('%Y-%m-%d') if j["date_posted"] else "Unknown"
                    st.markdown(
                        f'<p style="color:#6e7681;font-size:0.78rem;margin:0">'
                        f'👤 {j["username"]} &nbsp;·&nbsp; 📅 {date_str}</p>',
                        unsafe_allow_html=True
                    )

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
                            st.caption("🔒 Login")

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
                            st.markdown(
                                '<div style="background:#2d1b1b;border:1px solid #da3633;border-radius:8px;'
                                'padding:10px 6px;text-align:center;color:#f85149;font-size:0.8rem;font-weight:600;">'
                                '🔒 TAKEN</div>',
                                unsafe_allow_html=True
                            )
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
                        st.markdown(
                            '<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;'
                            'padding:10px 6px;text-align:center;color:#6e7681;font-size:0.78rem;">'
                            '🔒 Login<br>to claim</div>',
                            unsafe_allow_html=True
                        )

                st.divider()

except Exception as e:
    st.error(f"❌ Error loading jobs: {e}")
    with st.expander("Debug"):
        st.code(str(e))

st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
