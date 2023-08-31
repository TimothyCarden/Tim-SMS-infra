import logging
import os
import sys
import boto3
import json
import phonenumbers
import psycopg2
import psycopg2.extras
from aws_secretsmanager_caching import SecretCache, InjectSecretString
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
cognito_client = boto3.client('cognito-idp')
cache = SecretCache()

PROVIDER_USER_POOL_ID = os.environ['PROVIDER_USER_POOL_ID']


@InjectSecretString(os.environ['DB_URL'], cache)
@InjectSecretString(os.environ['DB_USERNAME'], cache)
@InjectSecretString(os.environ['DB_PASSWORD'], cache)
def pg_database_conn(password, username, jdbc_url):
    try:
        logger.info("getting connection from db")
        conn = psycopg2.connect(dsn=jdbc_url[5:jdbc_url.index('?')], user=username, password=password,
                                connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS PostgreSQL instance succeeded")
        return conn
    except psycopg2.Error as e:
        logger.error("ERROR: Unexpected error: Could not connect to PostgreSQL instance.")
        logger.error(e)
        sys.exit()


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
        return get_phone_from_attributes(user)
    except ClientError as client_error:
        logger.error(client_error)
        message = client_error.response['message']
        print(f'Updating record error {cognito_sub}. Error message: {message}')
        return None

def lambda_handler(event, context):

    cognito_sub = event.get("cognito_sub")
    new_phone = event.get("cell_phone")

    try:
        phone = phonenumbers.parse(new_phone, None)
        if not phonenumbers.is_possible_number(phone):
            raise Exception()
    except:
        logger.info(f'Bad phone number format {new_phone}')
        return send_response({"error_message": f"Wrong phone format {new_phone}"}, 400)

    if not cognito_sub:
        return send_response({"error_message": f"Cognito sub is missing in request"}, 400)

    cell_phone = update_cognito_phone(cognito_sub, new_phone)

    if cell_phone:
        return send_response({"cell_phone": cell_phone}, 200)
    else:
        return send_response({"error_message": "Something went wrong"}, 400)
