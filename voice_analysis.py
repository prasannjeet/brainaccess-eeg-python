import parselmouth

from utilities import plot_acoustic_features, trim_silence

# Load the audio file
sound = parselmouth.Sound("7558f0eb-0970-4c8d-84db-85616feb82c3_1.mp3")

# Create a pitch object
pitch = sound.to_pitch()

# Extract the PointProcess
pointProcess = parselmouth.praat.call(pitch, "To PointProcess")

# Jitter
jitter = parselmouth.praat.call(pointProcess, "Get jitter (local)", 0.0, 0.0, 0.001, 0.03, 1.3)

print("Jitter:", jitter)

# Shimmer (on sound)
# Extract the PointProcess of voiced sound
pointProcess_voiced = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)

# Shimmer
shimmer = parselmouth.praat.call([sound, pointProcess_voiced], "Get shimmer (local)", 0.0, 0.0, 0.001, 0.03, 1.3, 1.6)
print("Shimmer:", shimmer)

# HNR
hnr = parselmouth.praat.call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
hnr_value = parselmouth.praat.call(hnr, "Get mean", 0.0, 0.0)

# f0 mean, variability, range
mean_pitch = parselmouth.praat.call(pitch, "Get mean", 0.0, 0.0, "Hertz")
stddev_pitch = parselmouth.praat.call(pitch, "Get standard deviation", 0.0, 0.0, "Hertz")
pitch_range = [parselmouth.praat.call(pitch, "Get minimum", 0.0, 0.0, "Hertz", "None"),
               parselmouth.praat.call(pitch, "Get maximum", 0.0, 0.0, "Hertz", "None")]

# Intensity Mean and Variability
intensity = sound.to_intensity()
mean_intensity = parselmouth.praat.call(intensity, "Get mean", 0.0, 0.0, "energy")
stddev_intensity = parselmouth.praat.call(intensity, "Get standard deviation", 0.0, 0.0)


print("HNR:", hnr_value)
print("Mean Pitch:", mean_pitch)
print("Std Dev Pitch:", stddev_pitch)
print("Pitch Range:", pitch_range)
print("Mean Intensity:", mean_intensity)
print("Std Dev Intensity:", stddev_intensity)


sound1 = parselmouth.Sound("7558f0eb-0970-4c8d-84db-85616feb82c3_1.mp3")
sound1 = trim_silence(sound1)
sound2 = parselmouth.Sound("7558f0eb-0970-4c8d-84db-85616feb82c3_2.mp3")
sound2 = trim_silence(sound2)
sound3 = parselmouth.Sound("7558f0eb-0970-4c8d-84db-85616feb82c3_3.mp3")
sound3 = trim_silence(sound3)
sound4 = parselmouth.Sound("7558f0eb-0970-4c8d-84db-85616feb82c3_4.mp3")
sound4 = trim_silence(sound4)

plot_acoustic_features([sound1, sound2, sound3, sound4])