
# Resource Management and Booking System API

A RESTful Resource Management and Booking System built using Django REST Framework and PostgreSQL.

## Features

- JWT Authentication
- Role-Based Access Control
- User Management
- Resource Category Management
- Resource Management (CRUD)
- Booking Creation and Management
- Booking Approval and Rejection
- Resource Availability Tracking
- Double-Booking Prevention
- PostgreSQL Database Integration

## Technologies Used

- Python
- Django
- Django REST Framework
- PostgreSQL
- Simple JWT
- Django Filter

## User Roles

### Administrator
Manages users, resources, categories, and bookings.

### Resource Manager
Manages resources, reviews bookings, and monitors availability.

### Employee
Views resources, creates bookings, and manages their own requests.

## Installation

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

   pip install -r requirements.txt

4. Configure PostgreSQL credentials in the .env file.
5. Apply database migrations:

   python manage.py migrate

6. Start the development server:

   python manage.py runserver

## API Endpoints

- /api/auth/register/
- /api/auth/login/
- /api/auth/profile/
- /api/categories/
- /api/resources/
- /api/bookings/
- /api/availability/

## Project Status

Core backend implementation completed.
