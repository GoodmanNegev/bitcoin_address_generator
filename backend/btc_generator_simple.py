import hashlib
import secrets
import string
from typing import Optional, Tuple

class SimpleBitcoinAddressGenerator:
    """
    Simplified Bitcoin address generator for educational purposes.
    Uses only Python standard library.
    
    Note: This is a simplified implementation for learning purposes.
    Real Bitcoin address generation requires proper cryptographic libraries.
    """
    
    def __init__(self):
        # Base58 alphabet used by Bitcoin
        self.base58_alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        self.bech32_alphabet = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    
    def generate_private_key(self) -> bytes:
        """Generate a secure random 32-byte private key"""
        return secrets.token_bytes(32)
    
    def hash160(self, data: bytes) -> bytes:
        """RIPEMD160(SHA256(data)) - simplified version"""
        # Since RIPEMD160 is not in standard library, we'll use SHA256 for demo
        # In real implementation, you need proper RIPEMD160
        sha256_hash = hashlib.sha256(data).digest()
        # Using SHA256 as a substitute (THIS IS NOT SECURE FOR REAL USE)
        return hashlib.sha256(sha256_hash).digest()[:20]
    
    def hash256(self, data: bytes) -> bytes:
        """Double SHA256"""
        return hashlib.sha256(hashlib.sha256(data).digest()).digest()
    
    def base58_encode(self, data: bytes) -> str:
        """Simple Base58 encoding implementation"""
        # Convert bytes to integer
        num = int.from_bytes(data, 'big')
        
        # Encode
        encoded = ''
        while num > 0:
            num, remainder = divmod(num, 58)
            encoded = self.base58_alphabet[remainder] + encoded
        
        # Handle leading zeros
        for byte in data:
            if byte == 0:
                encoded = '1' + encoded
            else:
                break
        
        return encoded
    
    def bech32_encode(self, data: bytes, prefix: str = 'bc') -> str:
        """Simplified Bech32 encoding for demo purposes"""
        # This is a very simplified version - real Bech32 is more complex
        encoded_data = ''
        for byte in data:
            encoded_data += self.bech32_alphabet[byte % 32]
        
        return f"{prefix}1{encoded_data}"
    
    def create_mock_address(self, address_type: str, seed: bytes) -> str:
        """Create mock address for educational purposes"""
        # Use hash of seed to generate deterministic but pseudo-random address
        hash_result = hashlib.sha256(seed).digest()
        
        if address_type == "p2pkh":
            # Legacy address starting with '1'
            return '1' + self.base58_encode(hash_result[:20])
        
        elif address_type == "p2sh-p2wpkh":
            # Nested SegWit starting with '3'
            return '3' + self.base58_encode(hash_result[1:21])
        
        elif address_type == "p2wpkh":
            # Native SegWit starting with 'bc1q'
            return self.bech32_encode(hash_result[:20])
        
        elif address_type == "p2tr":
            # Taproot starting with 'bc1p'
            return 'bc1p' + self.bech32_encode(hash_result[:32])[3:]
        
        else:
            raise ValueError(f"Unsupported address type: {address_type}")
    
    def private_key_to_wif(self, private_key: bytes) -> str:
        """Convert private key to Wallet Import Format (WIF) - simplified"""
        # Simplified WIF format for demo
        wif_data = b'\x80' + private_key + b'\x01'
        checksum = self.hash256(wif_data)[:4]
        return self.base58_encode(wif_data + checksum)
    
    def generate_address(self, address_type: str, private_key: bytes = None) -> Tuple[str, str]:
        """Generate address of specified type"""
        if private_key is None:
            private_key = self.generate_private_key()
        
        address = self.create_mock_address(address_type, private_key)
        private_key_wif = self.private_key_to_wif(private_key)
        
        return address, private_key_wif
    
    def check_pattern_match(self, address: str, pattern: str, position: str) -> bool:
        """Check if address matches the pattern at specified position"""
        if not pattern:
            return True
        
        pattern = pattern.lower()
        address_lower = address.lower()
        
        if position == "start":
            # Skip the address prefix (1, 3, bc1)
            if address_lower.startswith('bc1'):
                search_part = address_lower[4:] if address_lower.startswith('bc1p') else address_lower[3:]
            else:
                search_part = address_lower[1:]
            return search_part.startswith(pattern)
        
        elif position == "end":
            return address_lower.endswith(pattern)
        
        elif position == "middle":
            # Check if pattern appears anywhere in the address (excluding prefix)
            if address_lower.startswith('bc1'):
                search_part = address_lower[4:] if address_lower.startswith('bc1p') else address_lower[3:]
            else:
                search_part = address_lower[1:]
            return pattern in search_part
        
        return False

# For backwards compatibility
BitcoinAddressGenerator = SimpleBitcoinAddressGenerator