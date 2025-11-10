#!/usr/bin/python
# -*- coding: utf-8 -*-
from textwrap import dedent
from string import Template

copilot_instructions_template = Template(dedent("""# GitHub Copilot Instructions for ${packName} system development

## Specific Copilot Chat Instructions

**I-1)** When copilot creates a new shell, for working with or testing ${packName}, WILL run `source env/${packName}/bin/activate` to set the vertual environment. All subsequent ${packName} commands will NOT included this source command.

**I-2)** Small focused changes can be implimented automaticly. If rather large refactoring is reqiured, work wiht the Programmer befor implement code changes based on thie type of request.

**I-3)** Copilot WILL explain back ${packName} concepts before implementing changes.

**I-4)** "Pertinent Information" (${packName}) as a core concept that may not align with common programming patterns. For this reason Copilot MUST defer to the programer when it comes to design choices. 

**I-5)** Copilot MUST NOT perform any automated testing without asking the Programmer to proceed.

**I-6)** Copilot CAN provide a list of CLI command to run, but the Programmer WILL execute them in a sperate zsh shell and paste results into the Copilot chat.

**I-7)** Intentional or accidental misspellings in code and documentation ("fraimwork", "challanges", "experance") WILL be encouterd. Copilot will point this out so it can be corrected. piFraimwork is such a case and piFramework is not.

## Project Overview

**Pi** is a versatile pertinent information collection, storage, and retrieval system. It is a research project investigating how user and AI generated content can be captured and stored in structure so users can reliably use it in repeatable semi-constant ways that can justify a protean understanding of their truth.

${packName} is a `cmdPackage` derived python package. `cmdPackage` generates framework (`copilot_instructions_cmdpackage_pi.md`) for derived python packages to add, modify, and remove command line interface (CLI) functionality. Also, enabling Python Package Index (PyPI) distribution. 

${packName} represents an object to manage an unlimited number of ideas. This number is unlimited because the type of information captured by Pi becomes a network of recursively self-defining (`copilot_definition_recursively_self_defining.md`) pieces of information. This idea stems from the notion of topics, an outcrop of ideas associated with topic oriented writing. Where reuse and agnostic output targeting is used with self-indexing and maps to manage topics during their authoring, editing, and output life-cycle phases of content delivery. The net result is a self indexing pertinent information (${packName}) json file storage system and CLI/API interfaces.

**Note:** The meaning/definition of what ${packName} represents are many:
1) 'Pi' represents system encapsulating inspired concepts for pertinent information management.
2) '${packName}' represents the derived python package. 
3) '${packName}' represents the concept of self-indexing pertinent information. 
4) '${packName}' represents the basic json data structure that other pis will inherit.
5) '${packName}' represents an unlimited number of ideas.

The notion that ${packName} sets can describe a users truth about an idea with a network of recursively self-defining pis stems from an idea that any ${packName} is a topic. Syntactically, a ${packName} name uses different conventions depending on context:

**Documentation Convention (piCase):** Any token or word-set predicted by '${packName}', concatenated into Pascal case variable naming convention, where spaces between words are removed. This naming convention puts the title of any topic into the ${packName} domain (e.g., piProgramInvestigates, piUserProfile, piDomainBody). This is used in documentation, conceptual discussions, and system design.

**Python Code Convention (snake_case):** Standard Python snake_case naming follows PEP 8 conventions for actual code implementation (e.g., pi_program_investigates, pi_user_profile, pi_domain_body). This ensures code readability and compliance with Python standards.

**Key Distinction:**
- **piCase** = Documentation, concepts, design discussions (piProgramInvestigates)
- **snake_case** = Python code implementation (pi_program_investigates)

Both conventions maintain the '${packName}' prefix to clearly identify variables as part of the Pi system, but adapt to their respective contexts for optimal readability and standards compliance.

The seed of `piDomain` is a topic. A topic is tuple of strings (type, title, and short description). In the piDomain, this tuple is named piSeed, when used as raw text, and `piBase` when stored as json. The piBase object has three attributes: 1) `piType`, 2) `piTitle`, and 3) `piSD`. A piSeed uses bash terminal CLI string handling (dog jade 'my dog is a rat terrier cattle dog mix. She is good, cute, and clever.').

The basic ${packName} json data structure is:
```
"piBase": {
  "piProlog": {
    "title": "",
    "version": "",
    "author": "",
    "copyright": ""
  },
  "piBase": {
    "piType": "",
    "piTitle": "",
    "piSD": ""
  },
  "piID": "",
  "piTouch": {
    "piCreationDate": "",
    "piModificationDate": "",
    "piTouchDate": "",
    "piTouches": 0
  },
  "piIndexer": {
    "piMD5": "",
    "piUser": "",
    "piRealm": "",
    "piDomain": "",
    "piSubject": ""
  },
  "piInfluence": {
    "piPrecedent": [],
    "piDescendent": []
  },
  "piBody": {}
}
```

Extensibility is drawn from the piBody that starts out as dict, but can assume the structure of any ${packName}<Type>Body.

## Pi Domain and Data Structure

The ${packName} system is built around the concept of topics and self-indexing pertinent information. For detailed implementation and cmdPackage framework information, see `copilot_instructions_cmdpackage_pi.md`.

## Pi Development Guidelines

When working with Pi concepts:
- **Documentation**: Use piCase naming for all ${packName}-related concepts (piProgramInvestigates, piUserProfile, piDomainBody)
- **Python Code**: Use snake_case naming following PEP 8 standards (pi_program_investigates, pi_user_profile, pi_domain_body)
- Remember that any topic can become a ${packName} by applying the appropriate naming convention for the context and programiclly constructing an inharited class of the `piPi.py` base class.
- Focus on the recursive, self-defining nature of ${packName} data structures
- Understand that piBody provides extensibility through ${packName}<Type>Body structures
- Be mindful of the philosophical aspects of "truth" representation in data
- Always maintain the '${packName}' prefix in both naming conventions to identify variables as part of the Pi system

This framework is designed to capture and manage pertinent information in a self-indexing, recursively expandable system that reflects the user's understanding of their truth.
"""))

