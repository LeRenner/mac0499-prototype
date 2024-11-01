import hashlib
import base64
import json

from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey, Box
from time import sleep
from .jsonOperator import *
from nacl.public import PublicKey, SealedBox

global privateSigningKey, privateEncryptionKey, publicSigningKey, publicEncryptionKey, address

TOR_PRIVATE_KEY_FILE = "tor/data/hidden-service/hs_ed25519_secret_key"
TOR_PUBLIC_KEY_FILE = "tor/data/hidden-service/hs_ed25519_public_key"
address = None


def crypto_getOwnAddress() -> str:
    global address

    while address is None:
        sleep(1)

    return address


def crypto_getOwnPublicKey() -> str:
    keyObj = {
        "publicSigningKey": publicSigningKey.encode(encoder=HexEncoder).decode('utf-8'),
        "publicEncryptionKey": publicEncryptionKey.encode(encoder=HexEncoder).decode('utf-8')
    }

    return json.dumps(keyObj)


def crypto_signMessage(message: str) -> str:
    # Sign the message
    signedMessage = privateSigningKey.sign(message.encode('utf-8'))

    # Encode the signature in base64
    signature = base64.b64encode(signedMessage.signature).decode('utf-8')

    return signature


def crypto_encryptMessage(message: str, destAddress: str) -> str:
    # Get the public key from the destination address
    public_key_hex = operator_getPublicKeyFromAddress(destAddress)["publicEncryptionKey"]

    public_key = PublicKey(public_key_hex, encoder=HexEncoder)

    # Create a SealedBox object for encryption
    sealed_box = SealedBox(public_key)

    # Encrypt the message
    encrypted_message = sealed_box.encrypt(message.encode('utf-8'))

    # Encode the encrypted message in base64
    encrypted_message_b64 = base64.b64encode(encrypted_message).decode('utf-8')

    return encrypted_message_b64


def crypto_decryptMessage(encryptedMessage: str) -> str:
    public_keys = json.loads(crypto_getOwnPublicKey())
    public_signing_key = base64.b64decode(public_keys["publicSigningKey"])

    # Create a SealedBox object for decryption
    box = SealedBox(privateEncryptionKey)

    # Decode the encrypted message from base64
    encrypted_message = base64.b64decode(encryptedMessage)

    # Decrypt the message
    decrypted_message = box.decrypt(encrypted_message)

    return decrypted_message.decode('utf-8')


def crypto_verifyMessage(message: str, signature: str, originAddress: str) -> bool:
    public_key_hex = operator_getPublicKeyFromAddress(originAddress)["publicSigningKey"]

    # Create a VerifyKey object from the public key
    verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)

    # Decode the signature from base64
    signature_bytes = base64.b64decode(signature)

    # Verify the message
    try:
        verify_key.verify(message.encode('utf-8'), signature_bytes)
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
    global privateSigningKey, privateEncryptionKey, publicSigningKey, publicEncryptionKey, address
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

        # Read the public key
        with open(TOR_PUBLIC_KEY_FILE, 'rb') as f:
            # skip the first 32 bytes
            f.seek(32)

            # Read the public key from the file (should be 32 bytes)
            public_key = f.read(32)
            if len(public_key) != 32:
                raise ValueError("Invalid public key length in the file.")
            public_tor_key = public_key

        address = crypto_generateTorAddress(public_tor_key)

        privateSigningKey = SigningKey(private_key_seed)
        privateEncryptionKey = PrivateKey(private_key_seed)
        publicSigningKey = privateSigningKey.verify_key
        publicEncryptionKey = privateEncryptionKey.public_key
        
    except Exception as e:
        print(f"Error: {e}")
        return None
