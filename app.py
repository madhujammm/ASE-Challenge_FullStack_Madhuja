import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import re
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Configure SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'employees.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

CORS(app)
db = SQLAlchemy(app)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Gemini API configured successfully")
    except Exception as e:
        print(f"Gemini configuration error: {e}")


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
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

    # Check if employee name already has a position
    if data.get('name'):
        existing_employee = Employee.query.filter_by(name=data['name'].strip()).first()
        if existing_employee:
            if employee_id and existing_employee.id == employee_id:
                pass
            elif existing_employee.position.lower() != data.get('position', '').strip().lower():
                errors.append(f'Employee "{data["name"].strip()}" already exists with position "{existing_employee.position}". Each employee can only have one position.')

    return errors

def get_ai_summary(employees_data):
    """Generate AI summary using Google Gemini"""
    try:
        if not employees_data:
            return "No employee data available for analysis."
        
        if not GEMINI_API_KEY:
            return "Gemini API key not configured. Please check your environment variables."
        
        # Extract positions and create analysis data
        positions = list(set([emp['position'] for emp in employees_data]))
        position_count = {}
        for emp in employees_data:
            position_count[emp['position']] = position_count.get(emp['position'], 0) + 1
        
        # Prepare the prompt
        prompt = f"""
        Analyze this employee management system data and provide a concise, professional business summary.
        
        WORKFORCE DATA:
        - Total Employees: {len(employees_data)}
        - Unique Positions: {len(positions)}
        - Position Distribution: {', '.join([f'{pos} ({count})' for pos, count in position_count.items()])}
        
        Please provide a structured analysis with these sections:
        
        1. WORKFORCE COMPOSITION: Brief overview of team structure and size
        2. ROLE DISTRIBUTION: Analysis of position diversity and specialization
        3. ORGANIZATIONAL INSIGHTS: Notable patterns and team dynamics
        4. OPTIMIZATION SUGGESTIONS: Practical recommendations for team improvement
        
        Format the response in clear, concise paragraphs. Use bullet points for suggestions.
        Keep it professional and actionable. Maximum 300 words.
        Focus on business insights that would help management understand their team structure.
        """
        
        # Try different model configurations
        model_attempts = [
            {'name': 'gemini-1.5-flash', 'config': {'temperature': 0.7, 'max_output_tokens': 500}},
            {'name': 'gemini-1.5-pro', 'config': {'temperature': 0.7, 'max_output_tokens': 500}},
            {'name': 'gemini-pro', 'config': {'temperature': 0.7, 'max_output_tokens': 500}},
        ]
        
        last_error = None
        
        for attempt in model_attempts:
            try:
                print(f"Attempting to use model: {attempt['name']}")
                model = genai.GenerativeModel(attempt['name'])
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=attempt['config']['temperature'],
                        max_output_tokens=attempt['config']['max_output_tokens'],
                    )
                )
                
                if response.text:
                    print(f"Successfully generated summary using {attempt['name']}")
                    return response.text.strip()
                    
            except Exception as e:
                last_error = str(e)
                print(f"Model {attempt['name']} failed: {last_error}")
                continue
        
        # If all models fail, try to list available models
        try:
            print("Attempting to list available models...")
            available_models = genai.list_models()
            model_names = [model.name for model in available_models]
            print(f"Available models: {model_names}")
            
            # Try the first available generation model
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    try:
                        model_short_name = model.name.split('/')[-1]  # Get just the model name
                        print(f"Trying available model: {model_short_name}")
                        gen_model = genai.GenerativeModel(model_short_name)
                        response = gen_model.generate_content(prompt)
                        if response.text:
                            return response.text.strip()
                    except Exception as e:
                        print(f"Available model {model.name} also failed: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error listing models: {e}")
        
        # Final fallback
        return f"""
        **AI Workforce Analysis Summary**
        
        **Team Overview**: Your organization has {len(employees_data)} employees across {len(positions)} different roles including {', '.join(list(positions)[:3])}.
        
        **Current Distribution**: 
        • Largest role: {max(position_count, key=position_count.get)} ({position_count[max(position_count, key=position_count.get)]} employees)
        • Role diversity: {'Good' if len(positions) >= 3 else 'Could be improved'}
        
        **Recommendations**:
        • Consider cross-training programs
        • Regular skills assessment
        • Succession planning for key roles
        
        _Note: Using fallback analysis due to AI service configuration. Please check your Gemini API setup._
        """
        
    except Exception as e:
        error_msg = str(e)
        print(f"Gemini API error: {error_msg}")
        
        if "API_KEY_INVALID" in error_msg:
            return "Gemini API key is invalid. Please check your API key configuration."
        elif "quota" in error_msg.lower():
            return "API quota exceeded. Please try again later or check your Google AI Studio quota."
        elif "location" in error_msg.lower() or "region" in error_msg.lower():
            return "API configuration issue: Please check if your region supports the Gemini API."
        else:
            return f"AI analysis temporarily unavailable: {error_msg}"

@app.route('/api/ai-summary', methods=['GET'])
def get_ai_summary_route():
    """Endpoint to get AI-powered summary of employees"""
    try:
        employees = Employee.query.all()
        employees_data = [emp.to_dict() for emp in employees]
        
        summary = get_ai_summary(employees_data)
        
        # Get position statistics
        positions = list(set([emp['position'] for emp in employees_data]))
        position_stats = {}
        for emp in employees_data:
            position_stats[emp['position']] = position_stats.get(emp['position'], 0) + 1
        
        return jsonify({
            'success': True,
            'summary': summary,
            'total_employees': len(employees_data),
            'unique_positions': len(positions),
            'position_distribution': position_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    init_db()
    app.run(debug=True, port=5000)
