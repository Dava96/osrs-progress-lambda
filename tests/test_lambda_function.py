import unittest
import json
import os
import requests
from unittest.mock import patch
from lambda_function import (
    lambda_handler, get_player_data, is_player_active, filter_experience_gains,
    filter_boss_gains, filter_activity_gains, get_efficiency_data, merge_player_data,
    sort_players_by, build_ranking_embed, build_player_embeds
)
from discord_webhook import DiscordEmbed

def load_fixture(filename):
    with open(f'tests/fixtures/{filename}', 'r') as f:
        return json.load(f)

class TestLambdaHandler(unittest.TestCase):
    @patch.dict(os.environ, {
        'WEBHOOK_URL': 'http://mockwebhookurl.com/test',
        'USERNAMES': 'PlayerOne,PlayerTwo',
        'SEND_RANKING_EMBED': 'true',
        'SEND_PLAYER_EMBED': 'true'
    })
    @patch('lambda_function.execute_discord_webhooks')
    def test_lambda_handler_embeds(self, mock_execute_webhooks):
        mock_player_data = {
            'data': {
                'skills': {
                    'overall': {'metric': 'overall', 'experience': {'gained': 1000}},
                    'attack': {'metric': 'attack', 'experience': {'gained': 500}},
                },
                'bosses': {},
                'activities': {},
                'computed': {'ehp': {'value': {'gained': 1.0}}, 'ehb': {'value': {'gained': 0.5}}}
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            response = lambda_handler({}, None)
            self.assertEqual(response['statusCode'], 200)
            mock_execute_webhooks.assert_called_once()

    @patch.dict(os.environ, {
        'WEBHOOK_URL': 'http://mockwebhookurl.com/test',
        'USERNAMES': 'PlayerOne,PlayerTwo',
        'SEND_RANKING_EMBED': 'false',
        'SEND_PLAYER_EMBED': 'true'
    })
    @patch('lambda_function.execute_discord_webhooks')
    def test_lambda_handler_only_player_embeds(self, mock_execute_webhooks):
        mock_player_data = {
            'data': {
                'skills': {'overall': {'metric': 'overall', 'experience': {'gained': 1000}}},
                'bosses': {}, 'activities': {},
                'computed': {'ehp': {'value': {'gained': 1.0}}, 'ehb': {'value': {'gained': 0.5}}}
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            response = lambda_handler({}, None)
            self.assertEqual(response['statusCode'], 200)
            mock_execute_webhooks.assert_called_once()

    @patch.dict(os.environ, {
        'WEBHOOK_URL': 'http://mockwebhookurl.com/test',
        'USERNAMES': 'PlayerOne,PlayerTwo',
        'SEND_RANKING_EMBED': 'true',
        'SEND_PLAYER_EMBED': 'false'
    })
    @patch('lambda_function.execute_discord_webhooks')
    def test_lambda_handler_only_ranking_embed(self, mock_execute_webhooks):
        mock_player_data = {
            'data': {
                'skills': {'overall': {'metric': 'overall', 'experience': {'gained': 1000}}},
                'bosses': {}, 'activities': {},
                'computed': {'ehp': {'value': {'gained': 1.0}}, 'ehb': {'value': {'gained': 0.5}}}
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            response = lambda_handler({}, None)
            self.assertEqual(response['statusCode'], 200)
            mock_execute_webhooks.assert_called_once()

    @patch.dict(os.environ, {
        'WEBHOOK_URL': 'http://mockwebhookurl.com/test',
        'USERNAMES': 'PlayerOne,PlayerTwo',
        'SEND_RANKING_EMBED': 'false',
        'SEND_PLAYER_EMBED': 'false'
    })
    @patch('lambda_function.execute_discord_webhooks')
    def test_lambda_handler_no_embeds_sent(self, mock_execute_webhooks):
        mock_player_data = {
            'data': {
                'skills': {'overall': {'metric': 'overall', 'experience': {'gained': 1000}}},
                'bosses': {}, 'activities': {},
                'computed': {'ehp': {'value': {'gained': 1.0}}, 'ehb': {'value': {'gained': 0.5}}}
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            response = lambda_handler({}, None)
            self.assertEqual(response['statusCode'], 200)
            mock_execute_webhooks.assert_not_called()

    @patch.dict(os.environ, {
        'WEBHOOK_URL': 'http://mockwebhookurl.com/test',
        'USERNAMES': 'InactiveUser'
    })
    @patch('lambda_function.execute_discord_webhooks')
    def test_lambda_handler_no_active_players(self, mock_execute_webhooks):
        mock_inactive_player_data = {
            'data': {
                'skills': {'overall': {'metric': 'overall', 'experience': {'gained': 0}}},
                'bosses': {}, 'activities': {},
                'computed': {'ehp': {'value': {'gained': 0}}, 'ehb': {'value': {'gained': 0}}}
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_inactive_player_data):
            response = lambda_handler({}, None)
            self.assertEqual(response['statusCode'], 200)
            mock_execute_webhooks.assert_not_called()

class TestIsPlayerActive(unittest.TestCase):
    def setUp(self):
        self.active = load_fixture('active-player-gained-response.json')
        self.inactive = load_fixture('inactive-player-gained-response.json')

    def test_is_player_active(self):
        self.assertTrue(is_player_active(self.active))
        self.assertFalse(is_player_active(self.inactive))

class TestGetPlayerData(unittest.TestCase):
    def setUp(self):
        self.mock_active = load_fixture('active-player-gained-response.json')

    @patch('requests.get')
    def test_get_player_data_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_active
        self.assertEqual(get_player_data('MyRandomPlayer'), self.mock_active)

    @patch('requests.get')
    def test_get_player_data_api_error(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        result = get_player_data('nonexistentplayer')
        self.assertIn('error', result)

    @patch('requests.get')
    def test_get_player_data_empty_username(self, mock_get):
        self.assertEqual(get_player_data(''), {'error': 'Username is empty'})

class TestFilterGains(unittest.TestCase):
    def setUp(self):
        self.active = load_fixture('active-player-gained-response.json')
        self.inactive = load_fixture('inactive-player-gained-response.json')

    def test_filter_experience_gains(self):
        result = filter_experience_gains(self.active)
        self.assertTrue(all(skill['gained'] > 0 for skill in result))
        self.assertEqual(filter_experience_gains(self.inactive), [])

    def test_filter_boss_gains(self):
        result = filter_boss_gains(self.active)
        self.assertTrue(all(boss['gained'] > 0 for boss in result))
        self.assertEqual(filter_boss_gains(self.inactive), [])

    def test_filter_activity_gains(self):
        result = filter_activity_gains(self.active)
        self.assertTrue(all(activity['gained'] > 0 for activity in result))
        self.assertEqual(filter_activity_gains(self.inactive), [])

class TestGetEfficiencyData(unittest.TestCase):
    def setUp(self):
        self.active = load_fixture('active-player-gained-response.json')
        self.inactive = load_fixture('inactive-player-gained-response.json')

    def test_get_efficiency_data(self):
        result = get_efficiency_data(self.active)
        self.assertIn('ehp', result[0])
        self.assertIn('ehb', result[0])
        self.assertIn('gained', result[0])
        self.assertTrue(result[0]['ehp'] >= 0)
        self.assertTrue(result[0]['ehb'] >= 0)

    def test_get_efficiency_data_no_gains(self):
        result = get_efficiency_data(self.inactive)
        self.assertEqual(result[0]['ehp'], 0)
        self.assertEqual(result[0]['ehb'], 0)

class TestMergePlayerData(unittest.TestCase):
    def setUp(self):
        self.active = load_fixture('active-player-gained-response.json')

    def test_merge_player_data(self):
        username = "TestUser"
        player_data = merge_player_data(username, self.active)
        self.assertEqual(player_data['username'], username)
        self.assertIsInstance(player_data['experience_gains'], list)
        self.assertIsInstance(player_data['boss_gains'], list)
        self.assertIsInstance(player_data['activity_gains'], list)
        self.assertIsInstance(player_data['efficiency_data'], list)

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

    def test_sort_players(self):
        cases = [
            ('experience_gains', ["Bob", "Alice"]),
            ('boss_gains', ["Alice", "Bob"]),
            ('activity_gains', ["Bob", "Alice"]),
            ('efficiency_data', ["Bob", "Alice"]),
            ('ehp', ["Bob", "Alice"]),
            ('ehb', ["Bob", "Alice"])
        ]
        for sort_by, expected in cases:
            with self.subTest(sort_by=sort_by):
                sorted_players = sort_players_by(self.players, sort_by)
                self.assertEqual(list(sorted_players.keys()), expected)

class TestBuildRankingEmbed(unittest.TestCase):
    def setUp(self):
        self.players_data = {
            "PlayerA": {
                "experience_gains": [{"skill": "attack", "gained": 1234567}, {"skill": "strength", "gained": 7654321}],
                "boss_gains": [],
                "activity_gains": [],
                "efficiency_data": [{"ehp": 12.3, "ehb": 1.2, "gained": 13.5}]
            },
            "PlayerB": {
                "experience_gains": [{"skill": "defence", "gained": 1000000}],
                "boss_gains": [],
                "activity_gains": [],
                "efficiency_data": [{"ehp": 10.0, "ehb": 0.5, "gained": 10.5}]
            }
        }
        self.sorted_players_exp = sort_players_by(self.players_data, 'experience_gains')

    def test_build_ranking_embed_fields_content(self):
        embed = build_ranking_embed(self.sorted_players_exp, sort_by='experience_gains')
        self.assertIsInstance(embed, DiscordEmbed)
        self.assertEqual(len(embed.fields), 2)
        self.assertEqual(embed.fields[0]['name'], "#1 PlayerA")
        self.assertEqual(embed.fields[1]['name'], "#2 PlayerB")

class TestBuildPlayerEmbeds(unittest.TestCase):
    def setUp(self):
        self.player_data = {
            "PlayerC": {
                "experience_gains": [{"skill": "attack", "gained": 500000}, {"skill": "magic", "gained": 250000}],
                "boss_gains": [{"boss": "zulrah", "gained": 5}, {"boss": "vorkath", "gained": 10}],
                "activity_gains": [{"activity": "league_points", "gained": 1200}],
                "efficiency_data": [{"ehp": 5.5, "ehb": 2.1, "gained": 7.6}]
            }
        }

    def test_build_player_embeds_content(self):
        embeds = build_player_embeds(self.player_data)
        self.assertEqual(len(embeds), 1)
        embed = embeds[0]
        self.assertIsInstance(embed, DiscordEmbed)
        self.assertEqual(embed.title, "Day Gains for PlayerC")
        self.assertEqual(embed.author['name'], "PlayerC")
        self.assertEqual(embed.author['url'], "https://wiseoldman.net/players/PlayerC/gained?period=day")

if __name__ == "__main__":
    unittest.main()
