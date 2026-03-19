# GameVCS - Version Control for Game Development

A simple, centralized version control system designed for game development with large binary assets.

## Why GameVCS?

- Designed for binary files (images, audio, models) that can't be merged
- Smart locking prevents conflicts on shared assets
- Simple client-server architecture
- Works without Git knowledge

## Quick Start

### 1. Start the Server

```bash
# Download from Releases or build from source
python -m gamevcs.server.main -path ./data -port 9000
```

### 2. Connect a Client

```bash
# Initialize workspace
gamevcs init -e your@email.com -h localhost:9000 -pw yourpassword

# Check status
gamevcs status
```

### 3. Start Working

```bash
# Add files
gamevcs add *.png

# Commit
gamevcs commit -m "Added player sprites"

# Or use the visual interface
gamevcs tui
```

## Commands

| Command | Description |
|---------|-------------|
| `gamevcs init -e email -h host -pw pass` | Connect to server |
| `gamevcs status` | Show pending changes |
| `gamevcs add <files>` | Add files to changelist |
| `gamevcs commit -m "message"` | Save changes |
| `gamevcs shelve -m "message"` | Save without committing |
| `gamevcs unshelve <id>` | Restore shelved changes |
| `gamevcs get [latest\|id\|tag]` | Get files from server |
| `gamevcs branch list\|add\|switch` | Manage branches |
| `gamevcs tag list\|add\|remove` | Manage tags |
| `gamevcs lock\|unlock <file>` | Lock files |
| `gamevcs tui` | Visual interface |

## Installation

### From Source
```bash
pip install -e .
```

### From Binary
Download from GitHub Releases, extract, and run.

## For Beginners

Run `gamevcs tui` for an interactive visual interface instead of typing commands.

## License

MIT