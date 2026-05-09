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

# =========================
# GET ALL JOBS
# =========================
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
                    u.email
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


def show_image(image):
    if not image:
        return
    try:
        st.image(io.BytesIO(image), width=250)
    except:
        st.warning("⚠️ Image could not be displayed")

st.set_page_config(page_title="Easy Jobs", page_icon=":briefcase:", layout="wide")

st.markdown("""
<style>


[data-testid="stAppViewContainer"] {
    background: #0b1220;
}


.block-container {
    max-width: 1100px;
    margin: auto;
    padding: 1.5rem 2rem 3rem 2rem;
}

h1 {
    text-align: left;
    font-size: 1.8rem;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 0.3rem;
}

/* subtitle */
p {
    color: #94a3b8;
}


div[data-testid="column"] {
    padding: 0.3rem;
}

.stButton > button {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.1);
    color: #e5e7eb;
    border-radius: 8px;
    padding: 0.4rem;
    font-weight: 500;
    transition: 0.2s ease;
}

.stButton > button:hover {
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.4);
}


section[data-testid="stSidebar"] {
    background: #0a0f1c;
    border-right: 1px solid rgba(255,255,255,0.06);
}


div[data-testid="stContainer"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
    box-shadow: none;
    transition: 0.2s ease;
}

div[data-testid="stContainer"]:hover {
    border: 1px solid rgba(56,189,248,0.4);
    transform: translateY(-2px);
}


.stButton > button {
    width: 100%;
    background: transparent;
    color: #e5e7eb;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 0.4rem;
    font-size: 0.85rem;
}

.stButton > button:hover {
    background: rgba(56,189,248,0.1);
}


input {
    background-color: #0f172a !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #e5e7eb !important;
}

input:focus {
    border: 1px solid #38bdf8 !important;
    box-shadow: none !important;
}


html, body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: #e5e7eb;
}

.stCaption {
    color: #9ca3af;
    font-size: 0.8rem;
}

hr {
    border-color: rgba(255,255,255,0.06);
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


st.title("🛠️ Easy Jobs Marketplace")
st.write("Connect with skilled workers or find your next opportunity")


col1, col2, col3, col4,col5 = st.columns(5)
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
        st.info("Feature coming soon!")
with col4:
    if st.button("🔔 Notifications", use_container_width=True):
        st.switch_page("pages/notifications.py")


st.divider()

with st.sidebar:
    st.header("🔍 Filters")

    st.subheader("Price Range")
    price_filter = st.radio(
        "Select price range:",
        ["All", "Under R500", "R500 - R1000", "R1000 - R5000", "Above R5000"],
        label_visibility="collapsed"
    )

    st.subheader("Posted Date")
    date_filter = st.radio(
        "Filter by date:",
        ["All Time", "Today", "This Week", "This Month"],
        label_visibility="collapsed"
    )

    st.subheader("Sort By")
    sort_by = st.selectbox(
        "Sort:",
        ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"],
        label_visibility="collapsed"
    )

    if st.button("Clear Filters", use_container_width=True):
        st.rerun()


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


user_id = st.session_state.get("user_id")


try:
    jobs = get_all_jobs()

    if not jobs:
        st.info("📭 No jobs posted yet. Be the first to post a job!")
        if st.button("Post Your First Job 🚀"):
            st.switch_page("pages/postJob.py")
    else:
        # Unpack jobs into dicts for easier handling
        job_list = []
        for job in jobs:
            job_id, job_name, description, price, image, date_posted, username, email = job
            job_list.append({
                "id": job_id,
                "job_name": job_name,
                "description": description,
                "price": price,
                "image": image,
                "date_posted": date_posted,
                "username": username,
                "email": email
            })

        
        if search_job:
            job_list = [
                j for j in job_list
                if search_job.lower() in str(j["job_name"]).lower() or
                   search_job.lower() in str(j["description"]).lower()
            ]

       
        if price_filter != "All":
            filtered = []
            for j in job_list:
                try:
                    price_num = float(str(j["price"]).replace("R", "").replace(",", "").strip() or 0)
                    if price_filter == "Under R500" and price_num < 500:
                        filtered.append(j)
                    elif price_filter == "R500 - R1000" and 500 <= price_num <= 1000:
                        filtered.append(j)
                    elif price_filter == "R1000 - R5000" and 1000 <= price_num <= 5000:
                        filtered.append(j)
                    elif price_filter == "Above R5000" and price_num > 5000:
                        filtered.append(j)
                except:
                    continue
            job_list = filtered

        
        if date_filter != "All Time":
            today = date.today()
            filtered = []
            for j in job_list:
                try:
                    dp = j["date_posted"].date() if hasattr(j["date_posted"], "date") else j["date_posted"]
                    if date_filter == "Today" and dp == today:
                        filtered.append(j)
                    elif date_filter == "This Week" and dp >= today - timedelta(days=7):
                        filtered.append(j)
                    elif date_filter == "This Month" and dp >= today - timedelta(days=30):
                        filtered.append(j)
                except:
                    continue
            job_list = filtered

       
        try:
            if sort_by == "Newest First":
                job_list = sorted(job_list, key=lambda x: x["date_posted"] or "", reverse=True)
            elif sort_by == "Oldest First":
                job_list = sorted(job_list, key=lambda x: x["date_posted"] or "")
            elif sort_by == "Price: Low to High":
                job_list = sorted(job_list, key=lambda x: float(str(x["price"] or 0).replace("R", "").replace(",", "").strip() or 0))
            elif sort_by == "Price: High to Low":
                job_list = sorted(job_list, key=lambda x: float(str(x["price"] or 0).replace("R", "").replace(",", "").strip() or 0), reverse=True)
        except:
            pass

        # Results count
        if search_job:
            st.success(f"✅ Found {len(job_list)} job(s) matching '{search_job}'")
        else:
            st.subheader(f"📋 All Jobs ({len(job_list)} available)")

        if not job_list:
            st.warning("No jobs found matching your criteria.")
        else:
            
            for i in range(0, len(job_list), 2):
                cols = st.columns(2)

                for idx, col in enumerate(cols):
                    if i + idx < len(job_list):
                        j = job_list[i + idx]

                        with col:
                            with st.container(border=True):

                                
                                show_image(j["image"])

                               
                                st.markdown(f"### {j['job_name']}")

                               
                                st.markdown(f"**💰 R{j['price'] if j['price'] else 0}**")

                                
                                desc = j["description"] or "_No description provided_"
                                st.write(desc[:100] + "..." if len(desc) > 100 else desc)

                                st.divider()

                                
                                st.caption(f"👤 Posted by: {j['username']}")

                                
                                if j["date_posted"]:
                                    try:
                                        st.caption(f"📅 {j['date_posted'].strftime('%Y-%m-%d')}")
                                    except:
                                        st.caption(f"📅 {j['date_posted']}")
                                else:
                                    st.caption("📅 Unknown date")

                                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

                                with btn_col1:
                                    if st.button("📧 Contact", key=f"contact_{j['id']}", use_container_width=True):
                                        st.toast(f"📧 {j['email']}")

                                with btn_col2:
                                    if st.button("ℹ️ Details", key=f"details_{j['id']}", use_container_width=True):
                                        with st.expander("Job Details", expanded=True):
                                            st.write(f"**Full Description:** {j['description']}")
                                            st.write(f"**Contact Email:** {j['email']}")
                                            st.write(f"**Posted by:** {j['username']}")

                                with btn_col3:
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
                                        st.caption("🔒 Login to save")
                                with btn_col4:
                                    if user_id:
                                        if st.button("🛠️ Claim", key=f"claim_{j['id']}", use_container_width=True):
                                            result = claim_job(j["id"], user_id)

                                            if result == "success":
                                                st.success("✅ Job claimed successfully!")
                                                st.rerun()
                                            elif result == "already_taken":
                                                st.warning("⚠️ This job is already taken.")
                                            elif result == "own_job":
                                                st.warning("⚠️ You cannot claim your own job.")
                                            else:
                                                st.error("❌ Something went wrong.")
                                    else:
                                        st.caption("🔒 Login to claim")

except Exception as e:
    st.error(f"❌ Error loading jobs: {e}")
    st.info("💡 Make sure the PostgreSQL database is running and properly configured.")
    with st.expander("Debug Information"):
        st.code(str(e))


st.divider()
st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")
