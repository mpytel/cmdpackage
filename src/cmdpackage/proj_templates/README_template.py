#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

README_template = Template(dedent("""#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

README_template = Template(dedent(\"\"\"# ${packName}
version: ${version}

${description}

**The framework for adding/modifying ${packName} commands is discribed in README_Command_modifications.md**

## Overview
TBD
                                     
## Installation
### From Source
```bash
git clone <repository-url>
cd ${packName}
pip install -e .
```
\"\"\"))"""))

