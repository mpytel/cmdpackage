#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

cmdOptSwitchbordFileStr = dedent(
    """from ..classes.optSwitches import OptSwitches

def cmdOptSwitchbord(switchFlag: str, switchFlags: dict):
    optSwitches = OptSwitches(switchFlags)
    optSwitches.toggleSwitchFlag(switchFlag)
"""
)