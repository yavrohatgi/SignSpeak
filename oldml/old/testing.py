import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split # split data into test/train
from sklearn.neighbors import KNeighborsClassifier # for knn
from sklearn.neural_network import MLPClassifier # for neural networks
from sklearn.preprocessing import LabelEncoder, StandardScaler # to encode/decode in NN

# ======= Load Data =======
data = pd.read_csv('data.csv')
X = data[['flex', 'acc-x', 'acc-y', 'acc-z', 'gyro-x', 'gyro-y', 'gyro-z']] # training features
y = data['label'] # training outputs (labels)

# ==== Neural Networks =======
label_encoder = LabelEncoder() # define label encoder
y_encoded = label_encoder.fit_transform(y) # convert to integers 
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

scaler = StandardScaler() # define scaler
X_train_scaled = scaler.fit_transform(X_train) # scale training data
X_test_scaled = scaler.transform(X_test) # scale testing data

# 64 and 32 are the number of neurons in the first and second hidden layers (commonly used values)
nn_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
nn_model.fit(X_train_scaled, y_train) # build the model 
nn_predictions = nn_model.predict(X_test_scaled) # make predictions on new data 

# ==== K-Nearest Neighbors =======
# Using 5 neighbors since its commonly used, ballances overfitting and underfitting
knn_model = KNeighborsClassifier(n_neighbors=5) # define model with 5 neighbors
knn_model.fit(X_train_scaled, y_train) # build the model
knn_predictions = knn_model.predict(X_test_scaled) # make predictions on new data

# ======= Results =======
# Average misclassification rate when predicted label doesnt equal actual label
# Ie the actual is left and the model predicts right or up or down (doesnt matter all wrong)
nn_error_rate = np.mean(nn_predictions != y_test)
print(f"Neural Network Results: Average Classification Error: {nn_error_rate:.4%}") # 4 sf

knn_error_rate = np.mean(knn_predictions != y_test)  
print(f"KNN Results: Average Classification Error: {knn_error_rate:.4%}") # 4 sf

"""
Local Testing Results:
Neural Network Results: Average Classification Error: 0.0000%
KNN Results: Average Classification Error: 0.0000%
I beleive this is because we are doing something very simple and have a decent amount of data
This will be a lot more when we to sign detect with 5 imus
"""