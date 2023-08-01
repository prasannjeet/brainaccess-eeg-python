import mne
import matplotlib.pyplot as plt
import numpy as np

# Load the data
file_path = 'C:\\Users\\Prasannjeet\\Documents\\Project\\test-6.fif'
raw = mne.io.read_raw_fif(file_path, preload=True)

raw.drop_channels(['Accel_x', 'Accel_y', 'Accel_z', 'Digital', 'Sample'])

# Define a function to remove the mean (baseline)
def remove_mean(x):
    return x - np.mean(x)

# Apply the function
raw.apply_function(remove_mean, picks='eeg')

# Filter the data
raw.filter(0.5, 30)

# Get the participant's name
participant_name = None
if raw.info['subject_info'] is not None:
    participant_name = raw.info['subject_info'].get('user_id', 'Unknown')

# start_timestamp = raw.info['temp']['start_timestamp']
# if start_timestamp:
#     print(f"Start Timestamp: {start_timestamp}")
# else:
#     print("Start Timestamp not found in the EEG data file.")

# Get the events from annotations
events, event_id = mne.events_from_annotations(raw)

# Get the start timestamp
start_timestamp = raw.info.get('start_timestamp')

# Print the start timestamp
if start_timestamp:
    print(f'Start Timestamp: {start_timestamp}')
else:
    print('Start timestamp not found in the file.')

# Plot the data
fig = raw.plot(scalings='auto', verbose=False, events=events)
fig.subplots_adjust(top=0.9)  # make room for title
fig.suptitle(f'Participant: {participant_name}', size='xx-large', weight='bold')

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
                ax.axvline(event[0] / raw.info['sfreq'], color='r', linestyle='--')

plt.show()
