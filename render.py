from jinja2 import Environment, FileSystemLoader
import yaml
import os

# Load Jinja2 template
env = Environment(loader=FileSystemLoader('./templates'))
template = env.get_template('lambda-eventbridge-template.yaml.j2')

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Loop through all parameter files in team_configs/
for param_file in os.listdir('team_configs'):
    if param_file.endswith('.yaml'):
        with open(f'team_configs/{param_file}') as f:
            configs = yaml.safe_load(f)

        for config in configs:
            # Build base name from schema + table
            base_name = f"{config['schema_name']}-{config['table_name']}"
            # Replace underscores with hyphens for CloudFormation compliance
            safe_name = base_name.replace("_", "-")

            # Render template
            output = template.render(**config)

            # Save file with safe name
            output_path = f"output/lambda-eb-{safe_name}.yaml"
            with open(output_path, 'w') as f:
                f.write(output)

            print(f"✅ Generated: {output_path} from {param_file}")
