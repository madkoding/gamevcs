# GameVCS - Version Control for Game Development

A centralized version control system designed for game development projects with large binary assets. Built with Python, it provides a simple CLI interface, TUI, and REST API server.

## Features

- **Client-Server Architecture**: Connect to a central server for team collaboration
- **Binary File Support**: Optimized for large binary assets that can't be merged
- **Smart Locking**: Queue-based file locking to prevent conflicts on binary files
- **Shelving**: Store work-in-progress on the server without committing
- **Branches**: Create parallel versions of your project
- **Tags**: Mark important commits for easy reference
- **Rich CLI**: Beautiful terminal interface with colors and tables
- **TUI**: Interactive terminal user interface
- **SQLite Storage**: Simple, portable database with no external dependencies

## Quick Start (Run Directly)

No installation required! Run directly from the repository:

```bash
# Clone the repository
git clone https://github.com/yourrepo/game-version-control.git
cd game-version-control

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Start the server
python -m gamevcs.server.main -path /path/to/server/data -port 9000
```

Or run the client:

```bash
# Initialize a workspace
python -m gamevcs.client.main init -e your@email.com -h localhost:9000 -pw password

# Use the CLI
python -m gamevcs.client.main status
python -m gamevcs.client.main add file.txt
python -m gamevcs.client.main commit -m "message"

# Or use the TUI
python -m gamevcs.client.main tui
```

## Installation

### From Source

```bash
# Clone and install
cd game-version-control
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Or install globally
pip install -e . --target /usr/local
```

### From Pre-built Executables

Download from `dist/` folder:

```bash
# Server
tar -xzf gamevcs-server-linux-x64.tar.gz
cd gamevcs-server
./gamevcs-server -path /path/to/data -port 9000

# Client
tar -xzf gamevcs-client-linux-x64.tar.gz
cd gamevcs
./gamevcs init -e email -h server:port -pw password
./gamevcs status
./gamevcs tui
```

## CLI Commands

### Initialization

```bash
gamevcs init -e email -h host:port -pw password
```

Initialize a new workspace. The first user becomes admin automatically.

### Status

```bash
gamevcs status
```

Shows current project, branch, workspace changelist, and pending changes.

### Adding Files

```bash
gamevcs add file.txt
gamevcs add file1.txt file2.txt
gamevcs add *.png
```

Add files to the workspace changelist.

### Committing

```bash
gamevcs commit -m "Added player character"
```

Commit the workspace changelist to the server history.

### Shelving

```bash
gamevcs shelve -m "Work in progress"
```

Store changes on the server without committing. Other users can unshelve your work.

```bash
gamevcs unshelve 5
```

Restore shelved changelist #5 to your workspace.

### Branches

```bash
# List branches
gamevcs branch list

# Create a branch
gamevcs branch add feature-branch -desc "New feature"

# Switch to a branch
gamevcs branch switch feature-branch

# Merge another branch into current
gamevcs branch merge feature-branch
```

### Tags

```bash
# List tags
gamevcs tag list

# Add tag to current changelist
gamevcs tag add v1.0

# Add tag to specific changelist
gamevcs tag add release -cl 42

# Remove tag
gamevcs tag remove v1.0
```

### File Locking

```bash
# Lock a file
gamevcs lock file.png

# Unlock a file
gamevcs unlock file.png

# View all locks
gamevcs locks
```

When a file is locked, other users can request to be added to the lock queue.

### Getting Files

```bash
# Get latest
gamevcs get latest
gamevcs get

# Get specific changelist
gamevcs get 42

# Get by tag
gamevcs get v1.0
```

### TUI (Terminal User Interface)

Launch the interactive TUI:

```bash
gamevcs tui
```

The TUI shows:
- Project and branch status
- Workspace changes
- Commit history
- Branches and tags
- Interactive menus for all operations

## Architecture

### Server Components

- **FastAPI REST API**: Handles all client requests
- **SQLite Database**: Stores users, projects, branches, changelists, tags, locks
- **File Storage**: Binary files stored on disk by hash

### Database Schema

```
users
  - id, email, username, password_hash, role, is_active

projects
  - id, name, description

branches
  - id, project_id, name, description, root_cl_id

changelists
  - id, project_id, branch_id, user_id, message, status, is_shelf

files
  - id, changelist_id, path, hash, size, operation

file_locks
  - id, file_id, user_id, queue_position, status

tags
  - id, project_id, name, changelist_id
```

### API Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{id}/branches` - List branches
- `POST /projects/{id}/branches` - Create branch
- `GET /changelists` - List changelists
- `POST /changelists` - Create changelist
- `POST /changelists/{id}/commit` - Commit
- `POST /changelists/{id}/shelve` - Shelve
- `POST /changelists/{id}/files` - Upload file
- `GET /locks` - List locks
- `POST /locks` - Request lock
- `DELETE /locks/{id}` - Release lock
- `GET /tags` - List tags
- `POST /tags` - Create tag

## Configuration

### Server Options

```bash
gamevcs-server -path <dir> -port <port> -log_level <level>
```

- `-path`: Required. Server data directory
- `-port`: Server port (default: 9000)
- `-log_level`: debug, info, warning, error
- `-allow_dv_upgrade`: Allow database version upgrades
- `-allow_non_empty_path`: Allow non-empty data directory

### Workspace Config

The `.gamevcs/config.json` file stores:

- Server URL and token
- Current project and branch
- Workspace changelist ID

## User Roles

- **Admin**: Full access, can manage users and projects
- **Manager**: Can manage normal users and projects
- **Normal**: Basic version control operations

## Building Executables

```bash
# Install pyinstaller
pip install pyinstaller

# Build client and server
./build.sh
```

Or manually:

```bash
pyinstaller client.spec --clean --noconfirm
pyinstaller server.spec --clean --noconfirm
```

## Project Structure

```
gamevcs/
├── server/           # Server code
│   ├── main.py      # Entry point
│   ├── models.py    # SQLAlchemy models
│   ├── database.py  # Database connection
│   ├── auth.py      # Authentication
│   └── api/         # REST API endpoints
├── client/          # Client code
│   ├── main.py     # CLI entry point
│   ├── api.py      # API client
│   ├── tui.py      # Terminal UI
│   └── commands/   # CLI commands
├── setup.py
├── client.spec     # PyInstaller config
├── server.spec     # PyInstaller config
└── build.sh        # Build script
```

## License

MIT License