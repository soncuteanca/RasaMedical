import pymysql

def get_connection():
    """Establish and return a connection to the MySQL database."""
    return pymysql.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="Password1!",  # Replace with your MySQL password
        database="medical_bot"  # Replace with your database name
    )
