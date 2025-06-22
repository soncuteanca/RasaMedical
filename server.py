from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from actions.db_connect import db_manager
import logging
import hashlib
import secrets

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Create a secure password hash using SHA-256 with salt"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Create hash
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    # Return salt:hash format
    return f"{salt}:{password_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Handle both hashed and plain text passwords for backward compatibility
        if ':' not in hashed_password:
            # Plain text password (legacy users)
            return password == hashed_password
        
        # Extract salt and hash
        salt, stored_hash = hashed_password.split(':', 1)
        # Hash the provided password with the same salt
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        # Compare hashes
        return password_hash == stored_hash
    except Exception:
        return False

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
            query = "INSERT INTO appointments (user_id, doctor_id, appointment_date, reason) VALUES (%s, %s, %s, %s)"
            params = (data['user_id'], data['doctor_id'], data['appointment_date'], data['reason'])
            db_manager.execute_query(query, params, fetch=False)
            return jsonify({'message': 'Appointment added successfully'}), 201
        except Exception as e:
            logger.error(f"Error adding appointment: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        try:
            user_id = request.args.get('user_id')
            if user_id:
                query = """
                    SELECT a.*, d.name as doctor_name 
                    FROM appointments a 
                    LEFT JOIN doctors d ON a.doctor_id = d.id 
                    WHERE a.user_id = %s 
                    ORDER BY a.appointment_date DESC
                """
                results = db_manager.execute_query(query, (user_id,))
            else:
                query = """
                    SELECT a.*, d.name as doctor_name 
                    FROM appointments a 
                    LEFT JOIN doctors d ON a.doctor_id = d.id 
                    ORDER BY a.appointment_date DESC
                """
                results = db_manager.execute_query(query)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error fetching appointments: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    try:
        # First check if the appointment exists
        check_query = "SELECT id FROM appointments WHERE id = %s"
        result = db_manager.execute_query(check_query, (appointment_id,))
        
        if not result:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Delete the appointment
        delete_query = "DELETE FROM appointments WHERE id = %s"
        db_manager.execute_query(delete_query, (appointment_id,), fetch=False)
        
        logger.info(f"Appointment {appointment_id} deleted successfully")
        return jsonify({'message': 'Appointment deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting appointment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/records', methods=['GET', 'POST'])
def handle_records():
    if request.method == 'POST':
        try:
            data = request.json
            query = """
                INSERT INTO medical_records (patient_id, doctor_id, record_type, title, description, record_date) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                data['patient_id'], 
                data.get('doctor_id'), 
                data.get('record_type', 'note'), 
                data['title'], 
                data.get('description', ''), 
                data['record_date']
            )
            db_manager.execute_query(query, params, fetch=False)
            return jsonify({'message': 'Medical record added successfully'}), 201
        except Exception as e:
            logger.error(f"Error adding medical record: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        try:
            user_id = request.args.get('user_id')
            if user_id:
                query = """
                    SELECT mr.*, d.name as doctor_name 
                    FROM medical_records mr 
                    LEFT JOIN doctors d ON mr.doctor_id = d.id 
                    WHERE mr.patient_id = %s 
                    ORDER BY mr.record_date DESC, mr.created_at DESC
                """
                results = db_manager.execute_query(query, (user_id,))
            else:
                query = """
                    SELECT mr.*, d.name as doctor_name, 
                           u.first_name, u.last_name
                    FROM medical_records mr 
                    LEFT JOIN doctors d ON mr.doctor_id = d.id 
                    LEFT JOIN users u ON mr.patient_id = u.id
                    ORDER BY mr.record_date DESC, mr.created_at DESC
                """
                results = db_manager.execute_query(query)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error fetching records: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    try:
        # First check if the record exists
        check_query = "SELECT id FROM medical_records WHERE id = %s"
        result = db_manager.execute_query(check_query, (record_id,))
        
        if not result:
            return jsonify({'error': 'Medical record not found'}), 404
        
        # Delete the record
        delete_query = "DELETE FROM medical_records WHERE id = %s"
        db_manager.execute_query(delete_query, (record_id,), fetch=False)
        
        logger.info(f"Medical record {record_id} deleted successfully")
        return jsonify({'message': 'Medical record deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting medical record: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Hash the password before storing
            hashed_password = hash_password(data['password'])
            
            query = """
                INSERT INTO users (first_name, last_name, email, password, sex, age, phone) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                data['first_name'],
                data['last_name'],
                data['email'],
                hashed_password,  # Store hashed password
                data['sex'],
                data['age'],
                data['phone']
            )
            db_manager.execute_query(query, params, fetch=False)
            logger.info(f"User created successfully: {data['email']}")
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
            
            if result and verify_password(data['password'], result[0]['password']):
                logger.info(f"Successful login for user: {data['email']}")
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
                logger.warning(f"Failed login attempt for email: {data.get('email', 'unknown')}")
                return jsonify({'error': 'Invalid email or password'}), 401
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Delete the user directly
        db_manager.execute_query("DELETE FROM users WHERE id = %s", (user_id,), fetch=False)
        return jsonify({'message': 'User account deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-session', methods=['POST'])
def validate_session():
    try:
        data = request.json
        user_id = data.get('user_id')
        token = data.get('token')
        
        if not user_id or not token:
            return jsonify({'valid': False, 'error': 'Missing user_id or token'}), 400
        
        # For now, we'll do a simple validation by checking if user exists
        # In a real application, you'd validate the actual token
        query = "SELECT id, first_name, last_name, email FROM users WHERE id = %s"
        result = db_manager.execute_query(query, (user_id,))
        
        if result:
            return jsonify({
                'valid': True,
                'user': {
                    'id': result[0]['id'],
                    'name': f"{result[0]['first_name']} {result[0]['last_name']}",
                    'email': result[0]['email']
                }
            }), 200
        else:
            return jsonify({'valid': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"Error validating session: {str(e)}")
        return jsonify({'valid': False, 'error': str(e)}), 500

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