# backend/seed.py

from database import SessionLocal
from models.models import User
from services.auth_service import hash_password

def seed():
    db = SessionLocal()
    try:
        # Clear existing users
        db.query(User).delete()
        db.commit()

        users = [
            User(name="Vijay", email="vijay@example.com",
                 hashed_password=hash_password("vijay123")),
            User(name="Alice", email="alice@example.com",
                 hashed_password=hash_password("alice123")),
            User(name="Bob",   email="bob@example.com",
                 hashed_password=hash_password("bob123")),
        ]
        db.add_all(users)
        db.commit()
        print("✅ Seeded 3 users with hashed passwords")
    finally:
        db.close()

if __name__ == "__main__":
    seed()