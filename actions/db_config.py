import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'medical_bot'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4',
    'cursorclass': 'DictCursor'
}

# Backward compatibility
DB_CONFIG = DATABASE_CONFIG 