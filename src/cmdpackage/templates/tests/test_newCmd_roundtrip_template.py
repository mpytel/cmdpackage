#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

test_newCmd_roundtrip_template = Template(dedent("""#!/usr/bin/env python3
\"\"\"
Test script for newCmd round trip functionality
Tests command creation with various flags and templates, then cleanup with rmCmd
\"\"\"

import os
import sys
import json
import subprocess
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
        else:
            self.failed += 1

    def print_summary(self):
        total = self.passed + self.failed
        print(f"\\n{Colors.BLUE}TEST SUMMARY:{Colors.NC}")
        print(f"Total tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.NC}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.NC}")

        if self.failed > 0:
            print(f"\\n{Colors.RED}Failed tests:{Colors.NC}")
            for test_name, passed, message in self.tests:
                if not passed:
                    print(f"  - {test_name}: {message}")


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
        # Change to project directory
        project_dir = Path(__file__).parent.parent

        # Activate virtual environment and run command
        full_cmd = f"cd {project_dir} && source env/${packName}/bin/activate && {cmd}"

        result = subprocess.run(
            full_cmd,
            shell=True,
            input=input_text,
            text=True,
            capture_output=capture_output,
            executable="/bin/bash",
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_command_exists(cmd_name: str) -> bool:
    \"\"\"Check if command exists in commands.json\"\"\"
    commands_file = (
        Path(__file__).parent.parent / "src" / "${packName}" / "commands" / "commands.json"
    )
    try:
        with open(commands_file, "r") as f:
            data = json.load(f)
        return cmd_name in data
    except Exception:
        return False


def check_flags_in_${packName}rc(cmd_name: str) -> bool:
    \"\"\"Check if flags exist in .${packName}rc\"\"\"
    ${packName}rc_file = Path(__file__).parent.parent / "src" / ".${packName}rc"
    try:
        if not ${packName}rc_file.exists():
            return False
        with open(${packName}rc_file, "r") as f:
            data = json.load(f)
        return cmd_name in data.get("commandFlags", {})
    except Exception:
        return False


def check_flag_value(cmd_name: str, flag_name: str, expected_value) -> bool:
    \"\"\"Check if a specific flag has the expected value in .${packName}rc\"\"\"
    ${packName}rc_file = Path(__file__).parent.parent / "src" / ".${packName}rc"
    try:
        if not ${packName}rc_file.exists():
            return False
        with open(${packName}rc_file, "r") as f:
            data = json.load(f)
        command_flags = data.get("commandFlags", {}).get(cmd_name, {})
        return command_flags.get(flag_name) == expected_value
    except Exception:
        return False


def file_exists(file_path: str) -> bool:
    \"\"\"Check if a file exists\"\"\"
    full_path = Path(__file__).parent.parent / file_path
    return full_path.exists()


def file_contains(file_path: str, search_text: str) -> bool:
    \"\"\"Check if a file contains specific text\"\"\"
    full_path = Path(__file__).parent.parent / file_path
    try:
        with open(full_path, "r") as f:
            content = f.read()
        return search_text in content
    except Exception:
        return False


def cleanup_test_commands():
    \"\"\"Clean up any existing test commands\"\"\"
    print_info("Cleaning up any existing test commands...")

    # Regular test commands plus template test commands
    test_commands = ["testCmd01", "testCmd02", "testCmd03", "invalidTest"]

    # Add template-based test commands
    template_dir = (
        Path(__file__).parent.parent / "src" / "${packName}" / "commands" / "templates"
    )
    for template_file in template_dir.glob("*.py"):
        if template_file.name != "__init__.py":
            template_name = template_file.stem
            test_cmd_name = f"test{template_name.capitalize()}"
            test_commands.append(test_cmd_name)

    # Remove test commands if they exist
    for cmd in test_commands:
        if check_command_exists(cmd):
            run_command(f'echo "y" | ${packName} rmCmd {cmd}')

        # Remove .py files if they exist
        py_file = f"src/${packName}/commands/{cmd}.py"
        if file_exists(py_file):
            os.remove(Path(__file__).parent.parent / py_file)

    # Clean up .${packName} if it exists
    ${packName}rc_file = Path(__file__).parent.parent / "src" / ".${packName}rc"
    if ${packName}rc_file.exists():
        ${packName}rc_file.unlink()

    print_pass("Cleanup completed")


def test_basic_command(result: TestResult) -> bool:
    \"\"\"Test 1: Basic command creation with default template\"\"\"
    print_test("Test 1: Basic command creation with default template")

    # Create basic command
    input_text = "Test command description\\nFirst argument description"
    returncode, stdout, stderr = run_command("${packName} newCmd testCmd01 arg1", input_text)

    if not check_command_exists("testCmd01"):
        print_fail("Command testCmd01 was not created")
        result.add_result(
            "Basic command creation", False, "Command not found in commands.json"
        )
        return False

    print_pass("Command testCmd01 created successfully")

    if not file_exists("src/${packName}/commands/testCmd01.py"):
        print_fail("Python file testCmd01.py was not created")
        result.add_result("Basic command creation", False, "Python file not created")
        return False

    print_pass("Python file testCmd01.py created")
    result.add_result("Basic command creation", True)
    return True


def test_command_with_bool_flags(result: TestResult) -> bool:
    \"\"\"Test 2: Command creation with boolean flags\"\"\"
    print_test("Test 2: Command creation with boolean flags")

    input_text = "Command with flags\\nArgument description\\nEnable verbose mode\\nEnable debug mode"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd testCmd02 arg1 -verbose -debug", input_text
    )

    if not check_command_exists("testCmd02"):
        print_fail("Command testCmd02 was not created")
        result.add_result("Boolean flags creation", False, "Command not created")
        return False

    print_pass("Command testCmd02 created successfully")

    if not check_flags_in_${packName}rc("testCmd02"):
        print_fail("Boolean flags were not saved to .${packName}rc")
        result.add_result("Boolean flags creation", False, "Flags not saved to .${packName}rc")
        return False

    print_pass("Boolean flags saved to .${packName}rc")

    # Check specific flag values
    if not (
        check_flag_value("testCmd02", "verbose", False)
        and check_flag_value("testCmd02", "debug", False)
    ):
        print_fail("Boolean flags do not have correct default values")
        result.add_result("Boolean flags creation", False, "Incorrect default values")
        return False

    print_pass("Boolean flags have correct default values (false)")
    result.add_result("Boolean flags creation", True)
    return True


def test_command_with_string_options(result: TestResult) -> bool:
    \"\"\"Test 3: Command creation with string options and template\"\"\"
    print_test("Test 3: Command creation with string options and template")

    input_text = "Simple command\\nArgument description\\nOutput file path"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd testCmd03 arg1 --output --template=simple", input_text
    )

    if not check_command_exists("testCmd03"):
        print_fail("Command testCmd03 was not created")
        result.add_result("String options and template", False, "Command not created")
        return False

    print_pass("Command testCmd03 created successfully")

    # Check if template flag was saved for newCmd
    if not (
        check_flags_in_${packName}rc("newCmd")
        and check_flag_value("newCmd", "template", "simple")
    ):
        print_fail("Template flag was not saved correctly")
        result.add_result(
            "String options and template", False, "Template flag not saved"
        )
        return False

    print_pass("Template flag saved to .${packName}rc under newCmd")

    # Verify the template was actually used by checking the generated file
    if file_contains(
        "src/${packName}/commands/testCmd03.py", "# Generated using simple template"
    ):
        print_pass("Simple template was used for code generation")
    else:
        print_info("Note: Template verification skipped (template marker not found)")

    result.add_result("String options and template", True)
    return True


def test_flag_toggle(result: TestResult) -> bool:
    \"\"\"Test 4: Flag toggle operations\"\"\"
    print_test("Test 4: Flag toggle operations")

    # Toggle verbose flag on
    returncode, stdout, stderr = run_command("${packName} testCmd02 arg1 +verbose")

    if not check_flag_value("testCmd02", "verbose", True):
        print_fail("Flag +verbose was not toggled correctly")
        result.add_result("Flag toggle operations", False, "+verbose toggle failed")
        return False

    print_pass("Flag +verbose toggled to true")

    # Toggle verbose flag off
    returncode, stdout, stderr = run_command("${packName} testCmd02 arg1 -verbose")

    if not check_flag_value("testCmd02", "verbose", False):
        print_fail("Flag -verbose was not toggled correctly")
        result.add_result("Flag toggle operations", False, "-verbose toggle failed")
        return False

    print_pass("Flag -verbose toggled to false")
    result.add_result("Flag toggle operations", True)
    return True


def test_help_system(result: TestResult) -> bool:
    \"\"\"Test 5: Help system functionality\"\"\"
    print_test("Test 5: Help system functionality")

    # Test command-specific help
    returncode, stdout, stderr = run_command("${packName} testCmd02 -h")

    if returncode != 0:
        print_fail("Command-specific help failed")
        result.add_result("Help system", False, "Help command failed")
        return False

    print_pass("Command-specific help works")

    # Test that help doesn't create unwanted side effects
    ${packName}rc_file = Path(__file__).parent.parent / "src" / ".${packName}rc"
    flags_before = ""
    if ${packName}rc_file.exists():
        flags_before = ${packName}rc_file.read_text()

    run_command("${packName} testCmd02 --help")

    flags_after = ""
    if ${packName}rc_file.exists():
        flags_after = ${packName}rc_file.read_text()

    if flags_before != flags_after:
        print_fail("Help command unexpectedly modified .${packName}rc")
        result.add_result("Help system", False, "Help modified .${packName}rc")
        return False

    print_pass("Help command doesn't modify .${packName}rc")
    result.add_result("Help system", True)
    return True


def test_template_listing(result: TestResult) -> bool:
    \"\"\"Test 6: Template listing functionality\"\"\"
    print_test("Test 6: Template listing functionality")

    returncode, stdout, stderr = run_command("${packName} newCmd --templates")

    if returncode != 0:
        print_fail("Template listing failed")
        result.add_result("Template listing", False, "Command failed")
        return False

    print_pass("Template listing works")
    result.add_result("Template listing", True)
    return True


def test_error_handling(result: TestResult) -> bool:
    \"\"\"Test 7: Error handling\"\"\"
    print_test("Test 7: Error handling")

    # Test invalid template
    input_text = "Test command\\nArgument description"
    returncode, stdout, stderr = run_command(
        "${packName} newCmd invalidTest arg1 --template=nonexistent", input_text
    )

    if check_command_exists("invalidTest"):
        print_fail("Invalid template error not handled correctly")
        result.add_result(
            "Error handling", False, "Command created despite invalid template"
        )
        return False

    print_pass("Invalid template error handled correctly (command not created)")
    result.add_result("Error handling", True)
    return True


def test_rmcmd_cleanup(result: TestResult) -> bool:
    \"\"\"Test 8: Cleanup with rmCmd\"\"\"
    print_test("Test 8: Cleanup with rmCmd")

    # Remove testCmd02 (which has flags in .${packName}rc)
    returncode, stdout, stderr = run_command('echo "y" | ${packName} rmCmd testCmd02')

    if check_command_exists("testCmd02"):
        print_fail("Command testCmd02 was not removed from commands.json")
        result.add_result("rmCmd cleanup", False, "Command not removed from JSON")
        return False

    print_pass("Command testCmd02 removed from commands.json")

    if file_exists("src/${packName}/commands/testCmd02.py"):
        print_fail("Python file testCmd02.py was not removed")
        result.add_result("rmCmd cleanup", False, "Python file not removed")
        return False

    print_pass("Python file testCmd02.py removed")

    if check_flags_in_${packName}rc("testCmd02"):
        print_fail("Command flags were not removed from .${packName}rc")
        result.add_result("rmCmd cleanup", False, "Flags not removed from .${packName}rc")
        return False

    print_pass("Command flags removed from .${packName}rc")
    result.add_result("rmCmd cleanup", True)
    return True


def test_all_templates(result: TestResult) -> bool:
    \"\"\"Test 9: All template functionality\"\"\"
    print_test("Test 9: All template functionality")

    # Get list of available templates
    template_dir = (
        Path(__file__).parent.parent / "src" / "${packName}" / "commands" / "templates"
    )
    templates = []

    for file in template_dir.iterdir():
        if (
            file.suffix == ".py"
            and file.name != "__init__.py"
            and file.name != "argDefTemplate.py"
        ):
            template_name = file.stem
            templates.append(template_name)

    if not templates:
        print_fail("No templates found")
        result.add_result("All templates test", False, "No templates found")
        return False

    print_info(f"Found templates: {', '.join(sorted(templates))}")

    # Test each template
    template_tests_passed = 0
    template_tests_total = 0

    for template_name in sorted(templates):
        template_tests_total += 1
        test_cmd_name = f"test{template_name.capitalize()}"

        print_step(f"Testing template: {template_name}")

        try:
            # Create command with this template
            input_text = f"Test command using {template_name} template\\nTest argument"
            cmd = f"${packName} newCmd {test_cmd_name} arg1 --template={template_name}"
            returncode, stdout, stderr = run_command(cmd, input_text)

            # Check if command was created
            if not check_command_exists(test_cmd_name):
                print_fail(
                    f"Command {test_cmd_name} was not created with template {template_name}"
                )
                continue

            # Check if Python file was created
            py_file = f"src/${packName}/commands/{test_cmd_name}.py"
            if not file_exists(py_file):
                print_fail(
                    f"Python file {test_cmd_name}.py was not created with template {template_name}"
                )
                continue

            # Check if template marker exists
            expected_marker = f"# Generated using {template_name} template"
            if not file_contains(py_file, expected_marker):
                print_fail(
                    f"Template marker not found in {test_cmd_name}.py for template {template_name}"
                )
                continue

            print_pass(f"Template {template_name} works correctly")
            template_tests_passed += 1

        except Exception as e:
            print_fail(f"Template {template_name} test failed with exception: {e}")
            continue

        finally:
            # Clean up the test command
            if check_command_exists(test_cmd_name):
                run_command(f'echo "y" | ${packName} rmCmd {test_cmd_name}')

    # Summary
    if template_tests_passed == template_tests_total:
        print_pass(f"All {template_tests_total} templates work correctly")
        result.add_result("All templates test", True)
        return True
    else:
        print_fail(
            f"Only {template_tests_passed}/{template_tests_total} templates work correctly"
        )
        result.add_result(
            "All templates test",
            False,
            f"Failed {template_tests_total - template_tests_passed} template tests",
        )
        return False


def test_complete_cleanup(result: TestResult) -> bool:
    \"\"\"Test 10: Complete cleanup\"\"\"
    print_test("Test 10: Complete cleanup")

    # Remove remaining test commands
    remaining_commands = ["testCmd01", "testCmd03"]
    for cmd in remaining_commands:
        if check_command_exists(cmd):
            run_command(f'echo "y" | ${packName} rmCmd {cmd}')

    # Verify all test commands are gone (including template test commands)
    test_commands = ["testCmd01", "testCmd02", "testCmd03"]

    # Add template-based test commands to verification
    template_dir = (
        Path(__file__).parent.parent / "src" / "${packName}" / "commands" / "templates"
    )
    for template_file in template_dir.glob("*.py"):
        if template_file.name != "__init__.py":
            template_name = template_file.stem
            test_cmd_name = f"test{template_name.capitalize()}"
            test_commands.append(test_cmd_name)

    remaining_count = sum(1 for cmd in test_commands if check_command_exists(cmd))

    if remaining_count > 0:
        print_fail(f"{remaining_count} test commands still exist")
        result.add_result(
            "Complete cleanup", False, f"{remaining_count} commands remain"
        )
        return False

    print_pass("All test commands removed")

    # Check if .${packName}rc is cleaned up appropriately
    ${packName}rc_file = Path(__file__).parent.parent / "src" / ".${packName}rc"
    if ${packName}rc_file.exists():
        content = ${packName}rc_file.read_text()
        if any(cmd in content for cmd in test_commands):
            print_fail(".${packName}rc still contains test command flags")
            result.add_result("Complete cleanup", False, ".${packName}rc not cleaned")
            return False

    print_pass(".${packName}rc cleaned up (no test command flags remain)")
    result.add_result("Complete cleanup", True)
    return True


def main():
    \"\"\"Main test execution\"\"\"
    print("=" * 48)
    print("${packName} NewCmd Round Trip Test (Python Version)")
    print("=" * 48)

    # Check if we're in the right directory
    project_dir = Path(__file__).parent.parent
    if not (project_dir / "src" / "${packName}").exists():
        print_fail("Error: Not in ${packName} project directory")
        return 1

    # Check virtual environment
    venv_activate = project_dir / "env" / "${packName}" / "bin" / "activate"
    if not venv_activate.exists():
        print_fail("Warning: Virtual environment not found at env/${packName}/bin/activate")
        print_info("Please ensure the virtual environment is set up correctly")
        return 1

    print_info("Virtual environment found")

    result = TestResult()

    print("Starting newCmd round trip tests...")
    print()

    # Initial cleanup
    cleanup_test_commands()
    print()

    # Run all tests
    test_functions = [
        test_basic_command,
        test_command_with_bool_flags,
        test_command_with_string_options,
        test_flag_toggle,
        test_help_system,
        test_template_listing,
        test_error_handling,
        test_rmcmd_cleanup,
        test_all_templates,
        test_complete_cleanup,
    ]

    for test_func in test_functions:
        try:
            test_func(result)
        except Exception as e:
            print_fail(f"Test failed with exception: {e}")
            result.add_result(test_func.__name__, False, str(e))
        print()

    # Print results
    if result.failed == 0:
        print("=" * 48)
        print(f"{Colors.GREEN}All tests completed successfully!{Colors.NC}")
        print("=" * 48)
        return 0
    else:
        print("=" * 48)
        print(f"{Colors.RED}Some tests failed!{Colors.NC}")
        print("=" * 48)
        result.print_summary()
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""))

