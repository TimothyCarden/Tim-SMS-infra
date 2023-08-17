import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')

facility_manager_user_pool_id = os.environ.get('FACILITY_MANAGER_USER_POOL_ID')


def switch_user_enabled(email, activate):
    if activate:
        cognito_client.admin_disable_user(
            UserPoolId=facility_manager_user_pool_id,
            Username=email
        )
    else:
        cognito_client.admin_enable_user(
            UserPoolId=facility_manager_user_pool_id,
            Username=email
        )


def lambda_handler(event, context):
    logger.info(event)
    email = event.get("email")
    activate = event.get("activate")

    switch_user_enabled(email, activate)

    return {
        "StatusCode": 200,
        "Payload": json.dumps({"status": "SUCCESS"})
    }
