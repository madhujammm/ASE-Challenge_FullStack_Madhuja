# app.py
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import re
import os
from datetime import datetime

app = Flask(__name__)

# Configure SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'employees.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Add a secret key for security

CORS(app)

db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # Add unique constraint
    email = db.Column(db.String(120), unique=True, nullable=False)
    position = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'position': self.position,
            'created_at': self.created_at.isoformat()
        }

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_employee_data(data, check_required=True, employee_id=None):
    errors = []

    if check_required:
        if not data.get('name') or not data['name'].strip():
            errors.append('Name is required and cannot be empty')
        if not data.get('email') or not data['email'].strip():
            errors.append('Email is required and cannot be empty')
        if not data.get('position') or not data['position'].strip():
            errors.append('Position is required and cannot be empty')

    if data.get('email'):
        if not validate_email(data['email']):
            errors.append('Invalid email format')

    if data.get('name') and len(data['name']) > 100:
        errors.append('Name must be 100 characters or less')

    if data.get('position') and len(data['position']) > 100:
        errors.append('Position must be 100 characters or less')

    # NEW: Check if employee name already has a position
    if data.get('name'):
        existing_employee = Employee.query.filter_by(name=data['name'].strip()).first()
        if existing_employee:
            # If we're updating an employee, allow same name but different position check
            if employee_id and existing_employee.id == employee_id:
                pass  # It's the same employee being updated
            elif existing_employee.position.lower() != data.get('position', '').strip().lower():
                errors.append(f'Employee "{data["name"].strip()}" already exists with position "{existing_employee.position}". Each employee can only have one position.')

    return errors

def init_db():
    """Initialize the database with sample data"""
    with app.app_context():
        db.create_all()
        
        # Add sample data if the database is empty
        if Employee.query.count() == 0:
            sample_employees = [
                Employee(name='John Smith', email='john.smith@company.com', position='Software Engineer'),
                Employee(name='Jane Doe', email='jane.doe@company.com', position='Product Manager'),
                Employee(name='Mike Johnson', email='mike.johnson@company.com', position='UX Designer'),
                Employee(name='Sarah Wilson', email='sarah.wilson@company.com', position='Data Analyst')
            ]
            
            for employee in sample_employees:
                db.session.add(employee)
            
            db.session.commit()
            print("Sample employees added to the database.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        employees = Employee.query.all()
        return jsonify({
            'success': True,
            'data': [emp.to_dict() for emp in employees],
            'count': len(employees)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/employees', methods=['POST'])
def create_employee():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        errors = validate_employee_data(data)
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400

        existing_employee = Employee.query.filter_by(email=data['email']).first()
        if existing_employee:
            return jsonify({
                'success': False,
                'error': 'Employee with this email already exists'
            }), 409

        # NEW: Check for existing employee name
        existing_name = Employee.query.filter_by(name=data['name'].strip()).first()
        if existing_name:
            return jsonify({
                'success': False,
                'error': f'Employee "{data["name"].strip()}" already exists with position "{existing_name.position}". Each employee can only have one position.'
            }), 409

        new_employee = Employee(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            position=data['position'].strip()
        )

        db.session.add(new_employee)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Employee created successfully',
            'data': new_employee.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'error': 'Employee not found'
            }), 404

        return jsonify({
            'success': True,
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'error': 'Employee not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        errors = validate_employee_data(data, check_required=False, employee_id=employee_id)
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400

        if 'email' in data and data['email'] != employee.email:
            existing = Employee.query.filter_by(email=data['email']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Employee with this email already exists'
                }), 409

        # NEW: Check for existing employee name (excluding current employee)
        if 'name' in data and data['name'].strip() != employee.name:
            existing_name = Employee.query.filter_by(name=data['name'].strip()).first()
            if existing_name:
                return jsonify({
                    'success': False,
                    'error': f'Employee "{data["name"].strip()}" already exists with position "{existing_name.position}". Each employee can only have one position.'
                }), 409

        if 'name' in data:
            employee.name = data['name'].strip()
        if 'email' in data:
            employee.email = data['email'].strip().lower()
        if 'position' in data:
            employee.position = data['position'].strip()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Employee updated successfully',
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'error': 'Employee not found'
            }), 404

        db.session.delete(employee)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Employee deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize the database when the app starts
    init_db()
    app.run(debug=True, port=5000)
