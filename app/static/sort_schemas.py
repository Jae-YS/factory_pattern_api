import yaml

# Input and output file paths
input_file = "bundled.yaml"
output_file = "bundled-sorted.yaml"

# Load the bundled YAML
with open(input_file, "r") as f:
    data = yaml.safe_load(f)

# Sort components.schemas alphabetically
if "components" in data and "schemas" in data["components"]:
    schemas = data["components"]["schemas"]
    sorted_schemas = dict(sorted(schemas.items()))
    data["components"]["schemas"] = sorted_schemas


# Save the sorted YAML
with open(output_file, "w") as f:
    yaml.dump(data, f, sort_keys=False, allow_unicode=True)
