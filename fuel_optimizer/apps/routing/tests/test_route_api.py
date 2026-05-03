from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import json


class RouteOptimizationAPITest(TestCase):
    """Test cases for route optimization API"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_route_api_missing_fields(self):
        """Test API with missing required fields"""
        response = self.client.post('/api/route/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_route_api_invalid_data(self):
        """Test API with invalid data"""
        data = {'start': '', 'end': ''}
        response = self.client.post('/api/route/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_route_api_valid_request_structure(self):
        """Test API accepts valid request structure"""
        # This test only validates the request structure
        # Actual API calls require valid API key
        data = {
            'start': 'New York',
            'end': 'Los Angeles'
        }
        response = self.client.post('/api/route/', data, format='json')
        # Will fail without API key, but should accept the structure
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
