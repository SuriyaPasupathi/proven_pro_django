# Proven Pro Backend

A Django REST API backend for the Proven Pro professional profile platform.

## Setup and Installation

### Prerequisites
- Python 3.10+
- MySQL
- Git

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/proven_pro.git
   cd proven_pro
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory with the following:
   ```
   # Django Settings
   SECRET_KEY=your_secret_key_here
   DEBUG=True

   # Database Settings
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=proven_pro
   DB_USER=your_db_username
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306

   # Email Settings
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   DEFAULT_FROM_EMAIL=your_email@gmail.com
   EMAIL_TIMEOUT=30

   # Frontend URL
   FRONTEND_URL=http://localhost:5173

  
   ```

5. **Create MySQL database**
   ```sql
   CREATE DATABASE proven_pro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'your_db_username'@'localhost' IDENTIFIED BY 'your_db_password';
   GRANT ALL PRIVILEGES ON proven_pro.* TO 'your_db_username'@'localhost';
   FLUSH PRIVILEGES;
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create admin user**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start development server**
   ```bash
   python manage.py runserver
   ```

## API Documentation

### Authentication Endpoints
- `POST /api/register/` - Register new user
- `POST /api/login/` - Login and get JWT tokens
- `POST /api/logout/` - Logout (blacklist refresh token)
- `POST /api/google-auth/` - Login with Google
- `POST /api/request-reset-password/` - Request password reset
- `POST /api/reset-password-confirm/` - Reset password with token

### Profile Endpoints
- `GET /api/profile/` - Get user profile
- `POST /api/profile/` - Create user profile
- `PUT /api/profile/` - Update user profile

### Verification Endpoints
- `POST /api/upload-verification-document/` - Upload verification documents
- `POST /api/request-mobile-verification/` - Request mobile verification
- `POST /api/verify-mobile-otp/` - Verify mobile OTP
- `GET /api/verification-status/` - Get verification status

### Review Endpoints
- `POST /api/generate-profile-share/` - Generate profile share link
- `GET /api/verify-profile-share/<token>/` - Verify profile share
- `POST /api/submit-review/<token>/` - Submit review
- `GET /api/get-reviews/` - Get user reviews

### Subscription Endpoints
- `GET /api/subscription-check/` - Check subscription status
- `POST /api/update-subscription/` - Update subscription
- `POST /api/create-gcash-payment/` - Create GCash payment
- `POST /api/verify-payment/` - Verify payment

## Testing

Run the test suite:
```bash
python manage.py test
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Verify MySQL is running
   - Check credentials in `.env` file
   - Ensure database exists

2. **Email Configuration**
   - For Gmail, use App Password instead of regular password
   - Test email connection with:
     ```bash
     python manage.py shell
     >>> from django.core.mail import send_mail
     >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
     ```

3. **File Upload Problems**
   - Check file size limits
   - Verify using multipart/form-data
   - Ensure correct document_type values (exactly `gov_id` or `address`)

4. **API Endpoint Errors**
   - Remember trailing slashes on all endpoints
   - Check authentication headers
   - Verify content types (application/json or multipart/form-data)
