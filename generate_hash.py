#!/usr/bin/env python3
"""
generate_hash.py - Admin Password Hash Setup Helper
"""
import sys
import getpass
try:
    import bcrypt
except ImportError:
    print('Error: bcrypt library is required. Run: pip install bcrypt')
    sys.exit(1)

def generate_admin_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        pwd = getpass.getpass('Enter Admin Password to Hash: ')
        confirm = getpass.getpass('Confirm Admin Password: ')
        if pwd != confirm:
            print('Error: Passwords do not match!')
            sys.exit(1)
            
    if len(pwd) < 8:
        print('Warning: Password length should be at least 8 characters for security.')
        
    hash_str = generate_admin_hash(pwd)
    print('
Generated Bcrypt Hash (Rounds=12):')
    print(f'ADMIN_PASSWORD_HASH="{hash_str}"')
    print('
Add this line to your .env file in the setu-scheme-matcher directory.')
