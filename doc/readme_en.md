# Pegasus Game Filter v1.0

A desktop application for managing and filtering Pegasus Frontend game ROMs.

![Demo](doc/gif/demo.gif)

[中文版](doc/readme.md) | [English]

## Features

- ✨ **Project Management**: Create, open, and edit projects, supporting name and directory modifications.
- ✨ **Dual View Mode**: One-click toggle between Source and Project directories (Tab key).
- ✨ **Task Queue System**: Plan operations (Add/Remove/Update) and execute them in bulk (F5 key) with real-time logs.
- ✨ **Media Preview**: Display Logo icons in the list, with real-time cover art and video previews on the right.
- ✨ **Metadata Editing**: Full support for editing, extracting, merging, and parsing game information.
- ✨ **Batch Operations**: Batch search and add games to the task queue from a name list.
- ✨ **Interactive Experience**: Multi-select (Space), real-time search filtering, and global hotkeys.
- ✨ **Logging System**: Color-coded logs detailing every task's execution status.

## Quick Start

### Option A: Direct Use (Recommended)

If you are a regular user, it is recommended to download the latest `.zip` package from the GitHub [Releases](https://github.com/mrwangyu2/pegasus-game-filter/releases) page. Extract and run `天马G游戏筛选器.exe` inside; no Python installation is required.

### Option B: Run from Source (Developers)

# 1. Clone the repository
```bash
git clone https://github.com/mrwangyu2/pegasus-game-filter.git
cd pegasus-game-filter
```

# 2. Install dependencies
```bash
pip install -r requirements.txt
```

# 3. Install Video Decoders (Required)
To enable in-app video preview, please install LAVFilters:
Download: https://github.com/Nevcairiel/LAVFilters/releases

# 4. Run the application
```bash
python main.py
```

## First Time Use

1. **Create Project**
   - Click "File" -> "New Project"
   - Enter a project name
   - Select the Source ROM root (the Roms folder containing platform subdirectories)
   - Select the Project ROM root (an empty folder for your filtered games)
   - Save the project file

2. **Browse & Run Games**
   - Browse all games in the list.
   - Click a game to see its cover and video preview.
   - **Run Game**: Double-click a game entry to launch it using the system's associated emulator.
   - **Note**: To ensure games run correctly, it is recommended to use the full Pegasus-G collection. You can download it from [Archmage83/game_collection](https://github.com/Archmage83/game_collection).

3. **Select Games**
   - Press Space to select/deselect a game (selected games have a yellow background).
   - You can select multiple games.

4. **Execute Tasks**
   - Click "Add to Task" (or press A) after selecting games.
   - Tasks are queued, and the status bar shows the count.
   - Press F5 to execute all tasks.
   - Monitor the log window for progress.

## User Guide

### Pegasus Directory Structure

The application follows Pegasus Frontend naming conventions:

```
Roms/                           # ROM Root
├── GBA/                        # Platform folder
│   ├── metadata.pegasus.txt   # Metadata file (Required)
│   ├── media/                 # Media folder
│   │   ├── Game Name/         # Game-specific media folder
│   │   │   ├── logo.png       # Logo image
│   │   │   ├── boxFront.png   # Cover image
│   │   │   └── video.mp4      # Video preview
│   │   └── ...
│   ├── Game1.gba
│   ├── Game2.zip
│   └── ...
```

### Hotkeys

| Hotkey | Function | Description |
|--------|----------|-------------|
| **Tab** | Toggle View | Switch between Source and Project views |
| **Space** | Select/Deselect | Toggle selection status for current game (Multi-select) |
| **Enter/Return** | Play Preview | Play the video preview of the current game |
| **J / K** | Navigate | Move down / up the game list (Vim style) |
| **PageUp / Down**| Page Nav | Quickly scroll through the game list |
| **F5** | Execute | Execute all pending tasks (Copy or Delete) |
| **Ctrl+R** | Run Game | Launch the selected game using an emulator |
| **Ctrl+F** | Focus Search | Jump focus to the search box |
| **Ctrl+B** | Batch Add | Open the batch search and add dialog |
| **Ctrl+E** | Metadata | Edit project metadata or view source metadata |
| **Ctrl+Shift+C** | Clear Tasks | Clear all pending tasks in the queue |
| **Alt+Up/Down** | Switch Platform| Quickly toggle between different platforms |
| **Ctrl+Alt+L/G** | Language | Toggle between Chinese and English |
| **Ctrl+Alt+0-9** | Theme | Switch between different UI themes |


## Developer Info

- **Version**: 1.0.1
- **Developer**: Wang Yu
- **Email**: wangyuxxx@163.com
- **Tech Stack**: Python 3, PyQt5
- **Documentation**:
  - [Deployment & Packaging](doc/deployment_en.md)
  - [Architecture & Implementation](doc/implementation_en.md)
  - [Project Structure](doc/structure_en.md)


## License

This project is for educational and personal use only.

## Credits

Special thanks to the Pegasus Frontend project for providing such an excellent frontend solution.
