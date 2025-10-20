from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
import requests
from open_webui.env import GLOBAL_LOG_LEVEL
import logging


logging.basicConfig(level=GLOBAL_LOG_LEVEL, force=True)
log = logging.getLogger(__name__)
log.setLevel(GLOBAL_LOG_LEVEL)


def validate_keycloak_jwt(
    token: str, public_key: str, audience: str, issuer: str
) -> Optional[dict[str, any]]:
    try:
        decoded_token = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],  # Keycloak typically uses RS256
            audience=audience,
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )
        return decoded_token
    except ExpiredSignatureError:
        log.exception("Token has expired.")
        return None
    except InvalidTokenError as e:
        log.exception(f"Invalid token: {e}")
        return None
    except DecodeError as e:
        log.exception(f"Error decoding token: {e}")
        return None


def getKeycloakPublicKey(keycloakURL: str) -> Optional[dict[str, any]]:
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.request("GET", keycloakURL, headers=headers)
    except Exception as e:
        log.exception(f"Refresh token error: {e}")
        return None

    try:
        resp_json = resp.json()
    except Exception as e:
        log.exception(f"Failed to parse refresh token response: {e}")
        return None
    return resp_json


def makePEMKey(publicKey: str) -> str:
    publicKey = (
        """-----BEGIN PUBLIC KEY-----\n"""
        + publicKey
        + """\n-----END PUBLIC KEY-----"""
    )
    return publicKey


def decode_token(token: str) -> Optional[dict]:
    try:
        options = {"verify_signature": False}
        decoded = jwt.decode(token, options=options)  # works in PyJWT >= v2.0
        return decoded
    except Exception:
        return None


def decodeAndValidateToken(token: str, issuer: str = "") -> Optional[dict[str, any]]:
    decoded = decode_token(token)
    if not decode_token:
        return None

    if not issuer:
        issuer = decoded.get("iss", "")
        if not issuer:
            return None

    k = getKeycloakPublicKey(issuer)
    if not k:
        return None

    public_key = k.get("public_key", "")
    if not public_key:
        return None

    public_key = makePEMKey(public_key)

    audience = decoded.get("aud", "")
    if not audience:
        return None

    decodedAndVerifiedPayload = validate_keycloak_jwt(
        token, public_key, audience, issuer
    )
    return decodedAndVerifiedPayload


# iis = 'https://kck-box-dev.k2g.ai/realms/openweb-ui'

# token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJxS3prZFFSaUI4Q05UejBQQ3pQSTBySEJidlpra3FJN3BVNFJPd2R1QVlzIn0.eyJleHAiOjE3NTM3MTcxMzEsImlhdCI6MTc1MzcxNjgzMSwiYXV0aF90aW1lIjoxNzUzNzEwOTcyLCJqdGkiOiIxNjRkYWYzYi03ODExLTRmNDYtODFjMS02ZGI3YTZiOTI1M2IiLCJpc3MiOiJodHRwczovL2tjay1ib3gtZGV2LmsyZy5haS9yZWFsbXMvb3BlbndlYi11aSIsImF1ZCI6Im9wZW53ZWItdWkiLCJzdWIiOiJmMjY0OWU2Ni1mMzIyLTRkZTUtOTkyNC0wMmQyNTU1NTMzMGMiLCJ0eXAiOiJJRCIsImF6cCI6Im9wZW53ZWItdWkiLCJzaWQiOiIxNzYzNzkxMC03NGNmLTQxMjUtOTU2Ny1iYmM1YjFlMzI4YWYiLCJhdF9oYXNoIjoiWVA0eXBMbEo1UFVCMlpnSWVnQmJTQSIsImFjciI6IjEiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmFtZSI6IkFuZHJpaSBTaHlyaWFpZXYiLCJncm91cHMiOlsiL3RyaWFsIl0sInByZWZlcnJlZF91c2VybmFtZSI6ImEuc2h5cmlhaWV2QGsyZy5haSIsImdpdmVuX25hbWUiOiJBbmRyaWkiLCJmYW1pbHlfbmFtZSI6IlNoeXJpYWlldiIsImVtYWlsIjoiYS5zaHlyaWFpZXZAazJnLmFpIn0.CwBy3rRGsoPsCIgAv1TIKe8nm3jwUPzZzoolh_S4zGJg07-viVqu1JyV-WC-3JnwFAfBY_4j1DFI8iARmpxSIsgQ8nMAFibYDs5A9d_ei63MSiBNXMWacNyPoKEerMSNfFYcGcZihlxRudQ7EkPgz81VbubbwoUyFA5cdTbdhMPONgmN3cxkQf9Xt6XGK7ZYFzPpkqAaNCLjntiFoTu0b8Bi1MzYJgPG0rGbkEFOKueJGYBdq65vSreG4x086essZvK7_z40iYa1DhYQPrecLTZTQaiSOm4JUqysAKUPrRj4dB4A9S0DqhFUF1qR6Wy5qtvZOCCgty4RxqjVjQyxCQ"
# decoded_payload = decodeAndValidateToken(token, iis)
# if decoded_payload:
#     log.debug("Token is valid. Decoded payload:", decoded_payload)
# else:
#     log.debug("Token is not valid.")
