# -*- coding: utf-8 -*-
"""ProiectSACCDMM_Color.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WfDxp7agMVGpG_yCA4ZDLEDbjUCcrSFn

Importare biblioteci necesare
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
import math
import random
import shutil

from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from keras import Sequential
from keras.layers import Dense, Conv2D, MaxPooling2D, UpSampling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import tensorflow_datasets as tfds

# from tensorflow.keras.models import Model

"""Importare baza de date cu imagini"""

# NU - E IN CELULA URMATOARE!!!!!!!!!!!!!

_URL = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"

zip_file = tf.keras.utils.get_file(origin=_URL,
                                   fname="flower_photos.tgz",
                                   extract=True)

base_dir = os.path.join(os.path.dirname(zip_file), 'flower_photos')

# Download the flower image dataset (if not already downloaded)
_URL = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
zip_file = tf.keras.utils.get_file(origin=_URL, fname="flower_photos.tgz", extract=True)


# Extract the downloaded file (if necessary)
base_dir = os.path.join(os.path.dirname(zip_file), 'flower_photos')
if not os.path.exists(base_dir):
    os.makedirs(base_dir)  # Create the base directory if it doesn't exist

# Create the train and test directories (if they don't exist)
train_dir = os.path.join(base_dir, 'train')
test_dir = os.path.join(base_dir, 'test')
if not os.path.exists(train_dir):
    os.makedirs(train_dir)
if not os.path.exists(test_dir):
    os.makedirs(test_dir)

train_datagen = ImageDataGenerator(rescale=1./255) # normalizare
test_datagen = ImageDataGenerator(rescale=1./255)

x_train = train_datagen.flow_from_directory(
    train_dir,
    target_size=(150, 150),
    batch_size=32,
    class_mode='categorical'
)

x_test = test_datagen.flow_from_directory(
    test_dir,
    target_size=(150, 150),
    batch_size=32,
    class_mode='categorical'
)

"""Adaugare zgomot asupra imaginilor"""

# Get a batch of images from the iterator
x_batch, y_batch = next(x_train)

# Add noise to the batch
x_batch_noisy = np.clip(x_batch + np.random.normal(0, 25, x_batch.shape), 0, 255)

from tensorflow.keras.preprocessing.image import ImageDataGenerator

class SaltAndPepperNoiseGenerator(ImageDataGenerator):
    def __init__(self, noise_prob=0.5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.noise_prob = noise_prob

    def random_transform(self, x, seed=None):
        x = super().random_transform(x, seed)
        # Adăugăm zgomot de sare și piper
        s_vs_p = 0.5  # Probabilitate de a fi sare sau piper
        salt = np.random.randint(0, 256, x.shape)
        pepper = 255 - salt
        mask = np.random.rand(x.shape[0], x.shape[1], x.shape[2]) < self.noise_prob
        x[mask] = np.where(mask, salt[mask], pepper[mask])
        return x

# Creează generatoare de date cu zgomot de sare și piper
noisy_train_datagen = SaltAndPepperNoiseGenerator(rescale=1./255, noise_prob=0.5)
noisy_test_datagen = SaltAndPepperNoiseGenerator(rescale=1./255, noise_prob=0.5)

# Creează generatoare de date cu zgomot de sare și piper pentru antrenament și testare
x_train_noisy = noisy_train_datagen.flow_from_directory(
    train_dir,
    target_size=(150, 150),
    batch_size=32,
    class_mode='categorical'
)

x_test_noisy = noisy_test_datagen.flow_from_directory(
    test_dir,
    target_size=(150, 150),
    batch_size=32,
    class_mode='categorical'
)

"""Afisare cateva imagini pentru a vedea cum arata datele"""

# Get a batch of 5 images from both generators
# Reset the iterator
x_train.reset()

# Get a batch of 5 images from x_train
x_train, y_train = next(iter(x_train))

# Get a batch of 5 noisy images from x_batch_noisy
x_batch_noisy, y_batch_noisy = next(iter(x_batch_noisy))

# Select 5 random indices from the batch
indices = np.random.randint(0, len(x_train), size=5)

# Create a figure with 2 rows and 5 columns
fig, axes = plt.subplots(2, 5, figsize=(15, 6))

# Display original and noisy images
for i, ax in enumerate(axes.flat):
    if i < 5:
        ax.imshow(x_train[indices[i]])
        ax.set_title(f"Original Image {i+1}")
    else:
        ax.imshow(x_batch_noisy[indices[i-5]])
        ax.set_title(f"Noisy Image {i-4}")
    ax.axis('off')

plt.tight_layout()
plt.show()

"""Definire Model"""

model = Sequential([
    # retea de codificare
    Conv2D(64, 3, activation='relu', padding='same', input_shape=(32,32,3)),
    MaxPooling2D(2, padding='same'),
    Conv2D(32, 3, activation='relu', padding='same'),
    MaxPooling2D(2, padding='same'),
    Conv2D(16, 3, activation='relu', padding='same'),
    MaxPooling2D(2, padding='same'),

    # retea de decodificare
    Conv2D(16, 3, activation='relu', padding='same'),
    UpSampling2D(2),
    Conv2D(32, 3, activation='relu', padding='same'),
    UpSampling2D(2),
    Conv2D(64, 3, activation='relu', padding='same'),
    UpSampling2D(2),

    # Strat de iesire
    Conv2D(3, 3, activation='sigmoid', padding='same')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

"""Antrenare Model"""

history = model.fit(x_train_noisy, x_train, epochs=10, batch_size=256,  shuffle=True, validation_data=(x_test_noisy, x_test))

# Plot loss and accuracy from training step
def PlotModelHistoryEpoch(model_history):  # plot some data

  print(model_history.history.keys())
  plt.figure(figsize=(20, 5))

  # loss
  plt.subplot(1, 2, 1)
  plt.plot(model_history.history['loss'], label='train loss')
  plt.plot(model_history.history['val_loss'], label='val loss')
  plt.ylabel('loss')
  plt.xlabel('epoch')
  plt.legend()
  # plt.show()

  # accuracies
  plt.subplot(1, 2, 2)
  plt.plot(model_history.history['accuracy'], label='train acc')
  plt.plot(model_history.history['val_accuracy'], label='val acc')
  plt.ylabel('accuracy')
  plt.xlabel('epoch')
  plt.legend()
  plt.show()


# print model_history for model
PlotModelHistoryEpoch(history)

"""Vizualizare Rezultate"""

# prezicere rezultate de la model
pred = model.predict(x_test_noisy)

# selectare imagine aleator
index = np.random.randint(len(x_test))
# vizualizare imagine
ax = plt.subplot(1, 2, 1)
plt.imshow(x_test_noisy[index].reshape(32,32,3))
plt.show()
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
# vizualizare imagine prezisa
plt.imshow(pred[index].reshape(32,32,3))
plt.show()
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)

"""Evaluarea performantei"""