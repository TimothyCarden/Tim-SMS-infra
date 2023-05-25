import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(event["request"])
    try:
        expected_answer = event['request']['privateChallengeParameters']['otp']
    except:
        event['response']['answerCorrect'] = False
        return event

    event['response']['answerCorrect'] = event['request']['challengeAnswer'] == expected_answer

    return event

