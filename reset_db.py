import os
from app import create_app, db
from app.models import seed_data


def main():
    app = create_app()

    # Delete DB file safely
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "", 1)
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted: {db_path}")

    with app.app_context():
        db.create_all()
        
        seed_data()
        print("Database reset and seeded.")


if __name__ == "__main__":
    main()
