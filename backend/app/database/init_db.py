import os
import time
import urllib.parse
import psycopg2
import redis

# Connection configurations from environment variables with local fallback defaults
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/BobaMaster")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Locate schema.sql relative to this script path
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def initialize_database():
    print(f"Connecting to database at {DATABASE_URL} ...")
    conn = None
    retries = 10
    delay = 3
    
    # Connection retry loop to handle database startup lag in Docker
    for i in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("Successfully connected to database.")
            break
        except psycopg2.OperationalError as e:
            print(f"Database connection attempt {i + 1}/{retries} failed: {e}")
            if i < retries - 1:
                print(f"Waiting {delay} seconds...")
                time.sleep(delay)
            else:
                print("Could not connect to database after maximum retries.")
                raise e

    try:
        # Load schema.sql file content
        if not os.path.exists(SCHEMA_PATH):
            raise FileNotFoundError(f"Schema file not found at: {SCHEMA_PATH}")
            
        with open(SCHEMA_PATH, "r") as f:
            schema_sql = f.read()

        # Run script within transaction
        with conn.cursor() as cursor:
            print("Applying schema migrations...")
            cursor.execute(schema_sql)
            conn.commit()
            print("Database schemas initialized successfully.")
            
            # Verification: print the created tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"Verified tables in database: {[t[0] for t in tables]}")
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error during schema migration: {e}")
        raise e
    finally:
        if conn:
            conn.close()

def initialize_redis():
    print(f"Connecting to Redis at {REDIS_URL} ...")
    try:
        client = redis.Redis.from_url(REDIS_URL)
        # Test basic connection ping
        if client.ping():
            print("Successfully connected to Redis.")
        else:
            raise ConnectionError("Redis ping failed.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        raise e

if __name__ == "__main__":
    print("Initializing BobaMaster Infrastructure...")
    initialize_database()
    initialize_redis()
    print("Milestone 1 Initialization Complete!")
