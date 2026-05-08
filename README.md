# 48 Hours Forward
### Group 48 2033 code submission

<br>

48 Hours Forward is a recovery and wellbeing support platform designed to help users take meaningful steps toward overcoming addiction and improving their mental and physical health. The application allows users to track sobriety streaks for alcohol, nicotine, and narcotics through live updating dashboards and milestone systems that encourage long-term progress.

Users can privately journal their thoughts and experiences, helping them reflect on their recovery journey over time. The platform also provides access to trusted online recovery resources and an interactive map that helps users discover nearby support meetings and addiction services based on their needs.

Administrators are able to manage and add new support locations directly onto the map, ensuring local meeting information stays accurate and accessible. Moderators have access to anonymised platform statistics and analytics, allowing them to better understand user engagement and recovery trends across the application.

Additional account management and support features include credential updates, password changes, account verification, and a built-in help system that enables users to report bugs, issues, or concerns directly through the platform.

The goal of 48 Hours Forward is to provide a safe, supportive, and practical environment that empowers individuals to move forward one step at a time.



Check instructions.md for running our application

# Documentation

| Document                    | Purpose                                   |
|-----------------------------|-------------------------------------------|
| instructions.md             | Setup and running instructions            |
| CODING_STANDARDS.md         | Team programming conventions and cohesion |
| VERSION_CONTROL_WORKFLOW.md | Branching strategy and Git workflow       |

# Mapping Criteria to Codebase

| **Criteria**                                 | **Where to Find It (File Paths, Links, or Explanations)**                                                                                                |
|----------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Team Standards: Cohesion**                 | `CODING_STANDARDS.md`, modular Flask structure in `app/routes/`, `app/models/`, frontend styling in `app/static/`                                        |
| **Team Standards: Documentation**            | `README.md`, `instructions.md`, inline comments throughout backend/frontend files                                                                        |
| **Team Standards: Version Control Workflow** | `VERSION_CONTROL_WORKFLOW.md`, `.git` branch history showing feature and integration branches                                                            |
| **Design & Structure**                       | Functionality separated across `app/routes/`, `app/models/`, `app/templates/`, and `app/static/`                                                         |
| **GUI: Clever and Interesting Design**       | Frontend templates in `app/templates/`, CSS styling in `app/static/`, screenshots in `docs/gui-screenshots/`                                             |
| **Testing Documentation**                    | `tests/` folder and testing methodology described in specification document                                                                              |
| **Functionality and Features**               | Backend functionality implemented throughout `app/routes/`, authentication system, dashboard logic, map system, journal system, moderator/admin features |

# Functionality and Features

## Minimum Requirements Fulfilled

| Requirement                   | Implementation                                                 |
|-------------------------------|----------------------------------------------------------------|
| Database Integration          | PostgreSQL database integrated through Flask and SQLAlchemy    |
| Access Control                | User, Moderator, and Admin roles implemented                   |
| Three-Tier Architecture       | Frontend (HTML/CSS/JS), Backend (Flask), Database (PostgreSQL) |
| User Interaction              | Journal system, support map, dashboards, profile management    |
| Git & GitHub Usage            | Repository managed using GitHub with feature branches          |
| Functional Technology Product | Fully functional Dockerised web application                    |

# Intermediate and Advanced Features

| Feature                      | Description                                              | Location                            |
|------------------------------|----------------------------------------------------------|-------------------------------------|
| Email Reminder Notifications | Sends reminder emails to inactive users using Resend API | Email notification system           |
| Multiple User Roles          | User, Moderator, and Admin dashboards/access control     | Authentication and dashboard routes |
| Dashboards and Statistics    | Moderator/admin analytics and user statistics            | Dashboard system                    |
| Gamification                 | Streaks, milestone indicators, progress tracking         | Dashboard and streak logic          |
| Docker Integration           | Multi-container deployment using Docker Compose          | `docker-compose.yml`                |
| Location-Based Features      | Interactive support map with nearby support locations    | Map system                          |
| External APIs                | Google Maps API, Resend email API, reCAPTCHA integration | Backend integrations                |
| Accessibility Features       | High contrast mode and responsive layouts                | Frontend templates and CSS          |
| Secure Authentication        | Password hashing, 2FA verification, role-based access    | Authentication system               |
