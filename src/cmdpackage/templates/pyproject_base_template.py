#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

pyproject_base_template = Template(
    dedent(
        """\
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
    """
    )
)