import json
import os
import requests
import urllib.parse
from discord_webhook import DiscordWebhook, DiscordEmbed
from typing import List, Dict, Any, Optional, Tuple, Union

# --- Constants ---
WISE_OLD_MAN_API_BASE_URL = "https://api.wiseoldman.net/v2/players/"
DEFAULT_PERIOD = "day"
DEFAULT_SORT_BY = "experience_gains"
DEFAULT_SEND_RANKING_EMBED = "true"
DEFAULT_SEND_PLAYER_EMBED = "true"
REQUEST_TIMEOUT_SECONDS = 10
DEFAULT_SEND_UPDATE_REQUEST = "true"

# --- Helper Functions ---

def format_period_for_title(period: str) -> str:
    if period == "five_min":
        return "5 Minute"
    return period.replace('_', ' ').title()

def _extract_nested_value(data: Dict[str, Any], path: List[str], default: Any = 0) -> Any:
    temp = data
    for key in path:
        if not isinstance(temp, dict) or key not in temp:
            return default
        temp = temp[key]
    return temp

def _filter_gains(
    source: Optional[Dict[str, Any]],
    item_name_key: str,
    gained_path: List[str],
    result_item_name: str,
    exclude: Optional[set] = None
) -> List[Dict[str, Any]]:
    gains = []
    if not isinstance(source, dict):
        return gains
    exclude = exclude or set()
    for key, item in source.items():
        if key in exclude or not isinstance(item, dict):
            continue
        gained = _extract_nested_value(item, gained_path, 0)
        if isinstance(gained, (int, float)) and gained > 0:
            gains.append({
                result_item_name: item.get(item_name_key, "Unknown"),
                'gained': gained
            })
    return gains

# --- Data Fetching and Processing ---

def send_player_update(username: str):
    parsedUsername = urllib.parse.unquote(username)
    if not parsedUsername:
        return {"error": "Username is empty"}
    url = f"{WISE_OLD_MAN_API_BASE_URL}{parsedUsername}"
    try:
        response = requests.post(url, {})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}", "status_code": response.status_code}
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {REQUEST_TIMEOUT_SECONDS} seconds.", "status_code": 408}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request error occurred: {req_err}", "status_code": 500}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON response from API.", "status_code": 500}

def get_player_data(username: str, period: str = DEFAULT_PERIOD) -> Dict[str, Any]:
    username = urllib.parse.unquote(username)
    if not username:
        return {"error": "Username is empty"}
    url = f"{WISE_OLD_MAN_API_BASE_URL}{urllib.parse.quote(username)}/gained?period={period}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}", "status_code": response.status_code}
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {REQUEST_TIMEOUT_SECONDS} seconds.", "status_code": 408}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request error occurred: {req_err}", "status_code": 500}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON response from API.", "status_code": 500}

def is_player_active(response: Dict[str, Any]) -> bool:
    overall_gained = _extract_nested_value(response, ['data', 'skills', 'overall', 'experience', 'gained'], 0)
    return isinstance(overall_gained, (int, float)) and overall_gained > 0

