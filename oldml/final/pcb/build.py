import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# === Load the data ===
data = pd.read_csv('pcb_data.csv')  # Load the data
X = data[[col for col in data.columns if col.startswith(('acc', 'gyro', 'flex'))]]  # Input features
y = data['gesture']  # Output labels

# Encode the output labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)  # Convert up, down, left, right to numeric values

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train the Neural Network with a more complex architecture
nn_model = MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=1000, random_state=42, 
                          activation='relu', solver='adam', alpha=0.001)
nn_model.fit(X_train_scaled, y_train)

# Evaluate the model
y_pred = nn_model.predict(X_test_scaled)
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Save the model, scaler, and label encoder
joblib.dump(nn_model, 'nn_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')
print("\nModel, scaler, and label encoder saved successfully.")