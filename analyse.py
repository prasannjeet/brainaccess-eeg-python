import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode


class AudioData:
    def __init__(self, questionId, audioUrl, start):
        self.questionId = questionId
        self.audioUrl = audioUrl
        self.start = start
        self.audioBlob = requests.get(audioUrl).content


class UserData:
    def __init__(self, userId, audio, fifUrl, fifStartTime):
        self.userId = userId
        self.audio = [AudioData(**a) for a in audio]
        self.fifUrl = fifUrl
        self.fifStartTime = fifStartTime
        self.fifFileBlob = requests.get(fifUrl).content


def get_access_token():
    token_url = f"{os.getenv('KEYCLOAK_URL')}/realms/{os.getenv('REALM')}/protocol/openid-connect/token"
    data = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'grant_type': 'client_credentials'
    }
    response = requests.post(token_url, headers={'Content-Type': 'application/x-www-form-urlencoded'},
                             data=urlencode(data))
    return response.json().get('access_token')


def get_user_data(token):
    url = f"{os.getenv('SPRING_URL')}/api/users/analysisData"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    return [UserData(**user_data) for user_data in response.json()]


def main():
    load_dotenv()
    token = get_access_token()
    user_data_list = get_user_data(token)
    print("Done")


if __name__ == "__main__":
    main()
