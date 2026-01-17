#!/usr/bin/env python3
"""
auto_test.py - Automatic environment detection and test execution script

This script:
1. Detects the current operating system (Windows/Linux/macOS/Docker)
2. Runs appropriate test scripts
3. Logs all output with timestamps
4. Tests both input_backup.py and input.py
5. Reports final status: TEST PASSED or TEST FAILED
"""

import os
import sys
import platform
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Color output helper
def colored(text, color):
    """Add ANSI color codes to text."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"
def setup_logging():
    """Configure logging for the test run."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "test_run.log"
    
    # Configure logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__), log_file


def detect_environment():
    """Detect the current environment."""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Detecting Environment")
    logger.info("=" * 80)
    
    system = platform.system()
    logger.info(f"Operating System: {system}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Current Directory: {os.getcwd()}")
    
    # Check if running in Docker
    is_docker = os.path.isfile('/.dockerenv') or os.path.isfile('/run/.dockerenv')
    logger.info(f"Docker Environment: {is_docker}")
    
    env_type = "Docker" if is_docker else system
    
    logger.info("")
    return env_type, system


def run_test_file(file_path):
    """Run a test on a specific Python file."""
    logger = logging.getLogger(__name__)
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        status_msg = f"  {file_path.name:<30} " + colored("ERROR", "red") + " (File not found)"
        logger.info(status_msg)
        return False
    
    try:
        # Run Python syntax check
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            status_msg = f"  {file_path.name:<30} " + colored("PASSED", "green")
            logger.info(status_msg)
            return True
        else:
            error_detail = result.stderr.split('\n')[0] if result.stderr else "Syntax error"
            status_msg = f"  {file_path.name:<30} " + colored("ERROR", "red") + f" ({error_detail})"
            logger.info(status_msg)
            return False
    
    except subprocess.TimeoutExpired:
        status_msg = f"  {file_path.name:<30} " + colored("ERROR", "red") + " (Timeout)"
        logger.info(status_msg)
        return False
    except Exception as e:
        status_msg = f"  {file_path.name:<30} " + colored("ERROR", "red") + f" ({str(e)})"
        logger.info(status_msg)
        return False


def run_test_script(env_type, system):
    """Run the appropriate test script based on environment."""
    logger = logging.getLogger(__name__)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Running Platform-Specific Tests")
    logger.info("=" * 80)
    logger.info("")
    
    script_dir = Path(__file__).parent
    
    try:
        if system in ["Linux", "Darwin"]:  # Darwin is macOS
            test_script = script_dir / "run_test.sh"
            if test_script.exists():
                logger.info(f"Running test script: {test_script.name}")
                result = subprocess.run(
                    ["bash", str(test_script)],
                    cwd=str(script_dir),
                    timeout=120,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
                return result.returncode == 0
            else:
                logger.warning(f"Test script not found: {test_script}")
        
        elif system == "Windows":
            test_script = script_dir / "run_test.bat"
            if test_script.exists():
                logger.info(f"Running test script: {test_script.name}")
                result = subprocess.run(
                    [str(test_script)],
                    cwd=str(script_dir),
                    shell=True,
                    timeout=120,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
                return result.returncode == 0
            else:
                logger.warning(f"Test script not found: {test_script}")
    
    except subprocess.TimeoutExpired:
        logger.error("Test script execution timed out")
        return False
    except Exception as e:
        logger.error(f"Exception running test script: {e}")
        return False
    
    return None


def main():
    """Main execution function."""
    logger, log_file = setup_logging()
    
    try:
        logger.info("")
        logger.info("=" * 80)
        logger.info("Security Audit - Automatic Test Execution")
        logger.info("=" * 80)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log File: {log_file}")
        logger.info("")
        
        # Detect environment
        env_type, system = detect_environment()
        logger.info("")
        
        # Set environment variables for testing
        os.environ["FLASK_ENV"] = "production"
        os.environ["PAYMENT_TOKEN"] = "test_token_12345"
        os.environ["MAIL_SERVER_KEY"] = "test_mail_key"
        os.environ["INTERNAL_AUTH"] = "test_internal_key"
        
        logger.info("Environment Variables Set:")
        logger.info(f"  FLASK_ENV={os.environ.get('FLASK_ENV')}")
        logger.info(f"  PAYMENT_TOKEN=*****(hidden)")
        logger.info(f"  MAIL_SERVER_KEY=*****(hidden)")
        logger.info(f"  INTERNAL_AUTH=*****(hidden)")
        logger.info("")
        
        script_dir = Path(__file__).parent
        
        # Test files individually
        logger.info("=" * 80)
        logger.info("Test Results")
        logger.info("=" * 80)
        logger.info("")
        
        results = {}
        results["input_backup.py"] = run_test_file(script_dir / "input_backup.py")
        results["input.py"] = run_test_file(script_dir / "input.py")
        logger.info("")
        
        # Try to run platform-specific test scripts
        platform_result = run_test_script(env_type, system)
        
        # Final summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("Summary")
        logger.info("=" * 80)
        logger.info("")
        
        for file_name, passed in results.items():
            status = colored("PASSED", "green") if passed else colored("ERROR", "red")
            logger.info(f"  {file_name:<30} {status}")
        
        if platform_result is not None:
            status = colored("PASSED", "green") if platform_result else colored("ERROR", "red")
            logger.info(f"  {'Platform-specific tests':<30} {status}")
        
        logger.info("")
        
        # Determine overall status
        all_passed = all(results.values())
        if platform_result is not None:
            all_passed = all_passed and platform_result
        
        logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if all_passed:
            logger.info("")
            logger.info("=" * 80)
            status_msg = colored("TEST PASSED", "green")
            logger.info(status_msg)
            logger.info("=" * 80)
            return 0
        else:
            logger.info("")
            logger.info("=" * 80)
            status_msg = colored("TEST FAILED", "red")
            logger.info(status_msg)
            logger.info("=" * 80)
            return 1
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST FAILED")
        logger.info("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
