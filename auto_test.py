import os
import platform
import subprocess
import shlex
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "test_run.log")


def timestamp():
    return datetime.utcnow().isoformat() + "Z"


def run_cmd(cmd, is_windows=False):
    if is_windows:
        # when on Windows, pass an argv list to avoid quoting issues
        if isinstance(cmd, str):
            parts = [cmd]
        else:
            parts = cmd
        proc = subprocess.run(parts, shell=False, capture_output=True, text=True)
    else:
        proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main():
    is_windows = platform.system() == "Windows"
    base = os.path.dirname(__file__)
    runner = os.path.join(base, "run_test.bat") if is_windows else os.path.join(base, "run_test.sh")
    files = ["input_backup.py", "input.py"]

    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"{timestamp()} RUN START\n")
        overall_ok = True
        for f in files:
            path = os.path.join(base, f)
            if is_windows:
                cmd = [runner, path]
            else:
                cmd = f"{runner} \"{path}\""

            # log the command
            fh.write(f"{timestamp()} RUN {f}: {cmd}\n")
            print(f"[{timestamp()}] Running tests for: {f}")
            print(f"  command: {cmd}")

            # execute and capture output
            code, out = run_cmd(cmd, is_windows=is_windows)

            # write to persistent log
            fh.write(out + "\n")
            status = "TEST PASSED" if code == 0 else "TEST FAILED"
            fh.write(f"{timestamp()} {f} {status} (exit {code})\n")

            # print detailed result to console for immediate feedback
            print("----- test output start -----")
            if out:
                print(out.rstrip())
            else:
                print("(no output)")
            print("------ test output end ------")
            print(f"[{timestamp()}] Result for {f}: {status} (exit {code})\n")

            # expected: backup should be vulnerable (non-zero), fixed should be zero
            if f == "input.py" and code != 0:
                overall_ok = False
            if f == "input_backup.py" and code == 0:
                overall_ok = False

        final = "TEST PASSED" if overall_ok else "TEST FAILED"
        fh.write(f"{timestamp()} {final}\n\n")

    # final console summary
    print("==================== SUMMARY ====================")
    print(f"Run timestamp : {timestamp()}")
    print(f"Overall result: {final}")
    print("Detailed logs saved to:", LOG_FILE)

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
