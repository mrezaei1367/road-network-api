import os
import sys
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

engine = create_engine(os.getenv("DATABASE_URL"))
max_retries = 50

for _ in range(max_retries):
    try:
        with engine.connect():
            print("Database connection successful")
            sys.exit(0)
    except OperationalError:
        print("Waiting for database...")
        time.sleep(2)

print("Failed to connect to database")
sys.exit(1)
