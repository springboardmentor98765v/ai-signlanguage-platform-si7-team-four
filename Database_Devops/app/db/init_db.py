from app.db.database import Base, engine
from app.db import models  # noqa: F401  (import so tables register on Base.metadata)

def init():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init()
