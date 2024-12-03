import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ======= Load Data =======
data = pd.read_csv('gesture_data.csv')

X = data[['acc_x_t0.25', 'acc_y_t0.25', 'acc_z_t0.25', 
          'gyro_x_t0.25', 'gyro_y_t0.25', 'gyro_z_t0.25', 'flex_t0.25',
          'acc_x_t0.5', 'acc_y_t0.5', 'acc_z_t0.5', 
          'gyro_x_t0.5', 'gyro_y_t0.5', 'gyro_z_t0.5', 'flex_t0.5',
          'acc_x_t0.75', 'acc_y_t0.75', 'acc_z_t0.75', 
          'gyro_x_t0.75', 'gyro_y_t0.75', 'gyro_z_t0.75', 'flex_t0.75',
          'acc_x_t1.0', 'acc_y_t1.0', 'acc_z_t1.0', 
          'gyro_x_t1.0', 'gyro_y_t1.0', 'gyro_z_t1.0', 'flex_t1.0']] # training features
y = data['label']

# Encode labels and split data
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Scale the data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Neural Network Model
nn_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
nn_model.fit(X_train_scaled, y_train)
nn_predictions = nn_model.predict(X_test_scaled)

# K-Nearest Neighbors Model
knn_model = KNeighborsClassifier(n_neighbors=5)
knn_model.fit(X_train_scaled, y_train)
knn_predictions = knn_model.predict(X_test_scaled)

# Calculate error rates
nn_error_rate = np.mean(nn_predictions != y_test)
print(f"Neural Network Results: Average Classification Error: {nn_error_rate:.4%}")

knn_error_rate = np.mean(knn_predictions != y_test)
print(f"KNN Results: Average Classification Error: {knn_error_rate:.4%}")