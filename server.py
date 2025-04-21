from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from actions.db_connect import db_manager
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='html')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return send_from_directory('html', 'view_data.html')

@app.route('/api/patients')
def get_patients():
    try:
        logger.debug("Attempting to fetch patients...")
        query = "SELECT * FROM users"
        results = db_manager.execute_query(query)
        logger.debug(f"Retrieved {len(results) if results else 0} patients")
        logger.debug(f"Results: {results}")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments')
def get_appointments():
    try:
        query = "SELECT * FROM appointments"
        results = db_manager.execute_query(query)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/records')
def get_records():
    try:
        query = "SELECT * FROM medical_records"
        results = db_manager.execute_query(query)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching records: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Test database connection on startup
    try:
        test_query = "SELECT 1"
        db_manager.execute_query(test_query)
        logger.info("Database connection successful!")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
    
    # Run with localhost and port 5000
    app.run(host='127.0.0.1', port=5000, debug=True) 