import logging
import secrets
import string

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

otp_length = 6

client = boto3.client('sns')


def lambda_handler(event, context):
    logger.info("CUSTOM_CHALLENGE_LAMBDA: %s", event['request'])
    alphabet = string.digits
    otp = ''.join(secrets.choice(alphabet) for _ in range(otp_length))

    client.publish(
        Message=f'{otp} is your verification code for Actriv',
        PhoneNumber=event['request']['userAttributes']['phone_number']
    )

    event['response']['privateChallengeParameters'] = dict()
    event['response']['privateChallengeParameters']['otp'] = otp
    return event
