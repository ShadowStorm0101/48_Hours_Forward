from app import create_app, db
from app.models import seed_data


def main():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_data()
        print("Database reset and seeded.")


if __name__ == "__main__":
    main()