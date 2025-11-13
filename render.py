from jinja2 import Environment, FileSystemLoader
import yaml
import os

env = Environment(loader=FileSystemLoader('./templates'))
template = env.get_template('lambda-eventbridge-template.yaml.j2')

os.makedirs('output', exist_ok=True)

for param_file in os.listdir('team_configs'):
    if param_file.endswith('.yaml'):
        with open(f'team_configs/{param_file}') as f:
            configs = yaml.safe_load(f)

        for config in configs:
            base_name = f"{config['schema_name']}-{config['table_name']}"
            output = template.render(**config)

            output_path = f"output/lambda-eb-{base_name}.yaml"
            with open(output_path, 'w') as f:
                f.write(output)

            print(f"✅ Generated: {output_path} from {param_file}")
