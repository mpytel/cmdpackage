#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

cmdOptSwitchbord_template = Template(dedent("""from ..classes.optSwtces import OptSwtces


def cmdOptSwtcbord(swtcFlag: str, swtcFlags: dict):
    optSwtces = OptSwtces(swtcFlags)
    optSwtces.toggleSwtcFlag(swtcFlag)
"""))

