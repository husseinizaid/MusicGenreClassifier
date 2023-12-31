# -*- coding: utf-8 -*-
"""Music Genre Classifier Final Model

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1at2ywncHrrDgtp214hyAEU_NZo2AjFG1

I used the data from this data set: https://www.kaggle.com/datasets/andradaolteanu/gtzan-dataset-music-genre-classification/

you may need to download the Data folder and upload it to your drive

# Import all needed libs
"""



import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np
import joblib



"""# Code for getting the data and preprocessing

The code below was run locally on vscode and the subsequent folders were uploaded to google drive.
"""

import os
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import spectrogram
from pydub import AudioSegment
import pandas as pd
import librosa

base_path = 'C:/Users/samir/Desktop/APS360_Project'
testing_folder = os.path.join(base_path, 'SAMPLES') # Original Songs (No Trimming)
trimmed_folder = os.path.join(base_path, 'TRIMMED_SAMPLES') # 30 Second Trimming of Samples
threesecondtrimming_folder = os.path.join(base_path, 'TRIMMED_3SEC_SAMPLES') # 3 Second Trimming of Samples
spectrogram_folder = os.path.join(base_path, 'SPECTOGRAM_SAMPLES') # Spectrograms Generated from 30 Second Trimmings
genres = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']

# If directories (folders+genre folders) do not exist - create it
for genre in genres:
    os.makedirs(os.path.join(testing_folder, genre), exist_ok=True)
    os.makedirs(os.path.join(trimmed_folder, genre), exist_ok=True)
    os.makedirs(os.path.join(threesecondtrimming_folder, genre), exist_ok=True)  # 3 Second Trimming
    os.makedirs(os.path.join(spectrogram_folder, genre), exist_ok=True)

# Loop through each genre
for genre in genres:
    genre_test_folder = os.path.join(testing_folder, genre)
    genre_trimmed_folder = os.path.join(trimmed_folder, genre)
    genre_trimmed_3sec_folder = os.path.join(threesecondtrimming_folder, genre)  # 3-second trimmed folder
    genre_spectrogram_folder = os.path.join(spectrogram_folder, genre)

    # Loop through each song in the respective genre
    for song_file in os.listdir(genre_test_folder):
        song_path = os.path.join(genre_test_folder, song_file)

        song = AudioSegment.from_file(song_path) #loading song

        # Determine if padding is needed for 30 seconds clip
        pad_duration = 30 * 1000 - len(song)  # 30 seconds in milliseconds
        if pad_duration > 0:
            silence = AudioSegment.silent(duration=pad_duration)
            song_30sec = song + silence

        else:
            start_time = random.randint(0, len(song) - 30000)
            song_30sec = song[start_time:start_time + 30000]

        #File name for 30 second trim
        trimmed_song_name = f'trimmed_{os.path.splitext(song_file)[0]}.wav'
        trimmed_song_path = os.path.join(genre_trimmed_folder, trimmed_song_name)


        song_30sec.export(trimmed_song_path, format='wav')

        #Determining if padding is needed
        three_sec_duration = 3 * 1000  # 3 seconds in milliseconds
        if len(song) < three_sec_duration:
            pad_duration = three_sec_duration - len(song)
            silence = AudioSegment.silent(duration=pad_duration)
            song_3sec = song + silence

        else:
            start_time = random.randint(0, len(song) - three_sec_duration)
            song_3sec = song[start_time:start_time + three_sec_duration]

        #File name for 3 second trim
        trimmed_3sec_song_name = f'trimmed_3sec_{os.path.splitext(song_file)[0]}.wav'
        trimmed_3sec_song_path = os.path.join(genre_trimmed_3sec_folder, trimmed_3sec_song_name)

        song_3sec.export(trimmed_3sec_song_path, format='wav')
        sample_rate, audio_data = wavfile.read(trimmed_song_path)


        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        #Error check
        if len(audio_data) < 256:
            print(f"Audio data too short for spectrogram: {trimmed_song_name}")
            continue

        frequencies, times, Sxx = spectrogram(audio_data, fs=sample_rate)
        Sxx[Sxx <= 0] = 1e-10

        # Generate spectrogram using matplotlib
        plt.figure(figsize=(10, 4))
        plt.pcolormesh(times, frequencies, 10 * np.log10(Sxx), shading='gouraud')
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.colorbar(label='Intensity [dB]')
        plt.title(f'Spectrogram of {trimmed_song_name}')
        plt.tight_layout()
        spectrogram_filename = os.path.splitext(trimmed_song_name)[0] + '.png'
        plt.savefig(os.path.join(genre_spectrogram_folder, spectrogram_filename))
        plt.close()

