from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import random

otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_via_sendgrid(email: str):
    otp = generate_otp()
    otp_store[email] = otp

    message = Mail(
        from_email='shahbazalam@gyandata.com',
        to_emails=email,
        subject='Your OTP Code',
        plain_text_content=f'Your OTP is {otp}'
    )

    sg = SendGridAPIClient(os.getenv("EMAIL_KEY"))
    sg.send(message)

    return otp


if __name__ == "__main__":
    email = "msalamiid@gmail.com"
    send_otp_via_sendgrid(email)
    print(f"OTP sent to {email}: {otp_store[email]}")

