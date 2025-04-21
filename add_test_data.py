import pymysql
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def add_test_data():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Password1!',
        database='medical_bot',
        port=3306,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # First, check if John Doe exists
            cursor.execute("SELECT * FROM users WHERE name = 'John' AND surname = 'Doe'")
            existing_user = cursor.fetchone()
            
            if existing_user:
                logger.info("John Doe already exists:")
                logger.info(existing_user)
            else:
                # Add John Doe
                cursor.execute("""
                    INSERT INTO users (name, surname, age, medical_history)
                    VALUES ('John', 'Doe', 30, 'No significant medical history')
                """)
                connection.commit()
                logger.info("Added John Doe to the database")
            
            # Verify all users in the database
            cursor.execute("SELECT * FROM users")
            all_users = cursor.fetchall()
            logger.info("All users in database:")
            for user in all_users:
                logger.info(f"ID: {user['id']}, Name: {user['name']} {user['surname']}, Age: {user['age']}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    add_test_data() 