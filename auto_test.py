#!/usr/bin/env python3
"""Auto-run the test suite for both the legacy (input_backup.py) and the
fixed implementation (input.py). Writes timestamped logs to logs/test_run.log.

Behavior:
- Detects platform (Windows vs POSIX)
- Runs the platform test script with target 'backup' then 'fixed'
- Records stdout/stderr, exit code, timestamp, and final TEST PASSED / TEST FAILED
"""
import os
import platform
import shlex
import subprocess
from datetime import datetime

LOG_FILE = os.path.join('logs', 'test_run.log')
SHELL_SCRIPT = 'run_test.sh'
WINDOWS_SCRIPT = 'run_test.bat'

os.makedirs('logs', exist_ok=True)


def _now():
    return datetime.utcnow().isoformat() + 'Z'


def _run_cmd(cmd_list, env=None, timeout=120):
    # prefer list-args to avoid shell quoting issues on Windows
    p = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=timeout)
    return p.returncode, (p.stdout or b"").decode(errors='replace')


def _log(section, content):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{_now()}] {section}\n")
        f.write(content)
        f.write('\n')


def _parse_unittest_summary(output: str) -> dict:
    """Extract a small summary from unittest output.

    Returns dict: {tests_run:int, time:float, status:str, failures:int, errors:int, summary_line:str}
    """
    import re
    res = {"tests_run": 0, "time": 0.0, "status": "UNKNOWN", "failures": 0, "errors": 0, "summary_line": ""}
    m = re.search(r"Ran\s+(\d+)\s+tests\s+in\s+([0-9.]+)s", output)
    if m:
        res["tests_run"] = int(m.group(1))
        res["time"] = float(m.group(2))
    ok = re.search(r"\nOK\s*$", output)
    failed = re.search(r"FAILED\s*\(([^)]+)\)", output)
    if ok:
        res["status"] = "OK"
    elif failed:
        res["status"] = "FAILED"
        # parse failures/errors (e.g. failures=1, errors=0)
        parts = [p.strip() for p in failed.group(1).split(",")]
        for p in parts:
            if "fail" in p:
                res["failures"] = int(re.search(r"(\d+)", p).group(1))
            if "error" in p:
                res["errors"] = int(re.search(r"(\d+)", p).group(1))
    # capture the summary line (OK or FAILED(...))
    sline = None
    for line in output.splitlines()[::-1]:
        if line.strip().startswith("OK") or line.strip().startswith("FAILED"):
            sline = line.strip()
            break
    res["summary_line"] = sline or ""
    return res


def run_target(target):
    system = platform.system()
    project_root = os.getcwd()
    if system == 'Windows':
        script_path = os.path.join(project_root, WINDOWS_SCRIPT)
        cmd = ["cmd", "/c", script_path, target]
    else:
        script_path = os.path.join(project_root, SHELL_SCRIPT)
        cmd = ["bash", script_path, target]

    _log('RUN', f"Running: {' '.join(cmd)}")

    rc, out = _run_cmd(cmd)
    _log('OUTPUT', out)
    status = 'TEST PASSED' if rc == 0 else 'TEST FAILED'
    _log('STATUS', f'{target} {status} (exit_code={rc})')

    # Parse a compact unittest summary and print detailed, user-friendly output
    parsed = _parse_unittest_summary(out)
    header = f"== TEST REPORT: {target.upper()} -- {parsed['status']} (exit_code={rc}) =="
    print('\n' + header)
    print(f"Summary: {parsed['summary_line'] or 'No summary line found'}")
    print(f"Tests run: {parsed['tests_run']}  Time: {parsed['time']}s  Failures: {parsed['failures']}  Errors: {parsed['errors']}")

    # print full test output but truncate to reasonable size to avoid flooding the console
    MAX_CHARS = 16_000
    if len(out) > MAX_CHARS:
        print(out[:MAX_CHARS])
        print(f"... (output truncated, see {LOG_FILE} for full log) ...")
    else:
        print(out)

    return {"target": target, "rc": rc, "out": out, "parsed": parsed}


def main():
    results = []
    overall_ok = True
    for tgt in ('backup', 'fixed'):
        res = run_target(tgt)
        results.append(res)
        if res.get('rc', 1) != 0:
            overall_ok = False

    # print an overall summary
    print('\n== OVERALL TEST SUMMARY ==')
    for r in results:
        p = r.get('parsed', {})
        status = 'PASS' if r.get('rc', 1) == 0 else 'FAIL'
        print(f"- {r.get('target')}: {status} — tests={p.get('tests_run', '?')} failures={p.get('failures', '?')} errors={p.get('errors', '?')} time={p.get('time', '?')}s")

    final = 'TEST PASSED' if overall_ok else 'TEST FAILED'
    _log('FINAL', final)
    print('\n' + final)
    return 0 if overall_ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
