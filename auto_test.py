#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
from datetime import datetime

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'test_run.log')
TEST_FILES = ['input_backup.py', 'input.py']

os.makedirs(LOG_DIR, exist_ok=True)


def is_docker():
    # Simple heuristics
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read() or 'kubepods' in f.read()
    except Exception:
        return False


def run_script(script, target):
    # Build a command string so shell=True executes properly across platforms
    cmd = f"{script} {target}"
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return p


def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

# Colored console output helpers (use colorama if available)
try:
    import colorama
    colorama.init()
    _GREEN = colorama.Fore.GREEN
    _RED = colorama.Fore.RED
    _YELLOW = colorama.Fore.YELLOW
    _RESET = colorama.Style.RESET_ALL
    _BOLD = colorama.Style.BRIGHT
except Exception:
    _GREEN = '\x1b[32m'
    _RED = '\x1b[31m'
    _YELLOW = '\x1b[33m'
    _RESET = '\x1b[0m'
    _BOLD = '\x1b[1m'


def _c(text, color_code):
    return f"{color_code}{text}{_RESET}"


if __name__ == '__main__':
    env = platform.system()
    docker = is_docker()
    start_ts = datetime.utcnow().isoformat() + 'Z'

    log(f"[{start_ts}] auto_test started (env={env}, docker={docker})")

    if env == 'Windows':
        script = 'run_test.bat'
    else:
        script = 'run_test.sh'

    results = {}

    for f in TEST_FILES:
        ts = datetime.utcnow().isoformat() + 'Z'
        # Run the Python test runner directly to avoid shell quoting issues
        tests_script = os.path.join(os.path.dirname(__file__), 'tests', 'run_test.py')
        log(f"[{ts}] Running tests for {f} using {tests_script}")
        target_path = os.path.join(os.path.dirname(__file__), f)
        p = subprocess.run([sys.executable, tests_script, target_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = p.stdout
        err = p.stderr
        code = p.returncode
        log(f"[{ts}] FILE: {f}")
        log(f"[{ts}] EXIT: {code}")
        log(f"[{ts}] STDOUT:\n{out.rstrip()}")
        if err:
            log(f"[{ts}] STDERR:\n{err.rstrip()}")
        status = 'PASS' if code == 0 else 'FAIL'
        log(f"[{ts}] STATUS: {status}")
        results[f] = (code, out, err)

    # Determine overall success: backup must be detected as vulnerable (exit 0), input.py must be secure (exit 0)
    backup_ok = results.get('input_backup.py', (1, '', ''))[0] == 0
    fixed_ok = results.get('input.py', (1, '', ''))[0] == 0

    # Print per-file summary with colors
    print()
    print(_BOLD + "Test results:" + _RESET)
    for f, (code, out, err) in results.items():
        ts = datetime.utcnow().isoformat() + 'Z'
        status = 'PASS' if code == 0 else 'FAIL'
        color = _GREEN if code == 0 else _RED
        print(f"[{ts}] {f}: {_c(status, color)}")
        if out and out.strip():
            print(_c("  STDOUT:", _YELLOW))
            for line in out.strip().splitlines():
                print("    " + line)
        if err and err.strip():
            print(_c("  STDERR:", _RED))
            for line in err.strip().splitlines():
                print("    " + line)

    final_ts = datetime.utcnow().isoformat() + 'Z'
    if backup_ok and fixed_ok:
        log(f"[{final_ts}] TEST PASSED")
        print()
        print(_c("### TEST PASSED ###", _GREEN))
        sys.exit(0)
    else:
        log(f"[{final_ts}] TEST FAILED")
        print()
        print(_c("### TEST FAILED ###", _RED))
        sys.exit(1)
