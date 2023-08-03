import mne
import io
from analyse import fetch_first_user_fif_blob
import matplotlib.pyplot as plt
import numpy as np


def preprocess_raw_data(raw):
    # Drop unwanted channels
    raw.drop_channels(['Accel_x', 'Accel_y', 'Accel_z', 'Digital', 'Sample'])

    # Define a function to remove the mean (baseline)
    def remove_mean(x):
        return x - np.mean(x)

    # Apply the function to remove the mean
    raw.apply_function(remove_mean, picks='eeg')
    # Filter the data
    raw.filter(0.5, 30)
    return raw


# Fetch the FIF blob of the first user
fif_blob = fetch_first_user_fif_blob()

# Create a BytesIO object from the blob
fif_buffer = io.BytesIO(fif_blob)

# Read the FIF data from the buffer
raw = mne.io.read_raw_fif(fif_buffer, preload=True)

# Preprocess the raw data
raw = preprocess_raw_data(raw)

fig2 = raw.plot(scalings='auto', verbose=False)
plt.show()

# Extract the annotations
annotations = raw.annotations

# Find the Q and R annotations and their timestamps
q_r_pairs = []
for i, description in enumerate(annotations.description):
    if description.startswith('Q'):
        q_time = annotations.onset[i]
        r_description = 'R' + description[1:]
        r_times = annotations.onset[annotations.description == r_description]
        if len(r_times) > 0:
            r_time = r_times[0]
            q_r_pairs.append((q_time, r_time))
            print(f"Found a pair: {description} & {r_description}")

# Print the number of pairs found
print(
    f"Found {len(q_r_pairs)} pairs. Dividing the plot into {len(q_r_pairs)} parts and displaying each plot separately.")

# Plot the segments between Q and R annotations
for i, (q_time, r_time) in enumerate(q_r_pairs):
    print(f"Plotting segment {i}: {q_time} to {r_time}")
    # Crop the data to the desired segment
    raw_segment = raw.copy().crop(tmin=q_time, tmax=r_time)

    events, event_id = mne.events_from_annotations(raw_segment)
    fig = raw_segment.plot(scalings='auto', verbose=False, events=events, title=f"Segment {i}: {q_time} to {r_time}")

    # Plot the cropped segment
    # raw_segment.plot(title=f"Segment {i}: {q_time} to {r_time}")
    plt.show()  # Add this line
