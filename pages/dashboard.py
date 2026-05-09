import streamlit as st
import psycopg2
import pandas as pd
import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


if "page_history" not in st.session_state:
    st.session_state.page_history = []

CURRENT_PAGE = "Dashboard"
if not st.session_state.page_history or st.session_state.page_history[-1] != CURRENT_PAGE:
    st.session_state.page_history.append(CURRENT_PAGE)


def get_stats():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM jobs")
            jobs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users")
            users = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(price) FROM jobs")
            avg_price = cursor.fetchone()[0] or 0

    return jobs, users, avg_price


def get_price_distribution():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT 
                CASE
                    WHEN price < 500 THEN 'Under R500'
                    WHEN price BETWEEN 500 AND 1000 THEN 'R500 - R1000'
                    WHEN price BETWEEN 1000 AND 5000 THEN 'R1000 - R5000'
                    ELSE 'Above R5000'
                END as range,
                COUNT(*) as total
            FROM jobs
            WHERE price IS NOT NULL
            GROUP BY range
        """, conn)
    return df


def get_users_over_time():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT DATE(created_at) as date, COUNT(*) as total
            FROM users
            GROUP BY DATE(created_at)
            ORDER BY date
        """, conn)
    return df


def get_recent_jobs():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT job_name, price, DATE(date_posted) as date
            FROM jobs
            ORDER BY date_posted DESC
            LIMIT 5
        """, conn)
    return df


st.set_page_config(page_title="Dashboard", layout="wide")

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
    font-size: 1.8rem;
    font-weight: 700;
    color: #38bdf8;
    text-align: left;
}


div[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 12px;
    box-shadow: none;
}

div[data-testid="metric-container"] > div {
    color: #e5e7eb;
}

div[data-testid="stPlotlyChart"], 
div[data-testid="stChart"] {
    background: #111827;
    border-radius: 12px;
    padding: 10px;
    border: 1px solid rgba(255,255,255,0.06);
}


table {
    background: #111827 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

thead tr th {
    background: #0f172a !important;
    color: #e5e7eb !important;
}

tbody tr td {
    color: #cbd5e1 !important;
}

.stButton > button {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.08);
    color: #e5e7eb;
    border-radius: 8px;
    padding: 0.4rem;
    font-weight: 500;
}

.stButton > button:hover {
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.4);
}



section[data-testid="stSidebar"] {
    background: #0a0f1c;
    border-right: 1px solid rgba(255,255,255,0.06);
}


html, body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: #e5e7eb;
}

p, span, label {
    color: #94a3b8;
}


hr {
    border-color: rgba(255,255,255,0.06);
}



.stButton > button[kind="secondary"] {
    border: 1px solid rgba(148,163,184,0.3);
}

.block-container {
    gap: 1rem;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


st.title("📊 Dashboard")

user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("Please log in first.")
    st.switch_page("EasyJobsWebApp.py")

jobs, users, avg_price = get_stats()

col1, col2, col3 = st.columns(3)

col1.metric("📋 Total Jobs", jobs)
col2.metric("👤 Users", users)
col3.metric("💰 Avg Price", f"R{round(avg_price, 2)}")

st.divider()

# =========================
# CHARTS SIDE BY SIDE
# =========================
st.subheader("📊 Analytics")

col1, col2 = st.columns(2)


with col1:
    st.write("💰 Price Distribution")

    price_data = get_price_distribution()

    if not price_data.empty:
        st.bar_chart(price_data.set_index("range"))
    else:
        st.info("No price data available")

# USERS OVER TIME (FIXED LINE GRAPH)
with col2:
    st.write("👤 Users Over Time")

    users_data = get_users_over_time()

    if not users_data.empty:
        users_data["date"] = pd.to_datetime(users_data["date"])
        users_data = users_data.sort_values("date")
        users_data = users_data.set_index("date")

        st.line_chart(users_data["total"])
    else:
        st.info("No user data available")

st.divider()


st.subheader("🆕 Recent Jobs")

recent = get_recent_jobs()

if not recent.empty:
    st.dataframe(recent, use_container_width=True)
else:
    st.info("No recent jobs")


st.divider()

if st.button("⬅️ Back"):
    st.switch_page("pages/home.py")

