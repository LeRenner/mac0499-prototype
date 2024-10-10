import hashlib
import base64
from nacl.signing import SigningKey

TOR_PRIVATE_KEY_FILE = "tor/data/hidden-service/hs_ed25519_secret_key"
TOR_PUBLIC_KEY_FILE = "tor/data/hidden-service/hs_ed25519_public_key"

global public_key
global private_key

def signMessage(message: str) -> str:
    global private_key
    if private_key is None:
        raise ValueError("Private key is not initialized.")

    # Create a SigningKey object from the private key
    signing_key = SigningKey(private_key[:32])  # Ed25519 private key is the first 32 bytes

    # Sign the message
    signed_message = signing_key.sign(message.encode('utf-8'))

    # Extract the signature
    signature = signed_message.signature

    # Encode the signature in base64
    signature_base64 = base64.b64encode(signature).decode('utf-8')

    return signature_base64


def verifyMessage(message: str, signature: str, public_key: bytes) -> bool:
    # Create a VerifyKey object from the public key
    verify_key = VerifyKey(public_key)

    # Decode the signature from base64
    signature_bytes = base64.b64decode(signature)

    # Verify the message
    try:
        verify_key.verify(message.encode('utf-8'), signature_bytes)
        return True
    except BadSignatureError:
        return False


def encryptMessage(message: str, public_key: bytes) -> str:
    # Create a Box object from the public key and private key
    box = Box(private_key[:32], public_key)

    # Encrypt the message
    encrypted_message = box.encrypt(message.encode('utf-8'))

    # Encode the encrypted message in base64
    encrypted_message_base64 = base64.b64encode(encrypted_message).decode('utf-8')

    return encrypted_message_base64

def decryptMessage(encrypted_message: str, public_key: bytes) -> str:
    # Create a Box object from the public key and private key
    box = Box(private_key[:32], public_key)

    # Decode the encrypted message from base64
    encrypted_message_bytes = base64.b64decode(encrypted_message)

    # Decrypt the message
    decrypted_message = box.decrypt(encrypted_message_bytes)

    return decrypted_message.decode('utf-8')


def torAddressFromBase64(public_key_base64: str) -> str:
    # Decode the public key from base64
    public_key = base64.b64decode(public_key_base64)

    return generateTorAddress(public_key)


def publicKeyInBase64() -> str:
    global public_key
    if public_key is None:
        raise ValueError("Public key is not initialized.")

    # Encode the public key in base64
    public_key_base64 = base64.b64encode(public_key).decode('utf-8')

    return public_key_base64


def generateTorAddress(public_key: bytes) -> str:
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
def initializeTorKeys():
    global public_key, private_key
    try:
        # Read the public key
        with open(TOR_PUBLIC_KEY_FILE, 'rb') as f:
            # Skip the first 32 bytes
            f.seek(32)

            # Read the public key from the file (should be 32 bytes)
            pubkey_bytes = f.read(32)
            if len(pubkey_bytes) != 32:
                raise ValueError("Invalid public key length in the file.")
            public_key = pubkey_bytes

        # Read the private key
        with open(TOR_PRIVATE_KEY_FILE, 'rb') as f:
            # Skip the first 32 bytes
            f.seek(32)

            # Read the private key from the file (should be 64 bytes)
            privkey_bytes = f.read(64)
            if len(privkey_bytes) != 64:
                raise ValueError("Invalid private key length in the file.")
            private_key = privkey_bytes

        return generateTorAddress(public_key)
    except Exception as e:
        print(f"Error: {e}")
        return None