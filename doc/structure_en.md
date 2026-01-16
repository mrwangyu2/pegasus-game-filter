# Project Structure

## Directory Layout

```
pegasus-game-filter/
│
├── main.py                           # Application entry point
│
├── requirements.txt                  # Python dependencies
├── run.bat                           # Windows launch script
│
├── doc/                              # Documentation
│   ├── readme.md                     # Manual (CN)
│   ├── readme_en.md                  # Manual (EN)
│   ├── implementation.md             # Technical Details (CN)
│   ├── implementation_en.md          # Technical Details (EN)
│   ├── deployment.md                 # Deployment Guide (CN)
│   ├── deployment_en.md              # Deployment Guide (EN)
│   ├── structure.md                  # Structure Info (CN)
│   └── structure_en.md               # Structure Info (EN)
│
├── core/                             # Business Logic
│   ├── project.py                   # Project config
│   ├── metadata_parser.py           # Pegasus metadata parser
│   ├── game_manager.py              # Game list and task execution
│   ├── task_system.py               # Async task queue
│   ├── i18n.py                      # Internationalization
│   └── theme.py                     # UI Theme & Icons
│
└── ui/                               # User Interface
    ├── main_window.py               # Main window logic
    ├── game_list_widget.py          # List component
    ├── game_detail_widget.py        # Detail & Preview component
    ├── log_window.py                # Logging window
    └── ...
```