# Prepare DataFrame to store features
columns = ['filename', 'length', 'chroma_stft_mean', 'chroma_stft_var', 'rms_mean', 'rms_var',
           'spectral_centroid_mean', 'spectral_centroid_var', 'spectral_bandwidth_mean',
           'spectral_bandwidth_var', 'rolloff_mean', 'rolloff_var', 'zero_crossing_rate_mean',
           'zero_crossing_rate_var', 'harmony_mean', 'harmony_var', 'perceptr_mean', 'perceptr_var',
           'tempo', 'mfcc1_mean', 'mfcc1_var', 'mfcc2_mean', 'mfcc2_var', 'mfcc3_mean', 'mfcc3_var',
           'mfcc4_mean', 'mfcc4_var', 'mfcc5_mean', 'mfcc5_var', 'mfcc6_mean', 'mfcc6_var',
           'mfcc7_mean', 'mfcc7_var', 'mfcc8_mean', 'mfcc8_var', 'mfcc9_mean', 'mfcc9_var',
           'mfcc10_mean', 'mfcc10_var', 'mfcc11_mean', 'mfcc11_var', 'mfcc12_mean', 'mfcc12_var',
           'mfcc13_mean', 'mfcc13_var', 'mfcc14_mean', 'mfcc14_var', 'mfcc15_mean', 'mfcc15_var',
           'mfcc16_mean', 'mfcc16_var', 'mfcc17_mean', 'mfcc17_var', 'mfcc18_mean', 'mfcc18_var',
           'mfcc19_mean', 'mfcc19_var', 'mfcc20_mean', 'mfcc20_var', 'label']

df1 = pd.DataFrame(columns=columns) #30 second csv
df2 = pd.DataFrame(columns=columns) #3 second csv

# Process each file for feature extraction - 30 second trimmings
for genre in genres:
    genre_folder = os.path.join(trimmed_folder, genre)
    for file in os.listdir(genre_folder):
        file_path = os.path.join(genre_folder, file)
        y, sr = librosa.load(file_path, sr=None, mono=True, duration=30)

        # Extract features
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        harmony = librosa.effects.harmonic(y)
        perceptr = librosa.effects.percussive(y)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)

        # Compute the mean and variance of each feature
        features = {
            'filename': file,
            'length': len(y),
            'chroma_stft_mean': np.mean(chroma_stft),
            'chroma_stft_var': np.var(chroma_stft),
            'rms_mean': np.mean(rms),
            'rms_var': np.var(rms),
            'spectral_centroid_mean': np.mean(spectral_centroid),
            'spectral_centroid_var': np.var(spectral_centroid),
            'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
            'spectral_bandwidth_var': np.var(spectral_bandwidth),
            'rolloff_mean': np.mean(rolloff),
            'rolloff_var': np.var(rolloff),
            'zero_crossing_rate_mean': np.mean(zero_crossing_rate),
            'zero_crossing_rate_var': np.var(zero_crossing_rate),
            'harmony_mean': np.mean(harmony),
            'harmony_var': np.var(harmony),
            'perceptr_mean': np.mean(perceptr),
            'perceptr_var': np.var(perceptr),
            'tempo': tempo,
            'label': genre
        }


        for i, mfcc in enumerate(mfccs, start=1):
            features[f'mfcc{i}_mean'] = np.mean(mfcc)
            features[f'mfcc{i}_var'] = np.var(mfcc)

       #CHECK FOR CALCULATIONS
#        print(f"Features for {file} in genre {genre}:")
#        for feature_name, feature_value in features.items():
#            print(f"{feature_name}: {feature_value}")
#        print("\n")

        # Append features of this file to the DataFrame
        df1 = pd.concat([df1, pd.DataFrame([features])], ignore_index=True)


