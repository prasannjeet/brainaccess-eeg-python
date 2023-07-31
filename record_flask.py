from flask import Flask, request
import threading
import matplotlib.pyplot as plt
import matplotlib
from sys import platform
import time
import mne
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime
from flask_cors import CORS
import requests
from io import BytesIO
import numpy as np
import time

from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager

# Global variable to store JWT token
jwt_token = None

app = Flask(__name__)
CORS(app)  # Enable CORS globally

# Load environment variables
load_dotenv()

# Get environment variables
com_port = os.getenv('COM_PORT')

# Path to the credentials.json file
cred_path = 'credentials.json'

# Initialize Firebase Admin SDK with the credentials file
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

matplotlib.use("TKAgg", force=True)

# Move the eeg object to the global scope so it can be accessed by the Flask route
eeg = acquisition.EEG()
mgr = EEGManager()
channel_mapping = {
    0: "F4",
    1: "F8",
    2: "F7",
    3: "F3",
    4: "AF7",
    5: "AF8"
}

def upload_to_firebase(file_bytes, file_name, content_type):
    # Create a storage reference
    bucket = storage.bucket()
    blob = bucket.blob(file_name)

    # Upload the file from in-memory bytes
    blob.upload_from_file(file_bytes, content_type=content_type)

    # Make the blob publicly readable
    blob.make_public()

    # The public URL can be used to directly access the uploaded file via HTTP
    return blob.public_url + "?timestamp=" + str(time.time())

@app.route('/annotate', methods=['POST'])
def annotate():
    annotation = request.json.get('annotation')
    if annotation:
        eeg.annotate(annotation)
        return {'status': 'success'}, 200
    else:
        return {'status': 'failure', 'error': 'No annotation provided'}, 400

@app.route('/start', methods=['POST'])
def start():
    global user_id, start_timestamp, jwt_token  # Declare jwt_token as a global variable
    user_id = request.json.get('user_id')
    jwt_token = request.json.get('jwt_token')  # Get JWT token from the request
    if user_id:
        # Start acquiring data
        eeg.start_acquisition()
        start_timestamp = datetime.now()  # Save the current timestamp
        return {'status': 'success'}, 200
    else:
        return {'status': 'failure', 'error': 'No user id provided'}, 400

@app.route('/stop', methods=['POST'])
def stop():
    # get all eeg data and stop acquisition
    eeg.get_mne()
    eeg.stop_acquisition()
    mgr.disconnect()

    # Add the start timestamp as a custom annotation
    eeg.data.mne_raw.info['temp'] = {'start_timestamp': start_timestamp}

    # Save EEG data to MNE fif format
    file_name = f'{user_id}-raw.fif'
    eeg.data.mne_raw.save(file_name, overwrite=True)

    # Read the saved file into a BytesIO object
    with open(file_name, 'rb') as file:
        fif_bytes = BytesIO(file.read())

    # Upload the FIF file to Firebase and print the public URL
    fif_url = upload_to_firebase(fif_bytes, f'fif/{user_id}-raw.fif', 'application/octet-stream')
    print(f'FIF file uploaded to: {fif_url}')

    # Show recorded data and save plot to memory
    plot_bytes = show_recorded_data()
    plot_bytes.seek(0)

    # Upload the plot image to Firebase and print the public URL
    image_url = upload_to_firebase(plot_bytes, f'images/{user_id}-plot.png', 'image/png')
    print(f'Image uploaded to: {image_url}')

    # Send the URLs to the Spring server
    spring_url = os.getenv('SPRING_URL')
    headers = {'Authorization': f'Bearer {jwt_token}'}  # Include JWT token in the header
    response = requests.post(f'{spring_url}/users/{user_id}/fifUrl', json={"fifUrl": fif_url, "imageUrl": image_url}, headers=headers)
    if response.status_code != 200:
        print(f'Error sending URLs to Spring server: {response.text}')

    # Close brainaccess library
    eeg.close()

    # Optionally, delete the temporary FIF file
    os.remove(file_name)

    return {'status': 'success'}, 200

def show_recorded_data():
    # Pre-process the EEG data
    eeg.data.mne_raw.drop_channels(['Accel_x', 'Accel_y', 'Accel_z', 'Digital', 'Sample'])  # Remove unwanted channels
    # Define a function to remove the mean (baseline)

    def remove_mean(x):
        return x - np.mean(x)
    
    # Apply the function
    eeg.data.mne_raw.apply_function(remove_mean, picks='eeg')
    eeg.data.mne_raw.filter(0.5, 30)
    total_duration = eeg.data.mne_raw.times[-1]  # Get the total duration of the data
    events, event_id = mne.events_from_annotations(eeg.data.mne_raw)
    fig = eeg.data.mne_raw.plot(scalings='auto', verbose=False, events=events, show=False, duration=total_duration)
    fig.subplots_adjust(top=0.9)  # make room for title
    fig.suptitle(f'Participant: {user_id}', size='xx-large', weight='bold')

    # Get the axes from the figure
    axes = fig.get_axes()

    # Print all events and add vertical lines
    for event in events:
        for description, id in event_id.items():
            if id == event[2]:
                print(f'Timestamp: {event[0]}, Annotation: {description}')
                # Add a vertical line at the timestamp of the event
                # Note: event[0] is in samples, so we convert it to seconds by dividing by the sampling rate
                for ax in axes:
                    ax.axvline(event[0] / eeg.data.mne_raw.info['sfreq'], color='r', linestyle='--')
                    # Add a text label at the top of the plot
                    ax.text(event[0] / eeg.data.mne_raw.info['sfreq'], ax.get_ylim()[1], description, color='r')

    plot_bytes = BytesIO()
    plt.savefig(plot_bytes, format='png')
    plt.close(fig)  # Close the plot

    return plot_bytes

def start_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Set correct Bluetooth port for windows or linux
eeg.setup(mgr, port=com_port, cap=channel_mapping)

# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=start_flask_app)

flask_thread.start()

flask_thread.join()

