import unittest
import json
from app import app, db, Employee

class EmployeeAPITestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_employees_empty(self):
        response = self.client.get('/api/employees')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 0)
        self.assertEqual(data['count'], 0)

    def test_create_employee_success(self):
        employee_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'position': 'Software Engineer'
        }
        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'John Doe')
        self.assertEqual(data['data']['email'], 'john.doe@example.com')
        self.assertEqual(data['data']['position'], 'Software Engineer')

    def test_create_employee_missing_name(self):
        employee_data = {
            'email': 'test@example.com',
            'position': 'Developer'
        }
        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('errors', data)

    def test_create_employee_invalid_email(self):
        employee_data = {
            'name': 'Jane Doe',
            'email': 'invalid-email',
            'position': 'Manager'
        }
        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_create_employee_duplicate_email(self):
        employee_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'position': 'Engineer'
        }
        self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )

        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('already exists', data['error'])

    def test_get_employees_after_creation(self):
        employee_data = {
            'name': 'Alice Smith',
            'email': 'alice@example.com',
            'position': 'Designer'
        }
        self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )

        response = self.client.get('/api/employees')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'Alice Smith')

    def test_get_single_employee(self):
        employee_data = {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'position': 'Developer'
        }
        create_response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        created_data = json.loads(create_response.data)
        employee_id = created_data['data']['id']

        response = self.client.get(f'/api/employees/{employee_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'Bob Johnson')

    def test_get_nonexistent_employee(self):
        response = self.client.get('/api/employees/9999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_update_employee_success(self):
        employee_data = {
            'name': 'Charlie Brown',
            'email': 'charlie@example.com',
            'position': 'Analyst'
        }
        create_response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        created_data = json.loads(create_response.data)
        employee_id = created_data['data']['id']

        update_data = {
            'name': 'Charles Brown',
            'position': 'Senior Analyst'
        }
        response = self.client.put(
            f'/api/employees/{employee_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'Charles Brown')
        self.assertEqual(data['data']['position'], 'Senior Analyst')

    def test_update_nonexistent_employee(self):
        update_data = {
            'name': 'Test Name'
        }
        response = self.client.put(
            '/api/employees/9999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_update_employee_duplicate_email(self):
        employee1 = {
            'name': 'Employee One',
            'email': 'one@example.com',
            'position': 'Developer'
        }
        employee2 = {
            'name': 'Employee Two',
            'email': 'two@example.com',
            'position': 'Designer'
        }

        self.client.post(
            '/api/employees',
            data=json.dumps(employee1),
            content_type='application/json'
        )

        create_response2 = self.client.post(
            '/api/employees',
            data=json.dumps(employee2),
            content_type='application/json'
        )
        employee2_id = json.loads(create_response2.data)['data']['id']

        update_data = {'email': 'one@example.com'}
        response = self.client.put(
            f'/api/employees/{employee2_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)

    def test_delete_employee_success(self):
        employee_data = {
            'name': 'David Lee',
            'email': 'david@example.com',
            'position': 'Manager'
        }
        create_response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        created_data = json.loads(create_response.data)
        employee_id = created_data['data']['id']

        response = self.client.delete(f'/api/employees/{employee_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        get_response = self.client.get(f'/api/employees/{employee_id}')
        self.assertEqual(get_response.status_code, 404)

    def test_delete_nonexistent_employee(self):
        response = self.client.delete('/api/employees/9999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_create_employee_with_empty_strings(self):
        employee_data = {
            'name': '   ',
            'email': '   ',
            'position': '   '
        }
        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_create_employee_no_data(self):
        response = self.client.post(
            '/api/employees',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_email_case_insensitive(self):
        employee_data = {
            'name': 'Test User',
            'email': 'Test@Example.COM',
            'position': 'Tester'
        }
        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['data']['email'], 'test@example.com')

    def test_name_and_position_trimming(self):
        employee_data = {
            'name': '  John Doe  ',
            'email': 'john@example.com',
            'position': '  Software Engineer  '
        }
        response = self.client.post(
            '/api/employees',
            data=json.dumps(employee_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['data']['name'], 'John Doe')
        self.assertEqual(data['data']['position'], 'Software Engineer')

if __name__ == '__main__':
    unittest.main()
