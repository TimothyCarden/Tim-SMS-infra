import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

domain_name = os.environ.get('CORS_DOMAIN_NAME')

region_name = os.environ['AWS_REGION']
account_id = os.environ['AWS_ACCOUNT_ID']
quicksight_namespace = os.environ['QUICKSIGHT_NAMESPACE']
authorized_resource_arns = os.environ['AUTHORIZED_RESOURCE_ARNS']
dashboard_id = os.environ['DASHBOARD_ID']
prod_quicksight_role_arn = os.environ['PROD_QUICKSIGHT_ROLE_ARN']
env_name = os.environ['ENV_NAME']

if env_name != "prod":
    sts = boto3.client('sts')

    # Request to assume the role , the ARN is the Role's ARN from the prod account.
    sts_response = sts.assume_role(
        RoleArn=prod_quicksight_role_arn,
        RoleSessionName="newsession"
    )

    # Save the details from assumed role into vars
    new_session_id = sts_response["Credentials"]["AccessKeyId"]
    new_session_key = sts_response["Credentials"]["SecretAccessKey"]
    new_session_token = sts_response["Credentials"]["SessionToken"]

    quicksight_client = boto3.client(
        "quicksight",
        region_name=region_name,
        aws_access_key_id=new_session_id,
        aws_secret_access_key=new_session_key,
        aws_session_token=new_session_token
    )
else:
    quicksight_client = boto3.client("quicksight")


def send_message_response(message, status_code):
    return send_data_response({"message": message}, status_code)


def send_data_response(data, status_code):
    return {
        "statusCode": status_code,
        "body": json.dumps(data),
        "headers": {
            "access-control-allow-origin": domain_name
        },
    }


def get_embedding_url(event):
    session_tags = event.get("requestContext").get("authorizer").get("claims").get("facility_ctms_id")
    try:
        response = quicksight_client.generate_embed_url_for_anonymous_user(
            AwsAccountId=account_id,
            Namespace=quicksight_namespace,
            AuthorizedResourceArns=[authorized_resource_arns],
            ExperienceConfiguration={"Dashboard": {"InitialDashboardId": dashboard_id}},
            SessionTags=[{"Key": " customer_id", "Value": session_tags}],
            SessionLifetimeInMinutes=600
        )
        return {
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin": domain_name, "Access-Control-Allow-Headers": "Content-Type"},
            'body': json.dumps({"status": response["Status"], "embed_url": response["EmbedUrl"]}),
            'isBase64Encoded': bool('false')
        }
    except ClientError as e:
        print(e)
        return "Error generating embeddedURL: " + str(e)


def lambda_handler(event, context):
    logger.info(event)

    operation = f"{event['httpMethod']}:{event.get('pathParameters', {}).get('proxy', None)}"
    logger.info(operation)
    # define the functions used to perform the CRUD operations
    operations = {
        'GET:dashboards': get_embedding_url
    }

    if operation in operations:
        try:
            return operations[operation](event)
        except Exception as e:
            logger.error(e)
            return send_message_response("Something went wrong", 400)
    else:
        return send_message_response("Not Found", 404)

