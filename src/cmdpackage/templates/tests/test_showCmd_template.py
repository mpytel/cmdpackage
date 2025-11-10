#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

test_showCmd_template = Template(dedent("""#!/usr/bin/env python3
\"\"\"
Test script for showCmd functionality
Tests command inspection capabilities and template information display
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


def run_command(cmd: list, capture_output=True) -> Tuple[int, str, str]:
    \"\"\"Run a command and return (return_code, stdout, stderr)\"\"\"
    try:
        # Activate virtual environment and run command
        env_cmd = ". env/${packName}/bin/activate && " + " ".join(cmd)
        result = subprocess.run(
            env_cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            cwd=Path(__file__).parent.parent,  # Run from project root
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def test_showCmd_basic_functionality(results: TestResult):
    \"\"\"Test basic showCmd functionality with existing commands\"\"\"
    print(f"{Colors.YELLOW}Testing basic showCmd functionality...{Colors.NC}")

    # Test showCmd with '${packName}' command (should exist)
    return_code, stdout, stderr = run_command(["${packName}", "showCmd", "${packName}"])

    if return_code == 0:
        if "${packName}" in stdout:
            results.add_result("showCmd_basic_pi", True, "Successfully shows ${packName} command info")
            print(f"{Colors.GREEN}✓ showCmd ${packName} works{Colors.NC}")
        else:
            results.add_result("showCmd_basic_pi", False, "Output doesn't contain ${packName} command info")
            print(f"{Colors.RED}✗ showCmd ${packName} output unexpected{Colors.NC}")
    else:
        results.add_result("showCmd_basic_pi", False, f"Command failed: {stderr}")
        print(f"{Colors.RED}✗ showCmd ${packName} failed{Colors.NC}")


def test_showCmd_with_newCmd_commands(results: TestResult):
    \"\"\"Test showCmd with commands created by newCmd\"\"\"
    print(f"{Colors.YELLOW}Testing showCmd with newCmd-created commands...{Colors.NC}")

    # Create a test command using +d (silent defaults)
    test_cmd_name = "testShowCmd"

    # Create command
    return_code, stdout, stderr = run_command(["${packName}", "newCmd", test_cmd_name, "testArg", "+d"])

    if return_code == 0:
        print(f"{Colors.GREEN}✓ Created test command {test_cmd_name}{Colors.NC}")

        # Test showCmd with the newly created command
        return_code, stdout, stderr = run_command(["${packName}", "showCmd", test_cmd_name])

        if return_code == 0:
            if test_cmd_name in stdout and ("argCmdDef" in stdout or "template" in stdout.lower()):
                results.add_result("showCmd_newCmd_created", True, f"Successfully shows {test_cmd_name} command info")
                print(f"{Colors.GREEN}✓ showCmd {test_cmd_name} works{Colors.NC}")
            else:
                results.add_result(
                    "showCmd_newCmd_created",
                    False,
                    f"Output doesn't contain expected template info for {test_cmd_name}",
                )
                print(f"{Colors.RED}✗ showCmd {test_cmd_name} output unexpected{Colors.NC}")
        else:
            results.add_result("showCmd_newCmd_created", False, f"showCmd failed: {stderr}")
            print(f"{Colors.RED}✗ showCmd {test_cmd_name} failed{Colors.NC}")

        # Cleanup: Remove test command
        return_code, stdout, stderr = run_command(["${packName}", "rmCmd", test_cmd_name, "+d"])
        if return_code == 0:
            print(f"{Colors.GREEN}✓ Cleaned up test command {test_cmd_name}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠ Warning: Could not clean up {test_cmd_name}{Colors.NC}")
    else:
        results.add_result("showCmd_newCmd_created", False, f"Failed to create test command: {stderr}")
        print(f"{Colors.RED}✗ Failed to create test command{Colors.NC}")


def test_showCmd_different_templates(results: TestResult):
    \"\"\"Test showCmd with commands created using different templates\"\"\"
    print(f"{Colors.YELLOW}Testing showCmd with different template types...{Colors.NC}")

    templates_to_test = ["simple", "classCall", "asyncDef"]

    for template in templates_to_test:
        test_cmd_name = f"test{template}Cmd"

        # Create command with specific template
        return_code, stdout, stderr = run_command(["${packName}", "newCmd", test_cmd_name, "--template", template, "+d"])

        if return_code == 0:
            print(f"{Colors.GREEN}✓ Created {test_cmd_name} with {template} template{Colors.NC}")

            # Test showCmd with this command
            return_code, stdout, stderr = run_command(["${packName}", "showCmd", test_cmd_name])

            if return_code == 0:
                if test_cmd_name in stdout:
                    results.add_result(
                        f"showCmd_{template}_template", True, f"Successfully shows {template} template command info"
                    )
                    print(f"{Colors.GREEN}✓ showCmd {test_cmd_name} ({template}) works{Colors.NC}")
                else:
                    results.add_result(
                        f"showCmd_{template}_template",
                        False,
                        f"Output doesn't contain expected info for {template} command",
                    )
                    print(f"{Colors.RED}✗ showCmd {test_cmd_name} ({template}) output unexpected{Colors.NC}")
            else:
                results.add_result(f"showCmd_{template}_template", False, f"showCmd failed for {template}: {stderr}")
                print(f"{Colors.RED}✗ showCmd {test_cmd_name} ({template}) failed{Colors.NC}")

            # Cleanup
            return_code, stdout, stderr = run_command(["${packName}", "rmCmd", test_cmd_name, "+d"])
            if return_code == 0:
                print(f"{Colors.GREEN}✓ Cleaned up {test_cmd_name}{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}⚠ Warning: Could not clean up {test_cmd_name}{Colors.NC}")
        else:
            results.add_result(f"showCmd_{template}_template", False, f"Failed to create {template} command: {stderr}")
            print(f"{Colors.RED}✗ Failed to create {test_cmd_name} with {template} template{Colors.NC}")


def test_showCmd_nonexistent_command(results: TestResult):
    \"\"\"Test showCmd behavior with non-existent commands\"\"\"
    print(f"{Colors.YELLOW}Testing showCmd with non-existent command...{Colors.NC}")

    # Test with a command that definitely doesn't exist
    return_code, stdout, stderr = run_command(["${packName}", "showCmd", "nonExistentCommand123"])

    # Should either fail gracefully or indicate command doesn't exist
    if return_code != 0 or "not found" in stdout.lower() or "does not exist" in stdout.lower():
        results.add_result("showCmd_nonexistent", True, "Properly handles non-existent command")
        print(f"{Colors.GREEN}✓ showCmd properly handles non-existent command{Colors.NC}")
    else:
        results.add_result("showCmd_nonexistent", False, "Unexpected behavior with non-existent command")
        print(f"{Colors.RED}✗ showCmd behavior unexpected with non-existent command{Colors.NC}")


def test_showCmd_help(results: TestResult):
    \"\"\"Test showCmd help functionality\"\"\"
    print(f"{Colors.YELLOW}Testing showCmd help functionality...{Colors.NC}")

    # Test showCmd help
    return_code, stdout, stderr = run_command(["${packName}", "showCmd", "-h"])

    if return_code == 0:
        if "help" in stdout.lower() or "usage" in stdout.lower() or "showCmd" in stdout:
            results.add_result("showCmd_help", True, "showCmd help works")
            print(f"{Colors.GREEN}✓ showCmd help works{Colors.NC}")
        else:
            results.add_result("showCmd_help", False, "showCmd help output unexpected")
            print(f"{Colors.RED}✗ showCmd help output unexpected{Colors.NC}")
    else:
        results.add_result("showCmd_help", False, f"showCmd help failed: {stderr}")
        print(f"{Colors.RED}✗ showCmd help failed{Colors.NC}")


def main():
    \"\"\"Main test execution\"\"\"
    print(f"{Colors.BLUE}Starting showCmd functionality tests...{Colors.NC}")

    results = TestResult()

    # Run all tests
    test_showCmd_basic_functionality(results)
    test_showCmd_with_newCmd_commands(results)
    test_showCmd_different_templates(results)
    test_showCmd_nonexistent_command(results)
    test_showCmd_help(results)

    # Print summary
    results.print_summary()

    # Return appropriate exit code
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
"""))

