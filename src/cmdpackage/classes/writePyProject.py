#!/usr/bin/python
# -*- coding: utf-8 -*-
from hashlib import md5
import os
import json
# Template imports are now handled dynamically from the new template structure
# These will be loaded from the templates/ directory structure
from sys import version_info
from subprocess import Popen, PIPE
from getpass import getuser
from ..defs.utilities import load_template, list_files_os_walk, runSubProc, CompletedProcess, init_git_repo, sanitize_var_name
from ..defs.logIt import printIt, lable

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

        self.src_dir = os.path.dirname(os.path.dirname(__file__))

        # Collect user input or use defaults
        self.projFields = self._collect_project_info()    
        
    def write_py_project(self) -> dict[str, str]:
        """
        Main method to write pyproject.toml and related files.
        
        Returns:
            dict: Dictionary containing all project configuration values
        """

        # Write project files
        init_repo = self._write_py_project_files()
        if init_repo:
            init_git_repo()

        return self.projFields
        
    def _collect_project_info(self) -> dict[str, str]:
        """Collect project information from user input or defaults."""
        self.projFields = {}
        
        for field_name in self.fields:
            default_value = self._get_default_values(field_name)
            if self.use_defaults:
                self.projFields[field_name] = default_value
                continue
            else:
                # When the str 'name' is in description, replace 'name' with actual project name
                # if field_name == 'description':
                #     default_value = default_value.replace('name', self.projFields['name'])
                input_msg = self._input_message(field_name, default_value)
                input_value = self._get_input(input_msg, default=default_value)
                self.projFields[field_name] = input_value
        
        # Generate classifiers
        self.projFields['classifiers'] = self._gen_classifiers()

        return self.projFields
    
    def _write_py_project_files(self) -> bool:
        """
        Write all project files from their templates in proj_templats dirctory.
        
        Returns:
            bool: True if user wants a git repository, False otherwise

        """
        repo_needed = False
    
        template_files = list_files_os_walk(self.src_dir)

        for template_file in template_files:
            if "__init__" in template_file:
                continue
            tmpFlileName = os.path.relpath(template_file, self.src_dir)
            if not tmpFlileName.startswith("proj_templates"):
                continue
            if tmpFlileName.startswith("proj_templates/classifiers"):
                continue
            tmplName = os.path.splitext(os.path.split(tmpFlileName)[1])[0]

            # only process pyproject, README, and .gitignore templates
            if tmplName not in ['pyproject_template', 'README_template', '.gitignore_template']:
                continue
            if tmplName == ".gitignore_template":
                tmplName = "gitignore_template"
                # ask user if they want to init a git repo
                repo_needed = self._ask_it_repo_needed()

            pyproject_base_template = load_template(tmpFlileName, tmplName)

            pyproject_content = pyproject_base_template.substitute(
                packName=self.projFields['name'],
                version=self.projFields['version'],
                description=self.projFields['description'],
                readme=self.projFields['readme'],
                license=self.projFields['license'],
                authors=self.projFields['authors'],
                authorsEmail=self.projFields['authorsEmail'],
                maintainers=self.projFields['maintainers'],
                maintainersEmail=self.projFields['maintainersEmail'],
                classifiers=self.projFields['classifiers']
            )

            # correct file names for README and .gitignore
            file_name = tmpFlileName.replace("proj_templates/", "")
            file_name = file_name.replace("_template", "")
            if file_name == "README.py":
                file_name = file_name.replace(".py", ".md")
            if file_name == ".gitignore.py":
                file_name = ".gitignore"

            with open(file_name, 'w') as pyproject_file:
                self._write_content(pyproject_file, pyproject_content)

            printIt(file_name, lable.SAVED)
        return repo_needed

    def _ask_it_repo_needed(self) -> bool:
        """Ask user if they want to initialize a git repository."""
        if self.use_defaults:
            repo_needed = 'y'
        else:
            repo_needed = self._get_input(
                'commit a git repo [Y/n]?: ', default='y')
        return repo_needed.lower() == 'y'

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
        classifiers_line = load_template(
            "proj_templates/classifiers_line.py",
            "classifiers_line"
        )
        classifiers_template = load_template(
            "proj_templates/classifiers_template.py",
            "classifiers_template"
        )
        
        classifiers_lines = ''
        for cls in classifiers:
            classifiers_lines += classifiers_line.substitute(classifier=cls)

        return classifiers_template.substitute(classifiers=classifiers_lines)

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

    def _get_default_values(self, field_name: str) -> str:
        """Get default values for project fields."""
        if field_name == 'name':
            rtn_str = os.path.relpath('.', '..')
            rtn_str = rtn_str.replace("-", "_")
            return rtn_str
        if field_name == 'version':
            return '0.1.0'
        elif field_name == 'description':
            return 'A command line interface package for developers to build upon.'
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
            if self.projFields and 'authors' in self.projFields:
                return self.projFields['authors']
            return self._get_username()
        elif field_name == 'maintainersEmail':
            # Use authorsEmail value if available, otherwise fall back to username@domain.com
            if self.projFields and 'authorsEmail' in self.projFields:
                return self.projFields['authorsEmail']
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
def writePyProject(usedefaults: bool, gen_temp_sync_data_write: bool = False) -> dict[str, str]:
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
