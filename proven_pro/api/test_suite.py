from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from api.models import UserProfile, ProfileShare, Review
from django.utils import timezone
import datetime

User = get_user_model()

class AuthenticationTests(TestCase):
    """Test authentication endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_register(self):
        url = '/api/register/'
        
        # Use a password that meets all requirements (uppercase + special character)
        # Use a unique email with timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        
        data = {
            'email': f'new{timestamp}@example.com',
            'username': f'newuser{timestamp}',
            'password': 'NewPass123!',  # Includes uppercase and special character
            'password2': 'NewPass123!',  # Confirmation password
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        print(f"Register response: {response.status_code}, data: {response.data if hasattr(response, 'data') else 'No data'}")
        
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK],
                     f"Expected 201 or 200, got {response.status_code}")
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email=data['email']).exists())
    
    def test_login(self):
        url = '/api/login/'
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_logout(self):
        # Login first
        login_url = '/api/login/'
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        login_response = self.client.post(login_url, login_data, format='json')
        
        # Then logout
        url = '/api/logout/'
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProfileTests(TestCase):
    """Test profile-related endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            name='Test User',
            job_title='Developer',
            job_specialization='Web'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_profile(self):
        url = '/api/get_profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test User')
    
    def test_profile_status(self):
        url = '/api/profile_status/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Print the actual response data for debugging
        print(f"Profile status response data: {response.data}")
        
        # Check for either 'is_complete' or 'has_profile' in the response
        self.assertTrue(
            'is_complete' in response.data or 'has_profile' in response.data,
            f"Expected 'is_complete' or 'has_profile' in response, got: {response.data}"
        )
        
        # If 'has_profile' is present, assert it's a boolean
        if 'has_profile' in response.data:
            self.assertIsInstance(response.data['has_profile'], bool)





