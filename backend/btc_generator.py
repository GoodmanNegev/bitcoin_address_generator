import hashlib
import secrets
import base58
import bech32
from ecdsa import SigningKey, SECP256k1
from typing import Optional, Tuple, List
import struct
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

class BitcoinAddressGenerator:
    def __init__(self):
        # Pre-compute some values for better performance
        self._secp256k1_curve = SECP256k1
        # Cache for reused hash objects
        self._ripemd160_cache = []
        self._sha256_cache = []
        
    def _get_ripemd160(self):
        """Get a fresh RIPEMD160 hash object"""
        # Always create a new hash object to avoid state issues
        return hashlib.new('ripemd160')
    
    def _return_ripemd160(self, hasher):
        """Return a RIPEMD160 hash object to cache (no-op now)"""
        # No longer caching to avoid state issues
        pass
    
    def _get_sha256(self):
        """Get a fresh SHA256 hash object"""
        # Always create a new hash object to avoid state issues
        return hashlib.sha256()
    
    def _return_sha256(self, hasher):
        """Return a SHA256 hash object to cache (no-op now)"""
        # No longer caching to avoid state issues
        pass
    
    def clear_cache(self):
        """Clear all cached hash objects to free memory"""
        self._ripemd160_cache.clear()
        self._sha256_cache.clear()
        print("Generator cache cleared")
    
    def generate_private_key(self) -> bytes:
        """Generate a secure random 32-byte private key"""
        return secrets.token_bytes(32)
    
    def private_key_to_public_key(self, private_key: bytes) -> bytes:
        """Convert private key to public key using SECP256k1"""
        sk = SigningKey.from_string(private_key, curve=SECP256k1)
        vk = sk.get_verifying_key()
        return b'\x04' + vk.to_string()
    
    def compress_public_key(self, public_key: bytes) -> bytes:
        """Convert uncompressed public key to compressed format"""
        if len(public_key) == 65 and public_key[0] == 0x04:
            x = public_key[1:33]
            y = public_key[33:65]
            # Check if y is even or odd
            if int.from_bytes(y, 'big') % 2 == 0:
                return b'\x02' + x
            else:
                return b'\x03' + x
        return public_key
    
    def hash160(self, data: bytes) -> bytes:
        """RIPEMD160(SHA256(data)) - optimized version"""
        # Use cached hash objects for better performance
        sha256_hasher = self._get_sha256()
        sha256_hasher.update(data)
        sha256_hash = sha256_hasher.digest()
        self._return_sha256(sha256_hasher)
        
        ripemd160_hasher = self._get_ripemd160()
        ripemd160_hasher.update(sha256_hash)
        result = ripemd160_hasher.digest()
        self._return_ripemd160(ripemd160_hasher)
        return result
    
    def hash256(self, data: bytes) -> bytes:
        """Double SHA256 - optimized version"""
        sha256_hasher1 = self._get_sha256()
        sha256_hasher1.update(data)
        first_hash = sha256_hasher1.digest()
        self._return_sha256(sha256_hasher1)
        
        sha256_hasher2 = self._get_sha256()
        sha256_hasher2.update(first_hash)
        result = sha256_hasher2.digest()
        self._return_sha256(sha256_hasher2)
        return result
    
    def create_p2pkh_address(self, public_key: bytes) -> str:
        """Create Legacy P2PKH address"""
        compressed_pubkey = self.compress_public_key(public_key)
        pubkey_hash = self.hash160(compressed_pubkey)
        
        # Add version byte (0x00 for mainnet)
        versioned_payload = b'\x00' + pubkey_hash
        
        # Calculate checksum
        checksum = self.hash256(versioned_payload)[:4]
        
        # Create address
        address_bytes = versioned_payload + checksum
        return base58.b58encode(address_bytes).decode('utf-8')
    
    def create_p2sh_p2wpkh_address(self, public_key: bytes) -> str:
        """Create Nested SegWit P2SH-P2WPKH address"""
        compressed_pubkey = self.compress_public_key(public_key)
        pubkey_hash = self.hash160(compressed_pubkey)
        
        # Create redeem script: OP_0 + pubkey_hash
        redeem_script = b'\x00\x14' + pubkey_hash
        redeem_script_hash = self.hash160(redeem_script)
        
        # Add version byte (0x05 for P2SH mainnet)
        versioned_payload = b'\x05' + redeem_script_hash
        
        # Calculate checksum
        checksum = self.hash256(versioned_payload)[:4]
        
        # Create address
        address_bytes = versioned_payload + checksum
        return base58.b58encode(address_bytes).decode('utf-8')
    
    def create_p2wpkh_address(self, public_key: bytes) -> str:
        """Create Native SegWit P2WPKH address"""
        compressed_pubkey = self.compress_public_key(public_key)
        pubkey_hash = self.hash160(compressed_pubkey)
        
        # Create bech32 address using the encode function
        address = bech32.encode('bc', 0, pubkey_hash)
        return address
    
    def create_p2tr_address(self, public_key: bytes) -> str:
        """Create Taproot P2TR address (simplified version)"""
        compressed_pubkey = self.compress_public_key(public_key)
        
        # For educational purposes, we'll use a simplified approach
        # In reality, Taproot addresses require more complex key tweaking
        x_coord = compressed_pubkey[1:33]
        
        # Create bech32m address (version 1) using the encode function
        # The bech32.encode function automatically uses bech32m for version 1+
        address = bech32.encode('bc', 1, x_coord)
        return address
    
    def generate_address(self, address_type: str, private_key: bytes = None) -> Tuple[str, str]:
        """Generate address of specified type"""
        if private_key is None:
            private_key = self.generate_private_key()
        
        public_key = self.private_key_to_public_key(private_key)
        private_key_wif = self.private_key_to_wif(private_key)
        
        if address_type == "p2pkh":
            address = self.create_p2pkh_address(public_key)
        elif address_type == "p2sh-p2wpkh":
            address = self.create_p2sh_p2wpkh_address(public_key)
        elif address_type == "p2wpkh":
            address = self.create_p2wpkh_address(public_key)
        elif address_type == "p2tr":
            address = self.create_p2tr_address(public_key)
        else:
            raise ValueError(f"Unsupported address type: {address_type}")
        
        return address, private_key_wif
    
    def private_key_to_wif(self, private_key: bytes) -> str:
        """Convert private key to Wallet Import Format (WIF)"""
        # Add version byte (0x80 for mainnet)
        extended_key = b'\x80' + private_key + b'\x01'  # \x01 for compressed
        
        # Calculate checksum
        checksum = self.hash256(extended_key)[:4]
        
        # Create WIF
        wif_bytes = extended_key + checksum
        return base58.b58encode(wif_bytes).decode('utf-8')
    
    def check_pattern_match(self, address: str, pattern: str, position: str) -> bool:
        """Check if address matches the pattern at specified position"""
        if not pattern:
            return True
        
        pattern = pattern.lower()
        address_lower = address.lower()
        
        if position == "start":
            # Skip the address prefix (1, 3, bc1)
            if address_lower.startswith('bc1'):
                return address_lower[3:].startswith(pattern)
            else:
                return address_lower[1:].startswith(pattern)
        elif position == "end":
            return address_lower.endswith(pattern)
        elif position == "middle":
            # Check if pattern appears anywhere in the address (excluding prefix)
            if address_lower.startswith('bc1'):
                return pattern in address_lower[3:]
            else:
                return pattern in address_lower[1:]
        
        return False
    
    def generate_batch(self, address_type: str, batch_size: int = 100) -> List[Tuple[str, str]]:
        """Generate multiple addresses in batch for better performance"""
        results = []
        for _ in range(batch_size):
            address, private_key = self.generate_address(address_type)
            results.append((address, private_key))
        return results
    
    def find_pattern_batch(self, address_type: str, pattern: str, position: str, 
                          batch_size: int = 1000, max_attempts: int = None) -> Optional[Tuple[str, str, int]]:
        """Find address matching pattern using batch processing"""
        attempts = 0
        
        while max_attempts is None or attempts < max_attempts:
            # Generate batch of addresses
            if max_attempts is None:
                current_batch_size = batch_size
            else:
                current_batch_size = min(batch_size, max_attempts - attempts)
            
            batch = self.generate_batch(address_type, current_batch_size)
            
            for address, private_key in batch:
                attempts += 1
                if self.check_pattern_match(address, pattern, position):
                    return address, private_key, attempts
            
            if max_attempts is not None and attempts >= max_attempts:
                break
                
        return None
    
    def find_pattern_multiprocess(self, address_type: str, pattern: str, position: str,
                                 max_attempts: int = None, num_processes: int = None) -> Optional[Tuple[str, str, int]]:
        """Find address matching pattern using multiple processes"""
        if num_processes is None:
            num_processes = min(os.cpu_count(), 8)  # Limit to 8 processes max
        
        if max_attempts is None:
            # Set a large number for each process when no limit is specified
            attempts_per_process = 1000000  # 1 million attempts per process
        else:
            attempts_per_process = max_attempts // num_processes
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # Submit tasks to each process
            futures = []
            for i in range(num_processes):
                future = executor.submit(
                    _find_pattern_worker,
                    address_type, pattern, position, attempts_per_process, i, max_attempts is None
                )
                futures.append(future)
            
            # Check for completion
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    # Cancel remaining tasks
                    for f in futures:
                        f.cancel()
                    return result
        
        return None


def _find_pattern_worker(address_type: str, pattern: str, position: str, 
                        max_attempts: int, worker_id: int, unlimited: bool = False) -> Optional[Tuple[str, str, int]]:
    """Worker function for multiprocess pattern finding"""
    generator = BitcoinAddressGenerator()
    
    attempt = 0
    while unlimited or attempt < max_attempts:
        address, private_key = generator.generate_address(address_type)
        attempt += 1
        if generator.check_pattern_match(address, pattern, position):
            return address, private_key, attempt + (worker_id * max_attempts)
    
    return None