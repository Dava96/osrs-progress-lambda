import json
import requests
import urllib.parse

def get_player_data(username):
    username = urllib.parse.unquote(username)

    if not username:
        return {"error": "Username is empty"}

    url = f"https://api.wiseoldman.net/v2/players/{username}/gained?period=day"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": response.status_code }

    return response.json()

def is_player_active(response):
    overall_gained = response['data']['skills']['overall']['experience']['gained']
    if overall_gained > 0:
        return True

    return False

def filter_experience_gains(response):
    skills = response['data']['skills']
    skill_gains = []

    for skill in skills.values():
        if skill['experience']['gained'] > 0:
            skill_gains.append({
                'skill': skill['metric'],
                'gained': skill['experience']['gained']
            })
    return skill_gains

def filter_boss_gains(response):
    bosses = response['data']['bosses']
    boss_gains = []

    for boss in bosses.values():
        if boss['kills']['gained'] > 0:
            boss_gains.append({
                'boss': boss['metric'],
                'gained': boss['kills']['gained']
            })
    return boss_gains

def filter_activity_gains(response):
    activities = response['data']['activities']
    activity_gains = []

    for activity in activities.values():
        if activity['score']['gained'] > 0:
            activity_gains.append({
                'activity': activity['metric'],
                'gained': activity['score']['gained']
            })
    return activity_gains

def get_efficiency_data(response):
    ehp = response['data']['computed']['ehp']['value']['gained']
    ehb = response['data']['computed']['ehb']['value']['gained']
    efficiency_data = []
    efficiency_data.append({
        'ehp': ehp,
        'ehb': ehb,
        'gained': ehp + ehb
    })
    return efficiency_data

def merge_player_data(username, response):
    player_data = {
        'username': username,
        'experience_gains': filter_experience_gains(response),
        'boss_gains': filter_boss_gains(response),
        'activity_gains': filter_activity_gains(response),
        'efficiency_data': get_efficiency_data(response)
    }

    return player_data

def sort_players_by(players, sort_by = 'experience_gains'):
    if len(players) == 1:
        return players

    sorted_players = dict(
            sorted(
                players.items(),
                key=lambda item: sum(skill['gained'] for skill in item[1][sort_by]),
                reverse=True
            )
        )
    return sorted_players

def lambda_handler(event, context):
    players = {}
    for username in []:
        response = get_player_data(username)
        if response.get('error'):
            print(f"Error fetching data for {username}: {response['error']}")
            continue
        if is_player_active(response):
            players[username] = merge_player_data(username, response)


    if len(players) == 0:
        print("No active players found.")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'No active players found.',
            })
        }

    print(sort_players_by(players, 'experience_gains'))
    # Return a response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from Lambda!',
        })
    }

if __name__ == "__main__":
    lambda_handler({}, None)
