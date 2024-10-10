import hashlib
import base64


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


# Function to read the hs_ed25519_public_key file and return the onion address
def initializeTorKeys():
    try:
        with open(filename, 'rb') as f:
            # Skip the first 32 bytes
            f.seek(32)

            # Read the public key from the file (should be 32 bytes)
            pubkey_bytes = f.read(32)
            if len(pubkey_bytes) != 32:
                raise ValueError("Invalid public key length in the file.")

            return tor_v3_address(pubkey_bytes)
    except Exception as e:
        print(f"Error: {e}")
        return None