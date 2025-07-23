import yaml


input_file = "bundled.yaml"
output_file = "bundled-sorted.yaml"


with open(input_file, "r") as f:
    data = yaml.safe_load(f)


if "components" in data and "schemas" in data["components"]:
    schemas = data["components"]["schemas"]
    sorted_schemas = dict(sorted(schemas.items()))
    data["components"]["schemas"] = sorted_schemas



with open(output_file, "w") as f:
    yaml.dump(data, f, sort_keys=False, allow_unicode=True)
