#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

pyproject_base_template = Template(dedent("""\
    [project]

    name = "${name}"
    version = "${version}"
    description = "${description}"
    readme = "${readme}"
    license = {text = "${license}"}
    authors = [
    {name = "${authors}", email = "${authorsEmail}"}
    ]
    maintainers = [
    {name = "${maintainers}", email = "${maintainersEmail}"}
    ]
    ${classifiers}

    [build-system]
    requires = ["setuptools>=61.0", "wheel"]
    build-backend = "setuptools.build_meta"

    [tool.setuptools.packages.find]
    where = ["src"]
    [project.scripts]
    ${name} = "${name}.main:main"
    """))

classifiers_line = Template(
    '    "${classifier}",\n'
)

classifiers_template = Template(
    'classifiers=[\n'
    '${classifiers}'
    '    ]'
)

gitignore_content = """
# unmanged package file or directory
scrach/

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*,cover
.hypothesis/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py

# Sphinx documentation
docs/_build/

# PyBuilder
target/

#Ipython Notebook
.ipynb_checkpoints

# pyenv
.python-version
"""
