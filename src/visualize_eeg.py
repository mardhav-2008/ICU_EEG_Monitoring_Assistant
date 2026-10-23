import matplotlib.pyplot as plt
import pandas as pd

# Load one EEG recording
file = "data/raw/train_eegs/1000913311.parquet"
eeg = pd.read_parquet(file)

# Sampling frequency
sampling_rate = 200

# Time axis
time = eeg.index / sampling_rate

# Plot EEG channels
plt.figure(figsize=(15, 10))

channels = eeg.columns.drop("EKG")

for i, channel in enumerate(channels):
    plt.plot(time, eeg[channel] + i * 200, label=channel)

plt.xlabel("Time (seconds)")
plt.ylabel("EEG Channels")
plt.title("HMS EEG Recording")
plt.xlim(0, 50)

plt.tight_layout()
plt.show()
