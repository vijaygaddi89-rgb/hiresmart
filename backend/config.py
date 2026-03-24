from decouple import config

APP_NAME = config("APP_NAME", default="HireSmart")
DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY")
DATABASE_URL = config("DATABASE_URL")