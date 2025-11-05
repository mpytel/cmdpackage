#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

cmdOptSwitchbord_template = Template(dedent("""from ..classes.optSwitches import optSwitches as optSwtch


def cmdOptSwitchbord(swtcFlag: str, switchFlags: dict):
    optSwitches = optSwtch(switchFlags)
    optSwitches.toggleSwtcFlag(swtcFlag)
"""))

