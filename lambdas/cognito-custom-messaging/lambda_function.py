import logging
import os
import sys

import psycopg2
from aws_secretsmanager_caching import SecretCache, InjectSecretString
from jinja2 import FileSystemLoader, Environment, select_autoescape

logger = logging.getLogger()
logger.setLevel(logging.INFO)

domain = os.environ['APP_DOMAIN']
region_name = os.environ['AWS_REGION']

cache = SecretCache()

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)


@InjectSecretString(os.environ['DB_URL'], cache)
@InjectSecretString(os.environ['DB_USERNAME'], cache)
@InjectSecretString(os.environ['DB_PASSWORD'], cache)
def get_connection(password, username, jdbc_url):
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


def get_facility_name_by_manager(facility_manager_email):
    sql = """
        select name 
          from workforce.client_facility cf 
    inner join workforce.client_facility_manager cfm on cf.id = cfm.client_facility_id 
         where lower(cfm.email) = lower(%s)
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (facility_manager_email,))
            record = cur.fetchone()
            if record:
                return record[0]
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        raise error
    finally:
        if conn is not None:
            conn.close()
    raise Exception(f"Cannot find facility manager with email {facility_manager_email}")

def get_facility_manager_by_email(facility_manager_email):
    sql = """
        select CONCAT(first_name, ' ', last_name) AS full_name
          from workforce.client_facility_manager cfm
         where lower(cfm.email) = lower(%s)
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (facility_manager_email,))
            record = cur.fetchone()
            if record:
                return record[0]
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        raise error
    finally:
        if conn is not None:
            conn.close()
    raise Exception(f"Cannot find facility manager with email {facility_manager_email}")


def confirm_sign_up(request):
    email = request.get('userAttributes').get('email')
    code = request.get('codeParameter')
    template = env.get_template('confirm_sign_up.html')
    output = template.render({
        'email_title': 'Signup Confirmation',
        'user_name': request.get('usernameParameter'),
        'actrusfm_url': domain,
        'verification_code': code,
        'facility_name': get_facility_name_by_manager(email),
        'facility_manager_name': get_facility_manager_by_email(email)
    })
    return {
        'emailSubject': 'Signup Confirmation',
        'emailMessage': output
    }


def recover_password(request):
    email = request.get('userAttributes').get('email')
    code = request.get('codeParameter')
    template = env.get_template('recover_password.html')
    output = template.render({
        'user_name': email,
        'reset_link': f'{domain}/auth/reset-password?email={email}&code={code}',
        'actrusfm_url': domain
    })
    return {
        'emailSubject': 'Password Recovery',
        'emailMessage': output
    }


def lambda_handler(event, context):
    logger.info(event)
    if event.get('request').get('userAttributes') is None:
        return event

    if event.get('triggerSource') == "CustomMessage_AdminCreateUser":
        event['response'] = confirm_sign_up(event.get('request'))

    if event.get('triggerSource') == "CustomMessage_ForgotPassword":
        event['response'] = recover_password(event.get('request'))
    return event
