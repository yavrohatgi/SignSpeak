import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense, Input #type: ignore
from sklearn.preprocessing import LabelEncoder

# ===== Load the data =====
data = pd.read_csv("gesture_data.csv")
x_trn = data[['acc_x_t0.25', 'acc_y_t0.25', 'acc_z_t0.25', 
          'gyro_x_t0.25', 'gyro_y_t0.25', 'gyro_z_t0.25', 'flex_t0.25',
          'acc_x_t0.5', 'acc_y_t0.5', 'acc_z_t0.5', 
          'gyro_x_t0.5', 'gyro_y_t0.5', 'gyro_z_t0.5', 'flex_t0.5',
          'acc_x_t0.75', 'acc_y_t0.75', 'acc_z_t0.75', 
          'gyro_x_t0.75', 'gyro_y_t0.75', 'gyro_z_t0.75', 'flex_t0.75',
          'acc_x_t1.0', 'acc_y_t1.0', 'acc_z_t1.0', 
          'gyro_x_t1.0', 'gyro_y_t1.0', 'gyro_z_t1.0', 'flex_t1.0']] # training features
y_trn = data['label']

# ===== Preprocess the data =====
label_encoder = LabelEncoder() 
y_trn_encoded = label_encoder.fit_transform(y_trn) # convert the labels (up, down, left, right) to integers
y_trn_one_hot = tf.keras.utils.to_categorical(y_trn_encoded) # Convert the labels to one-hot encoding

# ===== Define a Neural Network =====
model = Sequential([
    Input(shape=(x_trn.shape[1],)), # Input layer with the number of features
    Dense(64, activation='relu'),   # Hidden layer with 64 neurons
    Dense(32, activation='relu'),   # Hidden layer with 32 neurons
    Dense(y_trn_one_hot.shape[1], activation='softmax')  # Output layer
])

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(x_trn, y_trn_one_hot, epochs=10, batch_size=32)

# ====== Convert the model to TensorFlow Lite ======
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the TFLite model
with open("model.tflite", "wb") as f:
    f.write(tflite_model)

print("TensorFlow Lite model generated successfully!")