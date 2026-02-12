import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ALLOWED_ROLES = {"user", "moderator", "admin"}

BANNED_PASSWORDS = {
    "password123$",
    "qwerty123!",
    "adminadmin1@",
    "welcome123!"
}


def validate_email(value: str, max_length: int = 80) -> str:
    if not isinstance(value, str):
        raise ValueError("Email must be a string.")
    value = value.strip()
    if not value:
        raise ValueError("Email is required.")
    if len(value) > max_length:
        raise ValueError("Email is too long.")
    if not EMAIL_REGEX.match(value):
        raise ValueError("Email must be a valid email address.")
    return value


def validate_password(value: str, username: str | None = None, min_length: int = 10, max_length: int = 60) -> str:
    if not isinstance(value, str):
        raise ValueError("Password must be a string.")
    value = value.strip()
    if not value:
        raise ValueError("Password is required.")
    if len(value) < min_length:
        raise ValueError(f"Password must be at least {min_length} characters long.")
    if len(value) > max_length:
        raise ValueError("Password is too long.")

    if not re.search(r"\d", value):
        raise ValueError("Password must include at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("Password must include at least one special character.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must include at least one uppercase letter.")

    lower_pw = value.lower()

    if username:
        u = username.lower()
        if u in lower_pw:
            raise ValueError("Password must not contain your email address.")

    if lower_pw in BANNED_PASSWORDS:
        raise ValueError("This password is too common. Choose a stronger one.")

    return value

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,50}$")
def validate_username(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Username must be a string.")
    value = value.strip()
    if not value:
        raise ValueError("Username is required.")
    if not USERNAME_RE.match(value):
        raise ValueError("Username must be 3–50 characters and contain only letters, numbers, or underscores.")
    return value


def validate_role(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Role must be a string.")
    value = value.strip().lower()
    if value not in ALLOWED_ROLES:
        raise ValueError("Invalid role.")
    return value


def validate_bio(value: str, max_length: int = 300) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Biography must be a string.")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"Biography is too long (max {max_length} characters).")
    return value
