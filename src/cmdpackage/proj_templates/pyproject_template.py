#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

pyproject_template = Template(dedent("""[project]

name = "${packName}"
version = "${version}"
description = "name related project"
readme = "${readme}"
license = {text = "${license}"}
authors = [
{name = "${authors}", email = "${authorsEmail}"}
]
maintainers = [
{name = "${authors}", email = "${authorsEmail}"}
]


[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
[project.scripts]
${packName} = "${packName}.main:main"
"""))

