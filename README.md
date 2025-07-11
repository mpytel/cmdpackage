# Command Package (cmdpackage)

## Table of Contents

- [Command Package (cmdpackage)](#command-package-cmdpackage)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Standard Installation from PyPI](#standard-installation-from-pypi)
    - [Command Line Usage](#command-line-usage)
    - [Using cmdpackage to Create New Python Packages](#using-cmdpackage-to-create-new-python-packages)
    - [Testing Generated Packages](#testing-generated-packages)
    - [Modifying New Python Packages](#modifying-new-python-packages)
      - [Install New Editable Python Package](#install-new-editable-python-package)
  - [Editable cmdpackage Installation](#editable-cmdpackage-installation)
    - [Automated Default New Package Setup with `cmdpackage.sh`](#automated-default-new-package-setup-with-cmdpackagesh)
  - [Important Notes](#important-notes)
    - [System Command Conflicts](#system-command-conflicts)
    - [Recent Improvements](#recent-improvements)

-----

## Introduction

**cmdpackage** is a pip package that generates opinionated Python command-line program packages. These derived program packages automate the creation of new CLI program commands that you can modify in a development environment. `cmdpackage` can be installed as a standard (or "production") installation or as an editable (or "development") installation directly from GitHub.

-----

## Standard Installation from PyPI

A standard installation allows a user to quickly create derived program packages.

```bash
pip install cmdpackage
```

The derived program packages will be modified in a virtual Python development environment using `virtualenv`. This virtual environment is isolated as a self-contained Python installation with its own `site-packages` directory. This isolation prevents dependency conflicts between different projects.

```bash
pip install virtualenv
```

### Command Line Usage

cmdpackage supports several command-line options:

```bash
# Show help and available options
cmdpackage -h

# Create a package in the current directory (uses directory name as package name)
cmdpackage

# Create a package with a specific name
cmdpackage myproject

# Create a package with comprehensive testing
cmdpackage -t myproject

# Create and test a package in the current directory
cmdpackage -t
```

**Important:** Avoid using system command names (like `kill`, `ls`, `cp`, `mv`, `rm`, etc.) as your package name, as they will conflict with existing system commands and cause issues when running your package.

### Using cmdpackage to Create New Python Packages

Once installed, you can create a package directory for your new Python package (e.g., `myTypes`) and run `cmdpackage` to generate the necessary files within this directory.

```bash
mkdir $HOME/myTypes
cd $HOME/myTypes
cmdpackage
```

You will be asked standard package generation questions:

```
name (myTypes):
version (0.1.0):
description (myTypes pip package):
readme ():
license (MIT License):
authors (username):
authorsEmail (username@domain.com):
maintainers (username):        # Now defaults to authors value
maintainersEmail (username@domain.com):  # Now defaults to authorsEmail value
classifiers ():
commit a git repo [Y/n]?:
```

The **default input** for each question is the bracketed value. The username will be set to your global Git config name if Git is present; otherwise, your system login username will be used.

### Testing Generated Packages

cmdpackage includes a comprehensive testing option (`-t`) that validates your generated package:

```bash
cmdpackage -t myproject
```

The test suite performs the following checks:

- **System Command Conflict Detection** - Warns if your package name conflicts with system commands
- **Virtual Environment Validation** - Ensures the virtual environment was created properly
- **Package Structure Verification** - Confirms all required directories and files exist
- **Syntax Validation** - Compiles generated Python files to catch syntax errors
- **Functional Testing** - Tests package installation, help system, and command creation

Example test output:
```
*** Running tests on myproject package ***
🔍 Test 0: Checking for system command conflicts...
  ✅ No system command conflicts detected for 'myproject'
🔍 Test 1: Checking virtual environment...
  ✅ Virtual environment created at env/myproject
🔍 Test 2: Checking package structure...
  ✅ Directory src/myproject exists
  ✅ Directory src/myproject/commands exists
  ✅ Directory src/myproject/classes exists
  ✅ Directory src/myproject/defs exists
🔍 Test 3: Checking key files...
  ✅ File src/myproject/main.py exists
  ✅ File src/myproject/defs/logIt.py exists
  ✅ File src/myproject/classes/argParse.py exists
  ✅ File src/myproject/commands/commands.py exists
  ✅ File pyproject.toml exists
🔍 Test 4: Checking logIt.py syntax...
  ✅ logIt.py has valid Python syntax
🔍 Test 5: Installing and testing package functionality...
  ✅ Package installed successfully
  ✅ Help command works
  ✅ newCmd functionality works
  ✅ Generated command executes and logIt.py works
✅ All tests passed!
```

### Modifying New Python Packages

You're now ready to work on your new Python package, `myTypes`, by first activating a Python virtual development environment.

  * **Activation Process:** To use a virtual environment, you must **activate** it. This is typically done by running a script within the environment's directory:

      * On Linux/macOS: `source /path/to/myTypes/env/bin/activate`
      * On Windows: `/path/to/myTypes/env/Scripts/activate` **(Not tested on Windows)**

    Activating the environment modifies your terminal's shell session, primarily by adjusting your `PATH` environment variable. This ensures that when you type `python` or `pip`, you are using the Python interpreter and package manager from within that specific virtual environment, rather than your system's global Python.

    **Deactivation Process:** When you **deactivate** a virtual environment, you return to the System/Global Python Environment.

      * Execute: `deactivate`

#### Install New Editable Python Package

```bash
pip install -e .
```

Executing `pip list` results in the following output, showing the localized package installation in the Python virtual environment:

```
Package    Version Editable project location
---------- ------- -----------------------------------
myTypes    0.1.0   /Users/<username>/proj/python/myTypes
pip        25.1.1
setuptools 80.9.0
wheel      0.45.1
```

Your new `myTypes` program is now ready to use as a launching point for your Python CLI development. A list of installed commands can be found using:

```bash
myTypes -h
```

To add a new command named `type` – which will record a token, a title representing the type of information this token represents, and a short description of what it is and where it can be used – use the following command:

```bash
myTypes newCmd type token title sd
```

You will then be prompted to enter help text for the command and each of the arguments you defined (`type`, `title`, `sd`):

1.  Enter a description of the 'type' command:
    *Records a token that represents a type of data or information.*
2.  Enter a description of the 'token' argument:
    *The token that represents a type of data or information.*
3.  Enter a description of the 'title' argument:
    *The title of the token that represents a type of data or information.*
4.  Enter a description of the 'sd' argument:
    *A short description of the type of data or information is entered for sd.*

Run the new `myTypes type` command:

```bash
myTypes type int integer 'An integer is a whole number that can be positive, negative, or zero.'
```

The path to the Python file that needs your modification (`type.py`) is displayed as output, along with the values of the three arguments (type, title, sd):

```
DEBUG: Modify default behavior in src/myTypes/commands/type.py
INFO: token: int
INFO: title: integer
INFO: sd: An integer is a whole number that can be positive, negative, or zero.
```

The `rmCmd` is used to remove a command from your `myTypes` program.

```bash
myTypes rmCmd run
```

-----

## Editable cmdpackage Installation

Modifying a clone of the `cmdpackage` GitHub repository allows a developer to change the initial files of new commands added to `cmdpackage` derived Python packages. The following commands are used to clone and install `cmdpackage` in a virtual environment for this purpose:

```bash
mkdir $HOME/proj
cd  $HOME/proj
git clone https://github.com/mpytel/cmdpackage.git
cd cmdpackage
pip install -e .
```

We purposely installed `cmdpackage` in the System/Global Python Environment. `cmdpackage` is then used to generate program packages that run in Virtual Python Environments set up by `cmdpackage` when run in a new Python package directory for modification in a development environment. This is performed using the commands described in the two above sections:

1.  [Creating a new package](#using-cmdpackage-to-create-new-python-packages)
2.  [Modifying new python packages](#modifying-new-python-packages)

### Automated Default New Package Setup with `cmdpackage.sh`

A shell script (`cmdpackage.sh`) is provided in the `cmdpackage` directory to automate the creation of a new package using default setup values. This script creates and changes the working directory to one named after your program package. It then creates and activates a virtual environment within this directory, and installs the `cmdpackage` pip package from the local repository. It then creates the new package and uninstalls `cmdpackage` from the new package's virtual environment. The new package is installed and run to create a 'helloWorld' command to test and illustrate the `newCmd` command that is provided with the new derived package.

From any directory, execute the following command to run this shell script:

```bash
source $HOME/proj/python/cmdpackage/cmdpackage.sh myPack
```

If you prefer not to use the `cmdpackage.sh` shell script, the manual command steps used to create/install/use a new package (`myPack`) with a new 'helloWorld' command are:

```bash
mkdir myPack
cd myPack
virtualenv env/myPack
source env/myPack/bin/activate
pip install $HOME/proj/python/cmdpackage
cmdpackage
   # Press the return key 11 times to accept the default values.
pip uninstall cmdpackage
   # Press the return key to accept the default value Y.
pip install -e .
myPack newCmd helloWorld greeting
   # When prompted by 'Enter help description for helloWorld:'
   # enter: 'Echo the greeting text.'
   # When prompted by 'Enter help description for greeting:'
   # enter: 'The text to echo.'
myPack helloWorld "You're ready to add and remove commands, and modify code in your myPack project!"
```

The following output results from executing `myPack helloWorld`:

```
DEBUG: Modify default behavior in src/myPack/commands/helloWorld.py
INFO: greeting: You're ready to add and remove commands, and modify code in your myPack project!
```

-----

## Important Notes

### System Command Conflicts

**Avoid using system command names** as your package name. Names like `kill`, `ls`, `cp`, `mv`, `rm`, `cat`, `grep`, etc., will conflict with existing system commands and cause issues when trying to run your package commands. The `-t` testing option will detect and warn about these conflicts.

**Good package names:** `myapp`, `dataprocessor`, `webtools`, `myproject`
**Problematic names:** `kill`, `ls`, `test`, `python`, `pip`

### Recent Improvements

- **Enhanced Help System:** `cmdpackage -h` now works properly and shows all available options
- **Improved Defaults:** Maintainer fields automatically default to author values for better user experience
- **Comprehensive Testing:** The `-t` option provides thorough validation of generated packages
- **Conflict Detection:** Automatic detection of system command name conflicts
- **Better Error Messages:** More helpful error messages and guidance when issues occur
