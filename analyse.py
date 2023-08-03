import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode
import json
from dataclasses import dataclass
from typing import List

# Load environment variables
load_dotenv()

class AudioData:
    def __init__(self, questionId, audioUrl, start):
        self.questionId = questionId
        self.audioUrl = audioUrl
        self.start = start
        self.audioBlob = requests.get(audioUrl).content

    def __str__(self):
        return f"AudioData(questionId={self.questionId}, audioUrl={self.audioUrl}, start={self.start})"

    def to_dict(self):
        return {
            "questionId": self.questionId,
            "audioUrl": self.audioUrl,
            "start": self.start
        }


class UserData:
    def __init__(self, userId, audio, fifUrl, fifStartTime):
        self.userId = userId
        self.audio = [AudioData(**a) for a in audio]
        self.fifUrl = fifUrl
        self.fifStartTime = fifStartTime
        self.fifFileBlob = requests.get(fifUrl).content

    def __str__(self):
        audio_str = ', '.join(str(a) for a in self.audio)
        return f"UserData(userId={self.userId}, audio=[{audio_str}], fifUrl={self.fifUrl}, fifStartTime={self.fifStartTime})"

    def to_dict(self):
        return {
            "userId": self.userId,
            "audio": [a.to_dict() for a in self.audio],
            "fifUrl": self.fifUrl,
            "fifStartTime": self.fifStartTime
        }


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


def save_files(user_data: UserData):
    # Save FIF file
    with open(f"{user_data.userId}.fif", "wb") as fif_file:
        fif_file.write(user_data.fifFileBlob)

    # Save audio files
    for audio_data in user_data.audio:
        with open(f"{user_data.userId}_{audio_data.questionId}.mp3", "wb") as audio_file:
            audio_file.write(audio_data.audioBlob)


def main():
    load_dotenv()
    token = get_access_token()
    user_data_list = get_user_data(token)

    # Save files for each user data
    for user_data in user_data_list:
        save_files(user_data)

    # user_data_dicts = [user_data.to_dict() for user_data in user_data_list]
    # pretty_json = json.dumps(user_data_dicts, indent=4)
    # print(pretty_json)
    print("Fetched all data from the API. Done")


def fetch_user_data():
    token = get_access_token()
    return get_user_data(token)


def fetch_first_user_fif_blob():
    user_data_list = fetch_user_data()
    first_user_data = user_data_list[0]
    return first_user_data.fifFileBlob


if __name__ == "__main__":
    main()
