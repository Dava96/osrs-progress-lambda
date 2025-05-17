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
    if overall_gained == 0:
        return False

    return True

def lambda_handler(event, context):
    message = 'Hello from Lambda!'

    # Return a response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': message
        })
    }

if __name__ == "__main__":
    lambda_handler({}, None)
