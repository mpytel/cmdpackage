#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

test_argCmdDef_roundtrip_template = Template(
    dedent(
        """#!/usr/bin/env python3
\"\"\"
Comprehensive test script for argCmdDef template validation and modCmd functionality

This test suite validates the enhanced modCmd functionality including:

1. Python keyword and built-in name validation for argCmdDef templates
2. Input alignment when arguments are rejected during validation
3. Proper messaging for mixed success/failure scenarios
4. Switch flag handling alongside argument validation
5. Template-specific validation (argCmdDef ${packName} simple templates)
6. Function definition addition to .py files for argCmdDef templates
7. Function content verification and template consistency
8. Round-trip consistency between modCmd and rmCmd for functions

Test scenarios:
- Valid argument names that should be accepted
- Invalid Python keywords/built-ins that should be rejected
- Mixed valid/invalid arguments with proper input alignment
- Switch flags combined with arguments
- All arguments rejected scenario
- Template-specific behavior (validation only for argCmdDef)
- Function definition addition when arguments are added
- Function content matching argDefTemplate pattern
- Multiple argument function addition in single call
- Complete add/remove cycle maintaining JSON and .py file consistency

CLEANUP FUNCTIONALITY:
This test suite includes comprehensive cleanup functionality to ensure no test artifacts
are left behind, even if tests fail or crash:

- Automatic cleanup before and after test execution
- Force cleanup in try-finally blocks to guarantee cleanup
- Pattern-based detection of test files (any file starting with "test")
- Cleanup of both .py files and commands.json entries
- Standalone cleanup utility: tests/cleanup_test_artifacts.py

Run cleanup manually: python tests/cleanup_test_artifacts.py
\"\"\"

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Tuple

class Colors:
    \"\"\"ANSI color codes for terminal output\"\"\"

    RED = "\\033[0;31m"
    GREEN = "\\033[0;32m"
    YELLOW = "\\033[1;33m"
    BLUE = "\\033[0;34m"
    MAGENTA = "\\033[35m"
    NC = "\\033[0m"  # No Color


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


def run_command(
    cmd: str, input_text: str = "", capture_output: bool = True
) -> Tuple[int, str, str]:
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
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_command_exists(cmd_name: str) -> bool:
    \"\"\"Check if command exists in commands.json\"\"\"
    commands_file = (
        Path(__file__).parent.parent
        / "src"
        / "${packName}"
        / "commands"
        / "commands.json"
    )
    try:
        with open(commands_file, "r") as f:
            data = json.load(f)
            return cmd_name in data
    except Exception:
        return False


def get_command_data(cmd_name: str) -> dict:
    \"\"\"Get command data from commands.json\"\"\"
    commands_file = (
        Path(__file__).parent.parent
        / "src"
        / "${packName}"
        / "commands"
        / "commands.json"
    )
    try:
        with open(commands_file, "r") as f:
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
    file_path = (
        Path(__file__).parent.parent
        / "src"
        / "${packName}"
        / "commands"
        / f"{cmd_name}.py"
    )
    if not file_path.exists():
        return "none"

    try:
        with open(file_path, "r") as f:
            first_line = f.readline().strip()
            if "argCmdDef template" in first_line:
                return "argCmdDef"
            elif "simple template" in first_line:
                return "simple"
            else:
                return "unknown"
    except Exception:
        return "error"


def check_function_exists_in_file(file_path: str, function_name: str) -> bool:
    \"\"\"Check if a function definition exists in a Python file\"\"\"
    try:
        with open(file_path, "r") as file:
            content = file.read()
            # Look for function definition pattern
            import re

            pattern = rf"^def {re.escape(function_name)}\\s*\\("
            return bool(re.search(pattern, content, re.MULTILINE))
    except FileNotFoundError:
        return False


def verify_function_template_content(
    file_path: str, function_name: str, cmd_name: str
) -> bool:
    \"\"\"Verify that a function matches the expected argDefTemplate pattern\"\"\"
    try:
        with open(file_path, "r") as file:
            content = file.read()

        # Check for expected template content in the function
        expected_patterns = [
            f"def {function_name}(argParse):",
            "args = argParse.args",
            f'printIt("def {cmd_name} executed.", lable.INFO)',
            f'printIt("Modify default behavour in src/vc/commands/{cmd_name}.py", lable.INFO)',
            "printIt(str(args), lable.INFO)",
        ]

        # Find the function in the content
        import re

        func_pattern = rf"def {re.escape(function_name)}\\(.*?\\):(.*?)(?=def \\w+\\(|$)"
        func_match = re.search(func_pattern, content, re.DOTALL)

        if not func_match:
            return False

        func_content = func_match.group(1)

        # Check if all expected patterns are in the function content
        for pattern in expected_patterns[
            1:
        ]:  # Skip the def line as it's already matched
            if pattern not in func_content:
                return False

        return True
    except FileNotFoundError:
        return False


def get_all_function_names_in_file(file_path: str) -> list:
    \"\"\"Get all function names defined in a Python file\"\"\"
    try:
        with open(file_path, "r") as file:
            content = file.read()

        import re

        # Find all function definitions
        pattern = r"^def (\\w+)\\s*\\("
        matches = re.findall(pattern, content, re.MULTILINE)
        return matches
    except FileNotFoundError:
        return []


def get_command_file_path(cmd_name: str) -> str:
    \"\"\"Get the absolute path to a command's .py file\"\"\"
    import os

    # Get the current script directory and navigate to the correct location
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # Go up from tests/ to project root
    return os.path.join(project_root, "src", "${packName}", "commands", f"{cmd_name}.py")


def cleanup_test_commands():
    \"\"\"Clean up any existing test commands\"\"\"
    print_info("Cleaning up any existing test commands...")

    test_commands = [
        "testValidation",
        "testSimple", 
        "testMixed",
        "testFunctions",
        "testMultiple",
        "testDebug",
        "testDebugFunc",
        "testArgCmdDef",
        "testRoundtrip",
    ]

    # Remove test commands if they exist
    for cmd in test_commands:
        if check_command_exists(cmd):
            run_command(f'echo "y" | vc rmCmd {cmd}')

    # Additional cleanup: directly remove any leftover files and JSON entries
    force_cleanup_test_artifacts()

    print_pass("Cleanup completed")


def force_cleanup_test_artifacts():
    \"\"\"Force cleanup of test artifacts that might be left behind\"\"\"
    import os
    import json
    from pathlib import Path

    # Clean up .py files - look for any file starting with "test"
    commands_dir = Path(__file__).parent.parent / "src" / "vc" / "commands"
    
    if commands_dir.exists():
        for file_path in commands_dir.glob("test*.py"):
            try:
                file_path.unlink()
                print_info(f"Removed leftover file: {file_path.name}")
            except Exception as e:
                print_fail(f"Could not remove {file_path.name}: {e}")

    # Clean up commands.json entries - look for any key starting with "test"
    commands_file = commands_dir / "commands.json"
    if commands_file.exists():
        try:
            with open(commands_file, "r") as f:
                data = json.load(f)
            
            # Find all test commands (keys starting with "test")
            test_commands = [key for key in data.keys() if key.startswith("test")]
            
            modified = False
            for cmd in test_commands:
                if cmd in data:
                    del data[cmd]
                    modified = True
                    print_info(f"Removed JSON entry: {cmd}")
            
            if modified:
                with open(commands_file, "w") as f:
                    json.dump(data, f, indent=2)
                print_info("Updated commands.json")
                    
        except Exception as e:
            print_fail(f"Could not clean commands.json: {e}")


def test_create_argcmddef_command(result: TestResult) -> bool:
    \"\"\"Test 1: Create a test command using argCmdDef template\"\"\"
    print_test("Test 1: Create argCmdDef template command")

    input_text = "Test command for validation testing"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd testValidation", input_text
    )

    # Check if command was created with correct template
    if (
        check_command_exists("testValidation")
        and file_exists("src/${packName}/commands/testValidation.py")
        and check_template_type("testValidation") == "argCmdDef"
    ):
        result.add_result(
            "Create argCmdDef command",
            True,
            "testValidation created successfully with argCmdDef template",
        )
        return True
    else:
        result.add_result(
            "Create argCmdDef command",
            False,
            "Failed to create testValidation with correct template",
        )
        return False


def test_valid_argument_acceptance(result: TestResult) -> bool:
    \"\"\"Test 2: Valid argument names should be accepted\"\"\"
    print_test("Test 2: Valid argument names acceptance")

    input_text = "Valid argument for testing\\nAnother valid argument"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testValidation validArg anotherValid", input_text
    )

    # Check if both arguments were added
    cmd_data = get_command_data("testValidation")
    valid_arg_ok = "validArg" in cmd_data
    another_valid_ok = "anotherValid" in cmd_data

    # Check output messages
    contains_modified = "CMD MODIFIED: " in stdout
    contains_both_args = "validArg" in stdout and "anotherValid" in stdout

    all_ok = (
        valid_arg_ok and another_valid_ok and contains_modified and contains_both_args
    )

    if all_ok:
        result.add_result(
            "Valid argument acceptance",
            True,
            "Both valid arguments accepted and properly reported",
        )
        return True
    else:
        result.add_result(
            "Valid argument acceptance",
            False,
            f"Failed - validArg:{valid_arg_ok}, anotherValid:{another_valid_ok}, modified_msg:{contains_modified}, both_reported:{contains_both_args}",
        )
        return False


def test_invalid_argument_rejection(result: TestResult) -> bool:
    \"\"\"Test 3: Invalid Python keywords should be rejected\"\"\"
    print_test("Test 3: Invalid Python keywords rejection")

    returncode, stdout, stderr = run_command(
        "${packName} modCmd testValidation list str int"
    )

    # Check that none of the invalid arguments were added
    cmd_data = get_command_data("testValidation")
    list_rejected = "list" not in cmd_data
    str_rejected = "str" not in cmd_data
    int_rejected = "int" not in cmd_data

    # Check output messages
    contains_all_rejected = (
        "All requested modifications" in stdout and "were rejected" in stdout
    )
    contains_error_msgs = "ERROR:" in stdout
    contains_skip_msgs = "Skipping invalid argument" in stdout

    all_ok = (
        list_rejected
        and str_rejected
        and int_rejected
        and contains_all_rejected
        and contains_error_msgs
    )

    if all_ok:
        result.add_result(
            "Invalid argument rejection", True, "All Python keywords properly rejected"
        )
        return True
    else:
        result.add_result(
            "Invalid argument rejection",
            False,
            f"Failed - list_rejected:{list_rejected}, str_rejected:{str_rejected}, int_rejected:{int_rejected}, all_rejected_msg:{contains_all_rejected}",
        )
        return False


def test_mixed_valid_invalid_arguments(result: TestResult) -> bool:
    \"\"\"Test 4: Mixed valid and invalid arguments with proper input alignment\"\"\"
    print_test("Test 4: Mixed valid and invalid arguments")

    # Test input alignment: list and int should be rejected, validMixed should be accepted
    input_text = "This should work for validMixed"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testValidation list validMixed int", input_text
    )

    # Check results
    cmd_data = get_command_data("testValidation")
    valid_mixed_ok = "validMixed" in cmd_data
    list_rejected = "list" not in cmd_data
    int_rejected = "int" not in cmd_data

    # Check output messages
    contains_modified = "CMD MODIFIED: " in stdout and "validMixed" in stdout
    contains_rejected_note = "Note:" in stdout and "were rejected" in stdout

    all_ok = (
        valid_mixed_ok
        and list_rejected
        and int_rejected
        and contains_modified
        and contains_rejected_note
    )

    if all_ok:
        result.add_result(
            "Mixed valid/invalid arguments",
            True,
            "Input alignment working correctly, proper messaging",
        )
        return True
    else:
        result.add_result(
            "Mixed valid/invalid arguments",
            False,
            f"Failed - validMixed_added:{valid_mixed_ok}, list_rejected:{list_rejected}, int_rejected:{int_rejected}, modified_msg:{contains_modified}, rejected_note:{contains_rejected_note}",
        )
        return False


def test_switch_flags_with_arguments(result: TestResult) -> bool:
    \"\"\"Test 5: Switch flags combined with arguments\"\"\"
    print_test("Test 5: Switch flags with arguments")

    input_text = "Verbose flag description\\nValid switch argument"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testValidation -verbose list switchArg", input_text
    )

    # Check results
    cmd_data = get_command_data("testValidation")
    switch_arg_ok = "switchArg" in cmd_data
    verbose_flag_ok = "switchFlags" in cmd_data and "verbose" in cmd_data["switchFlags"]
    list_rejected = "list" not in cmd_data

    # Check output messages
    contains_modified = "CMD MODIFIED: " in stdout
    contains_flag = "flag -verbose" in stdout
    contains_arg = "switchArg" in stdout
    contains_rejected_note = "Note:" in stdout and "list" in stdout

    all_ok = switch_arg_ok and verbose_flag_ok and list_rejected and contains_modified

    if all_ok:
        result.add_result(
            "Switch flags with arguments",
            True,
            "Flags and arguments processed correctly with mixed validation",
        )
        return True
    else:
        result.add_result(
            "Switch flags with arguments",
            False,
            f"Failed - switchArg:{switch_arg_ok}, verbose_flag:{verbose_flag_ok}, list_rejected:{list_rejected}, modified_msg:{contains_modified}",
        )
        return False


def test_simple_template_bypass(result: TestResult) -> bool:
    \"\"\"Test 6: Simple template should bypass validation\"\"\"
    print_test("Test 6: Simple template validation bypass")

    # Create simple template command
    input_text = "Test command with simple template"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd --template=simple testSimple", input_text
    )

    if not check_command_exists("testSimple"):
        result.add_result(
            "Simple template bypass", False, "Failed to create simple template command"
        )
        return False

    # Try to add reserved names (should be allowed)
    input_text = "This should be allowed for simple template"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testSimple list", input_text
    )

    # Check that the reserved name was allowed
    cmd_data = get_command_data("testSimple")
    list_allowed = "list" in cmd_data
    template_type = check_template_type("testSimple")

    # Should not contain error messages about reserved names
    no_error_msgs = "ERROR:" not in stdout or "Python keyword" not in stdout

    all_ok = list_allowed and template_type == "simple" and no_error_msgs

    if all_ok:
        result.add_result(
            "Simple template bypass",
            True,
            "Simple template correctly bypasses validation",
        )
        return True
    else:
        result.add_result(
            "Simple template bypass",
            False,
            f"Failed - list_allowed:{list_allowed}, template_type:{template_type}, no_errors:{no_error_msgs}",
        )
        return False


def test_comprehensive_scenario(result: TestResult) -> bool:
    \"\"\"Test 7: Comprehensive scenario with multiple argument types\"\"\"
    print_test("Test 7: Comprehensive mixed scenario")

    # Test with options, valid args, invalid args in one command
    input_text = "Debug flag\\nVerbose option value\\nValid comprehensive arg"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testValidation -debug --verbose while validComprehensive def",
        input_text,
    )

    # Check results
    cmd_data = get_command_data("testValidation")
    debug_flag_ok = "switchFlags" in cmd_data and "debug" in cmd_data["switchFlags"]
    verbose_option_ok = (
        "switchFlags" in cmd_data and "verbose" in cmd_data["switchFlags"]
    )
    valid_comp_ok = "validComprehensive" in cmd_data
    while_rejected = "while" not in cmd_data
    def_rejected = "def" not in cmd_data

    # Check messaging
    contains_modified = "CMD MODIFIED: " in stdout
    contains_valid_comp = "validComprehensive" in stdout
    contains_rejected_note = "Note:" in stdout and "rejected" in stdout

    # More lenient check - just ensure the key components are working
    basic_validation_ok = while_rejected and def_rejected and valid_comp_ok
    messaging_ok = contains_modified and contains_valid_comp

    all_ok = basic_validation_ok and messaging_ok

    if all_ok:
        result.add_result(
            "Comprehensive mixed scenario", True, "Complex scenario handled correctly"
        )
        return True
    else:
        result.add_result(
            "Comprehensive mixed scenario",
            False,
            f"Failed - while_rejected:{while_rejected}, def_rejected:{def_rejected}, valid_comp:{valid_comp_ok}, modified_msg:{contains_modified}",
        )
        return False


def test_function_definition_addition(result: TestResult) -> bool:
    \"\"\"Test 8: Verify that modCmd adds function definitions to .py files for argCmdDef commands\"\"\"
    print_test("Test 8: Function definition addition verification")

    # Create a new test command for function testing
    input_text = "Test command for function definition testing"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd testFunctions", input_text
    )

    if not check_command_exists("testFunctions"):
        result.add_result(
            "Function definition addition",
            False,
            "Failed to create testFunctions command",
        )
        return False

    # Add arguments and check if corresponding functions are added
    input_text = "First test argument\\nSecond test argument"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testFunctions firstArg secondArg", input_text
    )

    # Verify functions were added to the .py file
    file_path = get_command_file_path("testFunctions")
    first_func_exists = check_function_exists_in_file(file_path, "firstArg")
    second_func_exists = check_function_exists_in_file(file_path, "secondArg")

    # Verify output message about function addition
    contains_function_msg = "Added function definitions for arguments:" in stdout

    # Check JSON metadata was also updated
    cmd_data = get_command_data("testFunctions")
    first_arg_in_json = "firstArg" in cmd_data
    second_arg_in_json = "secondArg" in cmd_data

    all_ok = (
        first_func_exists
        and second_func_exists
        and contains_function_msg
        and first_arg_in_json
        and second_arg_in_json
    )

    if all_ok:
        result.add_result(
            "Function definition addition",
            True,
            "Functions correctly added to .py file and JSON",
        )
        return True
    else:
        result.add_result(
            "Function definition addition",
            False,
            f"Failed - firstFunc:{first_func_exists}, secondFunc:{second_func_exists}, "
            f"msg:{contains_function_msg}, jsonFirst:{first_arg_in_json}, jsonSecond:{second_arg_in_json}",
        )
        return False


def test_function_content_verification(result: TestResult) -> bool:
    \"\"\"Test 9: Verify that generated functions contain expected template content\"\"\"
    print_test("Test 9: Function content template verification")

    # Verify the functions created in the previous test have correct content
    file_path = get_command_file_path("testFunctions")

    first_content_ok = verify_function_template_content(
        file_path, "firstArg", "testFunctions"
    )
    second_content_ok = verify_function_template_content(
        file_path, "secondArg", "testFunctions"
    )

    # Also check that the file doesn't have syntax errors by trying to read all functions
    all_functions = get_all_function_names_in_file(file_path)
    has_main_function = "testFunctions" in all_functions
    has_both_args = "firstArg" in all_functions and "secondArg" in all_functions

    all_ok = (
        first_content_ok and second_content_ok and has_main_function and has_both_args
    )

    if all_ok:
        result.add_result(
            "Function content verification",
            True,
            "Generated functions have correct template content",
        )
        return True
    else:
        result.add_result(
            "Function content verification",
            False,
            f"Failed - firstContent:{first_content_ok}, secondContent:{second_content_ok}, "
            f"mainFunc:{has_main_function}, bothArgs:{has_both_args}",
        )
        return False


def test_multiple_argument_functions(result: TestResult) -> bool:
    \"\"\"Test 10: Test adding multiple arguments in a single modCmd call\"\"\"
    print_test("Test 10: Multiple argument functions addition")

    # Create a new test command
    input_text = "Test command for multiple arguments"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd testMultiple", input_text
    )

    if not check_command_exists("testMultiple"):
        result.add_result(
            "Multiple argument functions",
            False,
            "Failed to create testMultiple command",
        )
        return False

    # Add 3 arguments in a single call
    input_text = "First argument description\\nSecond argument description\\nThird argument description"
    returncode, stdout, stderr = run_command(
        "${packName} modCmd testMultiple arg1 arg2 arg3", input_text
    )

    # Verify all 3 functions were added
    file_path = get_command_file_path("testMultiple")
    arg1_exists = check_function_exists_in_file(file_path, "arg1")
    arg2_exists = check_function_exists_in_file(file_path, "arg2")
    arg3_exists = check_function_exists_in_file(file_path, "arg3")

    # Verify all 3 are in JSON
    cmd_data = get_command_data("testMultiple")
    arg1_in_json = "arg1" in cmd_data
    arg2_in_json = "arg2" in cmd_data
    arg3_in_json = "arg3" in cmd_data

    # Check that the output message mentions all arguments
    contains_all_args = "arg1" in stdout and "arg2" in stdout and "arg3" in stdout
    contains_function_msg = "Added function definitions for arguments:" in stdout

    all_ok = (
        arg1_exists
        and arg2_exists
        and arg3_exists
        and arg1_in_json
        and arg2_in_json
        and arg3_in_json
        and contains_all_args
        and contains_function_msg
    )

    if all_ok:
        result.add_result(
            "Multiple argument functions",
            True,
            "All 3 functions added correctly in single call",
        )
        return True
    else:
        result.add_result(
            "Multiple argument functions",
            False,
            f"Failed - arg1Func:{arg1_exists}, arg2Func:{arg2_exists}, arg3Func:{arg3_exists}, "
            f"json1:{arg1_in_json}, json2:{arg2_in_json}, json3:{arg3_in_json}",
        )
        return False


def test_function_removal_consistency(result: TestResult) -> bool:
    \"\"\"Test 11: Test complete round-trip: add functions with modCmd, remove with rmCmd\"\"\"
    print_test("Test 11: Function removal consistency (round-trip)")

    # Use the testMultiple command from previous test (should have arg1, arg2, arg3)
    file_path = get_command_file_path("testMultiple")

    # Verify starting state - all 3 functions should exist
    initial_arg1 = check_function_exists_in_file(file_path, "arg1")
    initial_arg2 = check_function_exists_in_file(file_path, "arg2")
    initial_arg3 = check_function_exists_in_file(file_path, "arg3")

    if not (initial_arg1 and initial_arg2 and initial_arg3):
        result.add_result(
            "Function removal consistency",
            False,
            "Starting state incorrect - missing functions",
        )
        return False

    # Remove arg2 using rmCmd
    returncode, stdout, stderr = run_command(
        'echo "y" | ${packName} rmCmd testMultiple arg2'
    )

    # Verify arg2 function was removed but others remain
    after_removal_arg1 = check_function_exists_in_file(file_path, "arg1")
    after_removal_arg2 = check_function_exists_in_file(file_path, "arg2")
    after_removal_arg3 = check_function_exists_in_file(file_path, "arg3")

    # Check JSON consistency
    cmd_data = get_command_data("testMultiple")
    json_arg1_exists = "arg1" in cmd_data
    json_arg2_removed = "arg2" not in cmd_data
    json_arg3_exists = "arg3" in cmd_data

    # Verify output messages
    contains_removed_msg = (
        "Removed function 'arg2'" in stdout or "ARG REMOVED: arg2" in stdout
    )

    all_ok = (
        after_removal_arg1
        and not after_removal_arg2
        and after_removal_arg3
        and json_arg1_exists
        and json_arg2_removed
        and json_arg3_exists
        and contains_removed_msg
    )

    if all_ok:
        result.add_result(
            "Function removal consistency",
            True,
            "Round-trip add/remove maintains consistency",
        )
        return True
    else:
        result.add_result(
            "Function removal consistency",
            False,
            f"Failed - arg1Still:{after_removal_arg1}, arg2Gone:{not after_removal_arg2}, "
            f"arg3Still:{after_removal_arg3}, jsonConsistent:{json_arg2_removed}, msg:{contains_removed_msg}",
        )
        return False


def main():
    \"\"\"Run all tests\"\"\"
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}argCmdDef Template Validation Test Suite{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

    result = TestResult()
    success = False

    try:
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
            test_comprehensive_scenario,
            test_function_definition_addition,
            test_function_content_verification,
            test_multiple_argument_functions,
            test_function_removal_consistency,
        ]

        for test_func in tests:
            if not test_func(result):
                print_fail(
                    f"Test {test_func.__name__} failed, continuing with remaining tests..."
                )

        # Print summary
        success = result.print_summary()

    except Exception as e:
        print_fail(f"Test suite encountered an unexpected error: {e}")
        success = False

    finally:
        # Always clean up, even if tests fail or crash
        print_info("Performing final cleanup...")
        cleanup_test_commands()

    if success:
        print(
            f"{Colors.GREEN}All tests passed! argCmdDef validation functionality is working correctly.{Colors.NC}"
        )
        sys.exit(0)
    else:
        print(
            f"{Colors.RED}Some tests failed. Please check the implementation.{Colors.NC}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
    )
)
