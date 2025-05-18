import unittest
import json
from unittest.mock import patch
import requests
from lambda_function import lambda_handler, get_player_data, is_player_active, filter_experience_gains, filter_boss_gains, filter_activity_gains, get_efficiency_data, merge_player_data, sort_players_by

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

class TestFilterExperienceGains(unittest.TestCase):
    def setUp(self):
        self.expected_experience = 12345678
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
            self.mock_active_response = json.load(f)


        with open('tests/fixtures/inactive-player-gained-response.json', 'r') as f:
            self.mock_inactive_response = json.load(f)

    def test_filter_experience_gains(self):
        result = filter_experience_gains(self.mock_active_response)
        self.assertEqual(24, len(result))
        for skill in result:
            self.assertEqual(skill['gained'], self.expected_experience)

    def test_filter_experience_gains_no_gains(self):
        result = filter_experience_gains(self.mock_inactive_response)
        self.assertEqual(0, len(result))

class TestFilterBossGains(unittest.TestCase):
    def setUp(self):
        self.expected_boss = 12345678
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
            self.mock_active_response = json.load(f)

        with open('tests/fixtures/inactive-player-gained-response.json', 'r') as f:
            self.mock_inactive_response = json.load(f)

    def test_filter_boss_gains(self):
        result = filter_boss_gains(self.mock_active_response)
        self.assertEqual(66, len(result))
        for boss in result:
            self.assertEqual(boss['gained'], self.expected_boss)

    def test_filter_boss_gains_no_gains(self):
        result = filter_boss_gains(self.mock_inactive_response)
        self.assertEqual(0, len(result))

class TestFilterActivityGains(unittest.TestCase):
    def setUp(self):
        self.expected_activity = 12345678
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
            self.mock_active_response = json.load(f)

        with open('tests/fixtures/inactive-player-gained-response.json', 'r') as f:
            self.mock_inactive_response = json.load(f)

    def test_filter_activity_gains(self):
        result = filter_activity_gains(self.mock_active_response)
        self.assertEqual(16, len(result))
        for activity in result:
            self.assertEqual(activity['gained'], self.expected_activity)

    def test_filter_activity_gains_no_gains(self):
        result = filter_activity_gains(self.mock_inactive_response)
        self.assertEqual(0, len(result))

class TestGetEfficiencyData(unittest.TestCase):
    def setUp(self):
        self.expected_gains = 12345678
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
            self.mock_active_response = json.load(f)

        with open('tests/fixtures/inactive-player-gained-response.json', 'r') as f:
            self.mock_inactive_response = json.load(f)

    def test_get_efficiency_data(self):
        result = get_efficiency_data(self.mock_active_response)
        self.assertEqual(1, len(result))
        self.assertEqual(self.expected_gains, result[0]['ehp'])
        self.assertEqual(self.expected_gains, result[0]['ehb'])

    def test_get_efficiency_data_no_gains(self):
        result = get_efficiency_data(self.mock_inactive_response)
        self.assertEqual(1, len(result))
        self.assertEqual(0,result[0]['ehp'])
        self.assertEqual(0, result[0]['ehb'])

class TestMergePlayerData(unittest.TestCase):
    def setUp(self):
        with open('tests/fixtures/active-player-gained-response.json', 'r') as f:
            self.mock_active_response = json.load(f)

    def test_merge_player_data(self):
        username = "TestUser"
        player_data = merge_player_data(username, self.mock_active_response)
        self.assertEqual(player_data['username'], username)
        self.assertTrue(isinstance(player_data['experience_gains'], list))
        self.assertTrue(isinstance(player_data['boss_gains'], list))
        self.assertTrue(isinstance(player_data['activity_gains'], list))
        self.assertTrue(isinstance(player_data['efficiency_data'], list))

class TestSortPlayersBy(unittest.TestCase):
    def setUp(self):
        self.players = {
            "Alice": {
                "experience_gains": [{"skill": "attack", "gained": 100}],
                "boss_gains": [{"boss": "boss1", "gained": 5}],
                "activity_gains": [{"activity": "activity1", "gained": 10}],
                "efficiency_data": [{"ehp": 50, "ehb": 5, "gained": 55}]
            },
            "Bob": {
                "experience_gains": [{"skill": "attack", "gained": 200}],
                "boss_gains": [{"boss": "boss1", "gained": 2}],
                "activity_gains": [{"activity": "activity1", "gained": 20}],
                "efficiency_data": [{"ehp": 100, "ehb": 10, "gained": 110}]
            }
        }

    def test_sort_players_by_experience(self):
        sorted_players = sort_players_by(self.players, 'experience_gains')
        self.assertEqual(list(sorted_players.keys())[0], "Bob")
        self.assertEqual(list(sorted_players.keys())[1], "Alice")

    def test_sort_players_by_boss_gains(self):
        sorted_players = sort_players_by(self.players, 'boss_gains')
        self.assertEqual(list(sorted_players.keys())[0], "Alice")
        self.assertEqual(list(sorted_players.keys())[1], "Bob")

    def test_sort_players_by_activity_gains(self):
        sorted_players = sort_players_by(self.players, 'activity_gains')
        self.assertEqual(list(sorted_players.keys())[0], "Bob")
        self.assertEqual(list(sorted_players.keys())[1], "Alice")

    def test_sort_players_by_efficiency_data(self):
        sorted_players = sort_players_by(self.players, 'efficiency_data')
        self.assertEqual(list(sorted_players.keys())[0], "Bob")
        self.assertEqual(list(sorted_players.keys())[1], "Alice")


if __name__ == '__main__':
    unittest.main()
