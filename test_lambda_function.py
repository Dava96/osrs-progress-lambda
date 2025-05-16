import unittest
import json
from unittest.mock import patch
import requests
from lambda_function import lambda_handler, get_playerData

class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler(self):
        event = {}
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Hello from Lambda!')

class TestGetPlayerData(unittest.TestCase):
    def setUp(self):
        self.mock_response = {
            'data': {
                'skills': {
                    'overall': {
                        'metric': 'overall',
                        'experience': {
                            'gained': 0,
                            'start': "2025-01-01",
                            'end': "2025-01-02"
                        }
                    }
                }
            }
        }

    def test_get_player_data(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.mock_response

            result = get_playerData('MyRandomPlayer')
            self.assertEqual(result, self.mock_response)

    def test_get_player_data_api_error(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404

            result = get_playerData('nonexistentplayer')
            self.assertEqual(result, {'error': 404 })

    def test_get_player_data_name_with_spaces(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.mock_response

            result = get_playerData('player with spaces')
            self.assertEqual(result, self.mock_response)


    def test_get_player_data_empty_username(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200

            result = get_playerData('')
            self.assertEqual(result, {'error': 'Username is empty'})

if __name__ == '__main__':
    unittest.main()
