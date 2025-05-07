import tensorflow as tf
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import layers
from tensorflow.keras.optimizers import Adam

# Import Data
print("\n---- Dataset Info ----")
gesture_data = pd.read_csv("imu_data.csv")

# Separate inputs and outputs
x = gesture_data.iloc[:, :-1].values  # Input (first 300 columns)
y = gesture_data.iloc[:, -1].values   # Output (column 301)

# Convert string labels to numeric (0-3)
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)
label_mapping = dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))

# Save the encoder for future use (important for inference)
joblib.dump(label_encoder, "label_encoder.pkl")

# Print dataset info
print(f"gesture_data.shape = {gesture_data.shape}")
print(f"features.shape = {x.shape}")
print(f"labels.shape = {y.shape}")
print("Label Mapping:", label_mapping)
print("\n")

# Settings
inputShape = (300,) # Change this to match the size of input
nsamples = 125      # Number of samples to use as a dataset
val_ratio = 0.1     # % of samples that should be held for validation set
test_ratio = 0.1    # % of samples that should be held for test set
tflite_model_name = 'SIGNSPEAK_MLP_full_model'    # Will be given .tflite suffix
c_model_name = 'SIGNSPEAK_MLP_full_model'         # Will be given .h suffix

# Split the dataset into training, validation, and test sets (80% train, 10% validation, 10% test)
x_train, x_temp, y_train, y_temp = train_test_split(x, y, test_size=0.2, random_state=42)
x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5, random_state=42)

# Create a model
model = tf.keras.Sequential([
    tf.keras.Input(shape=(300,)),
    layers.Dense(64, activation='relu'),
    layers.Dense(32, activation='relu'),
    layers.Dense(5, activation='softmax')  # Ensure 5 gesture classes
])

model.summary() # Print model summary


# Add optimizer, loss function, and metrics to model and compile it
model.compile(optimizer=Adam(learning_rate=0.001),
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
                    epochs=50,
                    batch_size=16,  # Small batch size for generalization
                    validation_data=(x_val, y_val))

test_loss, test_acc = model.evaluate(x_test, y_test)
print(f"Test Accuracy: {test_acc:.4f}")

model.save("my_model.h5")  # ✅ Saves in HDF5 format

# Load model from .h5
model = tf.keras.models.load_model("my_model.h5")  # ✅ Ensure it's loaded

converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Optimize for BeagleBone Black (ARMv7)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# Force downgrade of all ops to older versions for BBB compatibility
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]  # ✅ Use this instead

# Convert the model
tflite_model = converter.convert()

# Save optimized model
with open("SIGNSPEAK_MLP_compatible.tflite", "wb") as f:
    f.write(tflite_model)

print("TFLite model saved: SIGNSPEAK_MLP_compatible.tflite")