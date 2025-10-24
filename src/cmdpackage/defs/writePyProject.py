#!/usr/bin/python
# -*- coding: utf-8 -*-
from cmdpackage.templates.pyprojectTemplate import (
    pyproject_base_template, gitignore_content, classifiers_line,
    classifiers_template)
from cmdpackage.templates.readmeTemplate import readme_cmd_template, readme_template
from sys import version_info
from cmdpackage.defs.runSubProc import runSubProc, CompletedProcess
from subprocess import Popen, PIPE
from getpass import getuser
import os


def writePyProject(usedefaults: bool) -> dict[str, str]:
    rtnDict = {}
    fields = ['name', 'version', 'description', 'readme',
              'license', 'authors', 'authorsEmail', 'maintainers', 'maintainersEmail', 'classifiers']

    for field_name in fields:
        default_value = default_values(field_name, rtnDict)
        if usedefaults:
            rtnDict[field_name] = default_value
            continue
        else:
            if field_name == 'description':
                default_value = default_value.replace('name', rtnDict['name'])
            input_msg = input_message(field_name, default_value)
            input_value = get_input(input_msg, default=default_value)
            rtnDict[field_name] = input_value

    pyproject_content = pyproject_base_template.substitute(
        name=rtnDict['name'],
        version=rtnDict['version'],
        description=rtnDict['description'],
        readme=rtnDict['readme'],
        license=rtnDict['license'],
        authors=rtnDict['authors'],
        authorsEmail=rtnDict['authorsEmail'],
        maintainers=rtnDict['maintainers'],
        maintainersEmail=rtnDict['maintainersEmail'],
        classifiers=gen_classifiers()
    )

    with open('pyproject.toml', 'w') as pyproject_file:
        write_content(pyproject_file, pyproject_content)

    readme_content = readme_template.substitute(
        packName=rtnDict['name'], version=rtnDict['version'], description=rtnDict['description'])
    field_name = rtnDict['readme']
    with open(field_name, 'w') as readme_file:
        write_content(readme_file, readme_content)

    readme_content = readme_cmd_template.substitute(
        packName=rtnDict['name'], version=rtnDict['version'])
    field_name = rtnDict['readme'].replace('.md', '_Command_modifications.md')
    with open(field_name, 'w') as readme_file:
        write_content(readme_file, readme_content)

    if usedefaults:
        with_gitignore = 'y'
    else:
        with_gitignore = get_input('commit a git repo [Y/n]?: ', default='y')
    if with_gitignore.lower() == 'y':
        with open('.gitignore', 'w') as gitignore_file:
            write_content(gitignore_file, gitignore_content)
        rtnCP = initGitRepo()
        if rtnCP.returncode == 0:
            rtnDict['gitInitialized'] = True
            print("✅ Initialized git repository")
        else:
            rtnDict['gitInitialized'] = False
            print("❌ Failed to initialize git repository")
            print(f"{rtnCP.returncode}    {rtnCP.stdout}")
    return rtnDict


def input_message(field_name, default_value):
    return u'{} ({}): '.format(field_name, default_value)


def gen_classifiers():
    mayor, minor = version_info[:2]
    python = "Programming Language :: Python"
    local = "Programming Language :: Python :: {}.{}".format(mayor, minor)
    classifiers = [python, local]

    classifiers_lines = ''
    for cls in classifiers:
        classifiers_lines += classifiers_line.substitute(classifier=cls)

    return classifiers_template.substitute(classifiers=classifiers_lines)


def initGitRepo(commit_msg="initial commit") -> CompletedProcess:
    rtnCP: CompletedProcess = runSubProc('ls .git')
    if rtnCP.returncode != 0:
        rtnCP = runSubProc(f'git init')
    return rtnCP

def commitGitRepo(commit_msg="commit") -> CompletedProcess:
    rtnCP: CompletedProcess = runSubProc(f'git add .')
    if rtnCP.returncode == 0:
        rtnCP = runSubProc(f'git commit -m "{commit_msg}"', noOutput=False)
    return rtnCP

def get_username():
    '''Get git config values.'''
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


#fields = ['name', 'version', 'description', 'readme',
#          'license', 'author', author email, 'maintainer', 'maintainer email', 'classifiers']
def default_values(field_name, rtnDict=None):
    if field_name == 'name':
        rtnStr = os.path.relpath('.', '..')
        rtnStr = rtnStr.replace("-", "_")
        return rtnStr
    if field_name == 'version':
        return '0.1.0'
    elif field_name == 'description':
        return 'name related project'
    elif field_name == 'readme':
        return 'README.md'
    elif field_name == 'license':
        return 'MIT License'
    elif field_name == 'authors':
        return get_username()
    elif field_name == 'authorsEmail':
        return f'{get_username()}@domain.com'
    elif field_name == 'maintainers':
        # Use authors value if available, otherwise fall back to username
        if rtnDict and 'authors' in rtnDict:
            return rtnDict['authors']
        return get_username()
    elif field_name == 'maintainersEmail':
        # Use authorsEmail value if available, otherwise fall back to username@domain.com
        if rtnDict and 'authorsEmail' in rtnDict:
            return rtnDict['authorsEmail']
        return f'{get_username()}@domain.com'
    else: return ''

def get_input(input_msg, default=None):
    if version_info >= (3, 0):
        input_value = input(input_msg)
    else:
        input_value = input_msg.encode('utf8').decode('utf8')

    if input_value == '':
        return default
    return input_value


def write_content(file, content):
    if version_info >= (3, 0):
        file.write(content)
    else:
        file.write(content.encode('utf8'))
