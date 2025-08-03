import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
import time
import requests
import jwt

from pyemvue.auth import Auth, SimulatedAuth


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.tokens = {
            "access_token": "test_access_token",
            "id_token": "test_id_token", 
            "refresh_token": "test_refresh_token"
        }

    @patch('pyemvue.auth.Cognito')
    def test_init_with_tokens(self, mock_cognito):
        auth = Auth(
            host="https://api.test.com",
            tokens=self.tokens,
            connect_timeout=5.0,
            read_timeout=10.0
        )
        
        self.assertEqual(auth.host, "https://api.test.com")
        self.assertEqual(auth.connect_timeout, 5.0)
        self.assertEqual(auth.read_timeout, 10.0)
        mock_cognito.assert_called_once()

    @patch('pyemvue.auth.Cognito')
    def test_init_with_username_password(self, mock_cognito):
        auth = Auth(
            host="https://api.test.com",
            username="test@example.com",
            password="password123"
        )
        
        self.assertEqual(auth.host, "https://api.test.com")
        self.assertEqual(auth._password, "password123")
        mock_cognito.assert_called_once()

    @patch('pyemvue.auth.Cognito')
    def test_refresh_tokens_with_password(self, mock_cognito):
        mock_cognito_instance = Mock()
        mock_cognito_instance.authenticate.return_value = None
        mock_cognito_instance.renew_access_token.return_value = None
        mock_cognito_instance.access_token = "new_access_token"
        mock_cognito_instance.id_token = "new_id_token"
        mock_cognito_instance.refresh_token = "new_refresh_token"
        mock_cognito_instance.token_type = "Bearer"
        mock_cognito.return_value = mock_cognito_instance
        
        token_updater = Mock()
        auth = Auth(
            host="https://api.test.com",
            username="test@example.com",
            password="password123",
            token_updater=token_updater
        )
        
        tokens = auth.refresh_tokens()
        
        mock_cognito_instance.authenticate.assert_called_once_with(password="password123")
        mock_cognito_instance.renew_access_token.assert_called_once()
        token_updater.assert_called_once()
        self.assertIsNone(auth._password)
        self.assertEqual(tokens["access_token"], "new_access_token")

    @patch('pyemvue.auth.Cognito')
    def test_refresh_tokens_without_password(self, mock_cognito):
        mock_cognito_instance = Mock()
        mock_cognito_instance.renew_access_token.return_value = None
        mock_cognito_instance.access_token = "new_access_token"
        mock_cognito_instance.id_token = "new_id_token"
        mock_cognito_instance.refresh_token = "new_refresh_token"
        mock_cognito_instance.token_type = "Bearer"
        mock_cognito.return_value = mock_cognito_instance
        
        auth = Auth(host="https://api.test.com", tokens=self.tokens)
        auth._password = None
        
        tokens = auth.refresh_tokens()
        
        mock_cognito_instance.authenticate.assert_not_called()
        mock_cognito_instance.renew_access_token.assert_called_once()
        self.assertEqual(tokens["access_token"], "new_access_token")

    @patch('pyemvue.auth.Cognito')
    def test_get_username(self, mock_cognito):
        mock_cognito_instance = Mock()
        mock_user = Mock()
        mock_user._data = {"email": "test@example.com"}
        mock_cognito_instance.get_user.return_value = mock_user
        mock_cognito.return_value = mock_cognito_instance
        
        auth = Auth(host="https://api.test.com", tokens=self.tokens)
        username = auth.get_username()
        
        self.assertEqual(username, "test@example.com")
        mock_cognito_instance.get_user.assert_called_once()

    @patch('pyemvue.auth.Cognito')
    @patch('requests.request')
    def test_request_success(self, mock_request, mock_cognito):
        mock_cognito_instance = Mock()
        mock_cognito.return_value = mock_cognito_instance
        
        # Mock the JWT decode to return a valid token
        with patch.object(Auth, '_decode_token') as mock_decode:
            mock_decode.return_value = {"exp": int(time.time()) + 3600}  # Valid for 1 hour
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"success": true}'
            mock_request.return_value = mock_response
            
            auth = Auth(host="https://api.test.com", tokens=self.tokens)
            auth.tokens = self.tokens
            
            response = auth.request("GET", "test/endpoint")
            
            self.assertEqual(response.status_code, 200)
            mock_request.assert_called_once()

    @patch('pyemvue.auth.Cognito')
    def test_request_no_tokens_raises_error(self, mock_cognito):
        mock_cognito.return_value = Mock()
        
        auth = Auth(host="https://api.test.com")
        auth.tokens = {}
        
        with self.assertRaises(ValueError):
            auth.request("GET", "test/endpoint")

    @patch('pyemvue.auth.Cognito')
    @patch('requests.request')
    def test_request_401_refreshes_tokens(self, mock_request, mock_cognito):
        mock_cognito_instance = Mock()
        mock_cognito.return_value = mock_cognito_instance
        
        with patch.object(Auth, '_decode_token') as mock_decode, \
             patch.object(Auth, 'refresh_tokens') as mock_refresh:
            
            mock_decode.return_value = {"exp": int(time.time()) + 3600}
            mock_refresh.return_value = self.tokens
            
            # First request returns 401, second returns 200
            mock_response_401 = Mock()
            mock_response_401.status_code = 401
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_request.side_effect = [mock_response_401, mock_response_200]
            
            auth = Auth(host="https://api.test.com", tokens=self.tokens)
            auth.tokens = self.tokens
            
            response = auth.request("GET", "test/endpoint")
            
            self.assertEqual(response.status_code, 200)
            mock_refresh.assert_called_once()
            self.assertEqual(mock_request.call_count, 2)

    @patch('pyemvue.auth.Cognito')
    @patch('requests.request')
    @patch('time.sleep')
    def test_request_500_retries_with_backoff(self, mock_sleep, mock_request, mock_cognito):
        mock_cognito_instance = Mock()
        mock_cognito.return_value = mock_cognito_instance
        
        with patch.object(Auth, '_decode_token') as mock_decode:
            mock_decode.return_value = {"exp": int(time.time()) + 3600}
            
            # First request returns 500, second returns 200
            mock_response_500 = Mock()
            mock_response_500.status_code = 500
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_request.side_effect = [mock_response_500, mock_response_200]
            
            auth = Auth(host="https://api.test.com", tokens=self.tokens, max_retry_attempts=3)
            auth.tokens = self.tokens
            
            response = auth.request("GET", "test/endpoint")
            
            self.assertEqual(response.status_code, 200)
            mock_sleep.assert_called_once()
            self.assertEqual(mock_request.call_count, 2)

    @patch('pyemvue.auth.Cognito')
    @patch('requests.get')
    @patch('jwt.get_unverified_header')
    @patch('jwt.api_jwt.decode')
    def test_decode_token(self, mock_jwt_decode, mock_get_header, mock_requests_get, mock_cognito):
        mock_cognito_instance = Mock()
        mock_cognito_instance.user_pool_url = "https://cognito-idp.us-east-2.amazonaws.com/pool"
        mock_cognito.return_value = mock_cognito_instance
        
        # Mock JWKS response
        mock_jwks_response = Mock()
        mock_jwks_response.json.return_value = {
            "keys": [{"kid": "test_kid", "kty": "RSA", "n": "test_n", "e": "AQAB"}]
        }
        mock_requests_get.return_value = mock_jwks_response
        
        mock_get_header.return_value = {"kid": "test_kid"}
        mock_jwt_decode.return_value = {"sub": "user123", "exp": 1234567890}
        
        auth = Auth(host="https://api.test.com", tokens=self.tokens)
        
        with patch('jwt.api_jwk.PyJWK') as mock_pyjwk:
            mock_key_instance = Mock()
            mock_key_instance.key = "mock_key"
            mock_pyjwk.return_value = mock_key_instance
            
            result = auth._decode_token("test_token")
            
            self.assertEqual(result, {"sub": "user123", "exp": 1234567890})
            mock_jwt_decode.assert_called_once()

    def test_extract_tokens_from_cognito(self):
        mock_cognito = Mock()
        mock_cognito.access_token = "access_token"
        mock_cognito.id_token = "id_token"
        mock_cognito.refresh_token = "refresh_token"
        mock_cognito.token_type = "Bearer"
        
        auth = Auth(host="https://api.test.com")
        auth.cognito = mock_cognito
        
        tokens = auth._extract_tokens_from_cognito()
        
        expected = {
            "access_token": "access_token",
            "id_token": "id_token",
            "refresh_token": "refresh_token",
            "token_type": "Bearer"
        }
        self.assertEqual(tokens, expected)

    @patch('requests.request')
    def test_do_request_adds_auth_header(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        auth = Auth(host="https://api.test.com")
        auth.tokens = {"id_token": "test_id_token"}
        
        response = auth._do_request("GET", "test/endpoint")
        
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        headers = call_args[1]["headers"]
        self.assertEqual(headers["authtoken"], "test_id_token")


class TestSimulatedAuth(unittest.TestCase):
    def test_init(self):
        auth = SimulatedAuth(
            host="http://localhost:8080",
            username="test@example.com",
            password="password"
        )
        
        self.assertEqual(auth.host, "http://localhost:8080")
        self.assertEqual(auth.username, "test@example.com")
        self.assertEqual(auth.password, "password")
        self.assertEqual(auth.tokens, {"id_token": "simulator"})

    def test_refresh_tokens(self):
        auth = SimulatedAuth(host="http://localhost:8080")
        tokens = auth.refresh_tokens()
        self.assertEqual(tokens, {"id_token": "simulator"})

    def test_get_username(self):
        auth = SimulatedAuth(host="http://localhost:8080", username="test@example.com")
        username = auth.get_username()
        self.assertEqual(username, "test@example.com")

    def test_get_username_default(self):
        auth = SimulatedAuth(host="http://localhost:8080")
        username = auth.get_username()
        self.assertEqual(username, "simulator")

    @patch('requests.request')
    def test_request_success(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        auth = SimulatedAuth(host="http://localhost:8080")
        response = auth.request("GET", "test/endpoint")
        
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()

    @patch('requests.request')
    def test_request_401_refreshes_tokens(self, mock_request):
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_request.side_effect = [mock_response_401, mock_response_200]
        
        auth = SimulatedAuth(host="http://localhost:8080")
        
        with patch.object(auth, 'refresh_tokens', return_value={"id_token": "simulator"}) as mock_refresh:
            response = auth.request("GET", "test/endpoint")
            
            self.assertEqual(response.status_code, 200)
            mock_refresh.assert_called_once()
            self.assertEqual(mock_request.call_count, 2)


if __name__ == '__main__':
    unittest.main()