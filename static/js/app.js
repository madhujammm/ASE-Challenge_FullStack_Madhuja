const API_BASE_URL = 'http://localhost:5000/api';
const CACHE_KEY = 'employeeCache';
const CACHE_EXPIRY = 5 * 60 * 1000;

let employees = [];
let currentSort = { field: null, direction: 'asc' };
let editingEmployeeId = null;
let activityLog = [];

const elements = {
    darkModeToggle: document.getElementById('darkModeToggle'),
    searchInput: document.getElementById('searchInput'),
    addEmployeeBtn: document.getElementById('addEmployeeBtn'),
    employeeTableBody: document.getElementById('employeeTableBody'),
    employeeModal: document.getElementById('employeeModal'),
    deleteModal: document.getElementById('deleteModal'),
    employeeForm: document.getElementById('employeeForm'),
    modalTitle: document.getElementById('modalTitle'),
    closeModal: document.getElementById('closeModal'),
    cancelBtn: document.getElementById('cancelBtn'),
    closeDeleteModal: document.getElementById('closeDeleteModal'),
    cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
    confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
    submitBtn: document.getElementById('submitBtn'),
    toast: document.getElementById('toast'),
    totalEmployees: document.getElementById('totalEmployees'),
    totalPositions: document.getElementById('totalPositions'),
    employeeId: document.getElementById('employeeId'),
    employeeName: document.getElementById('employeeName'),
    employeeEmail: document.getElementById('employeeEmail'),
    employeePosition: document.getElementById('employeePosition'),
    nameError: document.getElementById('nameError'),
    emailError: document.getElementById('emailError'),
    positionError: document.getElementById('positionError'),
    deleteEmployeeName: document.getElementById('deleteEmployeeName')
};

function initializeApp() {
    loadTheme();
    setupEventListeners();
    loadActivityLog();
    updateActivityLog();
    loadEmployees();
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function setupEventListeners() {
    elements.darkModeToggle.addEventListener('click', toggleTheme);
    elements.searchInput.addEventListener('input', handleSearch);
    elements.addEmployeeBtn.addEventListener('click', () => openModal());
    elements.closeModal.addEventListener('click', closeModal);
    elements.cancelBtn.addEventListener('click', closeModal);
    elements.employeeForm.addEventListener('submit', handleFormSubmit);
    elements.closeDeleteModal.addEventListener('click', closeDeleteModal);
    elements.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    elements.confirmDeleteBtn.addEventListener('click', handleDelete);

    elements.employeeModal.addEventListener('click', (e) => {
        if (e.target === elements.employeeModal) closeModal();
    });

    elements.deleteModal.addEventListener('click', (e) => {
        if (e.target === elements.deleteModal) closeDeleteModal();
    });

    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => handleSort(th.dataset.sort));
    });

    [elements.employeeName, elements.employeeEmail, elements.employeePosition].forEach(input => {
        input.addEventListener('input', () => clearError(input));
        input.addEventListener('blur', () => validateField(input));
    });
}

async function loadEmployees() {
    try {
        const cachedData = getCachedData();
        if (cachedData) {
            employees = cachedData;
            renderEmployees(employees);
            updateAnalytics();
        }

        const response = await fetch(`${API_BASE_URL}/employees`);
        const result = await response.json();

        if (result.success) {
            employees = result.data;
            cacheData(employees);
            renderEmployees(employees);
            updateAnalytics();
        } else {
            showToast(result.error || 'Failed to load employees', 'error');
        }
    } catch (error) {
        console.error('Error loading employees:', error);
        showToast('Failed to connect to server', 'error');
    }
}

function getCachedData() {
    try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (!cached) return null;

        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp > CACHE_EXPIRY) {
            localStorage.removeItem(CACHE_KEY);
            return null;
        }

        return data;
    } catch {
        return null;
    }
}

function cacheData(data) {
    try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    } catch (error) {
        console.error('Failed to cache data:', error);
    }
}

