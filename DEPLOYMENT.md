# Deployment Guide for HealthAI Assistant

This guide details how to deploy the HealthAI Assistant to AWS using CloudFormation.

## Prerequisites

1.  **AWS Account**: You need an active AWS account.
2.  **AWS CLI**: Installed and configured with `aws configure`.
    -   [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3.  **Git**: Installed on your local machine.

## Step 1: Push Code to GitHub

The EC2 instance will clone the repository to run the code. Ensure your latest changes are pushed to GitHub.

```bash
git add .
git commit -m "Prepare for AWS deployment"
git push origin main
```

> **Note**: The CloudFormation template currently points to `https://github.com/kiran3035/healthai-assistant.git`. If you are using a different repository, update line 123 in `aws/cloudformation.yaml` before pushing.

## Step 2: Deploy CloudFormation Stack

You can deploy the stack using the AWS CLI or the AWS Console.

### Option A: Using AWS CLI (Recommended)

Run the following command in your terminal (replace `MyKeyPair` with your actual EC2 Key Pair name):

```bash
aws cloudformation create-stack \
  --stack-name healthai-stack \
  --template-body file://aws/cloudformation.yaml \
  --parameters ParameterKey=KeyName,ParameterValue=MyKeyPair \
  --capabilities CAPABILITY_IAM
```

### Option B: Using AWS Console

1.  Go to the [CloudFormation Console](https://console.aws.amazon.com/cloudformation).
2.  Click **Create stack** > **With new resources (standard)**.
3.  Select **Upload a template file** and choose `aws/cloudformation.yaml`.
4.  Click **Next**.
5.  Enter a **Stack name** (e.g., `healthai-stack`).
6.  Select your **KeyName** from the dropdown.
7.  Click **Next** through the options pages.
8.  At the review page, check the box **I acknowledge that AWS CloudFormation might create IAM resources**.
9.  Click **Submit**.

## Step 3: Monitor Deployment

The deployment will take approximately 15-20 minutes, primarily due to the OpenSearch Serverless collection creation.

You can monitor the status in the AWS Console or via CLI:

```bash
aws cloudformation describe-stacks --stack-name healthai-stack
```

Wait until the status is `CREATE_COMPLETE`.

## Step 4: Access the Application

Once the deployment is complete, get the application URL from the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name healthai-stack \
  --query "Stacks[0].Outputs[?OutputKey=='ServerURL'].OutputValue" \
  --output text
```

Or look for the **ServerURL** in the **Outputs** tab of the CloudFormation Console.

Open that URL in your browser to access the HealthAI Assistant.

## Troubleshooting

-   **Instance Connection**: You can SSH into the instance using the username `ubuntu` and your key pair.
    ```bash
    ssh -i /path/to/key.pem ubuntu@<ServerPublicIP>
    ```
-   **Logs**: Application logs can be viewed on the instance:
    ```bash
    docker logs healthai
    ```
-   **CloudInit Logs**: If the setup script failed, check:
    ```bash
    cat /var/log/cloud-init-output.log
    ```
