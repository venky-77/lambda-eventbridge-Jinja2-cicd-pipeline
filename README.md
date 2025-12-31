# Lambda + EventBridge CloudFormation Deployments using Jinja2 

This document explains how to deploy the generated CloudFormation templates in this repository using the AWS CLI, how to pass parameters, and how to verify the stacks.

## Prerequisites
- AWS CLI v2 installed and configured (`aws configure`) with appropriate IAM permissions to create Lambda, EventBridge, and IAM resources.
- An S3 bucket to receive exported CSV files.
- (Optional) A local terminal (PowerShell on Windows) and `yq` if you want to programmatically read YAML parameter files.

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

## Deploy other templates (no parameters added)
If the other templates haven't been parameterized, deploy them directly:

```bash
aws cloudformation deploy --template-file output/lambda-EB-customer_data-template.yaml --stack-name lambda-eb-customer --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

aws cloudformation deploy --template-file output/lambda-EB-sales_data-template.yaml --stack-name lambda-eb-sales --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

If you want to pass custom values to these templates, edit them to add `Parameters` (similar to the employee template) and use `--parameter-overrides`.

## Validate a template

```bash
aws cloudformation validate-template --template-body file://output/lambda-EB-empolyee_data-template.yaml
```

## Check stack status

```bash
aws cloudformation describe-stacks --stack-name lambda-eb-empolyee --query 'Stacks[0].StackStatus' --output text
```

## View stack resources (find Lambda function name, role, etc.)

```bash
aws cloudformation list-stack-resources --stack-name lambda-eb-empolyee
```

## Tail Lambda logs
1. Find the Lambda function name from stack resources (look for type `AWS::Lambda::Function`).
2. Tail logs (example):

```bash
aws logs tail /aws/lambda/<FUNCTION_NAME> --follow
```

## Delete stack

```bash
aws cloudformation delete-stack --stack-name lambda-eb-empolyee
```

## Passing parameters from `team_configs` files
The `team_configs/*.yaml` files contain example parameter values. You can map those values into `--parameter-overrides` manually, or use a small script (or `yq`) to read them and build the CLI arguments. Example (conceptual):

```bash
# using yq (install separately)
S3_BUCKET=my-bucket
SCHEMA=$(yq e '.[0].schema_name' team_configs/parameters_empolyee_data.yaml)
TABLE=$(yq e '.[0].table_name' team_configs/parameters_empolyee_data.yaml)
# then pass ${SCHEMA} and ${TABLE} into --parameter-overrides
```

## Notes & Troubleshooting
- The generated template references an IAM role ARN for Lambda; ensure that role exists or change the template to create a role. If the template contains `Role: arn:aws:iam::...:role/lambda-role`, either create that role before deployment or modify the template to use a created role resource.
- If CloudFormation fails with IAM errors, ensure your CLI credentials have permissions to create and attach IAM roles and policies.

---

