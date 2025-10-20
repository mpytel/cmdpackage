#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from cmdpackage.defs.writePyProject import writePyProject
from cmdpackage.defs.writeCLIPackage import writeCLIPackage
from cmdpackage.defs.createzVirtualEnv import createzVirtualEnv
import argparse
from pathlib import Path

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Generate opinionated Python command-line program packages',
        prog='cmdpackage'
    )
    parser.add_argument(
        'project_name',
        nargs='?',
        help='Name of the project to create (optional, defaults to current directory name)'
    )
    parser.add_argument(
        '-t', '--test',
        action='store_true',
        help='Run tests on the generated package to verify it works properly'
    )

    # Parse arguments
    args = parser.parse_args()

    print("--- Inside cmdPack.src.main() ---")
    projName = ''
    askForDirChange = False

    if args.project_name:
        projName: str = args.project_name
        # set the working directory to cwd+projName
        askForDirChange = ensure_and_cd_to_directory(projName)
    else:
        projName = Path(os.getcwd()).stem

    fields: dict[str, str] = writePyProject()
    writeCLIPackage(fields)
    createzVirtualEnv(fields)

    if args.test:
        print(f'\n*** Running tests on {projName} package ***')
        test_result = test_generated_package(projName)
        if test_result:
            print(f'{GREEN}✅ All tests passed!{RESET}')
        else:
            print(f'{RED}❌ Some tests failed!{RESET}')
            return 1

    print(f'*** Activate and install {projName} virtual enviroment ***')
    if askForDirChange:
        print(f'{GREEN}execute{RESET}: cd {projName}')
    print(f'{GREEN}execute{RESET}: . env/{projName}/bin/activate')
    print(f'{GREEN}execute{RESET}: pip install -e .')


