#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

README_Command_modifications_template = Template(dedent("""# ${packName}
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
${packName} --help
```

### Command Management

#### Create a New Command
```bash
${packName} newCmd mycommand "Description of my command"
```

#### Create a Command with Arguments
```bash
${packName} newCmd mycommand "Description" --args "arg1:str:Description of arg1" "arg2:int:Description of arg2"
```

#### Create a Command with Template
```bash
${packName} newCmd mycommand "Description" --template classCall
```

#### Modify an Existing Command
```bash
${packName} modCmd mycommand --description "New description"
${packName} modCmd mycommand --add-args "newarg:str:New argument description"
${packName} modCmd mycommand --remove-args newarg
```

#### Remove a Command
```bash
${packName} rmCmd mycommand
```

### Option Flags Management

#### Create Boolean Flags
```bash
${packName} newCmd mycommand "Description" --flags "verbose:bool:Enable verbose output"
```

#### Create String Flags
```bash
${packName} newCmd mycommand "Description" --flags "output:str:Output file path"
```

#### Use Flags in Commands
```bash
${packName} mycommand +verbose --output result.txt
${packName} mycommand -verbose  # Disable verbose flag
```

### Available Templates

1. **argCmdDef** (Default): Full-featured template with argument handling
2. **simple**: Minimal template for basic commands
3. **classCall**: Object-oriented template for structured commands
4. **asyncDef**: Async template for concurrent operations

### Test Management

#### Run All Tests
```bash
${packName} runTest
```

#### Run Specific Tests
```bash
${packName} runTest --tests test_newCmd_roundtrip
```

#### Run Tests with Different Output Modes
```bash
${packName} runTest --mode summary    # Brief summary
${packName} runTest --mode detailed   # Detailed output
${packName} runTest --mode json       # JSON format
```

## Project Structure

After installation, ${packName} creates the following structure in your working directory:

```
${packName}/
├── src/${packName}/
│   ├── main.py                     # Entry point
│   ├── classes/
│   │   ├── argParse.py            # Argument parsing logic
│   │   └── optSwi${packName}hes.py         # Option flag management
│   ├── commands/
│   │   ├── commands.json          # Command registry
│   │   ├── cmdSwi${packName}hbord.py       # Command dispa${packName}her
│   │   ├── commands.py            # Command loading
│   │   ├── newCmd.py              # Command creation
│   │   ├── modCmd.py              # Command modification
│   │   ├── rmCmd.py               # Command removal
│   │   ├── runTest.py             # Test runner
│   │   └── templates/             # Code templates
│   │       ├── argCmdDef.py       # Default template
│   │       ├── simple.py          # Simple template
│   │       ├── classCall.py       # Class template
│   │       └── asyncDef.py        # Async template
│   └── defs/
│       ├── logIt.py              # Logging utilities
│       └── validation.py         # Input validation
├── tests/                          # Test files
├── .${packName}rc                         # Configuration file
└── pyproject.toml                 # Package configuration
```

## Configuration

${packName} uses two main configuration files:

### commands.json
Stores command definitions, arguments, flags, and metadata:

```json
{
  "commands": {
    "mycommand": {
      "description": "My custom command",
      "args": {
        "arg1": {
          "type": "str",
          "description": "First argument"
        }
      },
      "flags": {
        "verbose": {
          "type": "bool",
          "description": "Enable verbose output",
          "default": false
        }
      }
    }
  }
}
```

### .${packName}rc
Stores user preferences and persistent flag values:

```json
{
  "mycommand": {
    "verbose": true,
    "output": "/path/to/file"
  }
}
```

## Command Templates

### argCmdDef Template
Full-featured template with comprehensive argument handling:
- Automatic help generation
- Argument validation
- Flag processing
- Error handling

### simple Template
Minimal template for basic commands:
- Basic structure
- Simple argument access
- Minimal boilerplate

### classCall Template
Object-oriented template:
- Class-based command structure
- Method organization
- State management

### asyncDef Template
Asynchronous template:
- Async/await support
- Concurrent operations
- Non-blocking execution

## Advanced Usage

### Complex Flag Scenarios
```bash
# Create command with multiple flag types
${packName} newCmd deploy "Deploy application" \\
  --flags "env:str:Target environment" \\
          "force:bool:Force deployment" \\
          "rollback:bool:Enable rollback"

# Use the command with flags
${packName} deploy +force --env production
```

### Template Customization
Commands are generated from templates that can be customized by modifying the template files in the `commands/templates/` directory.

### Test Automation
```bash
# Run comprehensive test suite
${packName} runTest --mode detailed --verbose

# Run specific test categories
${packName} runTest --tests newCmd modCmd rmCmd
```

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure ${packName} is installed and in your PATH
2. **Permission errors**: Check file permissions in the project directory
3. **JSON parsing errors**: Verify commands.json syntax
4. **Template errors**: Check template file syntax and variable substitution

### Debug Mode
Use verbose output for debugging:
```bash
${packName} <command> --verbose
```

### Log Files
${packName} maintains logs for debugging and audit purposes. Check the logs directory for detailed execution information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the ${license} - see the LICENSE file for details.

## Version History

- **${version}**: Current version with enhanced template system and comprehensive testing
- Previous versions: See CHANGELOG.md for detailed version history

## Support

For issues, questions, or contributions:
- Create an issue on the project repository
- Check the documentation for common solutions
- Review the test files for usage examples

---

*${packName} - Dynamic Command-Line Framework*
"""))

