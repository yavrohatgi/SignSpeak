import csv

input_file = "raw_data.txt" # Input file change as needed
output_file = "data.csv"    # Output file

# Open the files
with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
    csv_writer = csv.writer(outfile)                                                         # Create a CSV writer
    csv_writer.writerow([f"Feature_{i+1}" for i in range(300)] + ["Gesture"])                # Column headers
    current_gesture = None                                                                   # Current gesture label  

    for line in infile:
        line = line.strip()                                                                  # Remove leading/trailing whitespaces
        if line.startswith("Gesture:"):
            parts = line.split()                                                             # Split the line                                    
            current_gesture = parts[1]                                                       # Extract gesture label
        elif line and not line.startswith(("All", "Start", "In ", "Now!", "Gesture done.")): # Skip unwanted lines
            try:
                values = list(map(float, line.split()))
                if len(values) == 300:                                                       # Ensure each row has exactly 300 features
                    csv_writer.writerow(values + [current_gesture])                          # Append gesture at the end
            except ValueError:
                continue                                                                     # Skip lines with non-numeric values

print(f"CSV file created: {output_file}")