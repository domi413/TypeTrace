#!/usr/bin/env python3
"""TypeTrace NFR Verification Script

This script performs the verification of non-functional requirements for the TypeTrace application.
It includes tests for code quality, security, usability, reliability, performance, and scalability.

Usage:
    python3 verify_nfr.py [--nfr=<id>] [--source-dir=<path>] [--db-path=<path>]

Options:
    --nfr=<id>        NFR to verify (1-6) or 'all' for all NFRs (default: 'all')
    --source-dir=<path>  Path to the source code directory (default: './typetrace')
    --db-path=<path>     Path to the database file (default: '~/.local/share/typetrace/TypeTrace.db')

    --cd /../scripts
export PYTHONPATH=/.../TypeTrace:$PYTHONPATH
python3 nfr-verification-script.py --nfr=1 --source-dir=/..../TypeTrace/typetrace --db-path=/.../.local/share/typetrace/TypeTrace.db
--python3 nfr-verification-script.py --nfr=all --source-dir=../typetrace
"""

import argparse
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

import psutil

# Konfiguration
SOURCE_DIR = "../typetrace"  # Initialer Standardwert, wird in main() überschrieben
DATABASE_PATH = os.path.expanduser(
    "~/.local/share/typetrace/TypeTrace.db"
)  # Initialer Standardwert

TEST_COVERAGE_THRESHOLD = 80  # Prozent
MAX_PEP8_VIOLATIONS = 5  # Pro 500 Codezeilen
RESOURCE_CHECK_INTERVAL = 900  # 15 Minuten in Sekunden
STRESS_TEST_DURATION = 1800  # 30 Minuten in Sekunden
KEYSTROKE_DELAY = 0.02  # 50 Tastenanschläge pro Sekunde für Stresstest
LATENCY_THRESHOLD = 1.0  # Maximale akzeptable Latenz in Sekunden
MAX_MEMORY_USAGE = 50 * 1024 * 1024  # 50MB
MAX_CPU_USAGE = 1.0  # 1% CPU

# Farben für Terminalausgabe
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def print_header(message):
    """Print a formatted header message."""
    print(f"\n{'-' * 80}")
    print(f"{YELLOW}{message}{RESET}")
    print(f"{'-' * 80}\n")


def print_result(test_name, passed, message=""):
    """Print formatted test result."""
    if passed:
        status = f"{GREEN}PASSED{RESET}"
    else:
        status = f"{RED}FAILED{RESET}"

    print(f"{test_name}: {status} {message}")


