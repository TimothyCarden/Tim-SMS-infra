import json
import logging
import os
import sys

import boto3
import psycopg2
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region_name = os.environ['AWS_REGION']

session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name,
)

cognito_client = boto3.client('cognito-idp')

facility_user_pool_id = os.environ.get('FACILITY_USER_POOL_ID')
domain_name = os.environ.get('CORS_DOMAIN_NAME')


def get_secret(secret_name):
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error("The requested secret " + secret_name + " was not found")
        elif err.response['Error']['Code'] == 'InvalidRequestException':
            logger.error("The request was invalid due to:", err)
        elif err.response['Error']['Code'] == 'InvalidParameterException':
            logger.error("The request had invalid params:", err)
        elif err.response['Error']['Code'] == 'DecryptionFailure':
            logger.error("The requested secret can't be decrypted using the provided KMS key:", err)
        elif err.response['Error']['Code'] == 'InternalServiceError':
            logger.error("An error occurred on service side:", err)
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
        connect = psycopg2.connect(dsn=jdbc_url[5:jdbc_url.index('?')], user=username, password=password,
                                   connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS PostgreSQL instance succeeded")
        return connect
    except psycopg2.Error as e:
        logger.error("ERROR: Unexpected error: Could not connect to PostgreSQL instance.")
        logger.error(e)
        sys.exit()


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


def get_cognito_user(email):
    try:
        return cognito_client.admin_get_user(
            UserPoolId=facility_user_pool_id,
            Username=email
        )
    except Exception as e:
        logger.error(e)
    return None


def search_manager_internal(email):
    conn = None
    try:
        logger.info(f"Trying to find a user by email: {email}")
        if not email:
            return send_message_response("Missed required parameter: email", 400)
        conn = get_connection()
        with conn.cursor() as cur:
            sql = """
                    select 
                            m.first_name as manager_first_name, 
                            m.last_name as manager_last_name, 
                            m.ctms_status as manager_status, 
                            f.name as facility_name  
                       from workforce.client_facility_manager m 
                 inner join workforce.client_facility f on m.client_facility_id = f.id
                      where lower(m.email) = lower(%s);
                """
            cur.execute(sql, (email,))
            record = cur.fetchone()
            if record:
                logger.info(record)
                return Manager(email, record[0], record[1], record[2], record[3])
            else:
                return None
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        raise error
    finally:
        if conn is not None:
            conn.close()


def invite_manager(body, query_parameters):
    data = json.loads(body)
    email = data.get("email", None)
    if not email:
        return send_message_response("Missed required parameter: email", 400)
    manager = search_manager_internal(email)
    if not manager:
        return send_message_response(f"Provided email: {email} doesn't associated with facility manager", 404)
    user = get_cognito_user(email)
    if user:
        if user["UserStatus"] != 'FORCE_CHANGE_PASSWORD':
            return send_message_response("User has already been registered", 400)
        cognito_client.admin_create_user(
            UserPoolId=facility_user_pool_id,
            Username=email,
            MessageAction='RESEND',
            DesiredDeliveryMediums=['EMAIL']
        )
    else:
        cognito_client.admin_create_user(
            UserPoolId=facility_user_pool_id,
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
            DesiredDeliveryMediums=['EMAIL']
        )
    return send_message_response("Invite sent", 200)


def recovery_password(body, query_parameters):
    data = json.loads(body)
    email = data.get("email", None)
    if not email:
        return send_message_response("Missed required parameter: email", 400)
    user = get_cognito_user(email)
    if not user:
        return send_message_response("User doesn't exist", 400)

    cognito_client.admin_reset_user_password(
        UserPoolId=facility_user_pool_id,
        Username=email
    )
    return send_message_response("Sent password reset", 200)


def search_manager(body, query_parameters):
    manager = search_manager_internal(query_parameters.get("email", None))
    if manager:
        return send_data_response(manager.__dict__, 200)
    else:
        return send_message_response("Facility manager not found", 404)


def lambda_handler(event, context):
    logger.info(event)
    try:
        is_admin = event["requestContext"]["authorizer"]["claims"]["cognito:groups"] == 'admin'
    except (KeyError, TypeError):
        return send_message_response("Not Authorized", 403)

    if not is_admin:
        return send_message_response("Not Authorized", 403)

    operation = f"{event['httpMethod']}:{event.get('pathParameters', {}).get('proxy', None)}"
    logger.info(operation)
    # define the functions used to perform the CRUD operations
    operations = {
        'POST:users/invite': invite_manager,
        'POST:users/recovery': recovery_password,
        'GET:users/search': search_manager
    }

    if operation in operations:
        try:
            return operations[operation](event.get('body'), event.get('queryStringParameters'))
        except Exception as e:
            logger.error(e)
            return send_message_response("Something went wrong", 400)
    else:
        return send_message_response("Not Found", 404)


class Manager:
    manager_email = None
    manager_fist_name = None
    manager_last_name = None
    manager_status = None
    facility_name = None

    def __init__(self, manager_email, manager_fist_name, manager_last_name, manager_status, facility_name):
        self.manager_email = manager_email
        self.manager_fist_name = manager_fist_name
        self.manager_last_name = manager_last_name
        self.manager_status = manager_status
        self.facility_name = facility_name
