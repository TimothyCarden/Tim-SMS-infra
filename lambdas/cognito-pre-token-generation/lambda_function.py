import logging
import os
import sys

import boto3
import psycopg2
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region_name = os.environ['AWS_REGION']
logger.info(region_name)

session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name,
)


def get_secret(secret_name):
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif err.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", err)
        elif err.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", err)
        elif err.response['Error']['Code'] == 'DecryptionFailure':
            print("The requested secret can't be decrypted using the provided KMS key:", err)
        elif err.response['Error']['Code'] == 'InternalServiceError':
            print("An error occurred on service side:", err)
    else:
        # Secrets Manager decrypts the secret value using the associated KMS CMK
        # Depending on whether the secret was a string or binary, only one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return get_secret_value_response['SecretBinary']


# rds settings
jdbc_url = get_secret(os.environ['DB_URL'])
username = get_secret(os.environ['DB_USERNAME'])
password = get_secret(os.environ['DB_PASSWORD'])


def get_connection():
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


def lambda_handler(event, context):
    logger.info(event)
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            email = event['request']['userAttributes']['email']
            sql = """select cf.id, cf.ctms_id,cf.company_client_facility_id
                     from workforce.client_facility_manager cfm
                     left join workforce.client_facility cf on cfm.client_facility_id = cf.id
                     where lower(cf.status) = 'active' and  lower(cfm.email) = lower(%s) and lower(cfm.ctms_status) = 'active'"""
            cur.execute(sql, [email])
            records = cur.fetchall()
            if len(records) > 1:
                raise Exception(f"More than one manager with email: {email}")
            if len(records) == 0:
                raise Exception(f"Manager with email: {email} doesn't exist")
            record = records[0]
            logger.info(record)
            event['response']['claimsOverrideDetails'] = {
                'claimsToAddOrOverride': {
                    'facility_id': record[0],
                    'facility_ctms_id': record[1],
                    'company_facility_id': record[2] if record[2] else "-1"
                }
            }
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    finally:
        if conn is not None:
            conn.close()

    return event
