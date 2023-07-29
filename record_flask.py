from flask import Flask, request
import threading
import matplotlib.pyplot as plt
import matplotlib
from sys import platform
import time
import mne
import os
from dotenv import load_dotenv
from google.cloud import storage

from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager

# Load environment variables
load_dotenv()

# Get environment variables
com_port = os.getenv('COM_PORT')

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
    # Your Firebase project ID
    project_id = os.getenv('FIREBASE_PROJECT_ID')

    # Create a storage client
    storage_client = storage.Client(project_id)

    # The "bucket" in Firebase Storage is named the same as your Firebase project ID
    bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
    bucket = storage_client.get_bucket(bucket_name)

    # Name of the file in Firebase Storage (can be the same as the local file name)
    firebase_file_name = file_path.split('/')[-1]

    # Create a new blob and upload the file's content
    blob = bucket.blob(firebase_file_name)
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
    global user_id  # Declare user_id as a global variable so it can be accessed in the stop endpoint
    user_id = request.json.get('user_id')
    if user_id:
        # Start acquiring data
        eeg.start_acquisition()
        return {'status': 'success'}, 200
    else:
        return {'status': 'failure', 'error': 'No user id provided'}, 400

@app.route('/stop', methods=['POST'])
def stop():
    # get all eeg data and stop acquisition
    eeg.get_mne()
    eeg.stop_acquisition()
    mgr.disconnect()

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
    fig = eeg.data.mne_raw.plot(scalings='auto', verbose=False, events=events)
    fig.subplots_adjust(top=0.9)  # make room for title
    fig.suptitle(f'Participant: {user_id}', size='xx-large', weight='bold')
    plt.savefig(f'{time.strftime("%Y%m%d_%H%M")}-plot.png')

def start_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Set correct Bluetooth port for windows or linux
eeg.setup(mgr, port=com_port, cap=channel_mapping)

# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=start_flask_app)

flask_thread.start()

flask_thread.join()