function renderEmployees(employeeList) {
    if (employeeList.length === 0) {
        elements.employeeTableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="4">No employees found. Add your first employee to get started!</td>
            </tr>
        `;
        return;
    }

    elements.employeeTableBody.innerHTML = employeeList.map(employee => `
        <tr>
            <td>${escapeHtml(employee.name)}</td>
            <td>${escapeHtml(employee.email)}</td>
            <td>${escapeHtml(employee.position)}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-secondary btn-small" onclick="openModal(${employee.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        Edit
                    </button>
                    <button class="btn btn-danger btn-small" onclick="openDeleteModal(${employee.id}, '${escapeHtml(employee.name)}')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function updateAnalytics() {
    elements.totalEmployees.textContent = employees.length;
    const uniquePositions = new Set(employees.map(e => e.position.toLowerCase()));
    elements.totalPositions.textContent = uniquePositions.size;
}

function handleSearch(e) {
    const query = e.target.value.toLowerCase().trim();

    if (!query) {
        renderEmployees(employees);
        return;
    }

    const filtered = employees.filter(employee =>
        employee.name.toLowerCase().includes(query) ||
        employee.email.toLowerCase().includes(query) ||
        employee.position.toLowerCase().includes(query)
    );

    renderEmployees(filtered);
}

function handleSort(field) {
    const thElements = document.querySelectorAll('th[data-sort]');
    thElements.forEach(th => th.classList.remove('sorted'));

    if (currentSort.field === field) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.direction = 'asc';
    }

    const sortedEmployees = [...employees].sort((a, b) => {
        const aValue = a[field].toLowerCase();
        const bValue = b[field].toLowerCase();

        if (aValue < bValue) return currentSort.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const activeTh = document.querySelector(`th[data-sort="${field}"]`);
    activeTh.classList.add('sorted');

    renderEmployees(sortedEmployees);
}

function openModal(employeeId = null) {
    editingEmployeeId = employeeId;
    elements.employeeForm.reset();
    clearAllErrors();

    if (employeeId) {
        elements.modalTitle.textContent = 'Edit Employee';
        const employee = employees.find(e => e.id === employeeId);
        if (employee) {
            elements.employeeId.value = employee.id;
            elements.employeeName.value = employee.name;
            elements.employeeEmail.value = employee.email;
            elements.employeePosition.value = employee.position;
        }
    } else {
        elements.modalTitle.textContent = 'Add Employee';
        elements.employeeId.value = '';
    }

    elements.employeeModal.classList.add('show');
}

function closeModal() {
    elements.employeeModal.classList.remove('show');
    elements.employeeForm.reset();
    clearAllErrors();
    editingEmployeeId = null;
}

function openDeleteModal(employeeId, employeeName) {
    editingEmployeeId = employeeId;
    elements.deleteEmployeeName.textContent = employeeName;
    elements.deleteModal.classList.add('show');
}

function closeDeleteModal() {
    elements.deleteModal.classList.remove('show');
    editingEmployeeId = null;
}

function validateField(input) {
    const value = input.value.trim();
    const errorElement = document.getElementById(`${input.id.replace('employee', '').toLowerCase()}Error`);

    clearError(input);

    if (input.id === 'employeeName' && !value) {
        showError(input, errorElement, 'Name is required');
        return false;
    }

    if (input.id === 'employeeEmail') {
        if (!value) {
            showError(input, errorElement, 'Email is required');
            return false;
        }
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(value)) {
            showError(input, errorElement, 'Invalid email format');
            return false;
        }
    }

    if (input.id === 'employeePosition' && !value) {
        showError(input, errorElement, 'Position is required');
        return false;
    }

    return true;
}

function showError(input, errorElement, message) {
    input.classList.add('error');
    errorElement.textContent = message;
}

function clearError(input) {
    input.classList.remove('error');
    const errorElement = document.getElementById(`${input.id.replace('employee', '').toLowerCase()}Error`);
    if (errorElement) errorElement.textContent = '';
}

function clearAllErrors() {
    [elements.employeeName, elements.employeeEmail, elements.employeePosition].forEach(clearError);
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const isNameValid = validateField(elements.employeeName);
    const isEmailValid = validateField(elements.employeeEmail);
    const isPositionValid = validateField(elements.employeePosition);

    if (!isNameValid || !isEmailValid || !isPositionValid) {
        return;
    }

    const employeeData = {
        name: elements.employeeName.value.trim(),
        email: elements.employeeEmail.value.trim(),
        position: elements.employeePosition.value.trim()
    };

    elements.submitBtn.classList.add('loading');
    elements.submitBtn.disabled = true;

    try {
        const url = editingEmployeeId
            ? `${API_BASE_URL}/employees/${editingEmployeeId}`
            : `${API_BASE_URL}/employees`;

        const method = editingEmployeeId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(employeeData)
        });

        const result = await response.json();

        if (result.success) {
            const action = editingEmployeeId ? 'edited' : 'added';
            logActivity(action, employeeData.name, employeeData.position);
            showToast(result.message, 'success');
            closeModal();
            await loadEmployees();
        } else {
            if (result.errors) {
                result.errors.forEach(error => {
                    if (error.toLowerCase().includes('email')) {
                        showError(elements.employeeEmail, elements.emailError, error);
                    } else if (error.toLowerCase().includes('name')) {
                        showError(elements.employeeName, elements.nameError, error);
                    } else if (error.toLowerCase().includes('position')) {
                        showError(elements.employeePosition, elements.positionError, error);
                    } else {
                        // Show generic error for other validation issues
                        showToast(error, 'error');
                    }
                });
            } else if (result.error) {
                // Handle single error messages (like duplicate name/position)
                if (result.error.toLowerCase().includes('employee') && result.error.toLowerCase().includes('position')) {
                    showError(elements.employeeName, elements.nameError, result.error);
                } else if (result.error.toLowerCase().includes('email')) {
                    showError(elements.employeeEmail, elements.emailError, result.error);
                } else {
                    showToast(result.error, 'error');
                }
            } else {
                showToast('Operation failed', 'error');
            }
        }
    } catch (error) {
        console.error('Error saving employee:', error);
        showToast('Failed to connect to server', 'error');
    } finally {
        elements.submitBtn.classList.remove('loading');
        elements.submitBtn.disabled = false;
    }
}

async function handleDelete() {
    if (!editingEmployeeId) return;

    elements.confirmDeleteBtn.classList.add('loading');
    elements.confirmDeleteBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/employees/${editingEmployeeId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            const employee = employees.find(e => e.id === editingEmployeeId);
            if (employee) {
                logActivity('deleted', employee.name, employee.position);
            }
            showToast(result.message, 'success');
            closeDeleteModal();
            await loadEmployees();
        } else {
            showToast(result.error || 'Failed to delete employee', 'error');
        }
    } catch (error) {
        console.error('Error deleting employee:', error);
        showToast('Failed to connect to server', 'error');
    } finally {
        elements.confirmDeleteBtn.classList.remove('loading');
        elements.confirmDeleteBtn.disabled = false;
    }
}

