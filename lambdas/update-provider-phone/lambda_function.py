import logging
import os
import boto3
import json
import phonenumbers
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
cognito_client = boto3.client('cognito-idp')

PROVIDER_USER_POOL_ID = os.environ['PROVIDER_USER_POOL_ID']


def send_response(data, status_code):
    return {
        "StatusCode": status_code,
        "Payload": json.dumps(data)
    }

def get_phone_from_attributes(cognito_user):
    logger.info(cognito_user)
    attributes = cognito_user['User']['Attributes']
    for attribute in attributes:
        if attribute['Name'] == 'phone_number':
            return attribute['Value']

def update_cognito_phone(cognito_sub, new_phone):
    try:
        user = cognito_client.admin_update_user_attributes(
            UserPoolId=PROVIDER_USER_POOL_ID,
            Username=cognito_sub,
            UserAttributes=[
                {
                    'Name': 'phone_number',
                    'Value': new_phone
                },
                {
                    'Name': 'phone_number_verified',
                    'Value': 'True'
                }
            ]
        )
    except ClientError as client_error:
        logger.error(client_error)
        message = client_error.response['message']
        print(f'Updating record error {cognito_sub}. Error message: {message}')

def lambda_handler(event, context):

    cognito_sub = event.get("cognito_sub")
    cell_phone = event.get("cell_phone")

    try:
        phone = phonenumbers.parse(cell_phone, None)
        if not phonenumbers.is_possible_number(phone):
            raise Exception()
    except:
        logger.info(f'Bad phone number format {cell_phone}')
        return send_response({"error_message": f"Wrong phone format {cell_phone}"}, 400)

    if not cognito_sub:
        return send_response({"error_message": f"Cognito sub is missing in request"}, 400)

    update_cognito_phone(cognito_sub, cell_phone)

    return send_response({"cell_phone": cell_phone}, 200)
