#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

readme_template = Template(dedent("""# ${packName}
version: ${version}
framework information and overview for adding commands to ${packName} are provided in README_Command_modifications.md

${description}   
## Overview
TBD
                                     
## Installation
### From Source
```bash
git clone <repository-url>
cd ${packName}
pip install -e .
```
"""))

readme_cmd_template = Template(dedent("""# ${packName}
version - ${version}

A dynamic command-line tool for creating, modifying, and managing custom commands with interactive help and argument parsing.

## Overview

${packName} is a Python package that provides a framework for building extensible command-line applications. It allows you to dynamically create new commands, modify existing ones, and manage command arguments through an interactive interface.

## Features

- **Dynamic Command Creation**: Add new commands with custom arguments on-the-fly
- **Command-Specific Option Flags**: Create boolean and string option flags for commands
- **Persistent Flag Storage**: Command flags are automatically saved to `.${packName}rc` configuration file
- **Flag Toggle Syntax**: Use `+flag` and `-flag` syntax to enable/disable boolean flags
- **Multiple Code Templates**: Choose from different templates when creating commands (simple, class-based, asyncDef)
- **Interactive Help System**: Colored, formatted help text that adapts to terminal width
- **Command Management**: Modify or remove existing commands and their arguments
- **Flexible Argument Parsing**: Support for both string and integer arguments
- **Template-Based Code Generation**: Automatically generates Python files for new commands
- **JSON-Based Configuration**: Commands and their descriptions stored in JSON format
- **Comprehensive Test Runner**: Built-in test discovery, execution, and reporting with multiple output modes
- **Round-trip Testing**: Extensive test suite covering command creation, modification, and removal workflows
                                      
## Installation

### From Source
```bash
git clone <repository-url>
cd ${packName}
pip install -e .
```

### Using pip (if published)
```bash
pip install ${packName}
```

## Usage

After installation, you can use the `${packName}` command from anywhere in your terminal:

```bash
${packName} <command> [arguments...] [options]
```

### Available Commands

#### `newCmd` - Create New Command
Add a new command with optional arguments and option flags:

```bash
${packName} newCmd <cmdName> [argName1] [argName2] ... [--flagName] [-flagName]
```

**Creating Commands with Option Flags:**
```bash
# Create command with boolean and string flags
${packName} newCmd deploy server --config -verbose

# Create command using specific template
${packName} newCmd --template simple processor input --output -debug

# Create command with template specification using = syntax
${packName} newCmd --templates=simple backup source --destination -compress
```

**Option Flag Types:**
- **String Options** (`--flagName`): Store text values, specified with double hyphens
- **Boolean Flags** (`-flagName`): Store true/false values, specified with single hyphens

During command creation, you'll be prompted to provide descriptions for:
- The command itself
- Each regular argument
- Each option flag (with type indication)

**Command-Specific Options:**
- `--template <templateName>`: Specify which template to use for code generation
- `--templates`: List all available templates
- `--templates=<templateName>`: Alternative syntax for specifying template

**Available Templates:**
- `argCmdDef` (default): Standard template with argument handling
- `simple`: Minimal template for basic commands
- `classCall`: Object-oriented template using classes
- `asyncDef`: Asynchronous template for async operations

This will:
- Create a new command with the specified name
- Add arguments as specified
- Generate a `.py` file using the chosen template
- Prompt for descriptions of the command and each argument

#### `modCmd` - Modify Existing Command
Modify command or argument descriptions, or add new arguments and option flags:

```bash
${packName} modCmd <cmdName> [argName...] [--flagName] [-flagName]
```

**Modifying Commands with Option Flags:**
```bash
# Modify command description only
${packName} modCmd deploy

# Modify existing argument description
${packName} modCmd deploy timeout

# Add new argument to existing command
${packName} modCmd deploy newarg

# Add boolean and string flags to existing command
${packName} modCmd deploy -verbose --config

# Combine argument and flag modifications
${packName} modCmd deploy newarg -debug --output
```

**Option Flag Types in modCmd:**
- **String Options** (`--flagName`): Add string value options to existing commands
- **Boolean Flags** (`-flagName`): Add true/false flags to existing commands

During modification, you'll be prompted to:
- Confirm changes to command or argument descriptions
- Provide descriptions for new arguments
- Provide descriptions for new option flags (with type indication)

The `modCmd` command will:
- Update existing descriptions if you choose to modify them
- Add new arguments with descriptions
- Add new option flags to both `commands.json` and `.${packName}rc` configuration
- Leave the command's `.py` file unchanged (only modifies metadata)

Example:
```bash
# Modify existing argument description
${packName} modCmd deploy timeout

# Add new flags to existing command
${packName} modCmd deploy -verbose --config-file
```
```

#### `rmCmd` - Remove Command
Remove a command and its associated file and flags, or remove specific arguments:

```bash
${packName} rmCmd <cmdName> [argName...]
```

**Removing Commands:**
```bash
# Remove entire command (removes .py file, command definition, and associated flags from .${packName}rc)
${packName} rmCmd deploy

# Remove specific argument from command (leaves command intact)
${packName} rmCmd deploy timeout
```

**What gets removed:**
- **Entire command removal**: Deletes the `.py` file, removes entry from `commands.json`, and cleans up associated flags in `.${packName}rc`
- **Argument removal**: Only removes the argument definition from `commands.json` (command and file remain)

#### `runTest` - Test Runner
Run and manage tests in the `./tests` directory with comprehensive execution options:

```bash
${packName} runTest [testName] [listTests] [+verbose|-verbose] [+stop|-stop] [+summary|-summary]
```

**Test Discovery and Execution:**
```bash
# Run all tests
${packName} runTest

# Run specific test (with or without .py extension)
${packName} runTest test_modCmd_roundtrip
${packName} runTest test_newCmd_roundtrip.py

# List all available tests with descriptions
${packName} runTest listTests
```

**Execution Control Flags:**
- **`+verbose/-verbose`**: Show/hide detailed output during test execution including command traces and full test output
- **`+stop/-stop`**: Stop execution immediately on first test failure (useful for debugging)
- **`+summary/-summary`**: Show only final summary results, skip individual test progress and output

**Flag Usage Examples:**
```bash
# Run all tests with detailed output
${packName} runTest +verbose

# Run tests and stop on first failure
${packName} runTest +stop

# Run tests showing only the final summary
${packName} runTest +summary

# Run specific test with verbose output
${packName} runTest test_modCmd_roundtrip +verbose

# Combine flags (enable verbose, disable summary)
${packName} runTest +verbose -summary

# Toggle flags independently
${packName} runTest +stop    # Enable stop-on-failure for future runs
${packName} runTest -stop    # Disable stop-on-failure
```

**Test Runner Features:**
- **Automatic Discovery**: Finds all `test_*.py` files in the `./tests` directory
- **Color-coded Results**: Green PASS/Red FAIL status indicators with execution timing
- **Progress Tracking**: Shows current test progress (e.g., "[2/4] Running test_name...")
- **Comprehensive Summary**: Displays total tests, passed/failed counts, and total execution time
- **Error Details**: Shows detailed error information for failed tests (in verbose mode or when tests fail)
- **Virtual Environment**: Automatically activates the project's virtual environment (`env/${packName}/`)
- **Exit Codes**: Returns 0 for success, 1 if any tests fail (useful for CI/CD pipelines)

**Test Output Examples:**

*Normal execution (default):*
```
INFO: Running 4 test(s)...

INFO: [1/4] Running test_argCmdDef_roundtrip...
  PASS (0.29s)

INFO: [2/4] Running test_modCmd_roundtrip...
  PASS (0.75s)

...

============================================================
INFO: TEST EXECUTION SUMMARY
============================================================
Total Tests:  4
Passed:       4
Failed:       0
Total Time:   1.88s
============================================================
PASS: 🎉 All tests passed!
```

*Summary mode (`+summary`):*
```
INFO: Running 4 test(s)...

============================================================
INFO: TEST EXECUTION SUMMARY
============================================================
Total Tests:  4
Passed:       4
Failed:       0
Total Time:   1.89s
============================================================
PASS: 🎉 All tests passed!
```

*Verbose mode (`+verbose`):*
Shows full test output including all test details, setup/teardown messages, and debug information.

**Test File Requirements:**
- Test files must be named `test_*.py` and located in the `./tests` directory
- Tests should be executable Python scripts that return appropriate exit codes
- Test files can include docstrings for automatic description extraction

### Getting Help

```bash
# Show general help
${packName} -h

# Show help for specific command
${packName} <command> -h
```

## Option Types

${packName} supports multiple types of options:

### Global Options (Single Hyphen)
- Format: `-<letter>` or `+<letter>`
- Scope: Apply to the entire ${packName} application
- Example: `-h` for help

### Command-Specific Options (Double Hyphen)
- Format: `--<word>`
- Scope: Apply only to specific commands during command creation
- Example: `--template classCall` for the newCmd command

## Command Option Flags

Commands can define their own option flags that are created during command definition and persist between runs.

### Creating Option Flags

When creating a command with `newCmd`, you can specify option flags:

```bash
# Create command with string and boolean flags
${packName} newCmd backup source --destination -compress -verbose

# This creates:
# - source: regular argument
# - --destination: string option flag
# - -compress: boolean flag
# - -verbose: boolean flag
```

During creation, you'll be prompted for descriptions:
```
Enter help description for argument source:
> Source directory to backup

Enter help description for option --destination (stores value):
> Destination path for backup files

Enter help description for flag -compress (true/false):
> Enable compression for backup

Enter help description for flag -verbose (true/false):
> Show detailed backup progress
```

### Using Option Flags

#### String Options (Double Hyphen `--`)
String options store text values and can be used in multiple ways:

```bash
# Provide value as separate argument
${packName} backup /home/user --destination /backup/location

# Provide value using equals syntax
${packName} backup /home/user --destination=/backup/location

# Use without value (stores empty string)
${packName} backup /home/user --destination
```

#### Boolean Flags (Single Hyphen `-`)
Boolean flags are toggled using `+` (enable) and `-` (disable) syntax:

```bash
# Enable compression flag
${packName} backup +compress

# Disable compression flag  
${packName} backup -compress

# Enable verbose mode
${packName} backup +verbose

# Multiple flag operations
${packName} backup +compress +verbose
${packName} backup -compress -verbose
```

### Flag Persistence

All command flags are automatically saved to `.${packName}rc` configuration file:

```json
{
  "switchFlags": {},
  "commandFlags": {
    "backup": {
      "destination": "/backup/location",
      "compress": true,
      "verbose": false
    }
  }
}
```

### Flag Behavior

- **String flags**: Values persist until explicitly changed
- **Boolean flags**: State persists until toggled with `+` or `-`
- **Command execution**: Flags are saved before the command runs
- **Multiple flags**: Can combine multiple flags in single command

### Examples

```bash
# Create a deployment command with flags
${packName} newCmd deploy app --config --environment -verbose -dry-run

# Use the command with various flag combinations
${packName} deploy myapp --config /path/config.yml --environment production +verbose
${packName} deploy myapp --environment staging +dry-run
${packName} deploy myapp +verbose -dry-run
${packName} deploy myapp --config=/new/config.json

# Toggle flags independently
${packName} deploy +verbose    # Enable verbose mode
${packName} deploy -verbose    # Disable verbose mode
${packName} deploy +dry-run    # Enable dry run mode
```

## Project Structure

```
${packName}/
├── src/
│   └── ${packName}/
│       ├── main.py              # Entry point
│       ├── classes/
│       │   ├── argParse.py      # Custom argument parser with colored help
│       │   └── optSwitches.py   # Option flag persistence and management
│       ├── commands/
│       │   ├── commands.json    # Command definitions and option flag schemas
│       │   ├── commands.py      # Command loading and management
│       │   ├── cmdSwitchbord.py # Command routing and flag processing
│       │   ├── newCmd.py        # New command creation logic
│       │   ├── modCmd.py        # Command modification logic
│       │   ├── rmCmd.py         # Command removal logic
│       │   ├── runTest.py       # Enhanced test runner with execution control
│       │   └── templates/       # Code templates for new commands
│       │       ├── argCmdDef.py    # Default template with argument handling
│       │       ├── simple.py    # Simple template for basic commands
│       │       ├── classCall.py # Class-based template for OOP commands
│       │       └── asyncDef.py  # Async template for concurrent operations
│       └── defs/
│           ├── logIt.py         # Colored logging and output utilities
│           └── validation.py    # Input validation functions
├── tests/                       # Round-trip test suite
│   ├── test_newCmd_roundtrip.py    # Tests for command creation workflows
│   ├── test_modCmd_roundtrip.py    # Tests for command modification workflows
│   ├── test_rmCmd_roundtrip.py     # Tests for command removal workflows
│   └── test_argCmdDef_roundtrip.py # Tests for template functionality
├── env/${packName}/                      # Virtual environment for development
├── .${packName}rc                        # Configuration file (auto-generated)
├── pyproject.toml               # Package configuration
├── README.md                    # Basic documentation
└── README_Command_modifications.md  # This comprehensive guide
```

## Configuration File

The `.${packName}rc` file stores persistent configuration:

```json
{
  "switchFlags": {
    "globalFlag": false
  },
  "commandFlags": {
    "commandName": {
      "stringOption": "value",
      "booleanFlag": true
    }
  }
}
```

## Testing and Quality Assurance

The ${packName} framework includes a comprehensive test suite with an enhanced test runner to ensure reliability and quality.

### Running Tests

The `runTest` command provides multiple ways to execute and manage tests:

```bash
# Run all tests with default output
${packName} runTest

# Run tests with detailed verbose output (recommended for development)
${packName} runTest +verbose

# Run tests in summary mode (recommended for CI/CD)
${packName} runTest +summary

# Run tests and stop on first failure (useful for debugging)
${packName} runTest +stop

# Run a specific test file
${packName} runTest test_modCmd_roundtrip

# List all available tests
${packName} runTest listTests
```

### Test Suite Coverage

The included test suite provides comprehensive coverage:

- **`test_newCmd_roundtrip.py`**: Tests command creation workflows with various templates and flag combinations
- **`test_modCmd_roundtrip.py`**: Tests command modification including description updates, argument additions, and flag management
- **`test_rmCmd_roundtrip.py`**: Tests command and argument removal operations with proper cleanup verification
- **`test_argCmdDef_roundtrip.py`**: Tests template functionality and code generation processes

### Development Workflow

For developers contributing to ${packName} or creating complex command sets:

1. **Create commands**: Use `${packName} newCmd` to create new functionality
2. **Test immediately**: Run `${packName} runTest +verbose` to ensure no regressions
3. **Modify iteratively**: Use `${packName} modCmd` to refine command definitions
4. **Validate changes**: Run specific tests with `${packName} runTest test_name +verbose`
5. **Final verification**: Run full test suite with `${packName} runTest +summary`

### Continuous Integration

The test runner is designed for CI/CD environments:

- **Exit codes**: Returns 0 for success, 1 for any failures
- **Summary mode**: Use `+summary` for clean CI output
- **Stop on failure**: Use `+stop` to fail fast in CI pipelines
- **Verbose debugging**: Use `+verbose` when investigating CI failures

Example CI usage:
```bash
# In your CI pipeline
${packName} runTest +summary +stop  # Fast failure with clean output
```

## Development

### Adding New Commands

When you create a new command using `${packName} newCmd`, the system:

1. Prompts for descriptions of the command and its arguments
2. Prompts for descriptions of any option flags (string options and boolean flags)
3. Updates the `commands.json` file with the new command definition and flag schema
4. Generates a Python file in the `commands/` directory using the specified template
5. Makes the command immediately available for use

### Accessing Option Flags in Commands

Commands can access their stored flags using the `optSwitches` module:

```python
from ..classes.optSwitches import getCmdSwitchFlags

def mycommand(argParse):
    args = argParse.args
    arguments = args.arguments

    # Get stored command flags from .${packName}rc
    stored_flags = getCmdSwitchFlags('mycommand')

    # Get current run flags from command line
    current_flags = getattr(argParse, 'cmd_options', {})

    # Merge current run flags with stored flags (current takes precedence)
    all_flags = {**stored_flags, **current_flags}

    # Use the flags
    if all_flags.get('verbose', False):
        printIt("Verbose mode enabled", lable.INFO)

    config_file = all_flags.get('config', 'default.conf')
    printIt(f"Using config: {config_file}", lable.INFO)
```

### Command Flag Schema

The `commands.json` file stores the flag definitions:

```json
{
  "mycommand": {
    "description": "My custom command",
    "switchFlags": {
      "config": {
        "description": "Configuration file path",
        "type": "str"
      },
      "verbose": {
        "description": "Enable verbose output",
        "type": "bool"
      }
    },
    "arg1": "Description of first argument"
  }
}
```

### Template System

The template system allows you to generate different styles of command implementations:

#### Simple Template (`simple`) - Default
- Minimal implementation for basic commands
- Direct argument processing without complex logic

#### Argumment command Template (`argCmdDef`)
- The argument calles a function in the command file with the same name
  - Argument processing with exec-based function calls: exec(f"{anArg}(argParse)")
- Suitable for lauching general-purpose commands from command line that are complex
  - Custum argument handling logic can be implemented to uses other arguments during processing

#### Class-Based Template (`classCall`)
- Object-oriented approach using classes
- Method-based argument handling
- Better for complex commands with shared state

#### asyncDef Template (`asyncDef`)
- Asynchronous command implementation
- Suitable for I/O intensive operations
- Uses asyncio for concurrent processing

### Creating Custom Templates

To create a new template:

1. Create a new `.py` file in `src/${packName}/commands/templates/`
2. Define `cmdDefTemplate` and `argDefTemplate` using Python's `string.Template`
3. The template will automatically be available for use

### Custom Argument Types

The argument parser supports:
- **Strings**: Regular text arguments
- **Integers**: Numeric arguments (automatically detected)
- **Mixed**: Commands can accept both string and integer arguments

### Colored Output

The package includes a comprehensive colored logging system with different message types:
- `ERROR`: Red text for errors
- `WARN`: Yellow text for warnings
- `INFO`: White text for information
- `PASS`/`SAVED`: Green text for success messages
- `DEBUG`: Magenta text for debugging

## Configuration

Commands and their metadata are stored in `src/${packName}/commands/commands.json`. This file contains:

- Command descriptions
- Argument names and descriptions
- Switch flags and their help text

## Requirements

- Python 3.10+
- Standard library modules (no external dependencies)

## License

MIT License

## Author

**mpytel** - mpytel@domain.com

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Examples

### Creating Different Types of Commands

#### Simple Command
```bash
${packName} newCmd --template simple greet name
# Creates a basic greeting command
```

#### Class-Based Command
```bash
${packName} newCmd --template classCall database connect query
# Creates an object-oriented database command
```

#### asyncDef Command
```bash
${packName} newCmd --template asyncDef downloader url destination
# Creates an asyncDef file downloader command
```

### Using the Generated Commands

After creation, you can use your new commands:

```bash
# Simple command
${packName} greet "John Doe"

# Class-based command
${packName} database localhost "SELECT * FROM users"

# Async command
${packName} downloader "https://example.com/file.zip" "/downloads/"
```

### Development and Testing Workflow

Complete example of creating, testing, and refining commands:

```bash
# 1. Create a new command with flags
${packName} newCmd backup source --destination -compress -verbose

# 2. Test the command creation
${packName} runTest test_newCmd_roundtrip +verbose

# 3. Use the command
${packName} backup /home/data --destination /backup/data +compress +verbose

# 4. Modify the command to add features
${packName} modCmd backup --encryption -dry-run

# 5. Test modifications
${packName} runTest test_modCmd_roundtrip

# 6. Run full test suite to ensure no regressions
${packName} runTest +summary

# 7. List all available tests
${packName} runTest listTests

# 8. Debug specific test issues
${packName} runTest test_modCmd_roundtrip +verbose +stop
```

### Modifying Existing Commands

You can enhance existing commands by adding new arguments and option flags:

```bash
# Add new arguments to existing command
${packName} modCmd greet surname
# Prompts: "New argument description for surname"

# Add boolean flags to existing command
${packName} modCmd greet -formal -uppercase
# Prompts for descriptions of each flag

# Add string options to existing command  
${packName} modCmd greet --prefix --greeting
# Prompts for descriptions of each option

# Modify existing descriptions
${packName} modCmd greet name
# Prompts: "Replace description for name (y/N): "

# Combined modifications
${packName} modCmd database host query -verbose --timeout
# Adds new args and flags in one command
```

**Key modCmd Features:**
- Modify command and argument descriptions
- Add new arguments to existing commands
- Add option flags (boolean `-flag` and string `--option`) 
- Flags are automatically saved to `.${packName}rc` configuration
- Command `.py` files remain unchanged (metadata only)
- Interactive prompts guide you through the process

### Template Management

```bash
# List all available templates
${packName} newCmd --templates

# Use specific template
${packName} newCmd --template asyncDef processor input output

# Fallback to default if template doesn't exist
${packName} newCmd --template nonexistent fallback arg1
```

## Troubleshooting

### Command Not Found
If a command isn't recognized, check:
- The command exists in `commands.json`
- The corresponding `.py` file exists in the `commands/` directory
- The command name is spelled correctly

### Template Issues
If template-related errors occur:
- Verify the template exists using `${packName} newCmd --templates`
- Check that the template file has proper `cmdDefTemplate` and `argDefTemplate` definitions
- The system will fall back to the default template if the specified template is not found

### Test Execution Issues
If tests fail to run or behave unexpectedly:
- Ensure the virtual environment is properly set up: `source env/${packName}/bin/activate`
- Check that all test files are in the `./tests` directory and named `test_*.py`
- Use `${packName} runTest +verbose` to see detailed error output
- Verify the package is installed in development mode: `pip install -e .`
- Run `${packName} runTest listTests` to confirm test discovery is working

### Flag and Configuration Issues
If command flags aren't working properly:
- Check that flags are defined in the command's `switchFlags` section in `commands.json`
- Verify the `.${packName}rc` file exists and contains the command's flag definitions
- Use `+flag` to enable and `-flag` to disable boolean flags
- Remember that string options use `--option value` syntax

### Import Errors
Ensure the package is properly installed:
```bash
pip install -e .
```

### Terminal Width Issues
The help system automatically adapts to terminal width. If formatting looks odd, try resizing your terminal or using a standard terminal width (80+ characters recommended).

### Virtual Environment Issues
If commands fail to execute properly:
- Ensure you're in the project directory when running commands
- The test runner automatically activates `env/${packName}/bin/activate`, but manual command execution may require activation
- Verify the virtual environment has the correct Python version and dependencies
"""))