import json
import requests
import urllib.parse

def get_playerData(username):
    username = urllib.parse.unquote(username)

    if not username:
        return {"error": "Username is empty"}

    url = f"https://api.wiseoldman.net/v2/players/{username}/gained?period=day"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": response.status_code }

    return response.json()

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
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
