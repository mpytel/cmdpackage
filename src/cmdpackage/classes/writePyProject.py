#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
# Template imports are now handled dynamically from the new template structure
# These will be loaded from the templates/ directory structure
from sys import version_info
from cmdpackage.defs.runSubProc import runSubProc, CompletedProcess
from subprocess import Popen, PIPE
from getpass import getuser


class WritePyProject:
    """
    A class for writing PyProject.toml and related project files.
    
    This class handles the creation of pyproject.toml, README files, and .gitignore,
    along with git repository initialization.
    """
    
    def __init__(self, use_defaults: bool = False, gen_temp_sync_data_write: bool = False):
        """
        Initialize the WritePyProject with configuration options.
        
        Args:
            use_defaults (bool): Whether to use default values without prompting
            gen_temp_sync_data_write (bool): Flag to control temp sync data writing
        """
        self.use_defaults = use_defaults
        self.gen_temp_sync_data_write = gen_temp_sync_data_write
        self.temp_sync_files = {}
        self.fields = ['name', 'version', 'description', 'readme',
                      'license', 'authors', 'authorsEmail', 'maintainers', 'maintainersEmail', 'classifiers']
    
    def _load_template(self, template_file_path: str, template_name: str | None = None):
        """
        Load a template dynamically from the new templates directory structure.
        
        Args:
            template_file_path (str): Path to the template file relative to package root
            template_name (str): Name of the template object to extract (optional)
            
        Returns:
            Template object or content
        """
        import importlib.util
        
        # Get the cmdpackage directory (templates are now in src/cmdpackage/templates/)
        package_dir = os.path.dirname(os.path.dirname(__file__))  # Go up 2 levels from classes/ to cmdpackage/
        full_path = os.path.join(package_dir, template_file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Template file not found: {full_path}")
            
        # Load the module
        module_name = os.path.basename(template_file_path)[:-3]  # Remove .py
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load template module from {full_path}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # If template_name is specified, return that specific object
        if template_name:
            if hasattr(module, template_name):
                return getattr(module, template_name)
            else:
                raise AttributeError(f"Template '{template_name}' not found in {module_name}")
        
        # Otherwise, return the module
        return module
        
    def write_py_project(self) -> dict[str, str | bool]:
        """
        Main method to write pyproject.toml and related files.
        
        Returns:
            dict: Dictionary containing all project configuration values
        """
        # Collect user input or use defaults
        rtn_dict = self._collect_project_info()
        
        # Write project files
        self._write_pyproject_toml(rtn_dict)
        self._write_readme_files(rtn_dict)
        self._write_gitignore_and_init_git(rtn_dict)
        
        # Update temp sync data
        self._write_temp_sync_data(rtn_dict)
        
        return rtn_dict
        
    def _collect_project_info(self) -> dict[str, str | bool]:
        """Collect project information from user input or defaults."""
        rtn_dict = {}
        
        for field_name in self.fields:
            default_value = self._get_default_values(field_name, rtn_dict)
            if self.use_defaults:
                rtn_dict[field_name] = default_value
                continue
            else:
                if field_name == 'description':
                    default_value = default_value.replace('name', rtn_dict['name'])
                input_msg = self._input_message(field_name, default_value)
                input_value = self._get_input(input_msg, default=default_value)
                rtn_dict[field_name] = input_value
                
        return rtn_dict
        
    def _write_pyproject_toml(self, rtn_dict: dict[str, str | bool]) -> None:
        """Write the pyproject.toml file."""
        # Load the pyproject template dynamically
        pyproject_base_template = self._load_template(
            "templates/pyproject_base_template.py", 
            "pyproject_base_template"
        )
        
        pyproject_content = pyproject_base_template.substitute(
            name=rtn_dict['name'],
            version=rtn_dict['version'],
            description=rtn_dict['description'],
            readme=rtn_dict['readme'],
            license=rtn_dict['license'],
            authors=rtn_dict['authors'],
            authorsEmail=rtn_dict['authorsEmail'],
            maintainers=rtn_dict['maintainers'],
            maintainersEmail=rtn_dict['maintainersEmail'],
            classifiers=self._gen_classifiers()
        )
        
        file_name = 'pyproject.toml'
        with open(file_name, 'w') as pyproject_file:
            self._write_content(pyproject_file, pyproject_content)
            
        # Track for sync data
        # self._temp_sync_file_json("pyproject_base_template",
        #                         pyproject_base_template.__module__ if hasattr(pyproject_base_template, '__module__') else "pyprojectTemplate",
        #                         os.path.abspath(file_name), pyproject_content)
        
    def _write_readme_files(self, rtn_dict: dict[str, str | bool]) -> None:
        """Write README.md and command modifications README files."""
        # Load README templates dynamically
        readme_template_obj = self._load_template(
            "templates/README_template.py", 
            "README_template"
        )
        
        # Write main README.md
        readme_content = readme_template_obj.substitute(
            packName=rtn_dict['name'], 
            version=rtn_dict['version'], 
            description=rtn_dict['description'])
        
        readme_file_name = str(rtn_dict['readme'])
        with open(readme_file_name, 'w') as readme_file:
            self._write_content(readme_file, readme_content)
            
        # Track for sync data
        self._temp_sync_file_json("README_template", "templates/README_template.py",
                                os.path.abspath(readme_file_name), readme_content)
        
        # Load command modifications README template
        readme_cmd_template_obj = self._load_template(
            "templates/README_Command_modifications.py", 
            "README_Command_modifications_template"
        )
        
        # Write command modifications README
        readme_cmd_content = readme_cmd_template_obj.substitute(
            packName=rtn_dict['name'], 
            version=rtn_dict['version'],
            readme=rtn_dict['readme'],
            license=rtn_dict['license'],
            authors=rtn_dict['authors'],
            authorsEmail=rtn_dict['authorsEmail'])
        
        cmd_readme_file_name = str(rtn_dict['readme']).replace('.md', '_Command_modifications.md')
        with open(cmd_readme_file_name, 'w') as readme_file:
            self._write_content(readme_file, readme_cmd_content)
            
        # Track for sync data
        self._temp_sync_file_json("README_Command_modifications_template", "templates/README_Command_modifications.py",
                                  os.path.abspath(cmd_readme_file_name), readme_cmd_content)
        
    def _write_gitignore_and_init_git(self, rtn_dict: dict[str, str | bool]) -> None:
        """Write .gitignore file and initialize git repository."""
        if self.use_defaults:
            with_gitignore = 'y'
        else:
            with_gitignore = self._get_input('commit a git repo [Y/n]?: ', default='y')
            
        if with_gitignore.lower() == 'y':
            # Load gitignore content dynamically (it's a string, not a template)
            gitignore_content = self._load_template(
                "templates/gitignore_content.py", 
                "gitignore_content"
            )
            
            gitignore_file_name = '.gitignore'
            with open(gitignore_file_name, 'w') as gitignore_file:
                self._write_content(gitignore_file, str(gitignore_content))
                
            # Track for sync data
            # self._temp_sync_file_json("gitignore_content",
            #                         gitignore_content.__module__ if hasattr(gitignore_content, '__module__') else "pyprojectTemplate",
            #                         os.path.abspath(gitignore_file_name), gitignore_content)
                
            rtn_cp = self._init_git_repo()
            if rtn_cp.returncode == 0:
                rtn_dict['gitInitialized'] = True
                print("✅ Initialized git repository")
            else:
                rtn_dict['gitInitialized'] = False
                print("❌ Failed to initialize git repository")
                print(f"{rtn_cp.returncode}    {rtn_cp.stdout}")
        else:
            rtn_dict['gitInitialized'] = False
            
    def _write_temp_sync_data(self, rtn_dict: dict[str, str | bool]) -> None:
        """Write temporary sync data JSON file by reading existing content and updating it."""
        if self.gen_temp_sync_data_write:
            # Write sync data file to current working directory
            sync_file_path = os.path.join(os.path.abspath("."), "genTempSyncData.json")
            
            # Read existing sync data if it exists
            existing_data = {}
            if os.path.exists(sync_file_path):
                try:
                    with open(sync_file_path, "r") as rf:
                        existing_data = json.load(rf)
                except (json.JSONDecodeError, FileNotFoundError):
                    # If file is corrupted or doesn't exist, start with empty dict
                    existing_data = {}
            
            # Update existing data with new pyproject data
            existing_data.update(self.temp_sync_files)
            
            # Write updated data back to file (no need to create directories since it's in current working directory)
            with open(sync_file_path, "w") as wf:
                json.dump(existing_data, wf, indent=4)
                
    def _temp_sync_file_json(self, template: str, temp_file_name: str, out_file_name: str, file_str: str) -> None:
        """
        Create a temp sync file JSON entry.
        
        Args:
            template (str): Template name
            temp_file_name (str): Template file name
            out_file_name (str): Output file name
            file_str (str): File content for MD5 hash calculation
            
        Returns:
            None
        """
        if self.gen_temp_sync_data_write:
            file_md5 = md5(file_str.encode('utf-8')).hexdigest()
            self.temp_sync_files[out_file_name] = {
                "fileMD5": file_md5,
                "template": template,
                "tempFileName": temp_file_name
            }
    
    def _input_message(self, field_name: str, default_value: str) -> str:
        """Generate input message for user prompts."""
        return u'{} ({}): '.format(field_name, default_value)

    def _gen_classifiers(self) -> str:
        """Generate Python classifiers for pyproject.toml."""
        mayor, minor = version_info[:2]
        python = "Programming Language :: Python"
        local = "Programming Language :: Python :: {}.{}".format(mayor, minor)
        classifiers = [python, local]

        # Load classifier templates dynamically
        classifiers_line = self._load_template(
            "templates/classifiers_line.py", 
            "classifiers_line"
        )
        classifiers_template = self._load_template(
            "templates/classifiers_template.py", 
            "classifiers_template"
        )
        
        classifiers_lines = ''
        for cls in classifiers:
            classifiers_lines += classifiers_line.substitute(classifier=cls)

        return classifiers_template.substitute(classifiers=classifiers_lines)

    def _init_git_repo(self, commit_msg: str = "initial commit") -> CompletedProcess:
        """Initialize git repository."""
        rtn_cp: CompletedProcess = runSubProc('ls .git')
        if rtn_cp.returncode != 0:
            rtn_cp = runSubProc(f'git init')
        return rtn_cp

    def _get_username(self) -> str:
        """Get git config values."""
        username = ''

        # use try-catch to prevent crashes if user doesn't install git
        try:
            # run git config --global <key> to get username
            git_command = ['git', 'config', '--global', 'user.name']
            p = Popen(git_command, stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()

            # turn stdout into unicode and strip it
            username = output.decode('utf-8').strip()

            # if user doesn't set global git config name, then use getuser()
            if not username:
                username = getuser()
        except OSError:
            # if git command is not found, then use getuser()
            username = getuser()

        return username

    def _get_default_values(self, field_name: str, rtn_dict: dict | None = None) -> str:
        """Get default values for project fields."""
        if field_name == 'name':
            rtn_str = os.path.relpath('.', '..')
            rtn_str = rtn_str.replace("-", "_")
            return rtn_str
        if field_name == 'version':
            return '0.1.0'
        elif field_name == 'description':
            return 'name related project'
        elif field_name == 'readme':
            return 'README.md'
        elif field_name == 'license':
            return 'MIT License'
        elif field_name == 'authors':
            return self._get_username()
        elif field_name == 'authorsEmail':
            return f'{self._get_username()}@domain.com'
        elif field_name == 'maintainers':
            # Use authors value if available, otherwise fall back to username
            if rtn_dict and 'authors' in rtn_dict:
                return rtn_dict['authors']
            return self._get_username()
        elif field_name == 'maintainersEmail':
            # Use authorsEmail value if available, otherwise fall back to username@domain.com
            if rtn_dict and 'authorsEmail' in rtn_dict:
                return rtn_dict['authorsEmail']
            return f'{self._get_username()}@domain.com'
        else: return ''

    def _get_input(self, input_msg: str, default: str | None = None) -> str:
        """Get user input with fallback for older Python versions."""
        if version_info >= (3, 0):
            input_value = input(input_msg)
        else:
            input_value = input_msg.encode('utf8').decode('utf8')

        if input_value == '':
            return default or ''
        return input_value

    def _write_content(self, file, content: str) -> None:
        """Write content to file with encoding handling for older Python versions."""
        if version_info >= (3, 0):
            file.write(content)
        else:
            file.write(content.encode('utf8'))


# Convenience functions to maintain backward compatibility
def writePyProject(usedefaults: bool, gen_temp_sync_data_write: bool = False) -> dict[str, str | bool]:
    """
    Backward compatibility function that creates and uses the WritePyProject class.
    
    Args:
        usedefaults (bool): Whether to use default values without prompting
        gen_temp_sync_data_write (bool): Flag to control temp sync data writing
        
    Returns:
        dict: Dictionary containing all project configuration values
    """
    py_project_writer = WritePyProject(usedefaults, gen_temp_sync_data_write)
    return py_project_writer.write_py_project()


def commitGitRepo(commit_msg: str = "commit") -> CompletedProcess:
    """Commit git repository changes."""
    rtn_cp: CompletedProcess = runSubProc(f'git add .')
    if rtn_cp.returncode == 0:
        rtn_cp = runSubProc(f'git commit -m "{commit_msg}"', noOutput=False)
    return rtn_cp


def initGitRepo(commit_msg: str = "initial commit") -> CompletedProcess:
    """Initialize git repository (backward compatibility)."""
    rtn_cp: CompletedProcess = runSubProc('ls .git')
    if rtn_cp.returncode != 0:
        rtn_cp = runSubProc(f'git init')
    return rtn_cp


def get_username() -> str:
    """Get git username (backward compatibility)."""
    writer = WritePyProject()
    return writer._get_username()


def default_values(field_name: str, rtn_dict: dict | None = None) -> str:
    """Get default values (backward compatibility)."""
    writer = WritePyProject()
    return writer._get_default_values(field_name, rtn_dict)


def get_input(input_msg: str, default=None) -> str:
    """Get user input (backward compatibility)."""
    writer = WritePyProject()
    return writer._get_input(input_msg, default)


def write_content(file, content: str) -> None:
    """Write content to file (backward compatibility)."""
    writer = WritePyProject()
    writer._write_content(file, content)


def input_message(field_name: str, default_value: str) -> str:
    """Generate input message (backward compatibility)."""
    writer = WritePyProject()
    return writer._input_message(field_name, default_value)


def gen_classifiers() -> str:
    """Generate classifiers (backward compatibility)."""
    writer = WritePyProject()
    return writer._gen_classifiers()