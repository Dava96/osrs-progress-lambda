import unittest
import json
import os
from unittest.mock import patch
import requests
from lambda_function import lambda_handler, get_player_data, is_player_active, filter_experience_gains, filter_boss_gains, filter_activity_gains, get_efficiency_data, merge_player_data, sort_players_by, build_ranking_embed, build_player_embeds, execute_discord_webhooks
from discord_webhook import DiscordEmbed

class TestLambdaHandler(unittest.TestCase):
    @patch.dict(os.environ, {
        'WEBHOOK_URL': 'http://mockwebhookurl.com/test',
        'USERNAMES': 'PlayerOne,PlayerTwo',
        'SEND_RANKING_EMBED': 'true',
        'SEND_PLAYER_EMBED': 'true'
    })
    @patch('lambda_function.execute_discord_webhooks')
    def test_lambda_handler_success_with_players(self, mock_execute_webhooks):
        mock_player_data = {
            'data': {
                'skills': {
                    'overall': {'metric': 'overall', 'experience': {'gained': 1000}},
                    'attack': {'metric': 'attack', 'experience': {'gained': 500}},
                    'strength': {'metric': 'strength', 'experience': {'gained': 500}}
                },
                'bosses': {},
                'activities': {},
                'computed': {
                    'ehp': {'value': {'gained': 1.0}},
                    'ehb': {'value': {'gained': 0.5}}
                }
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data) as mock_get_player_data:
            event = {}
            context = None
            response = lambda_handler(event, context)
            self.assertEqual(response['statusCode'], 200)
            body = json.loads(response['body'])
            self.assertEqual(body['message'], 'Hello from Lambda!')
            self.assertEqual(mock_get_player_data.call_count, 2)
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
                'skills': {
                    'overall': {'metric': 'overall', 'experience': {'gained': 1000}},
                    'attack': {'metric': 'attack', 'experience': {'gained': 500}},
                    'strength': {'metric': 'strength', 'experience': {'gained': 500}}
                },
                'bosses': {},
                'activities': {},
                'computed': {
                    'ehp': {'value': {'gained': 1.0}},
                    'ehb': {'value': {'gained': 0.5}}
                }
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            event = {}
            context = None
            response = lambda_handler(event, context)
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
                'skills': {
                    'overall': {'metric': 'overall', 'experience': {'gained': 1000}},
                    'attack': {'metric': 'attack', 'experience': {'gained': 500}},
                    'strength': {'metric': 'strength', 'experience': {'gained': 500}}
                },
                'bosses': {},
                'activities': {},
                'computed': {
                    'ehp': {'value': {'gained': 1.0}},
                    'ehb': {'value': {'gained': 0.5}}
                }
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            event = {}
            context = None
            response = lambda_handler(event, context)
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
                'skills': {
                    'overall': {'metric': 'overall', 'experience': {'gained': 1000}},
                    'attack': {'metric': 'attack', 'experience': {'gained': 500}},
                    'strength': {'metric': 'strength', 'experience': {'gained': 500}}
                },
                'bosses': {},
                'activities': {},
                'computed': {
                    'ehp': {'value': {'gained': 1.0}},
                    'ehb': {'value': {'gained': 0.5}}
                }
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_player_data):
            event = {}
            context = None
            response = lambda_handler(event, context)
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
                'bosses': {},
                'activities': {},
                'computed': {'ehp': {'value': {'gained': 0}}, 'ehb': {'value': {'gained': 0}}}
            }
        }
        with patch('lambda_function.get_player_data', return_value=mock_inactive_player_data) as mock_get_player_data:
            event = {}
            context = None
            response = lambda_handler(event, context)
            self.assertEqual(response['statusCode'], 200)
            mock_execute_webhooks.assert_not_called()

    @patch.dict(os.environ, {'USERNAMES': 'UserForMissingWebhookTest'})
    @patch('lambda_function.get_player_data')
    @patch('lambda_function.is_player_active', return_value=False)
    @patch('builtins.print')
    def test_lambda_handler_missing_webhook_url(self, mock_print, mock_is_player_active, mock_get_player_data):
        mock_get_player_data.return_value = {
            'data': {'skills': {'overall': {'metric': 'overall', 'experience': {'gained': 0}}}}
        }
        event = {}
        context = None
        with self.assertRaises(KeyError) as context_manager:
            lambda_handler(event, context)
        self.assertEqual(str(context_manager.exception), "'WEBHOOK_URL'")

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
        # Check that efficiency_data contains 'ehp', 'ehb', and 'gained'
        eff = player_data['efficiency_data'][0]
        self.assertIn('ehp', eff)
        self.assertIn('ehb', eff)
        self.assertIn('gained', eff)

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

    def test_build_ranking_embed_structure(self):
        embed = build_ranking_embed(self.sorted_players_exp, sort_by='experience_gains')
        self.assertIsInstance(embed, DiscordEmbed)
        self.assertEqual(embed.title, "Daily Group Ranking by Experience Gains")
        self.assertEqual(embed.description, "Here is the daily activity ranking for the group.")
        self.assertEqual(embed.author['name'], "Osrs Activity Bot")
        self.assertEqual(embed.footer['text'], "Player Rankings - Generated by Osrs Activity Bot")
        self.assertIsNotNone(embed.timestamp)

    def test_build_ranking_embed_fields_content_exp_sort(self):
        embed = build_ranking_embed(self.sorted_players_exp, sort_by='experience_gains')
        self.assertEqual(len(embed.fields), 2)

        player_a_field = embed.fields[0]
        self.assertEqual(player_a_field['name'], "#1 PlayerA")
        expected_value_a = "EXP: `8,888,888`\nEHP: `12.3`\nEHB: `1.2`"
        self.assertEqual(player_a_field['value'], expected_value_a)
        self.assertFalse(player_a_field['inline'])

        player_b_field = embed.fields[1]
        self.assertEqual(player_b_field['name'], "#2 PlayerB")
        expected_value_b = "EXP: `1,000,000`\nEHP: `10.0`\nEHB: `0.5`"
        self.assertEqual(player_b_field['value'], expected_value_b)
        self.assertFalse(player_b_field['inline'])

    def test_build_ranking_embed_fields_content_ehp_sort(self):
        sorted_players_ehp = dict(sorted(self.players_data.items(), key=lambda item: item[1]['efficiency_data'][0]['ehp'], reverse=True))
        embed = build_ranking_embed(sorted_players_ehp, sort_by='ehp')
        self.assertEqual(len(embed.fields), 2)

        player_a_field = embed.fields[0]
        self.assertEqual(player_a_field['name'], "#1 PlayerA")
        expected_value_a = "EHP: `12.3`\nEXP: `8,888,888`\nEHB: `1.2`"
        self.assertEqual(player_a_field['value'], expected_value_a)

        player_b_field = embed.fields[1]
        self.assertEqual(player_b_field['name'], "#2 PlayerB")
        expected_value_b = "EHP: `10.0`\nEXP: `1,000,000`\nEHB: `0.5`"
        self.assertEqual(player_b_field['value'], expected_value_b)

    def test_build_ranking_embed_no_players(self):
        embed = build_ranking_embed({}, sort_by='experience_gains')
        self.assertEqual(len(embed.fields), 0)

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

    def test_build_player_embeds_structure_and_content(self):
        embeds = build_player_embeds(self.player_data)
        self.assertEqual(len(embeds), 1)
        embed = embeds[0]

        self.assertIsInstance(embed, DiscordEmbed)
        self.assertEqual(embed.title, "Daily Gains for PlayerC")
        self.assertEqual(embed.author['name'], "PlayerC")
        self.assertEqual(embed.author['url'], "https://wiseoldman.net/players/PlayerC/gained?period=day")
