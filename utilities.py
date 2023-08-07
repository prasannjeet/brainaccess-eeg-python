import matplotlib.pyplot as plt
import numpy as np
import parselmouth


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


def print_channel_values_at_timestamp(raw, timestamp):
    # Convert the timestamp to a sample index
    sample_index = raw.time_as_index(timestamp)[0]

    # Get the data for all channels at the specified sample index
    data_at_timestamp = raw.get_data(start=sample_index, stop=sample_index + 1)

    # Print the values for each channel
    for i, ch_name in enumerate(raw.ch_names):
        if data_at_timestamp[i].size > 0:  # Check if the array is not empty
            print(f"Value for channel {ch_name}: {data_at_timestamp[i][0]} at timestamp {timestamp}")
        else:
            print(f"No data for channel {ch_name} at timestamp {timestamp}")


def print_channel_values_at_random_timestamps(raw_seg):
    # Determine the total number of samples in the segment
    total_samples = raw_seg.n_times

    # Get 5 random sample indices within the segment
    random_sample_indices = np.random.randint(0, total_samples, size=5)

    for sample_index in random_sample_indices:
        # Convert the sample index to a timestamp
        timestamp = raw_seg.times[sample_index]

        # Get the data for all channels at the specified sample index
        data_at_timestamp = raw_seg.get_data(start=sample_index, stop=sample_index + 1)

        # Print a header to indicate which timestamp's data is being printed
        print(f"Data at timestamp: {timestamp} seconds")

        # Print the values for each channel
        for i, ch_name in enumerate(raw_seg.ch_names):
            if data_at_timestamp[i].size > 0:  # Check if the array is not empty
                print(f"Value for channel {ch_name}: {data_at_timestamp[i][0]}")
            else:
                print(f"No data for channel {ch_name} at timestamp {timestamp}")

        # Print a newline for clarity
        print()


def get_segment_timestamps(raw):
    """Return the start and end timestamps of a raw segment."""
    start_timestamp = raw.times[0]
    end_timestamp = raw.times[-1]
    return start_timestamp, end_timestamp


def add_plot_title(title, fig):
    fig.subplots_adjust(top=0.9)  # make room for title
    fig.suptitle(title, size='xx-large', weight='bold')
    return fig


# Sound analysis #######################################################################################################
# Sound analysis #######################################################################################################
# Sound analysis #######################################################################################################
# Sound analysis #######################################################################################################

def trim_silence(sound, threshold=40, min_silence_duration=0.5):
    """
    Trim silence from the beginning and end of the sound.

    Parameters:
    - sound: a parselmouth.Sound object.
    - threshold: intensity threshold (in dB) below which sound is considered silent.
    - min_silence_duration: minimum duration (in seconds) of silence to be considered for trimming.

    Returns:
    - Trimmed parselmouth.Sound object.
    """

    intensity = sound.to_intensity(minimum_pitch=75.0)
    times = intensity.xs()
    intensities = intensity.values[0]

    # Find start time of sound
    start_time = None
    for time, intensity in zip(times, intensities):
        if intensity > threshold:
            start_time = time
            break

    # Find end time of sound
    end_time = None
    for time, intensity in reversed(list(zip(times, intensities))):
        if intensity > threshold:
            end_time = time
            break

    # If no start or end time found, return original sound
    if start_time is None or end_time is None:
        return sound

    trimmed_from_start = (start_time - sound.xmin) * 1000  # Convert seconds to milliseconds
    trimmed_from_end = (sound.xmax - end_time) * 1000  # Convert seconds to milliseconds

    print(f"Trimmed {trimmed_from_start:.2f} ms from the start and {trimmed_from_end:.2f} ms from the end.")

    # Extract part of the sound between start_time and end_time
    return sound.extract_part(start_time, end_time, preserve_times=False)


def calculate_jitter(sound):
    pitch = sound.to_pitch()
    pointProcess = parselmouth.praat.call(pitch, "To PointProcess")
    jitter = parselmouth.praat.call(pointProcess, "Get jitter (local)", 0.0, 0.0, 0.001, 0.03, 1.3)
    return jitter


def calculate_shimmer(sound):
    pointProcess_voiced = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
    shimmer = parselmouth.praat.call([sound, pointProcess_voiced], "Get shimmer (local)", 0.0, 0.0, 0.001, 0.03, 1.3,
                                     1.6)
    return shimmer


def calculate_hnr(sound):
    hnr = parselmouth.praat.call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
    hnr_value = parselmouth.praat.call(hnr, "Get mean", 0.0, 0.0)
    return hnr_value


def calculate_mean_pitch(sound):
    pitch = sound.to_pitch()
    return parselmouth.praat.call(pitch, "Get mean", 0.0, 0.0, "Hertz")


def calculate_stddev_pitch(sound):
    pitch = sound.to_pitch()
    return parselmouth.praat.call(pitch, "Get standard deviation", 0.0, 0.0, "Hertz")


def calculate_mean_intensity(sound):
    intensity = sound.to_intensity()
    return parselmouth.praat.call(intensity, "Get mean", 0.0, 0.0, "energy")


def calculate_stddev_intensity(sound):
    intensity = sound.to_intensity()
    return parselmouth.praat.call(intensity, "Get standard deviation", 0.0, 0.0)


def plot_acoustic_features(sound_list):
    # Lists to store feature values
    jitter_vals = []
    shimmer_vals = []
    hnr_vals = []
    mean_pitch_vals = []
    stddev_pitch_vals = []
    mean_intensity_vals = []
    stddev_intensity_vals = []

    for sound in sound_list:
        jitter_vals.append(calculate_jitter(sound))
        shimmer_vals.append(calculate_shimmer(sound))
        hnr_vals.append(calculate_hnr(sound))
        mean_pitch_vals.append(calculate_mean_pitch(sound))
        stddev_pitch_vals.append(calculate_stddev_pitch(sound))
        mean_intensity_vals.append(calculate_mean_intensity(sound))
        stddev_intensity_vals.append(calculate_stddev_intensity(sound))

    x = range(len(sound_list))

    plt.figure(figsize=(15, 10))

    # Plot features
    plt.subplot(3, 3, 1)
    plt.bar(x, jitter_vals)
    plt.title("Jitter")

    plt.subplot(3, 3, 2)
    plt.bar(x, shimmer_vals)
    plt.title("Shimmer")

    plt.subplot(3, 3, 3)
    plt.bar(x, hnr_vals)
    plt.title("HNR")

    plt.subplot(3, 3, 4)
    plt.bar(x, mean_pitch_vals)
    plt.title("Mean Pitch")

    plt.subplot(3, 3, 5)
    plt.bar(x, stddev_pitch_vals)
    plt.title("Std Dev Pitch")

    plt.subplot(3, 3, 6)
    plt.bar(x, mean_intensity_vals)
    plt.title("Mean Intensity")

    plt.subplot(3, 3, 7)
    plt.bar(x, stddev_intensity_vals)
    plt.title("Std Dev Intensity")

    plt.tight_layout()
    plt.show()

# Example usage:
# sound1 = parselmouth.Sound("path_to_audio1.mp3")
# sound2 = parselmouth.Sound("path_to_audio2.mp3")
# plot_acoustic_features([sound1, sound2])
