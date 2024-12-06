import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

# === Load the data ===
data = pd.read_csv('data.csv') # load the data
X = data[[col for col in data.columns if col.startswith(('acc', 'gyro', 'flex'))]] # input
y = data['gesture'] # output

# Encode the output
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y) # convert up, down, left, right to numbers

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train the Neural Network
nn_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
nn_model.fit(X_train_scaled, y_train)

# Save the model, scaler, and label encoder
joblib.dump(nn_model, 'nn_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')
print("Model, scaler, and label encoder saved successfully.")