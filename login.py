# login.py
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
usernames = os.getenv("USERNAMES", "").split(",")
passwords = os.getenv("PASSWORDS", "").split(",")
USER_CREDENTIALS = dict(zip(usernames, passwords))

def login_page():
    st.title("🔐 Login to Walmart MSME ChatBOT")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.authenticated = True
                st.success("✅ Login successful! Loading application...")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials.")
