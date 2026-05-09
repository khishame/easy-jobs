import streamlit as st
import psycopg2
import bcrypt
import re
from dataclasses import dataclass

# =========================
# DATABASE CONFIG
# =========================
DB_CONFIG = {
    "dbname": "easy_jobs",
    "user": "postgres",
    "password": "Mulweli123?",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# =========================
# INIT DATABASE
# =========================
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                cellphone1 TEXT NOT NULL,
                cellphone2 TEXT,
                address TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# =========================
# USER MODEL
# =========================
@dataclass
class User:
    name: str
    surname: str
    username: str
    email: str
    cellphone1: str
    cellphone2: str
    address: str
    password: str

    def hash_password(self):
        return bcrypt.hashpw(self.password.encode(), bcrypt.gensalt()).decode()


def is_valid_email(email):
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", email)

def is_valid_phone(phone):
    return re.match(r"^(\+27|0)[6-8][0-9]{8}$", phone)

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
    )

# =========================
# SAVE USER
# =========================
def save_user(user: User):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users 
                (name, surname, username, email, cellphone1, cellphone2, address, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user.name,
                user.surname,
                user.username,
                user.email,
                user.cellphone1,
                user.cellphone2,
                user.address,
                user.password
            ))
        return True, "Success"

    except psycopg2.errors.UniqueViolation:
        return False, "Username or email already exists"

    except Exception as e:
        return False, str(e)


init_db()


st.set_page_config(page_title="Sign Up - Easy Jobs", page_icon=":briefcase:", layout="centered")

st.title("Sign Up for Easy Jobs")

name = st.text_input("First Name")
surname = st.text_input("Surname")
username = st.text_input("Username")
email = st.text_input("Email")

cell1 = st.text_input("Cellphone 1 (e.g. +27821234567)")
cell2 = st.text_input("Cellphone 2 (optional)")

address = st.text_area("Address")

password = st.text_input("Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")

if st.button("Create Account"):

    if not all([name, surname, username, email, cell1, address, password]):
        st.error("Please fill in all required fields")

    elif not is_valid_email(email):
        st.error("Invalid email format")

    elif not is_valid_phone(cell1):
        st.error("Invalid primary cellphone number")

    elif cell2 and not is_valid_phone(cell2):
        st.error("Invalid secondary cellphone number")

    elif not is_strong_password(password):
        st.error("Password must be at least 8 characters and include uppercase, lowercase, and numbers")

    elif password != confirm_password:
        st.error("Passwords do not match")

    else:
        user = User(
            name=name,
            surname=surname,
            username=username,
            email=email,
            cellphone1=cell1,
            cellphone2=cell2,
            address=address,
            password=password
        )

        user.password = user.hash_password()

        success, msg = save_user(user)

        if success:
            st.success("Account created successfully!")
            st.switch_page("pages/home.py")
        else:
            st.error(msg)

st.divider()
st.caption("Easy Jobs © 2026 | Connecting skilled workers with opportunities")