# Lambda + EventBridge CloudFormation Deployments using Jinja2 

This repository contains an AWS CloudFormation-based Lambda + EventBridge deployment pipeline that uses Jinja2 templates and parameter files for environment-specific rendering, plus CI/CD integration via CodeBuild/CodePipeline.

## Prerequisites
- An AWS account with permissions to create CloudFormation stacks, IAM roles, Lambda, EventBridge, CodeBuild, and CodePipeline resources.
- `aws` CLI installed and configured (profile or env vars).
- Python 3.8+ and `pip` available locally to run `render.py` (if needed).
- 
Install Python dependencies (if you plan to run `render.py` locally):

```bash
python -m pip install -r requirements.txt  # if repository includes requirements.txt
# or
python -m pip install jinja2 pyyaml
```
## Repository layout

- [templates/]: Jinja2 templates used to generate CloudFormation YAML.
- [team_configs/]: Environment-specific parameter files (YAML) used when rendering templates.
- `render.py`: Takes a `.j2` template and a parameters YAML to produce a final CloudFormation template.
- `buildspec.yaml`: Used by CodeBuild to validate and deploy the rendered template (or run tests).

- 
## Files
- `output/lambda-EB-empolyee_data-template.yaml` — parameterized CloudFormation template for empolyee data (now accepts Parameters).
- `output/lambda-EB-customer_data-template.yaml` — generated template for customer data.
- `output/lambda-EB-sales_data-template.yaml` — generated template for sales data.
- `team_configs/parameters_empolyee_data.yaml`, `team_configs/parameters_customer_data.yaml`, `team_configs/parameters_sales_data.yaml` — example parameter values used when generating templates.

## Deploy (recommended)
Replace `<YOUR-S3-BUCKET>` and optionally set `--profile` / `--region`.

```bash
aws cloudformation deploy \
  --template-file output/lambda-EB-empolyee_data-template.yaml \
  --stack-name lambda-eb-empolyee \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    SchemaName=public \
    TableName=empolyee \
    ScheduleExpression="cron(0/5 * * * ? *)" \
    WorkgroupName=default-workgroup \
    DatabaseName=dev \
    S3Bucket=<YOUR-S3-BUCKET> \
    S3Key=lambda/public_empolyee.csv
```

Notes:
- The employee template now exposes `SchemaName`, `TableName`, `ScheduleExpression`, `WorkgroupName`, `DatabaseName`, `S3Bucket`, and `S3Key` as parameters.
- If you use a non-default AWS profile or region, add `--profile myprofile --region us-east-1` to the command.

## Step-by-step workflow

1. Choose the parameter file for the target environment

   - Example: use `team_configs/parameters__sales_data.yaml` or `team_configs/parameters_customer_data.yaml`.

2. Render the Jinja2 template to a concrete CloudFormation template

   - Generic example using `render.py` (adjust flags per script implementation):

   ```bash
   python render.py \
     --template templates/lambda-eventbridge-template.yaml.j2 \
     --params team_configs/parameters__sales_data.yaml \
     --output rendered-template.yaml
   ```

   - If `render.py` has a different CLI, consult the top of `render.py` or run:

   ```bash
   python render.py --help
   ```

3. Validate the rendered CloudFormation template locally

```bash
aws cloudformation validate-template --template-body file://rendered-template.yaml
```

4. Deploy the CloudFormation stack (development example)

```bash
aws cloudformation deploy \
  --template-file rendered-template.yaml \
  --stack-name my-lambda-eventbridge-stack-dev \
  --capabilities CAPABILITY_NAMED_IAM
```

5. CI/CD with CodeBuild / CodePipeline

- `buildspec.yaml` contains the build and deployment steps to run inside CodeBuild. Typical stages:
  - Install dependencies (pip install, npm, etc.).
  - Run `render.py` to create the final template.
  - Lint/validate CloudFormation.
  - Deploy with `aws cloudformation deploy` or hand off to a CloudFormation deploy stage in CodePipeline.

- To start a CodeBuild run manually (example):

```bash
aws codebuild start-build --project-name MyProjectName
```

- Example CodePipeline flow:
  - Source: GitHub / CodeCommit / S3
  - Build: CodeBuild (uses `buildspec.yaml` to render templates and run tests)
  - Deploy: CloudFormation deploy action (or a custom action that runs `aws cloudformation deploy`)

6. Testing the deployed integration

- After deployment, verify the Lambda and EventBridge rule are created in the console or via CLI:

```bash
aws lambda list-functions
aws events list-rules
```

- To test EventBridge invocation, put a test event:

```bash
aws events put-events --entries '[{"Source":"custom.test","DetailType":"TestEvent","Detail":"{\"key\":\"value\"}"}]'
```

7. Troubleshooting

- CloudFormation failures: inspect the stack events:

```bash
aws cloudformation describe-stack-events --stack-name my-lambda-eventbridge-stack-dev
```

- CodeBuild logs: view the build logs in the AWS Console or fetch logs through CloudWatch Logs.
- IAM issues: ensure the deployer role has `iam:CreateRole`, `iam:AttachRolePolicy`, `cloudformation:*`, and other resource-specific permissions.

8. Cleanup

```bash
aws cloudformation delete-stack --stack-name my-lambda-eventbridge-stack-dev
```

## Parameterization & environments

- Use files under [team_configs/](team_configs/) to define environment-specific variables (e.g., names, ARNs, sizes).
- Structure parameter files consistently (keys expected by the Jinja2 template). Example YAML snippet:

```yaml
StackName: my-lambda-eventbridge-stack-dev
LambdaMemorySize: 128
Environment: dev
```

## Tips & best practices

- Keep secrets out of plain YAML files; use Secrets Manager or SSM Parameter Store and reference ARNs.
- Use separate `team_configs` files per environment (dev, staging, prod) and CI pipeline variables to choose the correct file.
- Use `CAPABILITY_NAMED_IAM` only when needed and review IAM changes before applying in prod.

## Example quick commands

```bash
# Render
python render.py --template templates/lambda-eventbridge-template.yaml.j2 --params team_configs/parameters__sales_data.yaml --output rendered.yaml

# Validate
aws cloudformation validate-template --template-body file://rendered.yaml

# Deploy
aws cloudformation deploy --template-file rendered.yaml --stack-name my-stack --capabilities CAPABILITY_NAMED_IAM

# Trigger test event
aws events put-events --entries '[{"Source":"custom.test","DetailType":"TestEvent","Detail":"{\"key\":\"value\"}"}]'
```

## Next steps (suggested)

- Run the render locally with a chosen `team_configs` file and validate the generated template.
- Create or update a CodeBuild project using `buildspec.yaml` and connect a Source provider to drive builds on commits.
- Optionally, create a CodePipeline to orchestrate Source → Build → Deploy stages.

## Where to look in this repo

- Template: [templates/lambda-eventbridge-template.yaml.j2](templates/lambda-eventbridge-template.yaml.j2)
- Parameter examples: [team_configs/](team_configs/)
- Build spec: [buildspec.yaml](buildspec.yaml)
- Helper script: [render.py](render.py)

If you want, I can also:
- run a local render using a particular parameter file,
- validate the rendered template,
- or create an example CodePipeline CloudFormation template to automate the pipeline.
