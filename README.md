- Role System
- NHS help pages (redirection)
- Streak function
- Reward scheme (using sponsors to distribute prizes such as coupons or gifts the sponsors give to us) if a user reaches a certain amount of points
- Admin and Moderator function 
- Settings page for accessibility features and log out
- Messaging System 
- Diary system (journellling system) 
- Try to fit it in mobile version too 
- Implement 2FA 
- Implement email notifiication system 
- Implement Data Analysis methods

<br>

# For Docker
Install docker at 
https://www.docker.com/products/docker-desktop/

Run this:
```
git pull
docker compose up --build
```
<br>

If port is in use try:
```
docker compose down
Use this as url, terminal link not correct (I'll fix this)
```

#### http://127.0.0.1:5001

Seeded users aren't on the database (I'll fix this)
Create a test account through register and use that instead.

Any questions just text me

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