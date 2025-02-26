import csv

# Input and output file paths
input_file = "imu_data.txt"
output_file = "imu_data.csv"

# Open the files
with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
    csv_writer = csv.writer(outfile)

    # Write header with 300 feature columns and gesture at the end
    csv_writer.writerow([f"Feature_{i+1}" for i in range(300)] + ["Gesture"])

    current_gesture = None

    for line in infile:
        line = line.strip()
        if line.startswith("Gesture:"):
            parts = line.split()
            current_gesture = parts[1]  # Extract gesture label
        elif line and not line.startswith(("All", "Start", "In ", "Now!", "Gesture done.")):
            try:
                values = list(map(float, line.split()))
                if len(values) == 300:  # Ensure each row has exactly 300 features
                    csv_writer.writerow(values + [current_gesture])  # Append gesture at the end
            except ValueError:
                continue  # Skip lines with non-numeric values

print(f"CSV file created: {output_file}")