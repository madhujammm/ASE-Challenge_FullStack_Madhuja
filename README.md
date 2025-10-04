# EmployeeHub — Smart Workforce Manager

A modern, full-stack employee management system built with Flask backend and vanilla JavaScript frontend. Features a responsive design with dark mode support, real-time activity tracking, and comprehensive CRUD operations.

## 🌟 Features

### Frontend

* **Modern UI/UX**: Clean, responsive design with green color palette
* **Dark Mode Support**: Toggle between light and dark themes
* **Real-time Search**: Instant filtering of employees by name, email, or position
* **Interactive Dashboard**: Statistics cards with trend indicators
* **Activity Log**: Sidebar showing recent employee additions, edits, and deletions
* **Sortable Table**: Click column headers to sort employees
* **Form Validation**: Client-side and server-side validation with error messages
* **Toast Notifications**: User-friendly feedback for all operations

### Backend

* **RESTful API**: Clean API design following REST principles
* **SQLite Database**: Lightweight, file-based database
* **Data Validation**: Comprehensive input validation and error handling
* **CORS Support**: Cross-origin resource sharing enabled
* **Sample Data**: Auto-populates with sample employees on first run

### Core Functionality

* **Employee Management**: Create, read, update, and delete employees
* **Unique Constraints**: Prevent duplicate emails and multiple positions per employee
* **Data Persistence**: Local storage caching for improved performance
* **Activity Tracking**: Log all operations with timestamps
* **Responsive Design**: Works seamlessly on desktop, tablet, and mobile

## 🚀 Quick Start

### Prerequisites

* Python 3.7+
* Modern web browser with JavaScript enabled

### Installation

1. **Clone or download the project files**

   ```bash
   # Project structure:
   # ├── app.py
   # ├── test_app.py
   # ├── static/
   # │   ├── css/
   # │   │   └── styles.css
   # │   └── js/
   # │       └── app.js
   # └── templates/
   #     └── index.html
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python app.py
   ```

4. **Access the application**

   * Open your browser and navigate to: `http://localhost:5000`
   * The application will automatically create the database with sample data

## 🤪 Testing

### Running Tests

```bash
# Run all tests
python -m unittest test_app.py -v

# Run specific test
python -m unittest test_app.py.EmployeeAPITestCase.test_create_employee_success -v
```

### Test Coverage

The test suite includes **17 comprehensive tests** covering:

#### ✅ Employee Creation (6 tests)

* Successful creation with valid data
* Missing required fields handling
* Invalid email format validation
* Duplicate email prevention
* Empty string validation
* No data request handling

#### ✅ Employee Retrieval (4 tests)

* Empty database handling
* Retrieval after creation
* Single employee fetching
* Non-existent employee handling

#### ✅ Employee Updates (3 tests)

* Successful updates
* Non-existent employee updates
* Duplicate email prevention during updates

#### ✅ Employee Deletion (2 tests)

* Successful deletion
* Non-existent employee deletion

#### ✅ Data Processing (2 tests)

* Email case normalization
* Name and position whitespace trimming

### Test Results

```
----------------------------------------------------------------------
Ran 17 tests in 2.405s
OK
```

**All tests pass** - ensuring API reliability and data integrity.

## 🛠️ REST API Implementation

### API Endpoints

| Method   | Endpoint              | Description           | Status Codes            |
| -------- | --------------------- | --------------------- | ----------------------- |
| `GET`    | `/api/employees`      | Get all employees     | 200, 500                |
| `GET`    | `/api/employees/<id>` | Get specific employee | 200, 404, 500           |
| `POST`   | `/api/employees`      | Create new employee   | 201, 400, 409, 500      |
| `PUT`    | `/api/employees/<id>` | Update employee       | 200, 400, 404, 409, 500 |
| `DELETE` | `/api/employees/<id>` | Delete employee       | 200, 404, 500           |

### Request/Response Examples

**Create Employee:**

