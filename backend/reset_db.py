# backend/reset_db.py
from database import engine, Base
import models.models  # imports all tables
from sqlalchemy import text

print("⏳ Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("✅ Recreating all tables from models...")
Base.metadata.create_all(bind=engine)

print("🌱 Seeding users...")
from sqlalchemy.orm import Session
from models.models import User
import bcrypt

users = [
    {"name": "Vijay", "email": "vijay@example.com", "password": "password123"},
    {"name": "Alice", "email": "alice@example.com", "password": "password123"},
    {"name": "Bob",   "email": "bob@example.com",   "password": "password123"},
]

with Session(engine) as db:
    for u in users:
        hashed = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
        db.add(User(name=u["name"], email=u["email"], hashed_password=hashed))
    db.commit()

print("🚀 Done! Database is fresh and ready.")