// Activity Log Functions
function logActivity(type, employeeName, position) {
    const activity = {
        type: type,
        employeeName: employeeName,
        position: position,
        timestamp: new Date().toISOString(),
        id: Date.now()
    };
    
    activityLog.unshift(activity); // Add to beginning of array
    activityLog = activityLog.slice(0, 10); // Keep only last 10 activities
    
    updateActivityLog();
    saveActivityLog();
}

function updateActivityLog() {
    const activityList = document.getElementById('activityList');
    
    if (!activityList) return;
    
    if (activityLog.length === 0) {
        activityList.innerHTML = `
            <div class="activity-item">
                <div class="activity-content">
                    <p>No recent activity</p>
                    <span class="activity-detail">Activities will appear here</span>
                </div>
            </div>
        `;
        return;
    }
    
    activityList.innerHTML = activityLog.map(activity => {
        const timeAgo = getTimeAgo(activity.timestamp);
        const icons = {
            added: '<line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>',
            edited: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>',
            deleted: '<polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>'
        };
        
        const messages = {
            added: 'New employee added',
            edited: 'Employee updated',
            deleted: 'Employee deleted'
        };
        
        return `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${icons[activity.type]}
                    </svg>
                </div>
                <div class="activity-content">
                    <p>${messages[activity.type]}</p>
                    <span class="activity-detail">${activity.employeeName} - ${activity.position}</span>
                    <span class="activity-time">${timeAgo}</span>
                </div>
            </div>
        `;
    }).join('');
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const past = new Date(timestamp);
    const diffInSeconds = Math.floor((now - past) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
}

function saveActivityLog() {
    try {
        localStorage.setItem('employeeActivityLog', JSON.stringify(activityLog));
    } catch (error) {
        console.error('Failed to save activity log:', error);
    }
}

function loadActivityLog() {
    try {
        const saved = localStorage.getItem('employeeActivityLog');
        if (saved) {
            activityLog = JSON.parse(saved);
        }
    } catch (error) {
        console.error('Failed to load activity log:', error);
    }
}

function showToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;

    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.openModal = openModal;
window.openDeleteModal = openDeleteModal;

document.addEventListener('DOMContentLoaded', initializeApp);
