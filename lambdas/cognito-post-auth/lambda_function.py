import datetime
import logging
import os
import sys

import psycopg2
from aws_secretsmanager_caching import SecretCache, InjectSecretString

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region_name = os.environ['AWS_REGION']
logger.info(region_name)
cache = SecretCache()


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


def lambda_handler(event, context):
    logger.info(event)
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            sql = "update workforce.client_facility_manager set last_login_date = %s where lower(email) = lower(%s)"
            cur.execute(sql, (datetime.datetime.now(), event['request']['userAttributes']['email']))
            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    finally:
        if conn is not None:
            conn.close()

    return event
