import os
import streamlit as st
from dotenv import load_dotenv
from shopping_chat_bot import ShoppingChatBot  # Assuming ShoppingChatBot is in this file

# Ensure this is the first Streamlit call
st.set_page_config(page_title="MSME ChatBOT", page_icon="💬")

class MsmeChatbotLoginApp:
    def __init__(self):
        load_dotenv()
        usernames = os.getenv("USERNAMES", "").split(",")
        passwords = os.getenv("PASSWORDS", "").split(",")
        self.user_credentials = dict(zip(usernames, passwords))

        if "authenticated" not in st.session_state:
            st.session_state['authenticated'] = False

        self.run()

    def run(self):
        if not st.session_state['authenticated']:
            self.login_form()
        else:
            # This method initializes and runs the chatbot interface
            self.load_home()

    def login_form(self):
        st.markdown("<h1 style='color:red;'>🔐 Intelligence MSME ChatBOT Login</h1>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

        if login_btn:
            if username in self.user_credentials and self.user_credentials[username] == password:
                st.session_state['authenticated'] = True
                st.experimental_rerun()  # Rerun the app where the state is now authenticated
            else:
                st.error("❌ Invalid username or password")

    def load_home(self):
        # Initialize and run the shopping chat bot
        ShoppingChatBot()

if __name__ == '__main__':
    MsmeChatbotLoginApp()
