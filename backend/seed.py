from database import SessionLocal, engine, Base
from models.models import User, Resume, InterviewSession

Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()

    # Check if already seeded
    existing = db.query(User).first()
    if existing:
        print("Database already seeded!")
        db.close()
        return

    # Create 3 test users
    users = [
        User(
            name="Vijay Test",
            email="vijay@test.com",
            hashed_password="hashed_dummy_password_1",
            is_active=True
        ),
        User(
            name="Alice Smith",
            email="alice@test.com",
            hashed_password="hashed_dummy_password_2",
            is_active=True
        ),
        User(
            name="Bob Jones",
            email="bob@test.com",
            hashed_password="hashed_dummy_password_3",
            is_active=True
        ),
    ]

    db.add_all(users)
    db.commit()
    print(f"✅ Seeded {len(users)} users successfully!")
    db.close()

if __name__ == "__main__":
    seed()