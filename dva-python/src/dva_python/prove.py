import jwt
from jwt import InvalidSignatureError, ExpiredSignatureError
from structlog import get_logger

logger = get_logger()

def verify_attestation(jws_token, public_key):
    try:        
        payload = jwt.decode(jws_token, public_key, algorithms=['RS256'])
        logger.info("Attestation successfully verified.")
        return payload
    except InvalidSignatureError:
        logger.warning("Invalid signature detected during verification.")
        return None
    except ExpiredSignatureError:
        logger.warning("Signature has expired.")
        return None
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise e


