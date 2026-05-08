# User Instructions
### For Docker
Install docker at 
https://www.docker.com/products/docker-desktop/

After creating your account, run this in your terminal:
```
docker compose up --build
docker compose exec web python reset_db.py
```
<br>

For running the app after initial seeding
```
docker compose up --build
```
<br>


And click this url

#### http://127.0.0.1:5001
<br>


If port is in use try:
```
docker compose down
```

<br>
<br>
<br>
<br>







# Email Reminder Setup
The email notification system uses Resend to send reminder emails to users who have not logged in for 24 hours.
To enable live email sending:
1. Create a Resend account:

https://resend.com

2. Generate an API key

3. Create a `.env` file in the project root and add:

RESEND_API_KEY=your_resend_api_key_here
EMAIL_FROM=48 Hours Forward <onboarding@resend.dev>

4. Run the application:
docker compose up --build

---

### Reminder Logic

Users receive a reminder email when:

- they have not logged in for 24 hours
- reminder emails are enabled
- they have not already received a reminder in the last 24 hours

---

### Testing Notes

When using Resend's default testing email address (`onboarding@resend.dev`), emails can only be sent to the email address linked to your own Resend account.

To send emails to any user email address, verify a custom domain in Resend and update the `EMAIL_FROM` value.