#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

cmdOptSwitchbord_template = Template(dedent("""from ..classes.optSwitches import optSwitches


def cmdOptSwitchbord(swtcFlag: str, switchFlags: dict):
    optSwitches = optSwitches(switchFlags)
    optSwitches.toggleSwtcFlag(swtcFlag)
"""))

