import resend
from flask import current_app


def send_checkin_reminder_email(user):
    api_key = current_app.config.get("RESEND_API_KEY")

    # If no API key is configured:
    # then you create own Resend account
    # add own API key for live email testing.
    if not api_key:
        current_app.logger.info(
            f"Reminder email would be sent to {user.email}"
        )
        return False

    resend.api_key = api_key

    try:
        resend.Emails.send({
            "from": current_app.config.get(
                "EMAIL_FROM",
                "48 Hours Forward <onboarding@resend.dev>"
            ),
            "to": [user.email],
            "subject": "We miss you at 48 Hours Forward",
            "text": (
                f"Hello {user.username},\n\n"
                "We noticed you missed your daily check in yesterday.\n"
                "Log in today to continue tracking your progress and maintain your streak.\n\n"
                "Stay strong,\n"
                "48 Hours Forward"
            )
        })

        return True

    except Exception as e:
        current_app.logger.error(
            f"Failed to send reminder email to {user.email}: {e}"
        )
        return False