csv_path = os.path.join(base_path, 'audio_features_30_sec.csv')
df1.to_csv(csv_path, index=False)


# Process each file for feature extraction - 3 second trimmings
for genre in genres:
    genre_folder = os.path.join(threesecondtrimming_folder, genre)
    for file in os.listdir(genre_folder):
        file_path = os.path.join(genre_folder, file)
        y, sr = librosa.load(file_path, sr=None, mono=True, duration=3)
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        harmony = librosa.effects.harmonic(y)
        perceptr = librosa.effects.percussive(y)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)


        features = {
            'filename': file,
            'length': len(y),
            'chroma_stft_mean': np.mean(chroma_stft),
            'chroma_stft_var': np.var(chroma_stft),
            'rms_mean': np.mean(rms),
            'rms_var': np.var(rms),
            'spectral_centroid_mean': np.mean(spectral_centroid),
            'spectral_centroid_var': np.var(spectral_centroid),
            'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
            'spectral_bandwidth_var': np.var(spectral_bandwidth),
            'rolloff_mean': np.mean(rolloff),
            'rolloff_var': np.var(rolloff),
            'zero_crossing_rate_mean': np.mean(zero_crossing_rate),
            'zero_crossing_rate_var': np.var(zero_crossing_rate),
            'harmony_mean': np.mean(harmony),
            'harmony_var': np.var(harmony),
            'perceptr_mean': np.mean(perceptr),
            'perceptr_var': np.var(perceptr),
            'tempo': tempo,
            'label': genre
        }

        # Add MFCCs features
        for i, mfcc in enumerate(mfccs, start=1):
            features[f'mfcc{i}_mean'] = np.mean(mfcc)
            features[f'mfcc{i}_var'] = np.var(mfcc)

        # cHECK FOR CALCULATIONS
#        print(f"Features for {file} in genre {genre}:")
#        for feature_name, feature_value in features.items():
#            print(f"{feature_name}: {feature_value}")
#        print("\n")  # Adds a new line for readability between files

        # Append features of this file to the DataFrame
        df2 = pd.concat([df2, pd.DataFrame([features])], ignore_index=True)

# Save DataFrame to CSV
csv_path = os.path.join(base_path, 'audio_features_3_sec.csv')
df2.to_csv(csv_path, index=False)

"""# Code For the Model and Training

"""

from google.colab import drive
drive.mount('/content/gdrive')



!ls -l /content/gdrive/MyDrive/APS360-music_classifier/Data/features_30_sec.csv

file_path = '/content/gdrive/MyDrive/APS360-music_classifier/3secondcook.csv'  # Update with the correct path
df = pd.read_csv(file_path)

# Separate features and labels
df = df.drop(columns=['filename'])
ls = df.iloc[:, -1]  # Selects the last column of the DataFrame
convertor = LabelEncoder()
y=convertor.fit_transform(ls)
fit = StandardScaler()
X = fit.fit_transform(np.array(df.iloc[:, :-1], dtype=float))  # Scaling all columns except the last one

# Save the StandardScaler instance to a file
scaler_file = '/content/gdrive/MyDrive/APS360-music_classifier/scalerSA.save'
joblib.dump(fit, scaler_file)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)  # 33% data as test set

