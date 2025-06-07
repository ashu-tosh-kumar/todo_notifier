"""
TODO Notifier - Automated TODO tracking and notifications for your codebase

Never forget a TODO again! Automatically parse, track, and get notified about TODO items
in your code.

## Features

- **Smart TODO Detection** - Automatically discovers TODO items across your entire
  codebase
- **Date-based Tracking** - Set completion dates and get notified about overdue items
- **User Assignment** - Assign TODOs to specific team members
- **Multiple Report Types** - Module-wise, user-wise, and deadline-based summaries
- **Email Notifications** - Automated email reports with HTML formatting
- **Flexible Configuration** - Extensive customization options for different workflows
- **Multiple Integration Methods** - Works with Git repositories, local directories, or
  single files
- **Export Options** - Save reports as HTML files for sharing and archiving

## Quick Start

```python
from todonotifier.config import DefaultConfig
from todonotifier.connect import ConnectMethod, Connect
from todonotifier.driver import run as driver_run

# Configure for a Git repository
git_url = "https://github.com/your-username/your-repo.git"
project_name = "your-project"

connect = Connect(
    connect_method=ConnectMethod.GIT_CLONE,
    project_dir_name=project_name,
    url=git_url,
    branch_name="main"
)

config = DefaultConfig(
    save_html_reports=True,
    ignore_todo_case=True
)

# Generate TODO reports
driver_run(connect=connect, config=config)
```

## TODO Format

TODO Notifier supports a flexible format for TODO items:

```python
# Full format with all components
# TODO {2024-12-31} @john_doe Implement user authentication

# Date only
# TODO {2024-12-31} Add error handling

# User only
# TODO @jane_smith Review this logic

# Simple TODO
# TODO Fix this bug
```

**Format Components:**
- `TODO` - The keyword (case-insensitive option available)
- `{YYYY-MM-DD}` - Optional completion date
- `@username` - Optional assignee
- `message` - Optional description

## Architecture

The system consists of several key components:

- **todo_notifier.py** - Main parsing logic that extracts TODO items using regex
  patterns
- **models.py** - Core data models (`TODO`, `USER`, `POSITION`) with date parsing and
  validation
- **config.py** - Configuration system with `BaseConfig` and `DefaultConfig` classes
- **driver.py** - Main orchestration layer that coordinates parsing, summary generation,
  and notifications
- **connect.py** - Repository connection handlers for git repos, local directories, and
  files
- **summary_generators.py** - Pluggable summary generators (by module, expired TODOs,
  upcoming TODOs)
- **notifier.py** - Notification system with email support and extensible base classes

## Generated Reports

TODO Notifier generates three types of reports by default:

1. **Module-wise Summary** - Lists all TODO items organized by file/module
2. **Expired TODOs by User** - Highlights overdue TODO items assigned to each team
   member
3. **Upcoming Week TODOs** - Shows TODO items due within the next 7 days

All reports can be saved as HTML files and/or sent via email notifications.

## Installation

```bash
pip install todonotifier
```

For more examples and advanced usage, see the individual module documentation.
"""
