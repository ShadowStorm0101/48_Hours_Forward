from app import create_app, db
from app.models import seed_data
from dotenv import load_dotenv
load_dotenv()
from app.models import seed_resources

app = create_app()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)   # including all network interfaces, container 'listens' on 5000