from flask import Flask, request
import threading
import matplotlib.pyplot as plt
import matplotlib
from sys import platform
import time
import mne

from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager

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
        # Set correct Bluetooth port for windows or linux
        if platform == "linux" or platform == "linux2":
            eeg.setup(mgr, port='/dev/rfcomm0', cap=channel_mapping)
        else:
            eeg.setup(mgr, port='COM3', cap=channel_mapping)
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

    # Save user id in the MNE dataset
    eeg.data.mne_raw.info['subject_info'] = {'user_id': user_id}

    # save EEG data to MNE fif format
    eeg.data.save(f'{time.strftime("%Y%m%d_%H%M")}-raw.fif')
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

    plt.savefig(f'{time.strftime("%Y%m%d_%H%M")}-plot.png')


def start_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=start_flask_app)

flask_thread.start()

flask_thread.join()
