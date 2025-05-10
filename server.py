from flask import Flask, jsonify, send_from_directory, request
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
    return send_from_directory('html', 'home_page.html')

@app.route('/add-data')
def add_data():
    return send_from_directory('html', 'add_data.html')

@app.route('/home_page.html')
def home_page():
    return send_from_directory('html', 'home_page.html')

@app.route('/create_user.html')
def create_user_page():
    return send_from_directory('html', 'create_user.html')

@app.route('/api/patients', methods=['GET', 'POST'])
def handle_patients():
    if request.method == 'POST':
        try:
            data = request.json
            query = "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)"
            params = (data['name'], data['email'], data['phone'])
            db_manager.execute_query(query, params, fetch=False)
            return jsonify({'message': 'Patient added successfully'}), 201
        except Exception as e:
            logger.error(f"Error adding patient: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        try:
            query = "SELECT * FROM users"
            results = db_manager.execute_query(query)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error fetching patients: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/appointments', methods=['GET', 'POST'])
def handle_appointments():
    if request.method == 'POST':
        try:
            data = request.json
            query = "INSERT INTO appointments (patient_id, appointment_date, reason) VALUES (%s, %s, %s)"
            params = (data['patient_id'], data['appointment_date'], data['reason'])
            db_manager.execute_query(query, params, fetch=False)
            return jsonify({'message': 'Appointment added successfully'}), 201
        except Exception as e:
            logger.error(f"Error adding appointment: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        try:
            query = "SELECT * FROM appointments"
            results = db_manager.execute_query(query)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error fetching appointments: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/records', methods=['GET', 'POST'])
def handle_records():
    if request.method == 'POST':
        try:
            data = request.json
            query = "INSERT INTO medical_records (patient_id, diagnosis, treatment) VALUES (%s, %s, %s)"
            params = (data['patient_id'], data['diagnosis'], data['treatment'])
            db_manager.execute_query(query, params, fetch=False)
            return jsonify({'message': 'Medical record added successfully'}), 201
        except Exception as e:
            logger.error(f"Error adding medical record: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        try:
            query = "SELECT * FROM medical_records"
            results = db_manager.execute_query(query)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error fetching records: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    if request.method == 'POST':
        try:
            data = request.json
            query = """
                INSERT INTO users (first_name, last_name, email, password, sex, age, phone) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                data['first_name'],
                data['last_name'],
                data['email'],
                data['password'],
                data['sex'],
                data['age'],
                data['phone']
            )
            db_manager.execute_query(query, params, fetch=False)
            return jsonify({'message': 'User created successfully'}), 201
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.json
            query = """
                SELECT id, first_name, last_name, email, password
                FROM users
                WHERE email = %s
            """
            params = (data['email'],)
            result = db_manager.execute_query(query, params)
            
            if result and result[0]['password'] == data['password']:
                return jsonify({
                    'message': 'Login successful',
                    'token': 'dummy_token',
                    'user': {
                        'id': result[0]['id'],
                        'name': f"{result[0]['first_name']} {result[0]['last_name']}",
                        'email': result[0]['email']
                    }
                }), 200
            else:
                return jsonify({'error': 'Invalid email or password'}), 401
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
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