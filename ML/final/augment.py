import pandas as pd
import numpy as np

# Load the original dataset
gesture_data = pd.read_csv('gesture_data.csv')

# Function to add noise to numeric features
def add_noise(data, noise_level=0.01, num_augmentations=4):
    augmented_data = []
    for _ in range(num_augmentations):
        noisy_data = data.copy()
        noisy_data.iloc[:, :-1] += np.random.normal(0, noise_level, data.iloc[:, :-1].shape)
        augmented_data.append(noisy_data)
    return pd.concat(augmented_data, ignore_index=True)

# Separate data by class
classes = gesture_data['label'].unique()
augmented_data = []

for cls in classes:
    class_data = gesture_data[gesture_data['label'] == cls]
    num_samples_needed = 400
    num_augmentations = num_samples_needed // len(class_data)  # How many times to duplicate
    augmented_class_data = add_noise(class_data, noise_level=0.01, num_augmentations=num_augmentations)
    augmented_data.append(augmented_class_data)

# Combine all augmented data
augmented_data = pd.concat(augmented_data, ignore_index=True)

# Combine original and augmented data
final_dataset = pd.concat([gesture_data, augmented_data], ignore_index=True)

# Save the augmented dataset
final_dataset.to_csv('gesture_data_augmented.csv', index=False)
print(f"Original samples: {len(gesture_data)}, Augmented samples: {len(final_dataset)}")