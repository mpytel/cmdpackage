#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

classifiers_template = Template("classifiers=[\n" "${classifiers}" "    ]")