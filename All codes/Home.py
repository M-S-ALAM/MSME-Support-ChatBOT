# main.py
import streamlit as st
import os
import sys
from st_pages import Page, show_pages

# Add 'pages' folder to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'pages')))

class MsmeChatbot:
    def __init__(self):
        self.setup_sidebar()
        self.render_home()

    def setup_sidebar(self):
        show_pages([
            Page("Home.py", "Home", "🏠"),
            Page("01_intro.py", "Introduction", "📖"),
            Page("../shopping_chat_bot.py", "Text-to-Text Testing", "💬"),
        ])

    def render_home(self):
        st.title("🏠 Intelligence MSME ChatBOT")
        st.write("Welcome to the chatbot! Use the sidebar to explore.")

if __name__ == '__main__':
    st.set_page_config(page_title="Intelligence MSME CHATBOT", page_icon="🤖", layout="wide")
    MsmeChatbot()
