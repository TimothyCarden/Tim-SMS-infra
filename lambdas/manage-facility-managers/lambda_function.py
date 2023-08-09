import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')

facility_manager_user_pool_id = os.environ.get('FACILITY_MANAGER_USER_POOL_ID')


def send_response(data, status_code):
    return {
        "StatusCode": status_code,
        "Payload": json.dumps(data)
    }

def get_cognito_sub(user):
    attributes = user['User']['Attributes']
    for attribute in attributes:
        if attribute['Name'] == 'sub':
            return attribute['Value']

def get_or_create_cognito_sub(email):
    try:
        user = cognito_client.admin_create_user(
            UserPoolId=facility_manager_user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'True'
                }
            ],
            ForceAliasCreation=False,
            MessageAction='SUPPRESS'
        )
        return get_cognito_sub(user)
    except ClientError as client_error:
        message = client_error.response['message']
        print(f'Email: {email}. Error: {message}')
        if message == 'An account with the given email already exists.':
            users = cognito_client.list_users(
                UserPoolId=facility_manager_user_pool_id,
                AttributesToGet=[],
                Filter=f'email ^= \"{email}\"'
            )
            if users.get('Users') is not None and users.get('Users'):
                user = users.get('Users')[0]
                return user['Username']
            return None
        else:
            raise client_error
    except Exception as error:
        logger.error(error)


def lambda_handler(event, context):
    logger.info(event)
    email = event.get("email")

    cognito_sub = get_or_create_cognito_sub(email)
    if cognito_sub:
        return send_response({"cognito_sub": cognito_sub}, 200)
    else:
        return send_response({"error_message": "Something went wrong"}, 400)