class MusicGenreClassifier(nn.Module):
    def __init__(self):
        super(MusicGenreClassifier, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(in_features=X_train.shape[1], out_features=512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(in_features=512, out_features=256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(in_features=256, out_features=128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(in_features=128, out_features=64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(in_features=64, out_features=10)
            # Removed the nn.Softmax layer
        )

    def forward(self, x):
        return self.network(x)

# Initialize the model
model = MusicGenreClassifier()

# Define the loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

from matplotlib.patches import Patch
def calculate_accuracy(model, data_loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, targets in data_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            correct += (predicted == targets).sum().item()
    return 100 * correct / total
def train_model(model, train_loader, val_loader, criterion, optimizer, epochs):
    print("Start training...")
    train_losses = []
    val_accuracies = []

    for epoch in range(epochs):
        # Training phase
        model.train()
        running_loss = 0.0
        train_correct = 0
        train_total = 0
        for inputs, targets in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += targets.size(0)
            train_correct += (predicted == targets).sum().item()

        # Calculate training loss and accuracy for the epoch
        train_loss = running_loss / len(train_loader)
        train_accuracy = 100 * train_correct / train_total
        print(f'Epoch {epoch+1}/{epochs} - Training Loss: {train_loss:.4f}, Training Accuracy: {train_accuracy:.2f}%', end='')

        # Append training loss for plotting
        train_losses.append(train_loss)

        # Calculate validation accuracy
        val_accuracy = calculate_accuracy(model, val_loader)
        print(f', Validation Accuracy: {val_accuracy:.2f}%')

        # Append validation accuracy for plotting
        val_accuracies.append(val_accuracy)
        plot_training_graph(train_losses, val_accuracies, epoch+1)
    return train_losses, val_accuracies

# Function to plot training graph
def plot_training_graph(train_losses, val_accuracies, epochs):
    plt.figure(figsize=(10, 5))

    # Plot training loss
    plt.plot(range(epochs), train_losses, label='Training Loss', color='blue')

    # Since accuracy is on a different scale, we'll create a secondary y-axis for it
    # Create a second y-axis for the validation accuracy
    ax2 = plt.twinx()
    ax2.plot(range(epochs), val_accuracies, label='Validation Accuracy', color='green')

    # Set the labels and titles
    plt.xlabel('Epochs')
    plt.ylabel('Loss', color='blue')
    ax2.set_ylabel('Accuracy (%)', color='green')
    plt.title('Training Loss and Validation Accuracy')

    # Set the legends
    blue_patch = Patch(color='blue', label='Training Loss')
    green_patch = Patch(color='green', label='Validation Accuracy')
    plt.legend(handles=[blue_patch, green_patch], loc='upper left')

    plt.show()

train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
val_dataset = TensorDataset(torch.FloatTensor(X_test), torch.LongTensor(y_test))

# DataLoader instances remain the same
train_loader = DataLoader(dataset=train_dataset, batch_size=128, shuffle=True)
val_loader = DataLoader(dataset=val_dataset, batch_size=128, shuffle=False)

# Now proceed to train the model and plot the results
train_losses, val_accuracies = train_model(model, train_loader, val_loader, criterion, optimizer, epochs=100)

import os
cwd = os.getcwd()
print("Current working directory:", cwd)

model_save_path = '/content/gdrive/MyDrive/APS360-music_classifier/modelCSVNEW.pth'
torch.save(model, model_save_path)

def index_to_genre(index):
  arr = ['Blues','Classical','Country','Disco','Hip-hop','Jazz','Metal','Pop','Reggae','Rock']
  return arr[index]

# Load the CSV file for the new song
file_path = '/content/gdrive/MyDrive/APS360-music_classifier/.csv'
df = pd.read_csv(file_path)

# Select the first row and drop non-feature columns
first_row = df.iloc[600:601]
print(first_row)
first_row=first_row.drop(columns=['filename', 'label'])  # Row index starts from 0

# Assuming 'fit' is the StandardScaler instance you used to scale your training data
fit = joblib.load('/content/gdrive/MyDrive/APS360-music_classifier/scalerS.save')

# Use 'transform' instead of 'fit_transform'
X_scaled = fit.transform(first_row)

# Convert to a PyTorch tensor
tensor_row = torch.FloatTensor(X_scaled).unsqueeze(0)

# Load your model and set it to evaluation mode
model = torch.load('/content/gdrive/MyDrive/APS360-music_classifier/modelCSVNEW.pth')
model.eval()  # Set it to evaluation mode

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Move the model to the specified device
model = model.to(device)

# Ensure that your input tensor is also on the same device
tensor_row = tensor_row.to(device)

# Make a prediction
with torch.no_grad():
    output = model(tensor_row)
print("Raw model output:", output)
predicted_index = torch.argmax(output, dim=2)
predicted_index = predicted_index.squeeze().item()
predicted_genre = index_to_genre(predicted_index)
print("Predicted Genre:", predicted_genre)

!pip show joblib