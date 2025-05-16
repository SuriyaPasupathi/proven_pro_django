# API Test Plan

## Overview
This document outlines the testing strategy for the Proven Pro API.

## Test Environment
- Django 5.1.1
- Python 3.10
- MySQL database

## Test Categories

### Unit Tests
- Model tests (User, UserProfile, SocialLink, Review, ProfileShare)
- View tests (authentication, profile management, reviews)
- URL routing tests

### Integration Tests
- API endpoint tests
- Authentication flow tests
- Profile creation and update flow

### Special Considerations
- The `/api/update_profile/` endpoint only accepts PUT requests with form data
- The `/api/register/` endpoint requires passwords with at least one uppercase letter AND one special character

## Password Requirements
All test passwords should include:
- At least one uppercase letter
- At least one special character
- Example: `'NewPass123!'`

## API Endpoint Requirements

### Register Endpoint
- Method: POST
- Content-Type: application/json
- Required fields: 
  - email (must be unique)
  - username (must be unique)
  - password (must include uppercase letter and special character)
  - password2 (confirmation password, must match password)
  - first_name (optional)
  - last_name (optional)
- Example request:
```json
{
  "email": "new@example.com",
  "username": "newuser",
  "password": "NewPass123!",
  "password2": "NewPass123!",
  "first_name": "New",
  "last_name": "User"
}
```
- Expected response: 201 Created

### Update Profile Endpoint
- Method: PUT
- Content-Type: multipart/form-data or application/x-www-form-urlencoded
- Does NOT accept JSON data

## Running Tests
```bash
# Run all tests
python manage.py test

# Run specific test class
python manage.py test api.tests.CustomUserTests

# Run with coverage
coverage run manage.py test
coverage report
```

## Continuous Integration
Tests are automatically run on GitHub Actions for all pull requests to main and develop branches.

## Test Debugging Tips

If you encounter issues with specific endpoints, use the `APIDebugTests` class to inspect them:

```python
python manage.py test api.tests.APIDebugTests
```

This will print detailed information about the endpoint's allowed methods, content types, and response codes.


