import sys
import os
import re
import sqlite3
from importlib.machinery import SourceFileLoader

BASE = os.path.dirname(os.path.dirname(__file__))

VULN_PATTERNS = [
    (re.compile(r"PAYMENT_TOKEN\s*=\s*\""), "hardcoded payment token"),
    (re.compile(r"INTERNAL_AUTH\s*=\s*\""), "hardcoded internal auth"),
    (re.compile(r"hashlib\.md5\("), "use of MD5"),
    (re.compile(r"SELECT .*%s"), "string-interpolated SQL"),
    (re.compile(r"subprocess\..*shell=True"), "shell execution with user input"),
]


def load_module(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return SourceFileLoader(name, path).load_module()


def check_source_rules(src):
    found = []
    for pat, desc in VULN_PATTERNS:
        if pat.search(src):
            found.append(desc)
    return found


def run_db_tests(mod):
    # prepare DB used by the module
    db_path = getattr(mod, "DB_FILE", os.path.join(os.path.dirname(__file__), "..", "appdata.db"))
    db_path = os.path.abspath(db_path)
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE profiles(id INTEGER PRIMARY KEY, name TEXT, balance REAL)")
    c.execute("INSERT INTO profiles(id,name,balance) VALUES (1,'alice',100.0)")
    c.execute("INSERT INTO profiles(id,name,balance) VALUES (2,'bob',50.0)")
    conn.commit()
    conn.close()

    good = True
    # baseline: valid id returns single row
    try:
        r = mod.query_profile("1")
        if not (isinstance(r, list) and len(r) == 1):
            print("FAIL: expected single-row result for id=1")
            good = False
    except Exception as e:
        print("FAIL: query_profile(""1"") raised", e)
        good = False

    # SQLi test: injection should NOT return both rows for secure module
    try:
        inj = "1' OR '1'='1"
        r = mod.query_profile(inj)
        if len(r) > 1:
            print("VULN: SQL injection possible (multiple rows returned)")
            return False
    except ValueError:
        # secure behaviour: invalid id
        pass
    except Exception as e:
        print("ERROR during SQLi test:", e)
        return False

    return good


def run_update_records_test(mod):
    # create a secret file outside configs
    secret_path = os.path.join(BASE, "tests", "secret_config.yml")
    with open(secret_path, "w", encoding="utf-8") as f:
        f.write("secret: topsecret")
    try:
        # attempt to read arbitrary file via update_records
        try:
            mod.update_records(secret_path)
            print("VULN: update_records allows arbitrary file read")
            return False
        except ValueError:
            # expected for secure module
            return True
        except Exception as e:
            # any other exception is considered secure for this test
            return True
    finally:
        try:
            os.remove(secret_path)
        except Exception:
            pass


def main():
    if len(sys.argv) < 2:
        print("Usage: run_tests.py <module-path>")
        return 2
    path = sys.argv[1]
    path = os.path.abspath(path)
    src = open(path, "r", encoding="utf-8").read()
    vuln_findings = check_source_rules(src)
    module = load_module(path)

    source_ok = len(vuln_findings) == 0
    db_ok = run_db_tests(module)
    update_ok = run_update_records_test(module)

    ok = source_ok and db_ok and update_ok

    # detailed output
    print(f"Source vulnerability findings: {vuln_findings}")
    print(f"DB tests passed: {db_ok}")
    print(f"update_records restricted: {update_ok}")

    if ok:
        print("All security checks passed for module:", path)
        return 0
    else:
        print("Security checks FAILED for module:", path)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
