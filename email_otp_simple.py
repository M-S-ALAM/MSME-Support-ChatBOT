import smtplib
import random
from email.message import EmailMessage

def send_otp_email(receiver_email, otp, sender_email, sender_password):
    msg = EmailMessage()
    msg['Subject'] = "Your OTP Code"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(f"Your OTP code is: {otp}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print(f"OTP sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send OTP: {e}")

def main():
    sender_email = input("Enter sender email (Gmail): ").strip()
    sender_password = input("Enter sender email password: ").strip()
    receiver_email = input("Enter receiver email: ").strip()

    otp = str(random.randint(100000, 999999))
    send_otp_email(receiver_email, otp, sender_email, sender_password)

    user_otp = input("Enter the OTP you received: ").strip()
    if user_otp == otp:
        print("✅ OTP verified successfully!")
    else:
        print("❌ Invalid OTP.")

if __name__ == "__main__":
    main()