```http
POST /api/employees
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john.doe@company.com",
  "position": "Software Engineer"
}

Response (201 Created):
{
  "success": true,
  "message": "Employee created successfully",
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@company.com",
    "position": "Software Engineer",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Response (409 Conflict):**

```json
{
  "success": false,
  "error": "Employee with this email already exists"
}
```

**Validation Error (400 Bad Request):**

```json
{
  "success": false,
  "errors": [
    "Name is required and cannot be empty",
    "Invalid email format"
  ]
}
```

### API Features

#### 🔒 Validation Rules

* **Name**: Required, max 100 characters, unique per position
* **Email**: Required, valid format, unique across system
* **Position**: Required, max 100 characters
* **Business Logic**: One employee name cannot have multiple positions

#### 📊 Response Format

All responses follow consistent structure:

```typescript
{
  success: boolean,
  data?: any,           // Present on success
  error?: string,       // Present on failure (single error)
  errors?: string[],    // Present on failure (multiple errors)
  message?: string,     // Success message
  count?: number        // For list endpoints
}
```

#### 🎯 Business Logic

* **Email Normalization**: All emails converted to lowercase
* **Input Trimming**: Whitespace removed from name and position
* **Duplicate Prevention**: Comprehensive checks for email and name conflicts

## 💾 Database Schema

```python
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    position = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## 🎨 UI Components

### Dashboard

* **Total Employees Card**: Shows current employee count with weekly trend
* **Unique Positions Card**: Displays number of distinct positions
* **Profile Completion Card**: Sample metrics card (static data)

### Employee Table

* Sortable columns (Name, Email, Position)
* Action buttons (Edit, Delete)
* Real-time search functionality
* Empty state handling

### Modals

* **Add/Edit Employee Modal**: Form with validation
* **Delete Confirmation Modal**: Safety confirmation for deletions

### Activity Sidebar

* Real-time activity feed
* Color-coded icons (green: added, blue: edited, red: deleted)
* Relative timestamps (e.g., "2 hours ago")

## 🔧 Configuration

### Environment Setup

The application uses the following configuration:

* **Port**: 5000
* **Database**: SQLite (`employees.db`)
* **CORS**: Enabled for all origins
* **Cache**: 5-minute client-side caching

### Customization

**Color Scheme** (in `styles.css`):

```css
:root {
    --primary-color: #059669;       /* Main green */
    --primary-hover: #047857;       /* Dark green */
    /* ... other variables */
}
```

**API Configuration** (in `app.js`):

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
const CACHE_KEY = 'employeeCache';
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes
```

## 📱 Browser Compatibility

* Chrome 90+
* Firefox 88+
* Safari 14+
* Edge 90+

## 🚀 Performance Features

* **Client-side Caching**: Reduces API calls
* **Efficient Rendering**: Virtual DOM-like updates
* **Debounced Search**: Optimized search performance
* **Local Storage**: Activity log persistence

## 🔄 Activity Tracking

The system automatically logs:

* Employee additions with "➕" icon
* Employee edits with "✏️" icon
* Employee deletions with "🗑️" icon

Activities are:

* Stored in browser localStorage
* Limited to last 10 activities
* Displayed with relative timestamps

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**

   ```bash
   # Kill process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

2. **Database issues**

   ```bash
   # Delete and recreate database
   rm employees.db
   python app.py
   ```

3. **CORS errors**

   * Ensure Flask-CORS is installed
   * Check browser console for errors

### Debug Mode

Enable debug mode by setting `debug=True` in `app.run()`:

```python
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
```

## 👥 Future Enhancements

Potential features for expansion:

* User authentication and authorization
* Department management
* Employee photos upload
* Advanced filtering and reporting
* Export functionality (CSV, PDF)
* Email notifications
* Bulk operations

## 🤝 Development

### Running Tests

```bash
# Run all tests with verbose output
python -m unittest test_app.py -v

# Run specific test case
python -m unittest test_app.py.EmployeeAPITestCase -v
```

### Test-Driven Development

The comprehensive test suite enables:

* **Confident refactoring**
* **Regression prevention**
* **API contract verification**
* **Data integrity assurance**


## 🙏 Acknowledgments

* Built with [Flask](https://flask.palletsprojects.com/)
* Icons from [Feather Icons](https://feathericons.com/)
* Modern CSS practices and responsive design
* Comprehensive testing with Python unittest

---

## 🏆 Quality Assurance

### Code Quality Metrics

* **Test Coverage**: 17 comprehensive unit tests
* **API Reliability**: All endpoints thoroughly tested
* **Error Handling**: Comprehensive edge case coverage
* **Data Integrity**: Business rules enforced at API level

### Deployment Ready

* **Production Stability**: All tests passing
* **Error Resilience**: Graceful error handling
* **Performance**: Client-side caching and optimization
* **Security**: Input validation and sanitization

**EmployeeHub** — Making workforce management simple, reliable, and efficient! 🚀
