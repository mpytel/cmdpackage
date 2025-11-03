#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

cmdOptSwitchbord_template = Template(dedent("""from ..classes.optSwi${packName}hes import OptSwi${packName}hes


def cmdOptSwi${packName}hbord(swi${packName}hFlag: str, swi${packName}hFlags: dict):
    optSwi${packName}hes = OptSwi${packName}hes(swi${packName}hFlags)
    optSwi${packName}hes.toggleSwi${packName}hFlag(swi${packName}hFlag)
"""))

