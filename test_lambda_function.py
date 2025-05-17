import unittest
import json
from unittest.mock import patch
import requests
from lambda_function import lambda_handler, get_player_data, is_player_active

class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler(self):
        event = {}
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Hello from Lambda!')

class TestIsPlayerActive(unittest.TestCase):
    def setUp(self):
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
                self.mock_active_response = json.load(f)

        with open('tests/fixtures/inactive-player-gained-response.json', 'r') as f:
                self.mock_inactive_response = json.load(f)

    def test_is_player_active_returns_true(self):
        self.assertTrue(is_player_active(self.mock_active_response))

    def test_is_player_active_returns_false(self):
        self.assertFalse(is_player_active(self.mock_inactive_response))

class TestGetPlayerData(unittest.TestCase):
    def setUp(self):
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
            self.mock_active_response = json.load(f)

    def test_get_player_data(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.mock_active_response

            result = get_player_data('MyRandomPlayer')
            self.assertEqual(result, self.mock_active_response)

    def test_get_player_data_api_error(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404

            result = get_player_data('nonexistentplayer')
            self.assertEqual(result, {'error': 404 })

    def test_get_player_data_name_with_spaces(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.mock_active_response

            result = get_player_data('player with spaces')
            self.assertEqual(result, self.mock_active_response)

    def test_get_player_data_empty_username(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200

            result = get_player_data('')
            self.assertEqual(result, {'error': 'Username is empty'})

if __name__ == '__main__':
    unittest.main()
