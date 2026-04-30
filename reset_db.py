from app import create_app, db
from app.models import seed_data, seed_location_services


def main():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_data()
        seed_location_services()   # function to add service locations, from models.py
        print("Database reset and seeded.")


if __name__ == "__main__":
    main()