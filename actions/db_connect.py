import pymysql
from pymysql import Error

class DatabaseManager:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Password1!',
            'database': 'medical_bot',
            'port': 3306,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    def get_connection(self):
        """Get a new database connection"""
        return pymysql.connect(**self.db_config)

    def execute_query(self, query, params=None, fetch=True):
        """Execute a query with proper error handling and connection management"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                result = cursor.fetchall()
                return result
            
            connection.commit()
            return True

        except Error as e:
            if connection:
                connection.rollback()
            raise Exception(f"Database error: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

# Create a singleton instance
db_manager = DatabaseManager()
