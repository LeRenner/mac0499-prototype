import hashlib
import base64


def tor_v3_address(public_key: bytes) -> str:
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
def get_onion_address_from_file(filename, version_byte):
    try:
        with open(filename, 'rb') as f:
            # Skip the first 32 bytes
            f.seek(32)
            # Read the public key from the file (should be 32 bytes)
            pubkey_bytes = f.read(32)
            if len(pubkey_bytes) != 32:
                raise ValueError("Invalid public key length in the file.")
            # Generate and return the onion address

            print(tor_v3_address(pubkey_bytes))

            return ed25519_to_onion_address(pubkey_bytes, version_byte)
    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage: Replace with the actual path to your hs_ed25519_public_key file
filename = "tor/data/hidden-service/hs_ed25519_public_key"  # Replace with the correct path

for version_byte in range(256):
    version_byte = bytes([version_byte])
    onion_address = get_onion_address_from_file(filename, version_byte)
    if onion_address:
        print(f"For version {version_byte.hex()}, onion address: {onion_address}")
    else:
        print(f"Failed to calculate the onion address for version {version_byte.hex()}.")