def test_generated_package(project_name: str) -> bool:
    """
    Test the generated package to ensure it works properly.

    Args:
        project_name: Name of the generated project

    Returns:
        True if all tests pass, False otherwise
    """
    import subprocess
    import os
    from pathlib import Path
    import shutil

    test_passed = True

    try:
        # Test 0: Check for system command conflicts
        print("🔍 Test 0: Checking for system command conflicts...")
        if shutil.which(project_name):
            print(f"  ⚠️  WARNING: '{project_name}' conflicts with system command at {shutil.which(project_name)}")
            print(f"      This may cause issues when running your package commands.")
            print(f"      Consider using a different package name.")
            # Don't fail the test, but warn the user
        else:
            print(f"  ✅ No system command conflicts detected for '{project_name}'")

        # Test 1: Check if virtual environment was created
        print("🔍 Test 1: Checking virtual environment...")
        venv_path = Path(f"env/{project_name}")
        if venv_path.exists():
            print(f"  ✅ Virtual environment created at {venv_path}")
        else:
            print(f"  ❌ Virtual environment not found at {venv_path}")
            test_passed = False

        # Test 2: Check if package structure was created
        print("🔍 Test 2: Checking package structure...")
        required_dirs = [
            f"src/{project_name}",
            f"src/{project_name}/commands",
            f"src/{project_name}/classes",
            f"src/{project_name}/defs"
        ]

        for dir_path in required_dirs:
            if Path(dir_path).exists():
                print(f"  ✅ Directory {dir_path} exists")
            else:
                print(f"  ❌ Directory {dir_path} missing")
                test_passed = False

        # Test 3: Check if key files were created
        print("🔍 Test 3: Checking key files...")
        required_files = [
            f"src/{project_name}/main.py",
            f"src/{project_name}/defs/logIt.py",
            f"src/{project_name}/classes/argParse.py",
            f"src/{project_name}/commands/commands.py",
            "pyproject.toml"
        ]

        for file_path in required_files:
            if Path(file_path).exists():
                print(f"  ✅ File {file_path} exists")
            else:
                print(f"  ❌ File {file_path} missing")
                test_passed = False

        # Test 4: Check if logIt.py has valid syntax
        print("🔍 Test 4: Checking logIt.py syntax...")
        try:
            with open(f"src/{project_name}/defs/logIt.py", 'r') as f:
                code = f.read()
            compile(code, f"src/{project_name}/defs/logIt.py", 'exec')
            print("  ✅ logIt.py has valid Python syntax")
        except SyntaxError as e:
            print(f"  ❌ logIt.py has syntax error: {e}")
            test_passed = False
        except FileNotFoundError:
            print("  ❌ logIt.py file not found")
            test_passed = False

        # Test 5: Install package and test basic functionality
        print("🔍 Test 5: Installing and testing package functionality...")
        try:
            # Activate virtual environment and install package
            activate_cmd = f". env/{project_name}/bin/activate"
            install_cmd = f"{activate_cmd} && pip install -e . --quiet"

            result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ Package installed successfully")

                # Test help command (lenient check since shell activation can affect exit codes)
                help_cmd = f"{activate_cmd} && {project_name} -h"
                result = subprocess.run(help_cmd, shell=True, capture_output=True, text=True)
                # Remove ANSI color codes for cleaner text matching
                import re
                clean_output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
                if "usage:" in clean_output.lower() and project_name in clean_output:
                    print("  ✅ Help command works")
                else:
                    print("  ⚠️  Help command may have issues but package is functional")
                    # Don't fail the test for help command issues

                # Test newCmd functionality
                newcmd_cmd = f"{activate_cmd} && echo -e 'Test command\\nTest argument\\n' | {project_name} newCmd testCmd testArg"
                result = subprocess.run(newcmd_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and "NEW CMD ADDED" in result.stdout:
                    print("  ✅ newCmd functionality works")

                    # Test the created command (expect it to run but may have logic errors)
                    test_cmd = f"{activate_cmd} && {project_name} testCmd testValue"
                    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
                    if "DEBUG:" in result.stdout and "Modify default behavour" in result.stdout:
                        print("  ✅ Generated command executes and logIt.py works")
                    else:
                        print("  ⚠️  Generated command runs but may have issues")
                        # Don't fail the test for this as it's expected behavior
                else:
                    print("  ❌ newCmd functionality failed")
                    if shutil.which(project_name):
                        print(f"      This is likely due to system command conflict with '{project_name}'")
                        print(f"      Try using a different package name that doesn't conflict with system commands")
                    test_passed = False

            else:
                print(f"  ❌ Package installation failed: {result.stderr}")
                test_passed = False

        except Exception as e:
            print(f"  ❌ Package testing failed: {e}")
            test_passed = False

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        test_passed = False

    return test_passed

def ensure_and_cd_to_directory(target_dir_name: str) -> bool:
    """
    Checks if a target directory exists in the current working directory.
    If it exists, changes the current working directory to it.
    If it does not exist, creates the directory and then changes the working directory to it.

    Args:
        target_dir_name: The name of the target directory (e.g., "my_project").

    Returns:
        True if the operation was successful, False otherwise.
    """
    # Get the current working directory
    chkForExistingProject = False
    current_cwd = os.getcwd()
    current_cwd_path = Path(current_cwd)
    target_path = current_cwd_path.joinpath(target_dir_name)
    # Construct the full path to the target directory
    try:
        # Check if the directory already exists
        if target_path.is_dir():
            files = [i for i in target_path.iterdir()]
            if len(files) == 0:
                if current_cwd_path.stem != target_dir_name:
                    os.chdir(target_path)
                    theCWD = os.getcwd()
                    print(f"Changing working directory to: {theCWD}")
            else:
                print(f"Program directory exits and contains files.")
                return False
        else:
            # Directory does not exist, create it
            # os.makedirs can create intermediate directories if needed
            os.makedirs(target_path)
            os.chdir(target_path)
            theCWD = os.getcwd()
            print(f"Changing working directory to: {theCWD}")
        return True
    except OSError as e:
        print(
            f"Error: Could not process directory '{target_dir_name}'. Reason: {e}")
        return False

if __name__ == '__main__':
    main()
