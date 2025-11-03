import os
import re
import importlib.util
from subprocess import run, DEVNULL, CompletedProcess
from .logIt import printIt, lable
from types import ModuleType

def chkDir(dirName: str):
    if not os.path.isdir(dirName):
        os.makedirs(dirName, exist_ok=True)

def list_files_os_walk(base_dir: str, extensions=None) -> list:
    """
    Lists all files matching any extension in a directory and its subdirectories.
        
        Args:
            base_dir (str): The root directory to start searching from.
            extensions (list or tuple): A list or tuple of file extensions (e.g., ['.py', '.json']).
        """
    if extensions is None:
        # Default to commonly used template extensions if none are provided
        extensions = ('.py', '.json')

    template_files = []

    # os.walk yields (dirpath, dirnames, filenames)
    for root, _, files in os.walk(base_dir):

        for file in files:
            # Check if the file name ends with ANY of the specified extensions
            # os.path.splitext returns a tuple (root, ext)
            if os.path.splitext(file)[1] in extensions:
                # Construct the full path
                full_path = os.path.join(root, file)
                template_files.append(full_path)

    return template_files


def load_template(template_file_path: str, template_name: str | None = None) -> ModuleType:
    """
    Load a template dynamically from a templates directory structure.
    
    Args:
        template_file_path (str): Path to the template file relative to package root
        template_name (str): Name of the template object to extract (optional)
        
    Returns:
        Template object or content
    """
    
    # Get the cmdpackage directory (templates are now in src/cmdpackage/templates/)
    # Go up 2 levels from classes/ to cmdpackage/
    package_dir = os.path.dirname(os.path.dirname(__file__))
    full_path = os.path.join(package_dir, template_file_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Template file not found: {full_path}")

    # Load the module
    module_name = os.path.basename(template_file_path)[:-3]  # Remove .py
    spec = importlib.util.spec_from_file_location(module_name, full_path)

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load template module from {full_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # If template_name is specified, return that specific object
    if template_name:
        if hasattr(module, template_name):
            return getattr(module, template_name)
        else:
            raise AttributeError(
                f"Template '{template_name}' not found in {module_name}")

    # Otherwise, return the module
    return module


def runSubProc(theCmd: str, noOutput=True) -> CompletedProcess:
    if noOutput:
        rtnCompProc = run(theCmd, shell=True,
                          stdout=DEVNULL,
                          stderr=DEVNULL)
    else:
        rtnCompProc = run(theCmd, shell=True)
    return rtnCompProc

def init_git_repo(commit_msg: str = "initial commit") -> CompletedProcess:
    """Initialize git repository."""
    # Check if .git directory exists
    rtn_cp: CompletedProcess = runSubProc('ls .git')
    # If .git does not exist, initialize git repository
    if rtn_cp.returncode != 0:
        rtn_cp = runSubProc(f'git init')
    # output result
    if rtn_cp.returncode == 0:
        printIt("Initialized git repository",lable.PASS)
    else:
        printIt("Failed to initialize git repository",lable.FAIL)
        printIt(f"Return Code: {rtn_cp.returncode}\nStd Outpt{rtn_cp.stdout}",lable.DEBUG)
    return rtn_cp

def commitGitRepo(commit_msg: str = "commit") -> CompletedProcess:
    """Commit git repository changes."""
    rtn_cp: CompletedProcess = runSubProc(f'git add .')
    if rtn_cp.returncode == 0:
        rtn_cp = runSubProc(f'git commit -m "{commit_msg}"', noOutput=False)
    return rtn_cp

def sanitize_var_name(requested_name):
    """
    Replaces characters not allowed in a Python variable name with an underscore (_).

    Args:
        requested_name (str): The initial string to be converted into a variable name.

    Returns:
        str: A sanitized variable name.
    """
    # 1. Replace all invalid characters (anything NOT a letter, digit, or underscore) with '_'
    #    The pattern [^a-zA-Z0-9_] matches any character not in the allowed set.
    sanitized_name = re.sub(r"[^a-zA-Z0-9_]", "_", requested_name)

    # 2. Handle the starting character rule: cannot start with a digit.
    #    If the string starts with a digit, prepend an underscore.
    if sanitized_name and sanitized_name[0].isdigit():
        sanitized_name = "_" + sanitized_name

    # 3. Clean up multiple or leading/trailing underscores (optional, but good practice)
    #    This prevents names like '__my_var__' or 'my__var'
    sanitized_name = re.sub(r"_+", "_", sanitized_name).strip("_")

    # 4. Handle edge case where input was empty or only invalid chars (returns a single underscore)
    if not sanitized_name:
        return "_"

    return sanitized_name
