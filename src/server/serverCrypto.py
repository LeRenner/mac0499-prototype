import hashlib
import base64

from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder
from pytor.ed25519 import Ed25519
from .jsonOperator import *
import json

TOR_PRIVATE_KEY_FILE = "tor/data/hidden-service/hs_ed25519_secret_key"
TOR_PUBLIC_KEY_FILE = "tor/data/hidden-service/hs_ed25519_public_key"

global private_key_seed
global private_key_signing_key_object
global public_tor_key
global public_signing_key
global address

def crypto_getOwnAddress() -> str:
    global address
    return address


def crypto_getOwnPublicKey() -> str:
    global public_signing_key
    return base64.b64encode(public_signing_key.encode(RawEncoder)).decode('utf-8')


def crypto_signMessage(message: str) -> str:
    # Sign the message
    signed_message = private_key_signing_key_object.sign(message.encode('utf-8'))

    # Encode the signature in base64
    signature = base64.b64encode(signed_message.signature).decode('utf-8')

    return signature


def crypto_verifyMessage(message: str, signature: str, originAddress: str) -> bool:

    # Get the public key from the origin address
    public_key = base64.b64decode(operator_getPublicKeyFromAddress(originAddress))

    # Create a VerifyKey object from the public key
    verify_key = VerifyKey(public_key)

    # Decode the signature from base64
    signature_bytes = base64.b64decode(signature)

    # Verify the message
    try:
        verify_key.verify(message.encode('utf-8'), signature_bytes)
        print("Message signature verified.")
        return True
    except Exception as e:
        print("Message verification failed.")
        print(f"Error: {e}")
        return False


def crypto_generateTorAddress(public_key: bytes) -> str:
    if len(public_key) != 32:
        raise ValueError("Public key must be 32 bytes long.")

    # Version byte for Tor v3 addresses (0x03)
    version = bytes([0x03])

    # Calculate the checksum
    checksum_prefix = b".onion checksum"
    hash_input = checksum_prefix + public_key + version
    checksum = hashlib.sha3_256(hash_input).digest()[:2]  # First two bytes of the SHA3-256 hash

    # Combine public key, checksum, and version
    onion_bytes = public_key + checksum + version

    # Encode in base32 without padding and convert to lowercase
    onion_address = base64.b32encode(onion_bytes).decode('utf-8').lower().strip('=') + ".onion"

    return onion_address


# Function to read the hs_ed25519_public_key and hs_ed25519_secret_key files and return the onion address
def crypto_initializeTorKeys():
    global private_key_seed, public_tor_key, public_signing_key, address, private_key_signing_key_object
    try:
        # Read the private key
        with open(TOR_PRIVATE_KEY_FILE, 'rb') as f:
            # Skip the first 32 bytes
            f.seek(32)

            # Read the private key from the file (should be 64 bytes)
            privkey_seed = f.read(32)
            if len(privkey_seed) != 32:
                raise ValueError("Invalid private key length in the file.")
            private_key_seed = privkey_seed

        priv_key_array = bytearray(private_key_seed)
        public_tor_key = Ed25519().public_key_from_hash(priv_key_array)
        address = crypto_generateTorAddress(public_tor_key)
        private_key_signing_key_object = SigningKey(private_key_seed)
        public_signing_key = private_key_signing_key_object.verify_key
    except Exception as e:
        print(f"Error: {e}")
        return None