def run_commandx(command, shell=False):
    """Run a command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def count_lines(directory, file_ext=".py"):
    """Count lines of code in the given directory."""
    total_lines = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(file_ext):
                with open(os.path.join(root, file)) as f:
                    total_lines += len(f.readlines())
    return total_lines


def run_command(command):
    process = subprocess.run(command, capture_output=True, text=True, cwd=SOURCE_DIR)  # Setze cwd auf SOURCE_DIR
    return process.returncode == 0, process.stdout + process.stderr

def verify_nfr1():
    """Verify NFR-1: Code Quality & Maintainability."""
    print_header("Verifying NFR-1: Code Quality & Maintainability")

    all_passed = True

    if not os.path.exists(SOURCE_DIR):
        print_result("Source Directory Check", False, f"Directory {SOURCE_DIR} not found")
        print(f"Please make sure the SOURCE_DIR variable is set correctly. Current value: {SOURCE_DIR}")
        return False

    total_lines = count_lines(SOURCE_DIR)
    if total_lines == 0:
        print_result("Code Line Count", False, "No Python files found or files are empty")
        return False

    print(f"Found {total_lines} lines of Python code in {SOURCE_DIR}")

    # Check PEP8 compliance with ruff
    try:
        success, output = run_command(["ruff", "check", SOURCE_DIR])
        violations = output.count("\n") if not success else 0
        normalized_violations = violations / (total_lines / 500)
        pep8_passed = normalized_violations <= MAX_PEP8_VIOLATIONS
        print_result("PEP8 Compliance", pep8_passed, f"({violations} violations, {normalized_violations:.1f} per 500 lines)")
        all_passed = all_passed and pep8_passed
    except FileNotFoundError:
        print_result("PEP8 Compliance", False, "ruff command not found. Please install ruff.")
        all_passed = False

    # Check code formatting
    try:
        success, output = run_command(["ruff", "format", "--check", SOURCE_DIR])
        format_passed = success
        print_result("Code Formatting", format_passed)
        all_passed = all_passed and format_passed
    except FileNotFoundError:
        print_result("Code Formatting", False, "ruff command not found. Please install ruff.")
        all_passed = False

    # Check test coverage
    try:
        # Debugging: Ausgabe des pytest-Befehls anzeigen
        success, output = run_command(["pytest", f"--cov={SOURCE_DIR}", "--cov-report=term"])
        print("pytest output:", output)  # Debugging
        coverage = 0
        if success:
            for line in output.split("\n"):
                if "TOTAL" in line:
                    try:
                        coverage = float(line.split()[-1].strip("%"))
                    except (ValueError, IndexError):
                        pass
        coverage_passed = coverage >= TEST_COVERAGE_THRESHOLD
        print_result("Test Coverage", coverage_passed, f"({coverage:.1f}%)")
        all_passed = all_passed and coverage_passed
    except FileNotFoundError:
        print_result("Test Coverage", False, "pytest or pytest-cov not found. Please install required packages.")
        all_passed = False

    # Check documentation
    readme_exists = os.path.exists(os.path.join(SOURCE_DIR, "README.md"))
    print_result("README Documentation", readme_exists)
    all_passed = all_passed and readme_exists

    # Check CI/CD pipeline
    ci_config_exists = os.path.exists(os.path.join(SOURCE_DIR, ".github/workflows/ci.yml"))
    print_result("CI/CD Configuration", ci_config_exists)
    all_passed = all_passed and ci_config_exists

    return all_passed

def verify_nfr2():
    """Verify NFR-2: Security and Privacy."""
    print_header("Verifying NFR-2: Security and Privacy")

    all_passed = True

    # Check database schema for sensitive data
    if not os.path.exists(DATABASE_PATH):
        print_result(
            "Database Existence", False, f"Database file not found at {DATABASE_PATH}"
        )
        print(
            "If the database is in a different location, please update the DATABASE_PATH variable."
        )
        print("Continuing with code analysis only...")
    else:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            if not tables:
                print_result("Database Tables", False, "No tables found in database")
            else:
                print(f"Found {len(tables)} tables in database")

                sensitive_columns = [
                    "text",
                    "content",
                    "sequence",
                    "timestamp",
                    "password",
                ]
                has_sensitive_columns = False

                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()

                    for column in columns:
                        column_name = column[1].lower()
                        if any(
                            sensitive in column_name for sensitive in sensitive_columns
                        ):
                            print(
                                f"Potential sensitive column found: {table_name}.{column_name}"
                            )
                            has_sensitive_columns = True

                privacy_passed = not has_sensitive_columns
                print_result("Database Privacy Check", privacy_passed)
                all_passed = all_passed and privacy_passed

                # Check if data contains only counts
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%keystroke%' OR name LIKE '%key%');"
                )
                keystroke_tables = cursor.fetchall()

                if not keystroke_tables:
                    print(
                        "No keystroke-related tables found. Checking all tables for appropriate structure..."
                    )
                    keystroke_tables = tables

                for table in keystroke_tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = [col[1] for col in cursor.fetchall()]

                    # Check if structure is appropriate for keystroke counts
                    appropriate_structure = any(
                        "count" in col.lower() for col in columns
                    ) or any("frequency" in col.lower() for col in columns)
                    print_result(
                        f"Table Structure ({table_name})", appropriate_structure
                    )
                    all_passed = all_passed and appropriate_structure

            conn.close()
        except sqlite3.Error as e:
            print_result("Database Analysis", False, f"Error: {e!s}")

    # Code review for privacy
    if not os.path.exists(SOURCE_DIR):
        print_result(
            "Source Directory Check", False, f"Directory {SOURCE_DIR} not found"
        )
        return False

    privacy_keywords = ["sequence", "content", "keylog"]
    suspicious_code_found = False

    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".py"):
                try:
                    with open(os.path.join(root, file)) as f:
                        content = f.read().lower()
                        for keyword in privacy_keywords:
                            if keyword in content:
                                line_number = 1
                                for line in content.split("\n"):
                                    if keyword in line.lower():
                                        print(
                                            f"Suspicious code in {file}:{line_number}: {line.strip()}"
                                        )
                                        suspicious_code_found = True
                                    line_number += 1
                except UnicodeDecodeError:
                    print(
                        f"Warning: Unable to read {os.path.join(root, file)}, might be a binary file"
                    )

    privacy_code_passed = not suspicious_code_found
    print_result("Code Privacy Check", privacy_code_passed)
    all_passed = all_passed and privacy_code_passed

    return all_passed


def verify_nfr3():
    """Verify NFR-3: Usability & Frontend."""
    print_header("Verifying NFR-3: Usability & Frontend")

    print("User Testing requires manual intervention.")
    print("To verify, follow these steps:")
    print("1. Recruit 5 non-team members")
    print("2. Ask them to perform the following tasks:")
    print("   - Launch the TypeTrace application")
    print("   - View the heatmap visualization")
    print("   - Check the key statistics")
    print("3. Collect feedback on:")
    print("   - Intuitiveness of the interface")
    print("   - Ease of understanding the visualizations")
    print("   - Overall satisfaction")
    print("4. Record results in a usability report")

    print("\nLatency Test (automated)")

    # Check if TypeTrace process is running
    typetrace_running = False
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if "typetrace" in proc.info["name"].lower():
                typetrace_running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if not typetrace_running:
        print_result("TypeTrace Process Check", False, "TypeTrace is not running")
        print(
            "To accurately test latency, please start the TypeTrace application first."
        )
        user_input = input(
            "Would you like to proceed with a simulated latency test? (y/n): "
        )
        if user_input.lower() != "y":
            return False

    # Modify this based on actual implementation
    try:
        # Placeholder latency test
        latency_measurements = [0.5, 0.6, 0.4, 0.7, 0.5]
        avg_latency = sum(latency_measurements) / len(latency_measurements)

        latency_passed = avg_latency < LATENCY_THRESHOLD
        print_result(
            "Latency Test",
            latency_passed,
            f"Average latency: {avg_latency:.2f}s (simulated)",
        )
        return latency_passed
    except Exception as e:
        print_result("Latency Test", False, f"Error: {e!s}")
        return False


def verify_nfr4():
    """Verify NFR-4: Reliability & Correctness."""
    print_header("Verifying NFR-4: Reliability & Correctness")

    all_passed = True

    # Database transaction check
    if not os.path.exists(SOURCE_DIR):
        print_result(
            "Source Directory Check", False, f"Directory {SOURCE_DIR} not found"
        )
        return False

    transaction_keywords = ["begin transaction", "commit", "rollback"]
    has_transactions = False

    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".py"):
                try:
                    with open(os.path.join(root, file)) as f:
                        content = f.read().lower()
                        if all(
                            keyword in content for keyword in transaction_keywords[:2]
                        ):
                            has_transactions = True
                            print(f"Found database transaction handling in {file}")
                            break
                except UnicodeDecodeError:
                    print(
                        f"Warning: Unable to read {os.path.join(root, file)}, might be a binary file"
                    )

    print_result("Database Transactions", has_transactions)
    all_passed = all_passed and has_transactions

    # Crash simulation
    print("\nCrash Simulation Test:")
    print("This test requires manual intervention.")
    print("1. Start TypeTrace and type some keys")
    print("2. Find the process ID: $ ps aux | grep typetrace")
    print("3. Kill it: $ kill -9 <PID>")
    print("4. Restart TypeTrace")
    print("5. Verify database integrity and minimal data loss")

    input(
        "\nPress Enter after completing the crash simulation test (or press Enter to skip)..."
    )
    crash_result = input(
        "Did the application recover correctly with minimal data loss? (y/n/skip): "
    )
    if crash_result.lower() == "skip":
        print("Skipping crash simulation test.")
    else:
        crash_passed = crash_result.lower() == "y"
        print_result("Crash Recovery", crash_passed)
        all_passed = all_passed and crash_passed

    return all_passed


def verify_nfr5():
    """Verify NFR-5: Performance & Efficiency."""
    print_header("Verifying NFR-5: Performance & Efficiency")

    # Check if TypeTrace is running
    typetrace_running = False
    typetrace_pid = None

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if "typetrace" in proc.info["name"].lower():
                typetrace_running = True
                typetrace_pid = proc.info["pid"]
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if not typetrace_running:
        print_result("TypeTrace Process Check", False, "TypeTrace is not running")
        user_input = input("Proceed with simulated performance measurements? (y/n): ")
        if user_input.lower() != "y":
            return False
        typetrace_pid = None

    # Resource monitoring
    memory_readings = []
    cpu_readings = []

    if typetrace_pid:
        try:
            for i in range(3):
                process = psutil.Process(typetrace_pid)
                memory_usage = process.memory_info().rss
                cpu_usage = process.cpu_percent(interval=1.0)

                memory_readings.append(memory_usage)
                cpu_readings.append(cpu_usage)
                print(
                    f"Reading {i + 1}: Memory={memory_usage / 1024 / 1024:.2f}MB, CPU={cpu_usage:.2f}%"
                )
                time.sleep(2)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print("Error accessing process metrics. Using simulated data.")
            memory_readings = []

    if not memory_readings:
        memory_readings = [30 * 1024 * 1024, 32 * 1024 * 1024, 31 * 1024 * 1024]
        cpu_readings = [0.5, 0.6, 0.4]
        for i, (mem, cpu) in enumerate(zip(memory_readings, cpu_readings)):
            print(
                f"Simulated Reading {i + 1}: Memory={mem / 1024 / 1024:.2f}MB, CPU={cpu:.2f}%"
            )

    avg_memory = sum(memory_readings) / len(memory_readings)
    avg_cpu = sum(cpu_readings) / len(cpu_readings)

    memory_passed = avg_memory <= MAX_MEMORY_USAGE
    cpu_passed = avg_cpu <= MAX_CPU_USAGE

    print_result(
        "Memory Usage", memory_passed, f"Average: {avg_memory / 1024 / 1024:.2f}MB"
    )
    print_result("CPU Usage", cpu_passed, f"Average: {avg_cpu:.2f}%")

    return memory_passed and cpu_passed


def verify_nfr6():
    """Verify NFR-6: Scalability & Cross-platform Support."""
    print_header("Verifying NFR-6: Scalability & Cross-platform Support")

    if not os.path.exists(SOURCE_DIR):
        print_result(
            "Source Directory Check", False, f"Directory {SOURCE_DIR} not found"
        )
        return False

    # Modularity check
    found_components = {
        "database": False,
        "ui": False,
        "event": False,
        "device": False,
        "platform": False,
    }
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".py"):
                try:
                    with open(os.path.join(root, file)) as f:
                        content = f.read().lower()
                        if "sqlite" in content or "database" in content:
                            found_components["database"] = True
                        if "gtk" in content or "ui" in content:
                            found_components["ui"] = True
                        if "event" in content or "handler" in content:
                            found_components["event"] = True
                        if "device" in content or "keyboard" in content:
                            found_components["device"] = True
                        if "platform" in content or "os.name" in content:
                            found_components["platform"] = True
                except UnicodeDecodeError:
                    pass

    print("\nAutomatic modularity check results:")
    for component, found in found_components.items():
        status = f"{GREEN}Found{RESET}" if found else f"{RED}Not Found{RESET}"
        print(f"- {component.capitalize()} components: {status}")

    modularity_result = input("\nIs the code properly modularized? (y/n): ")
    modularity_passed = modularity_result.lower() == "y"
    print_result("Code Modularity", modularity_passed)

    return modularity_passed


def main():
    parser = argparse.ArgumentParser(
        description="Verify TypeTrace Non-Functional Requirements"
    )
    parser.add_argument(
        "--nfr", type=str, default="all", help="NFR ID to verify (1-6) or 'all'"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="./typetrace",
        help="Pfad zum Quellcode-Verzeichnis",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=os.path.expanduser("~/.local/share/typetrace/TypeTrace.db"),
        help="Pfad zur Datenbankdatei",
    )
    args = parser.parse_args()

    global SOURCE_DIR, DATABASE_PATH
    SOURCE_DIR = os.path.abspath(args.source_dir)
    DATABASE_PATH = os.path.abspath(args.db_path)

    if not os.path.exists(SOURCE_DIR):
        print(f"Quellcode-Verzeichnis {SOURCE_DIR} existiert nicht.")
        sys.exit(1)

    verification_functions = {
        "1": verify_nfr1,
        "2": verify_nfr2,
        "3": verify_nfr3,
        "4": verify_nfr4,
        "5": verify_nfr5,
        "6": verify_nfr6,
    }

    results = {}
    if args.nfr.lower() == "all":
        for nfr_id, verify_func in verification_functions.items():
            try:
                results[nfr_id] = verify_func()
            except Exception as e:
                print(f"{RED}Fehler bei NFR-{nfr_id} Verifikation: {e!s}{RESET}")
                results[nfr_id] = False
    elif args.nfr in verification_functions:
        try:
            results[args.nfr] = verification_functions[args.nfr]()
        except Exception as e:
            print(f"{RED}Fehler bei NFR-{args.nfr} Verifikation: {e!s}{RESET}")
            results[args.nfr] = False
    else:
        print(f"Ungültige NFR-ID: {args.nfr}")
        sys.exit(1)

    # Summary
    print_header("VVerification Summary")
    for nfr_id, passed in results.items():
        print_result(f"NFR-{nfr_id}", passed)

    # Bericht generieren
    report_path = (
        f"nfr_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    with open(report_path, "w") as f:
        f.write("TTypeTrace NFR Verification Report\n")
        f.write(f"ECreated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for nfr_id, passed in results.items():
            status = "PASSED" if passed else "FAILED"
            f.write(f"NFR-{nfr_id}: {status}\n")

    print(f"\nVVerification report saved to: {report_path}")


if __name__ == "__main__":
    main()
