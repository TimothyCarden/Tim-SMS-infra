import json
import logging
import os
import sys

import boto3
import psycopg2

from botocore.exceptions import ClientError
from aws_secretsmanager_caching import SecretCache, InjectSecretString

logger = logging.getLogger()
logger.setLevel(logging.INFO)

domain_name = os.environ.get('CORS_DOMAIN_NAME')

region_name = os.environ['AWS_REGION']
account_id = os.environ['AWS_ACCOUNT_ID']
quicksight_namespace = os.environ['QUICKSIGHT_NAMESPACE']
facility_resource_arn = os.environ['FACILITY_RESOURCE_ARN']
facility_dashboard_id = os.environ['FACILITY_DASHBOARD_ID']
company_resource_arn = os.environ['COMPANY_RESOURCE_ARN']
company_dashboard_id = os.environ['COMPANY_DASHBOARD_ID']
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


cache = SecretCache()


@InjectSecretString(os.environ['DB_URL'], cache)
@InjectSecretString(os.environ['DB_USERNAME'], cache)
@InjectSecretString(os.environ['DB_PASSWORD'], cache)
def get_connection(password, username, jdbc_url):
    try:
        logger.info("getting connection from db")
        logger.info("getting connection from db - url : %s" % jdbc_url)
        logger.info("getting connection from db - user: %s" % username)
        conn = psycopg2.connect(dsn=jdbc_url[5:jdbc_url.index('?')], user=username, password=password,
                                connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS PostgreSQL instance succeeded")
        return conn
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


def unauthorized():
    return {
        'statusCode': 401,
        'headers': {"Access-Control-Allow-Origin": domain_name, "Access-Control-Allow-Headers": "Content-Type"},
        'body': json.dumps({"message": "Access denied"}),
        'isBase64Encoded': bool('false')
    }


def get_children_from_claim(event):
    children = event.get("requestContext").get("authorizer").get("claims").get("company_children")
    if children:
        return [int(i) for i in children.split(",")]
    else:
        return []


def get_ctms_id_by_id(actrus_id):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            sql = "select id from workforce.client_facility where ctms_id = %s"
            cur.execute(sql, [int(actrus_id)])
            records = cur.fetchall()
            if len(records) == 0:
                raise Exception(f"Facility with ctms id {actrus_id} doesn't exist")
            return records[0]['id']
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    finally:
        if conn is not None:
            conn.close()


def get_embedding_url(sessionTags, dashboard_id, resource_arns):
    try:
        response = quicksight_client.generate_embed_url_for_anonymous_user(
            AwsAccountId=account_id,
            Namespace=quicksight_namespace,
            AuthorizedResourceArns=[resource_arns],
            ExperienceConfiguration={"Dashboard": {"InitialDashboardId": dashboard_id}},
            SessionTags=sessionTags,
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


def get_facility_embedding_url(event):
    ctms_user_facility = event.get("requestContext").get("authorizer").get("claims").get("facility_ctms_id")
    user_facility = event.get("requestContext").get("authorizer").get("claims").get("facility_id")
    query_facility = event["queryStringParameters"]['facility'] if event["queryStringParameters"] else None

    if not query_facility or query_facility == user_facility:
        return get_embedding_url([{"Key": " customer_id", "Value": ctms_user_facility}],
                                 facility_dashboard_id, facility_resource_arn)

    is_company = event.get("requestContext").get("authorizer").get("claims").get("is_company")
    children = get_children_from_claim(event)
    is_actriv_admin = event.get("requestContext").get("authorizer").get("claims").get("is_actriv_admin")

    if is_actriv_admin == "true" or (is_company == "true" and int(query_facility) in children):
        return get_embedding_url([{"Key": " customer_id", "Value": get_ctms_id_by_id(query_facility)}],
                                 facility_dashboard_id, facility_resource_arn)
    logger.info("Unauthorized: is_actriv_admin %s, is_company %s, user_facility %s, query_facility %s" % (is_actriv_admin, is_company, user_facility, query_facility))
    return unauthorized()


def get_company_embedding_url(event):
    is_actriv_admin = event.get("requestContext").get("authorizer").get("claims").get("is_actriv_admin")
    if is_actriv_admin == "true":
        return get_company_embedding_url_admin(event)

    is_company = event.get("requestContext").get("authorizer").get("claims").get("is_company")

    if not is_company or is_company == "false":
        return unauthorized()

    user_facility = event.get("requestContext").get("authorizer").get("claims").get("facility_id")
    query_facility = event["queryStringParameters"]['facility'] if event["queryStringParameters"] else None
    if query_facility and query_facility != user_facility:
        return unauthorized()

    ctms_user_facility = event.get("requestContext").get("authorizer").get("claims").get("facility_ctms_id")
    return get_embedding_url([{"Key": " company_id", "Value": ctms_user_facility}], company_dashboard_id,
                             company_resource_arn)


def get_company_embedding_url_admin(event):
    ctms_user_facility = event.get("requestContext").get("authorizer").get("claims").get("facility_ctms_id")
    user_facility = event.get("requestContext").get("authorizer").get("claims").get("facility_ctms_id")
    query_facility = event["queryStringParameters"]['facility'] if event["queryStringParameters"] else None
    facility = get_ctms_id_by_id(query_facility) if query_facility else ctms_user_facility
    return get_embedding_url([{"Key": " company_id", "Value": facility}], company_dashboard_id,
                             company_resource_arn)


def lambda_handler(event, context):
    logger.info(event)

    operation = f"{event['httpMethod']}:{event.get('pathParameters', {}).get('proxy', None)}"
    logger.info(operation)
    # define the functions used to perform the CRUD operations
    operations = {
        'GET:dashboards': get_facility_embedding_url,
        'GET:dashboards/facility': get_facility_embedding_url,
        'GET:dashboards/company': get_company_embedding_url
    }

    if operation in operations:
        try:
            return operations[operation](event)
        except Exception:
            logger.exception("Problema")
            return send_message_response("Something went wrong", 400)
    else:
        return send_message_response("Not Found", 404)
