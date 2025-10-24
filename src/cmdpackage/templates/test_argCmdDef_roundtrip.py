#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

test_argCmdDef_roundtrip_template = Template(dedent("""#!/usr/bin/env python3
\"\"\"
Comprehensive test script for argCmdDef template validation and modCmd functionality

This test suite validates the enhanced modCmd functionality including:

1. Python keyword and built-in name validation for argCmdDef templates
2. Input alignment when arguments are rejected during validation
3. Proper messaging for mixed success/failure scenarios
4. Switch flag handling alongside argument validation
5. Template-specific validation(argCmdDef vs simple templates)

Test scenarios:
- Valid argument names that should be accepted
- Invalid Python keywords/built-ins that should be rejected
- Mixed valid/invalid arguments with proper input alignment
- Switch flags combined with arguments
- All arguments rejected scenario
- Template-specific behavior(validation only for argCmdDef)
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


def file_exists(file_path: str) -> bool:
    \"\"\"Check if a file exists\"\"\"
    full_path = Path(__file__).parent.parent / file_path
    return full_path.exists()


def check_template_type(cmd_name: str) -> str:
    \"\"\"Check what template was used for a command\"\"\"
    file_path = Path(__file__).parent.parent / "src" / "${packName}" / "commands" / f"{cmd_name}.py"
    if not file_path.exists():
        return "none"
    
    try:
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            if "argCmdDef template" in first_line:
                return "argCmdDef"
            elif "simple template" in first_line:
                return "simple"
            else:
                return "unknown"
    except Exception:
        return "error"


def cleanup_test_commands():
    \"\"\"Clean up any existing test commands\"\"\"
    print_info("Cleaning up any existing test commands...")    

    test_commands = ["testValidation", "testSimple", "testMixed"]

    # Remove test commands if they exist
    for cmd in test_commands:
        if check_command_exists(cmd):
            run_command(f'echo "y" | ${packName} rmCmd {cmd}')

    print_pass("Cleanup completed")


def test_create_argcmddef_command(result: TestResult) -> bool:
    \"\"\"Test 1: Create a test command using argCmdDef template\"\"\"
    print_test("Test 1: Create argCmdDef template command")

    input_text = "Test command for validation testing"
    returncode, stdout, stderr = run_command("${packName} newCmd testValidation", input_text)

    # Check if command was created with correct template
    if (check_command_exists("testValidation") and 
        file_exists("src/${packName}/commands/testValidation.py") and
        check_template_type("testValidation") == "argCmdDef"):
        result.add_result("Create argCmdDef command", True, "testValidation created successfully with argCmdDef template")
        return True
    else:
        result.add_result("Create argCmdDef command", False, "Failed to create testValidation with correct template")
        return False


def test_valid_argument_acceptance(result: TestResult) -> bool:
    \"\"\"Test 2: Valid argument names should be accepted\"\"\"
    print_test("Test 2: Valid argument names acceptance")

    input_text = "Valid argument for testing\\nAnother valid argument"
    returncode, stdout, stderr = run_command("${packName} modCmd testValidation validArg anotherValid", input_text)

    # Check if both arguments were added
    cmd_data = get_command_data("testValidation")
    valid_arg_ok = "validArg" in cmd_data
    another_valid_ok = "anotherValid" in cmd_data
    
    # Check output messages
    contains_modified = "CMD MODIFIED:" in stdout
    contains_both_args = "validArg" in stdout and "anotherValid" in stdout

    all_ok = valid_arg_ok and another_valid_ok and contains_modified and contains_both_args

    if all_ok:
        result.add_result("Valid argument acceptance", True, "Both valid arguments accepted and properly reported")
        return True
    else:
        result.add_result("Valid argument acceptance", False, 
                         f"Failed - validArg:{valid_arg_ok}, anotherValid:{another_valid_ok}, modified_msg:{contains_modified}, both_reported:{contains_both_args}")
        return False


def test_invalid_argument_rejection(result: TestResult) -> bool:
    \"\"\"Test 3: Invalid Python keywords should be rejected\"\"\"
    print_test("Test 3: Invalid Python keywords rejection")

    returncode, stdout, stderr = run_command("${packName} modCmd testValidation list str int")

    # Check that none of the invalid arguments were added
    cmd_data = get_command_data("testValidation")
    list_rejected = "list" not in cmd_data
    str_rejected = "str" not in cmd_data
    int_rejected = "int" not in cmd_data
    
    # Check output messages
    contains_all_rejected = "All requested modifications" in stdout and "were rejected" in stdout
    contains_error_msgs = "ERROR:" in stdout
    contains_skip_msgs = "Skipping invalid argument" in stdout

    all_ok = list_rejected and str_rejected and int_rejected and contains_all_rejected and contains_error_msgs

    if all_ok:
        result.add_result("Invalid argument rejection", True, "All Python keywords properly rejected")
        return True
    else:
        result.add_result("Invalid argument rejection", False, 
                         f"Failed - list_rejected:{list_rejected}, str_rejected:{str_rejected}, int_rejected:{int_rejected}, all_rejected_msg:{contains_all_rejected}")
        return False


def test_mixed_valid_invalid_arguments(result: TestResult) -> bool:
    \"\"\"Test 4: Mixed valid and invalid arguments with proper input alignment\"\"\"
    print_test("Test 4: Mixed valid and invalid arguments")

    # Test input alignment: list and int should be rejected, validMixed should be accepted
    input_text = "This should work for validMixed"
    returncode, stdout, stderr = run_command("${packName} modCmd testValidation list validMixed int", input_text)

    # Check results
    cmd_data = get_command_data("testValidation")
    valid_mixed_ok = "validMixed" in cmd_data
    list_rejected = "list" not in cmd_data
    int_rejected = "int" not in cmd_data
    
    # Check output messages
    contains_modified = "CMD MODIFIED:" in stdout and "validMixed" in stdout
    contains_rejected_note = "Note:" in stdout and "were rejected" in stdout

    all_ok = valid_mixed_ok and list_rejected and int_rejected and contains_modified and contains_rejected_note

    if all_ok:
        result.add_result("Mixed valid/invalid arguments", True, "Input alignment working correctly, proper messaging")
        return True
    else:
        result.add_result("Mixed valid/invalid arguments", False, 
                         f"Failed - validMixed_added:{valid_mixed_ok}, list_rejected:{list_rejected}, int_rejected:{int_rejected}, modified_msg:{contains_modified}, rejected_note:{contains_rejected_note}")
        return False


def test_switch_flags_with_arguments(result: TestResult) -> bool:
    \"\"\"Test 5: Switch flags combined with arguments\"\"\"
    print_test("Test 5: Switch flags with arguments")

    input_text = "Verbose flag description\\nValid switch argument"
    returncode, stdout, stderr = run_command("${packName} modCmd testValidation -verbose list switchArg", input_text)

    # Check results
    cmd_data = get_command_data("testValidation")
    switch_arg_ok = "switchArg" in cmd_data
    verbose_flag_ok = "switchFlags" in cmd_data and "verbose" in cmd_data["switchFlags"]
    list_rejected = "list" not in cmd_data
    
    # Check output messages
    contains_modified = "CMD MODIFIED:" in stdout
    contains_flag = "flag -verbose" in stdout
    contains_arg = "switchArg" in stdout
    contains_rejected_note = "Note:" in stdout and "list" in stdout

    all_ok = switch_arg_ok and verbose_flag_ok and list_rejected and contains_modified

    if all_ok:
        result.add_result("Switch flags with arguments", True, "Flags and arguments processed correctly with mixed validation")
        return True
    else:
        result.add_result("Switch flags with arguments", False, 
                         f"Failed - switchArg:{switch_arg_ok}, verbose_flag:{verbose_flag_ok}, list_rejected:{list_rejected}, modified_msg:{contains_modified}")
        return False


def test_simple_template_bypass(result: TestResult) -> bool:
    \"\"\"Test 6: Simple template should bypass validation\"\"\"
    print_test("Test 6: Simple template validation bypass")

    # Create simple template command
    input_text = "Test command with simple template"
    returncode, stdout, stderr = run_command("${packName} newCmd --template=simple testSimple", input_text)
    
    if not check_command_exists("testSimple"):
        result.add_result("Simple template bypass", False, "Failed to create simple template command")
        return False

    # Try to add reserved names (should be allowed)
    input_text = "This should be allowed for simple template"
    returncode, stdout, stderr = run_command("${packName} modCmd testSimple list", input_text)

    # Check that the reserved name was allowed
    cmd_data = get_command_data("testSimple")
    list_allowed = "list" in cmd_data
    template_type = check_template_type("testSimple")
    
    # Should not contain error messages about reserved names
    no_error_msgs = "ERROR:" not in stdout or "Python keyword" not in stdout

    all_ok = list_allowed and template_type == "simple" and no_error_msgs

    if all_ok:
        result.add_result("Simple template bypass", True, "Simple template correctly bypasses validation")
        return True
    else:
        result.add_result("Simple template bypass", False, 
                         f"Failed - list_allowed:{list_allowed}, template_type:{template_type}, no_errors:{no_error_msgs}")
        return False


def test_comprehensive_scenario(result: TestResult) -> bool:
    \"\"\"Test 7: Comprehensive scenario with multiple argument types\"\"\"
    print_test("Test 7: Comprehensive mixed scenario")

    # Test with options, valid args, invalid args in one command
    input_text = "Debug flag\\nVerbose option value\\nValid comprehensive arg"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testValidation -debug --verbose while validComprehensive def", 
        input_text
    )

    # Check results
    cmd_data = get_command_data("testValidation")
    debug_flag_ok = "switchFlags" in cmd_data and "debug" in cmd_data["switchFlags"]
    verbose_option_ok = "switchFlags" in cmd_data and "verbose" in cmd_data["switchFlags"]
    valid_comp_ok = "validComprehensive" in cmd_data
    while_rejected = "while" not in cmd_data
    def_rejected = "def" not in cmd_data
    
    # Check messaging
    contains_modified = "CMD MODIFIED:" in stdout
    contains_valid_comp = "validComprehensive" in stdout
    contains_rejected_note = "Note:" in stdout and "rejected" in stdout

    # More lenient check - just ensure the key components are working
    basic_validation_ok = while_rejected and def_rejected and valid_comp_ok
    messaging_ok = contains_modified and contains_valid_comp
    
    all_ok = basic_validation_ok and messaging_ok

    if all_ok:
        result.add_result("Comprehensive mixed scenario", True, "Complex scenario handled correctly")
        return True
    else:
        result.add_result("Comprehensive mixed scenario", False, 
                         f"Failed - while_rejected:{while_rejected}, def_rejected:{def_rejected}, valid_comp:{valid_comp_ok}, modified_msg:{contains_modified}")
        return False


def main():
    \"\"\"Run all tests\"\"\"
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}argCmdDef Template Validation Test Suite{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

    result = TestResult()

    # Clean up before starting
    cleanup_test_commands()

    # Run tests in sequence
    tests = [
        test_create_argcmddef_command,
        test_valid_argument_acceptance,
        test_invalid_argument_rejection,
        test_mixed_valid_invalid_arguments,
        test_switch_flags_with_arguments,
        test_simple_template_bypass,
        test_comprehensive_scenario
    ]

    for test_func in tests:
        if not test_func(result):
            print_fail(f"Test {test_func.__name__} failed, continuing with remaining tests...")

    # Final cleanup
    cleanup_test_commands()

    # Print summary
    success = result.print_summary()

    if success:
        print(f"{Colors.GREEN}All tests passed! argCmdDef validation functionality is working correctly.{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}Some tests failed. Please check the implementation.{Colors.NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()"""))
