import os
from .defs.writePyProject import writePyProject
from .defs.writeCLIPackage import writeCLIPackage
from .defs.createzVirtualEnv import createzVirtualEnv
import sys
from pathlib import Path

GREEN = "\033[32m"
RESET = "\033[0m"


def main():
    print("--- Inside cmdPack.src.main() ---")
    projName = ''
    askForDirChange = False
    if len(sys.argv) > 1:
        projName: str = sys.argv[1]
        # set the working directory to cwd+projName
        askForDirChange = ensure_and_cd_to_directory(projName)
    else:
        projName = Path(os.getcwd()).stem
    fields: dict[str, str] = writePyProject()
    writeCLIPackage(fields)
    createzVirtualEnv(fields)
    print(f'*** Activate and install {projName} virtual enviroment ***')
    if askForDirChange:
        print(f'{GREEN}execute{RESET}: cd {projName}')
    print(f'{GREEN}execute{RESET}: . env/{projName}/bin/activate')
    print(f'{GREEN}execute{RESET}: pip install -e .')


if __name__ == '__main__':
    main()


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