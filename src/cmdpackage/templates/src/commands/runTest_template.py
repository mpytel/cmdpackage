#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

runTest_template = Template(dedent("""# Generated using argCmdDef template
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from ..defs.logIt import printIt, lable, cStr, color
from .commands import Commands

commandJsonDict = {
    "runTest": {
        "description": "Run test(s) in ./tests directory. Use 'listTests' to see available tests.",
        "swi${packName}hFlags": {
            "verbose": {"description": "Verbose output flag", "type": "bool"},
            "stop": {"description": "Stop on failure flag", "type": "bool"},
            "summary": {"description": "Summary only flag", "type": "bool"},
        },
        "testName": "Optional name of specific test to run (without .py extension)",
        "listTests": "List all available tests in the tests directory",
    }
}

cmdObj = Commands()
commands = cmdObj.commands


class TestRunner:
    \"\"\"Class to handle test discovery and execution\"\"\"

    def __init__(
        self,
        verbose: bool = False,
        stop_on_failure: bool = False,
        summary_only: bool = False,
    ):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.verbose = verbose
        self.stop_on_failure = stop_on_failure
        self.summary_only = summary_only
        self.results: Dict[str, Tuple[bool, str, float]] = {}

    def discover_tests(self) -> List[Path]:
        \"\"\"Discover all test files in the tests directory\"\"\"
        if not self.tests_dir.exists():
            printIt(f"Tests directory not found: {self.tests_dir}", lable.ERROR)
            return []

        test_files = []
        for file_path in self.tests_dir.glob("test_*.py"):
            if file_path.is_file():
                test_files.append(file_path)

        return sorted(test_files)

    def run_single_test(self, test_file: Path) -> Tuple[bool, str, float]:
        \"\"\"Run a single test file and return (success, output, duration)\"\"\"
        start_time = time.time()

        try:
            # Change to project directory and activate virtual environment
            cmd = f"cd {self.project_root} && source env/${packName}/bin/activate && python {test_file}"

            if not self.summary_only and self.verbose:
                printIt(f"Running: {cmd}", lable.DEBUG)

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, executable="/bin/bash"
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Combine stdout and stderr for complete output
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\\nSTDERR:\\n{result.stderr}"

            return success, output, duration

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Exception running test: {str(e)}", duration

    def run_all_tests(
        self, test_files: List[Path]
    ) -> Dict[str, Tuple[bool, str, float]]:
        \"\"\"Run all discovered test files\"\"\"
        results = {}

        printIt(f"Running {len(test_files)} test(s)...", lable.INFO)
        print()

        for i, test_file in enumerate(test_files, 1):
            test_name = test_file.stem

            if not self.summary_only:
                printIt(f"[{i}/{len(test_files)}] Running {test_name}...", lable.INFO)

            success, output, duration = self.run_single_test(test_file)
            results[test_name] = (success, output, duration)

            # Show individual test results if not summary only
            if not self.summary_only:
                if success:
                    status = cStr("PASS", color.GREEN)
                else:
                    status = cStr("FAIL", color.RED)
                print(f"  {status} ({duration:.2f}s)")

                if self.verbose or not success:
                    # Show output for failed tests or when verbose is enabled
                    if output.strip():
                        print("  " + "\\n  ".join(output.strip().split("\\n")))
                print()

            # Stop on first failure if requested
            if not success and self.stop_on_failure:
                printIt(f"Stopping due to test failure in {test_name}", lable.WARN)
                break

        return results

    def print_summary(self, results: Dict[str, Tuple[bool, str, float]]):
        \"\"\"Print test execution summary\"\"\"
        total_tests = len(results)
        passed_tests = sum(1 for success, _, _ in results.values() if success)
        failed_tests = total_tests - passed_tests
        total_time = sum(duration for _, _, duration in results.values())

        print("=" * 60)
        printIt("TEST EXECUTION SUMMARY", lable.INFO)
        print("=" * 60)

        print(f"Total Tests:  {total_tests}")
        print(f"{cStr('Passed:', color.GREEN)}       {passed_tests}")
        print(f"{cStr('Failed:', color.RED)}       {failed_tests}")
        print(f"Total Time:   {total_time:.2f}s")

        if failed_tests > 0:
            print(f"\\n{cStr('Failed Tests:', color.RED)}")
            for test_name, (success, output, duration) in results.items():
                if not success:
                    print(f"  • {test_name} ({duration:.2f}s)")
                    if self.verbose and output.strip():
                        # Show first few lines of error output
                        lines = output.strip().split("\\n")
                        for line in lines[:5]:  # Show first 5 lines
                            print(f"    {line}")
                        if len(lines) > 5:
                            print(f"    ... ({len(lines) - 5} more lines)")

        print("=" * 60)

        if failed_tests == 0:
            printIt("🎉 All tests passed!", lable.PASS)
        else:
            printIt(f"❌ {failed_tests} test(s) failed", lable.ERROR)


def runTest(argParse):
    \"\"\"Main runTest function - entry point for the command\"\"\"
    args = argParse.args
    # Filter out flag arguments (starting with + or -)
    theArgs = [
        arg
        for arg in args.arguments
        if not (isinstance(arg, str) and len(arg) > 1 and arg[0] in "+-")
    ]

    # Get command-line flags from .${packName}rc file after flag processing
    from ..classes.optSwi${packName}hes import getCmdSwi${packName}hFlags

    cmd_flags = getCmdSwi${packName}hFlags("runTest")
    verbose = cmd_flags.get("verbose", False)
    stop_on_failure = cmd_flags.get("stop", False)
    summary_only = cmd_flags.get("summary", False)

    runner = TestRunner(
        verbose=verbose, stop_on_failure=stop_on_failure, summary_only=summary_only
    )

    if len(theArgs) == 0:
        # Run all tests
        test_files = runner.discover_tests()
        if not test_files:
            printIt("No test files found in ./tests directory", lable.WARN)
            return

        results = runner.run_all_tests(test_files)
        runner.print_summary(results)

        # Exit with error code if any tests failed
        failed_count = sum(1 for success, _, _ in results.values() if not success)
        if failed_count > 0:
            sys.exit(1)

    elif len(theArgs) == 1:
        # Check if it's the listTests argument
        if theArgs[0] == "listTests":
            listTests(argParse)
            return

        # Run specific test
        test_name = theArgs[0]
        if not test_name.endswith(".py"):
            test_name += ".py"

        test_file = runner.tests_dir / test_name
        if not test_file.exists():
            printIt(f"Test file not found: {test_name}", lable.ERROR)
            printIt("Use '${packName} runTest listTests' to see available tests", lable.INFO)
            return

        printIt(f"Running specific test: {test_name}", lable.INFO)
        success, output, duration = runner.run_single_test(test_file)

        if success:
            status = cStr("PASSED", color.GREEN)
        else:
            status = cStr("FAILED", color.RED)
        print(f"Test {status} ({duration:.2f}s)")

        if output.strip() and (verbose or not success):
            print(output)

        if not success:
            sys.exit(1)
    else:
        printIt(
            "Too many arguments. Usage: ${packName} runTest [testName] or ${packName} runTest listTests",
            lable.ERROR,
        )


def listTests(argParse):
    \"\"\"List all available tests in the tests directory\"\"\"
    runner = TestRunner()
    test_files = runner.discover_tests()

    if not test_files:
        printIt("No test files found in ./tests directory", lable.WARN)
        return

    printIt(f"Available tests in {runner.tests_dir}:", lable.INFO)
    print()

    for i, test_file in enumerate(test_files, 1):
        test_name = test_file.stem

        # Try to get test description from file
        description = "No description available"
        try:
            with open(test_file, "r") as f:
                lines = f.readlines()
                # Look for docstring in first few lines
                for line in lines[:10]:
                    if '\"\"\"' in line and line.strip() != '\"\"\"':
                        description = line.strip().replace('\"\"\"', "").strip()
                        break
        except Exception:
            pass

        print(f"{i:2d}. {cStr(test_name, color.CYAN)}")
        print(f"    {description}")
        print(f"    File: {test_file.name}")
        print()

    print(f"Usage:")
    print(f"  ${packName} runTest                       # Run all tests")
    print(f"  ${packName} runTest {test_files[0].stem}  # Run specific test")
    print(f"  ${packName} runTest -verbose              # Run all tests with verbose output")
    print(f"  ${packName} runTest -stop                 # Stop on first failure")
    print(f"  ${packName} runTest -summary              # Show only summary")
"""))

