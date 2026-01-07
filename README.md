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



---------------------------------------

# Contains cloudformation template to create the Lambda and potentially Stepfunction.

## Deployment of codebuild cloudformation template which will set the pipeline to deploy lambda

1. Run the sample command:
    `aws cloudformation deploy \
        --profile default \
        --capabilities CAPABILITY_AUTO_EXPAND \
        --no-execute-changeset \
        --no-fail-on-empty-changeset \
        --region  \
        --role-arn \
        --stack-name rs-unload-poc-codebuild-cft \
        --template-file ./cloudformation/codebuild-cloudformation.yaml \
        --parameter-overrides \
            CloudformationTemplate=lambda-eventbridge-cloudformation.yaml \
            GitHubBranch=cicd \
            GitHubRepoName=redshift-unload \
            GitHubUrl= \
            KmsKey= \
            GitHubCodeConnectionsArn= \
        --tags \
            env=nonprod \
            product=new \ `

## Testing the deployment of your lambda cloudformation template locally

1. Run the sample command:
    `aws cloudformation deploy \
        --profile default \
        --capabilities CAPABILITY_AUTO_EXPAND \
        --no-execute-changeset \
        --no-fail-on-empty-changeset \
        --region \
        --role-arn  \
        --stack-name rs-unload-poc-lambda-cft \
        --template-file lambda-eventbridge-cloudformation.yaml \
        --tags \
            env=nonprod \
            product=new \ `

3. Navigate to Cloudformation in the AWS Console and approve the changeset to deploy the cloudformation stack and respective resources as specified in your cloudformation.yaml template.


## CloudFormation Templates:
 
1. Lambda + EventBridge CFT  This sets up a scheduled Lambda function.
2. CodeBuild CFT → This automates the deployment of that Lambda setup using GitHub.
 
Together, they create a CI/CD pipeline that deploys a scheduled Lambda function automatically whenever code changes are merged into GitHub.
 
 
### Lambda + EventBridge CloudFormation Template
 
This template creates:
- A Lambda function that runs some code (inline).
- An EventBridge Scheduler that triggers the Lambda on a recurring schedule (e.g., every 5 minutes).
 
It's Useful
- You can run background tasks automatically (e.g., data cleanup, reporting, API calls).
- You don’t need to manually trigger the Lambda it runs on a schedule.
- Everything is defined as code, so it's repeatable and version-controlled.
 
Key Parameters
These are inputs you can customize:
- LambdaFunctionName: Lambda name
- LambdaRuntime: Python 3.9 or Node.js.
- LambdaHandler: Entry point for your code.
- LambdaRoleArn: IAM role that gives Lambda permission to run.
- ScheduleExpression: How often the Lambda runs (e.g., rate(5 minutes)).
- ScheduleGroup: Logical grouping for EventBridge schedules.
 
Resources Created
- AWS::Lambda::Function: The actual Lambda function.
- AWS::Scheduler::Schedule: The EventBridge rule that triggers the Lambda.
 
 
### CodeBuild CloudFormation Template
 
This template creates:
- A CodeBuild project that pulls code from GitHub.
- Runs a buildspec.yaml file to deploy the Lambda + EventBridge stack.
- Automatically triggers when a pull request is merged.
 
It's Useful
- You don’t need to manually deploy your infrastructure.
- It ensures consistent, automated deployments.
- It integrates with GitHub so changes are deployed as part of your development workflow.
 
 Key Parameters:
 These are inputs you can customize:
- GitHubBranch, GitHubRepoName, GitHubUrl: Where your code lives.
- BuildSpec: Instructions for CodeBuild (usually includes aws cloudformation deploy).
- CloudformationTemplate: The Lambda + EventBridge template to deploy.
- KmsKey, VpcConfig: Security and networking settings.
- TimeoutInMinutes: How long the build can run.
 
Resources Created
- AWS::CodeBuild::Project: The build project that runs your deployment logic.
 
How They Work Together
 
Here’s the full flow:
 
