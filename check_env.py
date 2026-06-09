from app.core.config import get_settings
s = get_settings()
print("DATABASE_URL:", s.DATABASE_URL)
print("SECRET_KEY:", bool(s.SECRET_KEY))
