# init_db.py
from app import app, db, Employee

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Optional: Add some sample data
        sample_employees = [
            Employee(name='John Smith', email='john.smith@company.com', position='Software Engineer'),
            Employee(name='Jane Doe', email='jane.doe@company.com', position='Product Manager'),
            Employee(name='Mike Johnson', email='mike.johnson@company.com', position='UX Designer'),
            Employee(name='Sarah Wilson', email='sarah.wilson@company.com', position='Data Analyst')
        ]
        
        # Add sample employees if the table is empty
        if Employee.query.count() == 0:
            for employee in sample_employees:
                db.session.add(employee)
            db.session.commit()
            print("Sample employees added to the database.")
        else:
            print("Database already contains data.")
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()