import streamlit as st
import psycopg2
import io
from datetime import date, timedelta
from dp import claim_job
import os

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

st.set_page_config(page_title="Easy Jobs", page_icon="💼", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }

[data-testid="stAppViewContainer"] {
    background: #0d1117;
}

.block-container {
    max-width: 1000px;
    margin: auto;
    padding: 2rem 1.5rem 4rem 1.5rem;
}

/* NAV BUTTONS */
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

/* JOB ROW CARD */
.job-row {
    display: flex;
    gap: 0;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
    transition: border-color 0.2s ease;
}
.job-row:hover {
    border-color: #58a6ff;
}

/* IMAGE SECTION */
.job-image-wrap {
    width: 200px;
    min-width: 200px;
    height: 160px;
    overflow: hidden;
    background: #0d1117;
    display: flex;
    align-items: center;
    justify-content: center;
}
.job-image-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.job-no-image {
    width: 200px;
    min-width: 200px;
    height: 160px;
    background: #21262d;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
}

/* CONTENT SECTION */
.job-content {
    flex: 1;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-width: 0;
}
.job-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0 0 4px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.job-price {
    font-size: 1.1rem;
    font-weight: 700;
    color: #3fb950;
    margin: 0 0 6px 0;
}
.job-desc {
    font-size: 0.88rem;
    color: #8b949e;
    margin: 0 0 10px 0;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.job-meta {
    font-size: 0.78rem;
    color: #6e7681;
    font-family: 'DM Mono', monospace;
}
.job-status-open {
    display: inline-block;
    background: #1a3a2a;
    color: #3fb950;
    border: 1px solid #2ea043;
    border-radius: 12px;
    padding: 1px 8px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-left: 6px;
}
.job-status-taken {
    display: inline-block;
    background: #2d1b1b;
    color: #f85149;
    border: 1px solid #da3633;
    border-radius: 12px;
    padding: 1px 8px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-left: 6px;
}

/* CLAIM SECTION */
.job-claim {
    width: 110px;
    min-width: 110px;
    background: #0d1117;
    border-left: 1px solid #30363d;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
}

/* Search input */
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

/* expander */
[data-testid="stExpander"] {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

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

with st.sidebar:
    st.header("🔍 Filters")
    st.subheader("Price Range")
    price_filter = st.radio("Price", ["All", "Under R500", "R500 - R1000", "R1000 - R5000", "Above R5000"], label_visibility="collapsed")
    st.subheader("Posted Date")
    date_filter = st.radio("Date", ["All Time", "Today", "This Week", "This Month"], label_visibility="collapsed")
    st.subheader("Sort By")
    sort_by = st.selectbox("Sort", ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"], label_visibility="collapsed")
    if st.button("Clear Filters", use_container_width=True):
        st.rerun()

search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    search_job = st.text_input("Search", placeholder="🔍 Search for plumber, electrician, gardener...", label_visibility="collapsed")
with search_col2:
    st.button("Search", use_container_width=True)

st.divider()

user_id = st.session_state.get("user_id")

try:
    jobs = get_all_jobs()

    if not jobs:
        st.info("📭 No jobs posted yet. Be the first to post a job!")
        if st.button("Post Your First Job 🚀"):
            st.switch_page("pages/postJob.py")
    else:
        job_list = []
        for job in jobs:
            job_id, job_name, description, price, image, date_posted, username, email, status = job
            job_list.append({
                "id": job_id, "job_name": job_name, "description": description,
                "price": price, "image": image, "date_posted": date_posted,
                "username": username, "email": email,
                "status": status or "open"
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
                    p = float(str(j["price"]).replace("R","").replace(",","").strip() or 0)
                    if price_filter == "Under R500" and p < 500: filtered.append(j)
                    elif price_filter == "R500 - R1000" and 500 <= p <= 1000: filtered.append(j)
                    elif price_filter == "R1000 - R5000" and 1000 <= p <= 5000: filtered.append(j)
                    elif price_filter == "Above R5000" and p > 5000: filtered.append(j)
                except: continue
            job_list = filtered

        # Date filter
        if date_filter != "All Time":
            today = date.today()
            filtered = []
            for j in job_list:
                try:
                    dp = j["date_posted"].date() if hasattr(j["date_posted"], "date") else j["date_posted"]
                    if date_filter == "Today" and dp == today: filtered.append(j)
                    elif date_filter == "This Week" and dp >= today - timedelta(days=7): filtered.append(j)
                    elif date_filter == "This Month" and dp >= today - timedelta(days=30): filtered.append(j)
                except: continue
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
        except: pass

        if search_job:
            st.success(f"✅ Found {len(job_list)} job(s) matching '{search_job}'")
        else:
            st.subheader(f"📋 All Jobs ({len(job_list)} available)")

        if not job_list:
            st.warning("No jobs found matching your criteria.")
        else:
            for j in job_list:
                # Image column | Content column | Claim column
                img_col, content_col, claim_col = st.columns([2, 5, 1.2])

                with img_col:
                    if j["image"]:
                        try:
                            import base64
                            img_b64 = base64.b64encode(bytes(j["image"])).decode()
                            st.markdown(
                                f'<img src="data:image/jpeg;base64,{img_b64}" '
                                f'style="width:100%;height:180px;object-fit:cover;border-radius:8px;">',
                                unsafe_allow_html=True
        )
    except:
        st.markdown("🖼️", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<div style="height:160px;background:#21262d;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2.5rem;">💼</div>',
                            unsafe_allow_html=True
                        )

                with content_col:
                    # Title + status badge
                    status = j["status"]
                    badge_color = "#3fb950" if status == "open" else "#f85149"
                    badge_bg = "#1a3a2a" if status == "open" else "#2d1b1b"
                    st.markdown(
                        f'<p style="font-size:1.1rem;font-weight:700;color:#e6edf3;margin:0">'
                        f'{j["job_name"]} '
                        f'<span style="background:{badge_bg};color:{badge_color};border:1px solid {badge_color};border-radius:12px;padding:1px 8px;font-size:0.72rem;font-weight:600;">'
                        f'{status.upper()}</span></p>',
                        unsafe_allow_html=True
                    )

                    # Price
                    st.markdown(
                        f'<p style="font-size:1.05rem;font-weight:700;color:#3fb950;margin:4px 0">💰 R{j["price"] if j["price"] else 0}</p>',
                        unsafe_allow_html=True
                    )

                    # Description
                    desc = j["description"] or "_No description_"
                    short_desc = desc[:120] + "..." if len(desc) > 120 else desc
                    st.markdown(f'<p style="color:#8b949e;font-size:0.88rem;margin:0 0 8px 0">{short_desc}</p>', unsafe_allow_html=True)

                    # Meta
                    date_str = j["date_posted"].strftime('%Y-%m-%d') if j["date_posted"] else "Unknown"
                    st.markdown(
                        f'<p style="color:#6e7681;font-size:0.78rem;margin:0">👤 {j["username"]} &nbsp;·&nbsp; 📅 {date_str}</p>',
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

                    # Expandable details inline
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
                                '<div style="background:#2d1b1b;border:1px solid #da3633;border-radius:8px;padding:10px 6px;text-align:center;color:#f85149;font-size:0.8rem;font-weight:600;">🔒 TAKEN</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            if st.button("🛠️\nClaim", key=f"claim_{j['id']}", use_container_width=True):
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
                            '<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 6px;text-align:center;color:#6e7681;font-size:0.78rem;">🔒 Login<br>to claim</div>',
                            unsafe_allow_html=True
                        )

                st.divider()

except Exception as e:
    st.error(f"❌ Error loading jobs: {e}")
    with st.expander("Debug"):
        st.code(str(e))

st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
