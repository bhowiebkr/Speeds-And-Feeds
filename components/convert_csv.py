import csv
import json


def rc_to_hb(rc):
    return (int(rc) - 15) * 10


def csv_to_json(csv_file_path, json_file_path):
    data = []

    # Read the CSV file using the csv module
    with open(csv_file_path, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for i, row in enumerate(reader):
            row["k-factor"] = float(row["k-factor"])  # Convert 'k-factor' to float

            hardness = row["hardness-brinell"].lower()
            row["material"] = row["material"].strip().title()
            del row["hardness-brinell"]

            h_min = None
            h_max = None

            if "rc" in hardness:
                hardness = hardness.replace("rc", "")

                if "-" in hardness:
                    h_min = rc_to_hb(hardness.split("-")[0])
                    h_max = rc_to_hb(hardness.split("-")[1])

                else:
                    print(row["material"], hardness)

                    h_min = rc_to_hb(hardness)
                    h_max = rc_to_hb(hardness)

            if "-" in hardness:
                h_min = hardness.split("-")[0]
                h_max = hardness.split("-")[1]
            else:
                h_min = hardness
                h_max = hardness

            row["hb_min"] = h_min
            row["hb_max"] = h_max

            data.append(row)

    # Convert CSV data to JSON
    json_data = json.dumps(data, indent=4)

    # Write the JSON data to a file
    with open(json_file_path, "w") as json_file:
        json_file.write(json_data)


# Example usage
csv_file_path = "materials.csv"  # Replace with your CSV file path
json_file_path = "materials.json"  # Replace with the desired output JSON file path

csv_to_json(csv_file_path, json_file_path)
