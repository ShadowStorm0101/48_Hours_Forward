from app import create_app, db
from app.models import seed_data

app = create_app()

with app.app_context():
    db.create_all()
    # removed seed data function from here

if __name__ == "__main__":
    app.run(debug=True)
