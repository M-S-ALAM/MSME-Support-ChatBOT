import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SendEmailVerify:
    @staticmethod
    def send_verify(recipient_email: str, token: str):
        email_address = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASS")

        if not email_address or not email_password:
            raise ValueError("EMAIL_USER or EMAIL_PASS not set in environment")

        msg = EmailMessage()
        msg['Subject'] = "Verify Your Account"
        msg['From'] = email_address
        msg['To'] = recipient_email
        msg.set_content(
            f"""\
Hi,

Please verify your account by clicking the link below:

http://localhost:8080/user/verify/{token}

If you didn't request this, please ignore this email.
"""
        )

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_address, email_password)
                smtp.send_message(msg)
                print(f"✅ Verification email sent to {recipient_email}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    SendEmailVerify.send_verify("msalamiitd@gmail.com", "test_token")
