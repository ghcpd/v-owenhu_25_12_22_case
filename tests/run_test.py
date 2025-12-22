#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def check_file(path):
    text = Path(path).read_text()
    patterns = {
        'hardcoded_token': re.compile(r'PAYMENT_TOKEN\s*=\s*"'),
        'md5': re.compile(r'hashlib\.md5|\bmd5\('),
        'shell': re.compile(r'shell=True|subprocess\.Popen\('),
        'sql_interp': re.compile(r"%\s*%\s*uid|SELECT .*%s"),
        'debug': re.compile(r'debug=True')
    }
    matches = {k: bool(p.search(text)) for k,p in patterns.items()}
    return matches

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: run_test.py <file>')
        sys.exit(2)
    path = sys.argv[1]
    matches = check_file(path)
    vulnerable = any(matches.values())
    expected_vulnerable = 'backup' in Path(path).name.lower()

    print('Test file:', path)
    print('Matches:', matches)

    if expected_vulnerable:
        if vulnerable:
            print('EXPECTED VULNERABLE: vulnerabilities detected')
            sys.exit(0)
        else:
            print('EXPECTED VULNERABLE: but no vulnerabilities detected')
            sys.exit(1)
    else:
        if vulnerable:
            print('EXPECTED SECURE: vulnerabilities found')
            sys.exit(1)
        else:
            print('EXPECTED SECURE: no vulnerabilities found')
            sys.exit(0)
