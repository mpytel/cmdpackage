#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import Template
from textwrap import dedent

readme_template = Template(dedent("""# ${packName}
version - ${version}

A dynamic command-line tool for creating, modifying, and managing custom commands with interactive help and argument parsing.

## Overview

${packName} is a Python package that provides a framework for building extensible command-line applications. It allows you to dynamically create new commands, modify existing ones, and manage command arguments through an interactive interface.

## Features

- **Dynamic Command Creation**: Add new commands with custom arguments on-the-fly
- **Multiple Code Templates**: Choose from different templates when creating commands (simple, class-based, asyncDef)
- **Interactive Help System**: Colored, formatted help text that adapts to terminal width
- **Command Management**: Modify or remove existing commands and their arguments
- **Flexible Argument Parsing**: Support for both string and integer arguments
- **Template-Based Code Generation**: Automatically generates Python files for new commands
- **JSON-Based Configuration**: Commands and their descriptions stored in JSON format
- **Command-Specific Options**: Use double-hyphen options for command-specific functionality

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
Add a new command with optional arguments:

```bash
${packName} newCmd <cmdName> [argName1] [argName2] ...
```

**Command-Specific Options:**
- `--template <templateName>`: Specify which template to use for code generation
- `--templates`: List all available templates

**Available Templates:**
- `newCmd` (default): Standard template with argument handling
- `simple`: Minimal template for basic commands
- `classCall`: Object-oriented template using classes
- `asyncDef`: Asynchronous template for asyncDef operations

Examples:
```bash
# Create command with default template
${packName} newCmd deploy server port

# Create command with specific template
${packName} newCmd --template classCall chatBot message response

# Create asyncDef command
${packName} newCmd --template asyncDef fileProcessor input output

# List available templates
${packName} newCmd --templates
```

This will:
- Create a new command with the specified name
- Add arguments as specified
- Generate a `.py` file using the chosen template
- Prompt for descriptions of the command and each argument

#### `modCmd` - Modify Existing Command
Modify command or argument descriptions, or add new arguments:

```bash
${packName} modCmd <cmdName> [argName...]
```

Example:
```bash
${packName} modCmd deploy timeout
```

#### `rmCmd` - Remove Command
Remove a command and its associated file, or remove specific arguments:

```bash
${packName} rmCmd <cmdName> [argName...]
```

Example:
```bash
# Remove entire command
${packName} rmCmd deploy

# Remove specific argument
${packName} rmCmd deploy timeout
```

### Getting Help

```bash
# Show general help
${packName} -h

# Show help for specific command
${packName} <command> -h
```

## Option Types

${packName} supports two types of options:

### Global Options (Single Hyphen)
- Format: `-<letter>` or `+<letter>`
- Scope: Apply to the entire ${packName} application
- Example: `-h` for help

### Command-Specific Options (Double Hyphen)
- Format: `--<word>`
- Scope: Apply only to specific commands
- Example: `--template classCall` for the newCmd command

## Project Structure

```
${packName}/
├── src/
│   └── ${packName}/
│       ├── main.py              # Entry point
│       ├── classes/
│       │   ├── argParse.py      # Custom argument parser with colored help
│       │   └── optSwitches.py   # Option switch handling
│       ├── commands/
│       │   ├── commands.json    # Command definitions and descriptions
│       │   ├── commands.py      # Command loading and management
│       │   ├── cmdSwitchbord.py # Command routing and execution
│       │   ├── newCmd.py        # New command creation logic
│       │   ├── modCmd.py        # Command modification logic
│       │   ├── rmCmd.py         # Command removal logic
│       │   └── templates/       # Code templates for new commands
│       │       ├── newCmd.py    # Default template
│       │       ├── simple.py    # Simple template
│       │       ├── classCall.py # Class-based template
│       │       └── asyncDef.py     # asyncDef template
│       └── defs/
│           └── logIt.py         # Colored logging and output utilities
├── pyproject.toml               # Package configuration
└── README.md                    # This file
```

## Development

### Adding New Commands

When you create a new command using `${packName} newCmd`, the system:

1. Prompts for descriptions of the command and its arguments
2. Updates the `commands.json` file with the new command definition
3. Generates a Python file in the `commands/` directory using the specified template
4. Makes the command immediately available for use

### Template System

The template system allows you to generate different styles of command implementations:

#### Default Template (`newCmd`)
- Standard argument processing with exec-based function calls
- Suitable for most general-purpose commands

#### Simple Template (`simple`)
- Minimal implementation for basic commands
- Direct argument processing without complex logic

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

# asyncDef command
${packName} downloader "https://example.com/file.zip" "/downloads/"
```

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

### Import Errors
Ensure the package is properly installed:
```bash
pip install -e .
```

### Terminal Width Issues
The help system automatically adapts to terminal width. If formatting looks odd, try resizing your terminal or using a standard terminal width (80+ characters recommended).
    """))
