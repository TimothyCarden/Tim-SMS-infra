import logging
import os
import re
import sys

import boto3
import phonenumbers
import psycopg2
import psycopg2.extras
from aws_secretsmanager_caching import SecretCache, InjectSecretString

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from botocore.exceptions import ClientError
from psycopg2.extras import execute_values

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


def get_cognito_sub(user):
    attributes = user['User']['Attributes']
    for attribute in attributes:
        if attribute['Name'] == 'sub':
            return attribute['Value']


def normalize_phone(phone):
    digits_phone = re.sub('\\D+', '', phone)
    if len(digits_phone) < 11:
        digits_phone = "+1" + digits_phone
    if len(digits_phone) >= 11 and not digits_phone.startswith("+"):
        digits_phone = "+" + digits_phone
    try:
        parsed_phone = phonenumbers.parse(digits_phone)
        if not phonenumbers.is_valid_number(parsed_phone):
            raise Exception()
        return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        print(f'Bad phone number format {phone}')
        return None


def get_or_create_cognito_sub(phone):
    try:
        user = cognito_client.admin_create_user(
            UserPoolId=PROVIDER_USER_POOL_ID,
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
                UserPoolId=PROVIDER_USER_POOL_ID,
                AttributesToGet=[],
                Filter=f'phone_number ^= \"{phone}\"'
            )
            if users.get('Users') is not None and users.get('Users'):
                user = users.get('Users')[0]
                return user['Username']
            raise client_error
        else:
            raise client_error
    except Exception as error:
        print(error)
        raise error


def update(cognito_subs):
    conn = pg_database_conn()
    logger.info('cognito_subs: ', cognito_subs)
    try:
        with conn.cursor() as cur:
            execute_values(cur, """UPDATE workforce.provider as provider
                                      SET cognito_sub = update_payload.cognito_sub 
                                     FROM (VALUES %s) AS update_payload (ctms_id, cognito_sub) 
                                    WHERE provider.ctms_id = update_payload.ctms_id""", cognito_subs)
    except Exception as error:
        print(error)
        exit(1)
    finally:
        if conn is not None:
            print("commit")
            conn.commit()
            conn.close()


def process_record(cognito_subs, record):
    ctms_id = record['ctms_id']
    debug_provider_cell_phone = record['cell_phone']

    if debug_provider_cell_phone == '206-637-8428':
        logger.info('Got bad provider in process_record before normalize_phone')

    phone = normalize_phone(record['cell_phone'])

    if debug_provider_cell_phone == '206-637-8428':
        logger.info('Got bad provider in process_record after normalize_phone')

    if phone:
        if debug_provider_cell_phone == '206-637-8428':
            logger.info('Got bad provider in process_record before get_or_create_cognito_sub')
        cognito_sub = get_or_create_cognito_sub(phone)
        if debug_provider_cell_phone == '206-637-8428':
            logger.info('Got bad provider in process_record after get_or_create_cognito_sub')
        print(
            f'Creating provider user for ctms_id: {ctms_id} phone: {phone} cognito_sub: {cognito_sub}')
        cognito_subs.append((ctms_id, cognito_sub))


def lambda_handler(event, context):
    connection = None
    try:
        connection = pg_database_conn()
        sql = """select ctms_id,
                        cell_phone
                   from workforce.provider 
                  where
                    status in ('Active', 'Prospect')
                    and cell_phone is not null
                    and cognito_sub is null"""
        with connection.cursor(name='fetch_active_providers', cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            cognito_subs = []
            while True:
                results = cur.fetchmany(250)
                if not results:
                    break
                for record in results:
                    process_record(cognito_subs, record)
                print('Processed records: %s' % cognito_subs)
                update(cognito_subs)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    finally:
        if connection is not None:
            connection.close()
