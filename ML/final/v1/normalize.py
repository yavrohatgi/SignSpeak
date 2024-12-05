import csv
import pandas as pd

gesture_data = pd.read_csv('gesture_data.csv')
# Extract the feature columns (exclude the label)
feature_columns = gesture_data.columns[:-1]  # All columns except 'label'

# Normalize each feature column using the given function
def lp_norm(vector, p=2):
    sum_val = sum(pow(abs(num), p) for num in vector)
    return pow(sum_val, 1/p)

def normalize_vector(vector, p=2):
    data_norm = lp_norm(vector, p)
    return [value / data_norm for value in vector] if data_norm != 0 else vector

# Normalize the feature columns
for column in feature_columns:
    gesture_data[column] = normalize_vector(gesture_data[column].values)

# Save the normalized dataset
normalized_file = 'gesture_data_normalized.csv'
gesture_data.to_csv(normalized_file)