# Python code snippet for verifying digital signatures or attestations (such as W3C Verifiable Credentials) 
# using cryptographic verification methods.

# How a data consumer (Alice) can verify an attestation (issued as a W3C Verifiable Credential or JWS token) 
#provided by a data provider (Bob)


import jwt      # PyJWT library, for handling JSON Web Signatures (JWS)
from jwt import InvalidSignatureError, ExpiredSignatureError

# Bob's public key (PEM format), known to Alice
BOB_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
YOUR_PUBLIC_KEY_HERE
-----END PUBLIC KEY-----
"""

# Attestation provided by Bob (JWT/JWS token)
bob_attestation_jws = "BOB_JWS_ATTESTATION_HERE"

# Function to verify attestation/signature by Alice
def verify_attestation(jws_token, public_key):
    try:
        # Decoding and verifying Bob's attestation (JWS token)
        payload = jwt.decode(jws_token, public_key, algorithms=['RS256'])
        print("Signature valid. Credential payload:")
        print(payload)
        return True
    except InvalidSignatureError:
        print("Invalid Signature! Verification failed.")
        return False
    except ExpiredSignatureError:
        print("Signature expired.")
        return False
    except Exception as e:
        print(f"Error verifying signature: {str(e)}")
        return False

# Example usage by Alice
if __name__ == '__main__':
    verified = verify_attestation(bob_attestation_jws, BOB_PUBLIC_KEY)
    if verified:
        print("Attestation verified successfully!")
    else:
        print("Attestation verification failed!")
