import smtplib
from email.mime.text import MIMEText
from flask import current_app


def send_verification_email(to_email, code):
    sender_email = current_app.config.get("EMAIL_USER")
    app_password = current_app.config.get("EMAIL_PASSWORD")

    if not sender_email or not app_password:
        print("❌ EMAIL CONFIG MISSING")
        print("EMAIL_USER:", sender_email)
        print("EMAIL_PASSWORD:", app_password)
        return

    msg = MIMEText(f"Your verification code is: {code}\n\nExpires in 5 minutes.")
    msg["Subject"] = "Verification Code"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        # Debugging to see if process is running through
        print("Email sent to:", to_email)
        print("Code:", code)

    except Exception as e:
        print("EMAIL ERROR:", e)