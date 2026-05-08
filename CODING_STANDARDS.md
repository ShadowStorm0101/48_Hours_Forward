# Coding Standards

## Team Programming Standards

To maintain consistency across the project, the team followed shared programming conventions across both backend and frontend development.

# Python Standards

- PEP8 formatting conventions
- snake_case naming for functions and variables
- PascalCase naming for classes
- Meaningful variable and function names
- Modular route separation
- Reusable helper functions where possible

Complex functionality such as authentication, streak calculations, and dashboard logic was commented where appropriate.

# Frontend Standards

- Consistent HTML/CSS formatting
- Descriptive CSS class names
- Shared page layouts and navigation styling
- Consistent user interface design across pages

# Project Structure

The project was separated into modules and folders for maintainability:

```text
app/routes/
app/models/
app/templates/
app/static/
```

# Team Collaboration

GitHub branches were used to separate features and reduce merge conflicts during development.

Examples include:

- feature/dashboard-access-control
- feature/map-add-location
- email-notifications
- front-end-help-page
- milestone-effects

# Technologies Used

- Flask
- PostgreSQL
- SQLAlchemy
- Docker
- HTML/CSS/JavaScript