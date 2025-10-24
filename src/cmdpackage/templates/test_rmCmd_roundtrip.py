#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

test_rmCmd_roundtrip_template = Template(dedent("""#!/usr/bin/env python3
\"\"\"
Comprehensive test script for rmCmd round trip functionality

This test suite validates the rmCmd command functionality including:

1. Creating a test command with arguments and switch flags
2. Modifying the command with additional arguments and flags
3. Removing individual arguments without affecting the command file
4. Removing individual switch flags from all locations(.${packName}rc, commands.json, source file)
5. Verifying that the command file remains intact during selective removals
6. Finally removing the entire command and verifying complete cleanup

All operations are verified across:
- commands.json
- .${packName}rc file
- source command file ( < cmdName > .py)
\"\"\"

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Tuple


class Colors:
    \"\"\"ANSI color codes for terminal output\"\"\"
    RED = '\\033[0;31m'
    GREEN = '\\033[0;32m'
    YELLOW = '\\033[1;33m'
    BLUE = '\\033[0;34m'
    MAGENTA = '\\033[35m'
    NC = '\\033[0m'  # No Color


class TestResult:
    \"\"\"Class to track test results\"\"\"
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append((test_name, passed, message))
        if passed:
            self.passed += 1
            print_pass(f"{test_name}: {message}")
        else:
            self.failed += 1
            print_fail(f"{test_name}: {message}")

    def print_summary(self):
        total = self.passed + self.failed
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"{Colors.BLUE}TEST SUMMARY{Colors.NC}")
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"Total tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.NC}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.NC}")
        
        if self.failed > 0:
            print(f"{Colors.RED}FAILED TESTS:{Colors.NC}")
            for test_name, passed, message in self.tests:
                if not passed:
                    print(f"  - {test_name}: {message}")
        
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        return self.failed == 0


def print_test(message: str):
    \"\"\"Print test status message\"\"\"
    print(f"{Colors.BLUE}[TEST]{Colors.NC} {message}")


def print_pass(message: str):
    \"\"\"Print pass message\"\"\"
    print(f"{Colors.GREEN}[PASS]{Colors.NC} {message}")


def print_fail(message: str):
    \"\"\"Print fail message\"\"\"
    print(f"{Colors.RED}[FAIL]{Colors.NC} {message}")


def print_info(message: str):
    \"\"\"Print info message\"\"\"
    print(f"{Colors.YELLOW}[INFO]{Colors.NC} {message}")


def print_step(message: str):
    \"\"\"Print step message\"\"\"
    print(f"{Colors.MAGENTA}[STEP]{Colors.NC} {message}")


def run_command(cmd: str, input_text: str = "", capture_output: bool = True) -> Tuple[int, str, str]:
    \"\"\"Run a shell command and return (returncode, stdout, stderr)\"\"\"
    try:
        # Change to the project directory
        project_dir = Path(__file__).parent.parent
        result = subprocess.run(
            cmd,
            shell=True,
            input=input_text,
            text=True,
            capture_output=capture_output,
            cwd=project_dir,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_command_exists(cmd_name: str) -> bool:
    \"\"\"Check if command exists in commands.json\"\"\"
    commands_file = Path(__file__).parent.parent / "src" / "${packName}" / "commands" / "commands.json"
    try:
        with open(commands_file, 'r') as f:
            data = json.load(f)
            return cmd_name in data
    except Exception:
        return False


def get_command_data(cmd_name: str) -> dict:
    \"\"\"Get command data from commands.json\"\"\"
    commands_file = Path(__file__).parent.parent / "src" / "${packName}" / "commands" / "commands.json"
    try:
        with open(commands_file, 'r') as f:
            data = json.load(f)
            return data.get(cmd_name, {})
    except Exception:
        return {}


def check_flag_in_${packName}rc(cmd_name: str, flag_name: str) -> bool:
    \"\"\"Check if a specific flag exists in .${packName}rc\"\"\"
    ${packName}rc_file = Path(__file__).parent.parent / "src" / ".${packName}rc"
    try:
        with open(${packName}rc_file, 'r') as f:
            data = json.load(f)
            return (cmd_name in data.get('commandFlags', {}) and 
                    flag_name in data['commandFlags'][cmd_name])
    except Exception:
        return False


def check_switch_flag_definition(cmd_name: str, flag_name: str, flag_type: str) -> bool:
    \"\"\"Check if a switch flag is properly defined in commands.json\"\"\"
    cmd_data = get_command_data(cmd_name)
    switch_flags = cmd_data.get('switchFlags', {})
    flag_def = switch_flags.get(flag_name, {})
    return flag_def.get('type') == flag_type


def file_exists(file_path: str) -> bool:
    \"\"\"Check if a file exists\"\"\"
    full_path = Path(__file__).parent.parent / file_path
    return full_path.exists()


def file_contains_flag(file_path: str, flag_name: str) -> bool:
    \"\"\"Check if a source file contains a specific flag in commandJsonDict\"\"\"
    full_path = Path(__file__).parent.parent / file_path
    try:
        with open(full_path, 'r') as f:
            content = f.read()
            return flag_name in content and 'switchFlags' in content
    except Exception:
        return False


def cleanup_test_commands():
    \"\"\"Clean up any existing test commands\"\"\"
    print_info("Cleaning up any existing test commands...")    
    
    test_commands = ["rmTestCmd01", "rmTestCmd02"]
    
    # Remove test commands if they exist
    for cmd in test_commands:
        if check_command_exists(cmd):
            run_command(f'echo "y" | ${packName} rmCmd {cmd}')
    
    print_pass("Cleanup completed")


def test_create_command(result: TestResult) -> bool:
    \"\"\"Test 1: Create a test command\"\"\"
    print_test("Test 1: Create test command")
    
    # Create test command
    input_text = "Test command for rmCmd testing"
    returncode, stdout, stderr = run_command("${packName} newCmd rmTestCmd01", input_text)
    
    # Check if command was created
    if check_command_exists("rmTestCmd01") and file_exists("src/${packName}/commands/rmTestCmd01.py"):
        result.add_result("Create command", True, "rmTestCmd01 created successfully")
        return True
    else:
        result.add_result("Create command", False, "Failed to create rmTestCmd01")
        return False


def test_add_flags_and_arguments(result: TestResult) -> bool:
    \"\"\"Test 2: Add switch flags and arguments to the command\"\"\"
    print_test("Test 2: Add switch flags and arguments")
    
    # Add switch flags
    input_text = "Verbose output flag\\nDebug mode flag\\n"
    returncode, stdout, stderr = run_command("${packName} modCmd rmTestCmd01 -verbose -debug", input_text)
    
    # Add regular arguments
    input_text = "First test argument\\nSecond test argument\\n"
    returncode, stdout, stderr = run_command("${packName} modCmd rmTestCmd01 arg1 arg2", input_text)
    
    # Verify flags were added
    verbose_ok = check_switch_flag_definition("rmTestCmd01", "verbose", "bool")
    debug_ok = check_switch_flag_definition("rmTestCmd01", "debug", "bool")
    verbose_${packName}rc = check_flag_in_${packName}rc("rmTestCmd01", "verbose")
    debug_${packName}rc = check_flag_in_${packName}rc("rmTestCmd01", "debug")
    
    # Verify arguments were added
    cmd_data = get_command_data("rmTestCmd01")
    arg1_ok = "arg1" in cmd_data
    arg2_ok = "arg2" in cmd_data
    
    all_ok = verbose_ok and debug_ok and verbose_${packName}rc and debug_${packName}rc and arg1_ok and arg2_ok
    
    if all_ok:
        result.add_result("Add flags and arguments", True, "All flags and arguments added successfully")
        return True
    else:
        result.add_result("Add flags and arguments", False, 
                         f"Failed - verbose:{verbose_ok}, debug:{debug_ok}, verbose_${packName}rc:{verbose_${packName}rc}, debug_${packName}rc:{debug_${packName}rc}, arg1:{arg1_ok}, arg2:{arg2_ok}")
        return False


def test_remove_regular_argument(result: TestResult) -> bool:
    \"\"\"Test 3: Remove a regular argument without affecting flags or command file\"\"\"
    print_test("Test 3: Remove regular argument")
    
    # Remove arg1
    returncode, stdout, stderr = run_command('echo "y" | ${packName} rmCmd rmTestCmd01 arg1')
    
    # Verify arg1 was removed but everything else remains
    cmd_data = get_command_data("rmTestCmd01")
    arg1_removed = "arg1" not in cmd_data
    arg2_exists = "arg2" in cmd_data
    verbose_exists = check_switch_flag_definition("rmTestCmd01", "verbose", "bool")
    debug_exists = check_switch_flag_definition("rmTestCmd01", "debug", "bool")
    file_exists_check = file_exists("src/${packName}/commands/rmTestCmd01.py")
    verbose_${packName}rc_exists = check_flag_in_${packName}rc("rmTestCmd01", "verbose")
    
    all_ok = arg1_removed and arg2_exists and verbose_exists and debug_exists and file_exists_check and verbose_${packName}rc_exists
    
    if all_ok:
        result.add_result("Remove regular argument", True, "arg1 removed, everything else preserved")
        return True
    else:
        result.add_result("Remove regular argument", False, 
                         f"Failed - arg1_removed:{arg1_removed}, arg2_exists:{arg2_exists}, verbose_exists:{verbose_exists}, debug_exists:{debug_exists}, file_exists:{file_exists_check}, verbose_${packName}rc:{verbose_${packName}rc_exists}")
        return False


def test_remove_switch_flag(result: TestResult) -> bool:
    \"\"\"Test 4: Remove a switch flag from all locations\"\"\"
    print_test("Test 4: Remove switch flag")
    
    # Remove verbose flag using flag name (without dash)
    returncode, stdout, stderr = run_command('echo "y" | ${packName} rmCmd rmTestCmd01 verbose')
    
    # Verify verbose flag was removed from all locations
    verbose_removed_json = not check_switch_flag_definition("rmTestCmd01", "verbose", "bool")
    verbose_removed_${packName}rc = not check_flag_in_${packName}rc("rmTestCmd01", "verbose")
    verbose_removed_source = not file_contains_flag("src/${packName}/commands/rmTestCmd01.py", "verbose")
    
    # Verify other items still exist
    debug_exists = check_switch_flag_definition("rmTestCmd01", "debug", "bool")
    arg2_exists = "arg2" in get_command_data("rmTestCmd01")
    file_exists_check = file_exists("src/${packName}/commands/rmTestCmd01.py")
    debug_${packName}rc_exists = check_flag_in_${packName}rc("rmTestCmd01", "debug")
    
    all_ok = (verbose_removed_json and verbose_removed_${packName}rc and verbose_removed_source and 
              debug_exists and arg2_exists and file_exists_check and debug_${packName}rc_exists)
    
    if all_ok:
        result.add_result("Remove switch flag", True, "verbose flag removed from all locations, everything else preserved")
        return True
    else:
        result.add_result("Remove switch flag", False, 
                         f"Failed - verbose_removed_json:{verbose_removed_json}, verbose_removed_${packName}rc:{verbose_removed_${packName}rc}, verbose_removed_source:{verbose_removed_source}, debug_exists:{debug_exists}, arg2_exists:{arg2_exists}, file_exists:{file_exists_check}, debug_${packName}rc:{debug_${packName}rc_exists}")
        return False


def test_remove_remaining_items(result: TestResult) -> bool:
    \"\"\"Test 5: Remove remaining argument and flag\"\"\"
    print_test("Test 5: Remove remaining argument and flag")
    
    # Remove remaining argument
    returncode, stdout, stderr = run_command('echo "y" | ${packName} rmCmd rmTestCmd01 arg2')
    
    # Remove remaining flag
    returncode, stdout, stderr = run_command('echo "y" | ${packName} rmCmd rmTestCmd01 debug')
    
    # Verify everything was removed except basic command structure
    cmd_data = get_command_data("rmTestCmd01")
    arg2_removed = "arg2" not in cmd_data
    debug_removed_json = not check_switch_flag_definition("rmTestCmd01", "debug", "bool")
    debug_removed_${packName}rc = not check_flag_in_${packName}rc("rmTestCmd01", "debug")
    file_exists_check = file_exists("src/${packName}/commands/rmTestCmd01.py")
    command_still_exists = check_command_exists("rmTestCmd01")
    
    all_ok = arg2_removed and debug_removed_json and debug_removed_${packName}rc and file_exists_check and command_still_exists
    
    if all_ok:
        result.add_result("Remove remaining items", True, "All arguments and flags removed, command file preserved")
        return True
    else:
        result.add_result("Remove remaining items", False, 
                         f"Failed - arg2_removed:{arg2_removed}, debug_removed_json:{debug_removed_json}, debug_removed_${packName}rc:{debug_removed_${packName}rc}, file_exists:{file_exists_check}, command_exists:{command_still_exists}")
        return False


def test_remove_entire_command(result: TestResult) -> bool:
    \"\"\"Test 6: Remove the entire command\"\"\"
    print_test("Test 6: Remove entire command")
    
    # Remove the entire command
    returncode, stdout, stderr = run_command('echo "y" | ${packName} rmCmd rmTestCmd01')
    
    # Verify command was completely removed
    command_removed = not check_command_exists("rmTestCmd01")
    file_removed = not file_exists("src/${packName}/commands/rmTestCmd01.py")
    ${packName}rc_cleaned = not check_flag_in_${packName}rc("rmTestCmd01", "debug") and not check_flag_in_${packName}rc("rmTestCmd01", "verbose")
    
    all_ok = command_removed and file_removed and ${packName}rc_cleaned
    
    if all_ok:
        result.add_result("Remove entire command", True, "Command completely removed from all locations")
        return True
    else:
        result.add_result("Remove entire command", False, 
                         f"Failed - command_removed:{command_removed}, file_removed:{file_removed}, ${packName}rc_cleaned:{${packName}rc_cleaned}")
        return False


def main():
    \"\"\"Run all tests\"\"\"
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}rmCmd Round Trip Test Suite{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    
    result = TestResult()
    
    # Clean up before starting
    cleanup_test_commands()
    
    # Run tests in sequence
    tests = [
        test_create_command,
        test_add_flags_and_arguments,
        test_remove_regular_argument,
        test_remove_switch_flag,
        test_remove_remaining_items,
        test_remove_entire_command
    ]
    
    for test_func in tests:
        if not test_func(result):
            print_fail(f"Test {test_func.__name__} failed, continuing with remaining tests...")
    
    # Final cleanup
    cleanup_test_commands()
    
    # Print summary
    success = result.print_summary()
    
    if success:
        print(f"{Colors.GREEN}All tests passed! rmCmd functionality is working correctly.{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}Some tests failed. Please check the implementation.{Colors.NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""))
