

# Example usage: Replace with the actual path to your hs_ed25519_public_key file
filename = "tor/data/hidden-service/hs_ed25519_public_key"  # Replace with the correct path

for version_byte in range(256):
    version_byte = bytes([version_byte])
    onion_address = get_onion_address_from_file(filename, version_byte)
    if onion_address:
        print(f"For version {version_byte.hex()}, onion address: {onion_address}")
    else:
        print(f"Failed to calculate the onion address for version {version_byte.hex()}.")
