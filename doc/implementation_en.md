# Pegasus Game Filter - Implementation v1.0

## 1. Overall Architecture

### 1.1 Design Pattern

Uses the MVC (Model-View-Controller) pattern with an added Task Queue layer:

```
┌─────────────────────────────────────┐
│         UI Layer (View)             │
│  - MainWindow                       │
│  - GameListWidget                   │
│  - GameDetailWidget                 │
│  - LogWindow                        │
│  - AboutDialog                      │
│  - ProjectSettingsDialog            │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Controller Layer               │
│  - Event Handling                   │
│  - User Interaction Logic           │
│  - Task Queue Management            │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     Task Queue Layer                │
│  - TaskQueue                        │
│  - Task Objects                     │
│  - TaskType Definitions             │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Core Layer (Model)             │
│  - Project Configuration            │
│  - GameManager                      │
│  - MetadataParser                   │
└─────────────────────────────────────┘
```

## 2. Core Modules

### 2.1 Metadata Parser (metadata_parser.py)

**Game Class**:
- `game`: Game name (matches media directory name)
- `file`: ROM filename
- `sort_by`: Sorting index
- `developer`: Developer
- `description`: Multi-line description
- `platform`: Platform name
- `platform_path`: Path to the platform folder

### 2.2 Task System (task_system.py)

**Task Types**:
- `ADD`: Copy game from source to project
- `REMOVE`: Delete game from project
- `UPDATE`: Save metadata changes

**Task Queue Features**:
- De-duplication: Prevents redundant tasks for the same game.
- Logging: Integrated callback system for UI feedback.

### 2.3 Game Manager (game_manager.py)

Handles file I/O operations:
- Scans platform directories for `metadata.pegasus.txt`.
- Performs file copying for ROMs and media (logo, boxFront, video).
- Updates metadata files after operations.

## 3. Deployment & Packaging

Uses `PyInstaller` for Windows distribution. Resource files (icons) are bundled using the `--add-data` flag.
