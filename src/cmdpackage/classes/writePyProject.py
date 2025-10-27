#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
import cmdpackage.templates.readmeTemplate as readme_template
from cmdpackage.templates.pyprojectTemplate import (
    pyproject_base_template, gitignore_content, classifiers_line,
    classifiers_template)
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
        # Write main README.md
        readme_content = readme_template.readme_template.substitute(
            packName=rtn_dict['name'], 
            version=rtn_dict['version'], 
            description=rtn_dict['description'])
        
        readme_file_name = str(rtn_dict['readme'])
        with open(readme_file_name, 'w') as readme_file:
            self._write_content(readme_file, readme_content)
            
        # Track for sync data
        self._temp_sync_file_json("readme_template", readme_template.__file__,
                                os.path.abspath(readme_file_name), readme_content)
        
        # Write command modifications README
        readme_cmd_content = readme_template.readme_cmd_template.substitute(
            packName=rtn_dict['name'], 
            version=rtn_dict['version'])
        
        cmd_readme_file_name = str(rtn_dict['readme']).replace('.md', '_Command_modifications.md')
        with open(cmd_readme_file_name, 'w') as readme_file:
            self._write_content(readme_file, readme_cmd_content)
            
        # Track for sync data
        self._temp_sync_file_json("readme_cmd_template", readme_template.__file__,
                                  os.path.abspath(cmd_readme_file_name), readme_cmd_content)
        
    def _write_gitignore_and_init_git(self, rtn_dict: dict[str, str | bool]) -> None:
        """Write .gitignore file and initialize git repository."""
        if self.use_defaults:
            with_gitignore = 'y'
        else:
            with_gitignore = self._get_input('commit a git repo [Y/n]?: ', default='y')
            
        if with_gitignore.lower() == 'y':
            gitignore_file_name = '.gitignore'
            with open(gitignore_file_name, 'w') as gitignore_file:
                self._write_content(gitignore_file, gitignore_content)
                
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
            # Set up source directory path for sync data file
            src_dir = os.path.join(os.path.abspath("."), 'src', str(rtn_dict['name']))
            sync_file_path = os.path.join(src_dir, "genTempSyncData.json")
            
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
            
            # Ensure the directory exists before writing
            os.makedirs(os.path.dirname(sync_file_path), exist_ok=True)
            
            # Write updated data back to file
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