def filter_experience_gains(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    skills = _extract_nested_value(response, ['data', 'skills'], {})
    return _filter_gains(skills, 'metric', ['experience', 'gained'], 'skill', exclude={'overall'})

def filter_boss_gains(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    bosses = _extract_nested_value(response, ['data', 'bosses'], {})
    return _filter_gains(bosses, 'metric', ['kills', 'gained'], 'boss')

def filter_activity_gains(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    activities = _extract_nested_value(response, ['data', 'activities'], {})
    return _filter_gains(activities, 'metric', ['score', 'gained'], 'activity')

def get_efficiency_data(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    ehp = _extract_nested_value(response, ['data', 'computed', 'ehp', 'value', 'gained'], 0.0)
    ehb = _extract_nested_value(response, ['data', 'computed', 'ehb', 'value', 'gained'], 0.0)
    return [{
        'ehp': ehp if isinstance(ehp, (int, float)) else 0.0,
        'ehb': ehb if isinstance(ehb, (int, float)) else 0.0,
        'gained': (ehp if isinstance(ehp, (int, float)) else 0.0) + (ehb if isinstance(ehb, (int, float)) else 0.0)
    }]

def merge_player_data(username: str, response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'username': username,
        'experience_gains': filter_experience_gains(response),
        'boss_gains': filter_boss_gains(response),
        'activity_gains': filter_activity_gains(response),
        'efficiency_data': get_efficiency_data(response)
    }

def sort_players_by(players: Dict[str, Any], sort_by: str = DEFAULT_SORT_BY) -> Dict[str, Any]:
    if not players or len(players) == 1:
        return players

    def get_sort_key(item: Tuple[str, Dict[str, Any]]) -> Union[int, float]:
        data = item[1]
        if sort_by in ['experience_gains', 'boss_gains', 'activity_gains']:
            return sum(detail.get('gained', 0) for detail in data.get(sort_by, []) if isinstance(detail, dict))
        elif sort_by == 'efficiency_data':
            eff = data.get('efficiency_data', [{}])
            return eff[0].get('gained', 0) if eff and isinstance(eff[0], dict) else 0
        elif sort_by == 'ehp':
            eff = data.get('efficiency_data', [{}])
            return eff[0].get('ehp', 0) if eff and isinstance(eff[0], dict) else 0
        elif sort_by == 'ehb':
            eff = data.get('efficiency_data', [{}])
            return eff[0].get('ehb', 0) if eff and isinstance(eff[0], dict) else 0
        else:
            return sum(detail.get('gained', 0) for detail in data.get(DEFAULT_SORT_BY, []) if isinstance(detail, dict))

    try:
        return dict(sorted(players.items(), key=get_sort_key, reverse=True))
    except Exception as e:
        print(f"Warning: Error during sorting by '{sort_by}': {e}")
        return players

def build_ranking_embed(players: Dict[str, Any], period: str = DEFAULT_PERIOD, sort_by: str = DEFAULT_SORT_BY) -> Optional[DiscordEmbed]:
    if not players:
        return None

    period_title = format_period_for_title(period)
    sort_by_title = sort_by.replace('_', ' ').title()
    embed = DiscordEmbed(
        title=f"{period_title} Group Ranking by {sort_by_title}",
        description=f"Here is the {period_title.lower()} activity ranking for the group.",
        color="03b2f8"
    )
    embed.set_author(name="Osrs Activity Bot")
    embed.set_footer(text="Player Rankings - Generated by Osrs Activity Bot")
    embed.set_timestamp()

    sort_configs = {
        'experience_gains': {
            'get_val': lambda exp, ehp, ehb: exp,
            'label': 'EXP',
            'other_metrics': [
                ('EHP', lambda exp, ehp, ehb: ehp),
                ('EHB', lambda exp, ehp, ehb: ehb)
            ]
        },
        'efficiency_data': {
            'get_val': lambda exp, ehp, ehb: ehp + ehb,
            'label': 'EHP+EHB',
            'other_metrics': [
                ('EXP', lambda exp, ehp, ehb: exp)
            ]
        },
        'ehp': {
            'get_val': lambda exp, ehp, ehb: ehp,
            'label': 'EHP',
            'other_metrics': [
                ('EXP', lambda exp, ehp, ehb: exp),
                ('EHB', lambda exp, ehp, ehb: ehb)
            ]
        },
        'ehb': {
            'get_val': lambda exp, ehp, ehb: ehb,
            'label': 'EHB',
            'other_metrics': [
                ('EXP', lambda exp, ehp, ehb: exp),
                ('EHP', lambda exp, ehp, ehb: ehp)
            ]
        }
    }
    config = sort_configs.get(sort_by, sort_configs['experience_gains'])

    for idx, (username, data) in enumerate(players.items(), 1):
        total_exp = sum(s.get('gained', 0) for s in data.get('experience_gains', []) if isinstance(s, dict))
        eff = data.get('efficiency_data', [{}])[0] if data.get('efficiency_data') else {}
        ehp = eff.get('ehp', 0)
        ehb = eff.get('ehb', 0)
        primary_metric_val = config['get_val'](total_exp, ehp, ehb)
        primary_metric_label = config['label']

        value_lines = [f"{primary_metric_label}: `{primary_metric_val:,}`"]
        for label, func in config['other_metrics']:
            metric_value = func(total_exp, ehp, ehb)
            value_lines.append(f"{label}: `{metric_value:,}`")

        field_value = "\n".join(value_lines)
        field_name = f"#{idx} {username}"

        embed.add_embed_field(name=field_name, value=field_value, inline=False)
    return embed

def build_player_embeds(players: Dict[str, Any], period: str = DEFAULT_PERIOD) -> List[DiscordEmbed]:
    player_embed_list = []
    period_title = format_period_for_title(period)
    for username, data in players.items():
        player_url = f"https://wiseoldman.net/players/{urllib.parse.quote(username)}/gained?period={period}"
        embed = DiscordEmbed(title=f"{period_title} Gains for {username}", color="03b2f8")
        embed.set_author(name=username, url=player_url)
        embed.set_footer(text=f"Details for {username} - Generated by Osrs Activity Bot")
        embed.set_timestamp()

        has_content = False

        for s in data.get('experience_gains', []):
            if s.get('gained', 0) > 0:
                embed.add_embed_field(name=s.get('skill', 'Unknown Skill').capitalize(), value=f"{s['gained']:,} xp", inline=False)
                has_content = True

        for b in data.get('boss_gains', []):
            if b.get('gained', 0) > 0:
                embed.add_embed_field(name=b.get('boss', 'Unknown Boss').replace('_', ' ').capitalize(), value=f"{b['gained']:,} kills", inline=False)
                has_content = True

        for a in data.get('activity_gains', []):
            if a.get('gained', 0) > 0:
                embed.add_embed_field(name=a.get('activity', 'Unknown Activity').replace('_', ' ').capitalize(), value=f"{a['gained']:,} score", inline=False)
                has_content = True

        eff = data.get('efficiency_data', [{}])[0] if data.get('efficiency_data') else {}
        ehp = eff.get('ehp', 0)
        ehb = eff.get('ehb', 0)
        if ehp > 0:
            embed.add_embed_field(name="EHP Gained", value=f"`{ehp:,}`", inline=False)
            has_content = True
        if ehb > 0:
            embed.add_embed_field(name="EHB Gained", value=f"`{ehb:,}`", inline=False)
            has_content = True

        if has_content:
            player_embed_list.append(embed)
    return player_embed_list

def execute_discord_webhooks(embeds_to_send: List[DiscordEmbed], webhook_url: str) -> None:
    current_embed_description = "N/A"
    try:
        for i, embed_content in enumerate(embeds_to_send):
            current_embed_description = embed_content.title if embed_content and hasattr(embed_content, 'title') else f"Embed #{i+1}"
            webhook = DiscordWebhook(url=webhook_url, username="Osrs Activity Bot")
            webhook.add_embed(embed_content)
            responses = webhook.execute()
            if responses:
                actual_responses = responses if isinstance(responses, list) else [responses]
                for response in actual_responses:
                    if hasattr(response, 'status_code') and response.status_code >= 400:
                        error_content = response.content.decode() if hasattr(response, 'content') else 'No content'
                        print(f"Discord webhook for embed '{current_embed_description}' returned error status {response.status_code}: {error_content}")
    except requests.exceptions.RequestException as e:
        print(f"Network error sending Discord embed '{current_embed_description}': {e}")
    except ValueError as e:
        print(f"Configuration error for Discord webhook (possibly for embed '{current_embed_description}'): {e}")
    except Exception as e:
        print(f"An unexpected error occurred sending Discord embed '{current_embed_description}': {e}")

def lambda_handler(event, context):
    usernames_to_fetch = [name.strip() for name in os.environ.get('USERNAMES', '').split(',') if name.strip()]
    webhook_url = os.environ.get('WEBHOOK_URL')
    send_ranking_embed = os.environ.get('SEND_RANKING_EMBED', DEFAULT_SEND_RANKING_EMBED).lower() == 'true'
    send_player_embed = os.environ.get('SEND_PLAYER_EMBED', DEFAULT_SEND_PLAYER_EMBED).lower() == 'true'
    period = os.environ.get('PERIOD', DEFAULT_PERIOD)
    sort_by = os.environ.get('SORT_BY', DEFAULT_SORT_BY)
    send_player_update_request = os.environ.get("SEND_PLAYER_UPDATE", DEFAULT_SEND_UPDATE_REQUEST).lower() == 'true'

    if not usernames_to_fetch or not webhook_url:
        print("USERNAMES and WEBHOOK_URL environment variables are required.")
        return {'statusCode': 400, 'body': json.dumps({'message': 'Missing configuration.'})}

    players = {}
    for username in usernames_to_fetch:
        if send_player_update_request:
            send_player_update(username)

        response = get_player_data(username, period)
        if response.get('error'):
            print(f"Error fetching data for {username}: {response['error']}")
            continue
        if is_player_active(response):
            players[username] = merge_player_data(username, response)

    if players:
        sorted_players = sort_players_by(players, sort_by)
        all_embeds_to_send = []

        ranking_embed = build_ranking_embed(sorted_players, period, sort_by)
        if ranking_embed and send_ranking_embed:
            all_embeds_to_send.append(ranking_embed)

        if send_player_embed:
            player_embeds = build_player_embeds(sorted_players, period)
            all_embeds_to_send.extend(player_embeds)

        if all_embeds_to_send:
            execute_discord_webhooks(all_embeds_to_send, webhook_url)

        print(f"Data processed for {len(sorted_players)} active players.")
    else:
        print("No active players found or data fetched.")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Data processed for {len(players)} players.",
        })
    }

if __name__ == "__main__":
    lambda_handler({}, None)
