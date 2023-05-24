import json
import logging
import os

import boto3
import phonenumbers
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')

provider_user_pool_id = os.environ.get('PROVIDER_USER_POOL_ID')


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


def get_or_create_cognito_sub(phone):
    try:
        user = cognito_client.admin_create_user(
            UserPoolId=provider_user_pool_id,
            Username=phone,
            UserAttributes=[
                {
                    'Name': 'phone_number',
                    'Value': phone
                },
                {
                    'Name': 'phone_number_verified',
                    'Value': 'True'
                }
            ],
            ForceAliasCreation=False,
            MessageAction='SUPPRESS'
        )
        return get_cognito_sub(user)
    except ClientError as client_error:
        message = client_error.response['message']
        print(f'Phone number: {phone}. Error: {message}')
        if message == 'An account with the given phone_number already exists.':
            users = cognito_client.list_users(
                UserPoolId=provider_user_pool_id,
                AttributesToGet=[],
                Filter=f'phone_number ^= \"{phone}\"'
            )
            if users.get('Users') is not None and users.get('Users'):
                user = users.get('Users')[0]
                return user['Username']
            return None
        else:
            raise client_error
    except Exception as error:
        print(error)
        return None


def lambda_handler(event, context):
    logger.info(event)
    cell_phone = event.get("cell_phone")

    try:
        phone = phonenumbers.parse(cell_phone, None)
        if not phonenumbers.is_possible_number(phone):
            raise Exception()
    except:
        logger.info(f'Bad phone number format {cell_phone}')
        return send_response({"error_message": f"Wrong phone format {cell_phone}"}, 400)

    cognito_sub = get_or_create_cognito_sub(cell_phone)
    if cognito_sub:
        return send_response({"cognito_sub": cognito_sub}, 200)
    else:
        return send_response({"error_message": "Something went wrong"}, 400)
