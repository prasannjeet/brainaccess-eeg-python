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

from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager

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

app = Flask(__name__)

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

def upload_to_firebase(file_path):
    # Use the user_id as the filename in Firebase Storage
    firebase_file_name = f'{user_id}-raw.fif'

    # Create a storage reference
    bucket = storage.bucket()
    blob = bucket.blob(firebase_file_name)

    # Upload the file
    blob.upload_from_filename(file_path)

    # The public URL can be used to directly access the uploaded file via HTTP
    return blob.public_url

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
    global user_id, start_timestamp  # Declare start_timestamp as a global variable
    user_id = request.json.get('user_id')
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
    eeg.data.mne_raw.info['start_timestamp'] = start_timestamp

    # save EEG data to MNE fif format
    file_name = f'{time.strftime("%Y%m%d_%H%M")}-raw.fif'
    eeg.data.save(file_name)

    # Upload the file to Firebase and print the public URL
    public_url = upload_to_firebase(file_name)
    print(f'File uploaded to: {public_url}')

    # Close brainaccess library
    eeg.close()
    # Show recorded data
    show_recorded_data()
    return {'status': 'success'}, 200

def show_recorded_data():
    eeg.data.mne_raw.filter(0.5, 30)
    events, event_id = mne.events_from_annotations(eeg.data.mne_raw)
    fig = eeg.data.mne_raw.plot(scalings='auto', verbose=False, events=events, show=False)
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

    file_path = f'{time.strftime("%Y%m%d_%H%M")}-plot.png'
    plt.savefig(file_path)
    plt.close(fig)  # Close the plot

def start_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Set correct Bluetooth port for windows or linux
eeg.setup(mgr, port=com_port, cap=channel_mapping)

# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=start_flask_app)

flask_thread.start()

flask_thread.join()

