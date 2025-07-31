#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Try to import the full version first, fall back to simple version
try:
    from btc_generator import BitcoinAddressGenerator
except ImportError:
    from btc_generator_simple import BitcoinAddressGenerator
    print("Using simplified Bitcoin address generator (educational version)")

def test_address_generation():
    generator = BitcoinAddressGenerator()
    
    print("🧪 Testing Bitcoin Address Generation...")
    print()
    
    # Test all address types
    address_types = ["p2pkh", "p2sh-p2wpkh", "p2wpkh", "p2tr"]
    
    for addr_type in address_types:
        try:
            address, private_key = generator.generate_address(addr_type)
            print(f"✅ {addr_type.upper()}: {address}")
            print(f"   Private Key: {private_key}")
            print()
        except Exception as e:
            print(f"❌ {addr_type.upper()}: Error - {e}")
            print()
    
    # Test pattern matching
    print("🔍 Testing pattern matching...")
    test_address = "1ABCdef123456789"
    
    patterns = [
        ("abc", "start", True),
        ("def", "middle", True), 
        ("789", "end", True),
        ("xyz", "start", False)
    ]
    
    for pattern, position, expected in patterns:
        result = generator.check_pattern_match(test_address, pattern, position)
        status = "✅" if result == expected else "❌"
        print(f"{status} Pattern '{pattern}' at {position}: {result}")
    
    print()
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_address_generation()