1. You write or update your Lambda code and CloudFormation templates in GitHub.
2. You merge a pull request into the main branch.
3. CodeBuild is triggered automatically.
4. CodeBuild runs the buildspec.yaml, which deploys the Lambda + EventBridge stack using CloudFormation.
5. Your Lambda is now scheduled to run automatically!
 
 
### CloudFormation Basics: 
Understanding !Ref, !Join, and !GetAtt
 
CloudFormation templates use intrinsic functions to dynamically reference and manipulate resources. Here are the three most important ones used in your templates:
 
1. !Ref — Reference a Parameter or Resource
 
Purpose: Gets the value of a parameter or the name/ID of a resource.
Used For:
- Passing user-defined parameters into resources.
- Linking resources together.
 Example: FunctionName: !Ref LambdaFunctionName

This tells CloudFormation to use the value of the LambdaFunctionName parameter (e.g., "stormline") as the name of the Lambda function.
 
2. !Join — Combine Strings Together
 
Purpose: Concatenates multiple strings into one.
Used For:
- Creating names, paths, or patterns dynamically.
- Formatting values like ARNs or branch names.
 Example: !Join ["-", [!Ref Product, "rs-unload-poc-codebuild-cft"]]

If Product = stormline, this becomes: stormline-rs-unload-poc-codebuild-cft

3. !GetAtt — Get Attributes of a Resource
 
Purpose: Retrieves properties (like ARN, URL, etc.) from a created resource.
Used For:
- Getting the ARN of a Lambda function to pass into EventBridge.
- Outputting useful values after deployment.
 Example: Arn: !GetAtt MyLambdaFunction.Arn

This grabs the ARN (Amazon Resource Name) of the Lambda function named MyLambdaFunction.
 
### Refference documents:
Lambda:
https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-lambda-function.html

Codebuild:
https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-codebuild-project.html


## Automated Lambda + EventBridge Deployment using Codebuild and jinja2
 
In modern cloud-native architectures, infrastructure-as-code (IaC) is essential for scalable, repeatable, and auditable deployments. This project demonstrates a modular and automated approach to deploying AWS Lambda functions triggered by EventBridge schedules using CloudFormation templates rendered via Jinja2. The pipeline is designed to support on different schema-table combinations, with full CI/CD integration via GitHub and AWS CodeBuild.

### Design
- Modularity: Each Lambda function is scoped to a specific table and schema.
- Parameterization: All dynamic values (e.g., schedule, S3 prefix, SQL query) are externalized in YAML    files.
- Automation: CloudFormation templates are generated and deployed automatically via CodeBuild.
- Reusability: The same Jinja2 template is reused across all deployments.

### Workflow Summary
 
Parameters.yaml file in jinja2 specifying:
   - schema_name
   - table_name
   - schedule_expression

A shared Jinja2 template (lambda-eventbridge-coudFormation.yaml.j2) defines the CloudFormation structure for:
   - Lambda function (with inline code)
   - EventBridge schedule
The render.py script loops through all parameter files and renders one CloudFormation template per table.
AWS CodeBuild runs render.py and deploys each template using aws cloudformation deploy.

### Template Logic
 
The Jinja2 template injects values from the YAML file into the CloudFormation structure. Each Lambda function includes:
 
- Inline Python code with logging
- Environment variables:
  - SCHEMA_NAME
  - TABLE_NAME
  - EB_SCHEDULE_EXPRESSION 

### Automation via CodeBuild
 
The buildspec.yaml file defines three phases:
 
- Install: Installs Python dependencies (Jinja2, PyYAML)
- Build: Executes render.py to generate templates
- Post-build: Deploys each template using AWS CLI

 Replace `<SSO>` with your SSO

aws cloudformation deploy 
    --profile default \
    --capabilities CAPABILITY_AUTO_EXPAND \
    --no-execute-changeset \
    --no-fail-on-empty-changeset \
    --region \
    --role-arn arn:aws-: \
    --stack-name lambda-poc-codebuild-cft \
    --template-file ./cloudformation/codebuild-cloudformation.yaml \
    --tags env=nonprod product=new`

This ensures that every GitHub push results in a fresh deployment of all defined Lambda + EventBridge stacks.
