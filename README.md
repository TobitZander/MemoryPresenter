# Memory Presenter

A locally running memory game application built with Flask and
Flask-SocketIO. When started as an executable, it also provides a system tray
icon with options to open the browser or exit the server. This repository contains only source code, neutral demo
graphics, and public sample data. Personal photos, audio/video files, and
other private media do not belong in this repository.

> **AI-assisted development:** This project was developed with the assistance
> of artificial intelligence. All generated code and content should be
> reviewed, tested, and adapted by a human before use.

## Start development

```powershell
py -3 -m pip install -r requirements.txt
py -3 app.py
```

Then open the moderator view at `http://127.0.0.1:5000/moderator` and the
display view at `http://127.0.0.1:5000/display`.

The server shuts down automatically 30 seconds after the last browser client
disconnects. It can also be stopped with the `Beenden` button in the moderator
view or from the system tray menu.

## Build a Windows executable

The cross-platform builder detects the operating system automatically:

```powershell
py -3 -m pip install -r requirements.txt pyinstaller
py -3 build.py
```

The executable is created at `dist\WeddingMemory.exe`. The build script also
copies the local `images` folder to `dist\images`, because the images remain
external to the executable. This allows the executable to start immediately
after a build while keeping media out of the bundled binary.

## Images outside the repository and executable

Personal images are not versioned by Git and are not embedded in the
executable. The builder copies the current local `images` folder next to the
executable. You can also create or replace that folder manually:

```text
dist\
  WeddingMemory.exe
  images\
    memory1\
      001_a.jpg
      001_b.jpg
    memory2\
      ...
```

Alternatively, any local image folder can be selected with the
`WEDDING_MEMORY_IMAGES` environment variable:

```powershell
$env:WEDDING_MEMORY_IMAGES = "D:\WeddingMemoryBilder"
.\dist\WeddingMemory.exe
```

The repository contains only neutral demo SVGs under `images/memory1`, so the
application can be started and tested directly after cloning. Personal photos
should be stored in an external folder. Supported formats are JPG, JPEG, PNG,
SVG, and WEBP.

> **Privacy:** Before committing, make sure that no personal photos, videos,
> audio files, names, addresses, or other private descriptions have been
> placed under `images/`. The `.gitignore` file prevents the usual private
> media formats from being tracked.

Every subfolder named `memory1`, `memory2`, and so on is automatically
recognized as a memory. Image files are loaded automatically at each start.
The recommended naming scheme is:

```text
001_a.jpg
001_b.jpg
002_a.jpg
002_b.jpg
```

The automatically discovered memories are sorted alphabetically by default.
Set `RANDOMIZE_ALL_MEMORIES = True` in `config.py` to randomize their order at
the start of every game. All discovered memories are shown as selectable
buttons in the moderator view. The `Play memories randomly` setting can also
be enabled directly on the moderator page.

After the last memory, the current scores are displayed. If multiple teams
are tied, the moderator can start a tiebreaker using `Start tiebreaker`.
Only the tied teams participate, and random pairs from a randomly selected
memory are loaded. If the teams are tied again, another tiebreaker can be
started.

Before a tiebreaker starts, the current scores remain visible as the winner
display. The moderator starts it with `Start tiebreaker`. During the regular
game, `Skip memory` can be used at any time to move to the next memory.

Regular points are collected across all regular memories. A tiebreaker counts
only its own tiebreaker points; regular points determine only which teams
qualify for the tiebreaker.

A custom card back can be placed as `card-back.svg` or `card-back.png` in the
external `images` folder and selected through `CARD_BACK_IMAGE` in `config.py`.
A browser icon is already included at `static/favicon.svg`.

## Image descriptions

Moderators can see a description when revealing an image and in the enlarged
view. Add a UTF-8 CSV named `descriptions.csv` to each memory:

```csv
filename,description
001_a.jpg,"A shared moment."
001_b.jpg,"The second perspective of this moment."
```

Descriptions are matched by the complete filename, so the two images in a
pair can have different descriptions. Public projects should contain only
neutral or self-published descriptions.

## Publishing on GitHub

Before publishing:

1. Check `git status --short` and `git ls-files` for personal files.
2. Run `git grep -n -i -E "name|address|phone|private|password|token"` and
   evaluate the matches carefully.
3. Use `git log --all --stat` to verify that no private media remains in the
   published history.
4. Install the dependencies and start the application with the demo graphics.

The former local history containing private media was removed from this
publication state. If this project has already been pushed to a remote, the
cleaned state must subsequently be published using an agreed force-push.
Other clones must then be freshly cloned or migrated to the new history.

## Settings and zoom

The `Settings` menu in the moderator view can be used to change the grid size,
number of teams, round duration, and delay after an incorrect attempt. The
grid must contain an even number of cards so that complete pairs can be
formed. In an enlarged view, the image fills the screen; use the mouse wheel
to zoom in or out and drag with the mouse button pressed to pan. The zoomed
card, zoom factor, and image position are synchronized between the moderator
and display views. If the image is zoomed during an incorrect attempt, the
timer pauses until the cards are automatically covered; both views then show
only the remaining `Still open` display.

## Game rules

The complete rules view is identical in the moderator and display views:

 1. Each table plays as a team.
 2. The game starts paused; the first selection or opened card starts it.
 3. Each table has a configurable time limit.
 4. A matching pair earns one point; the next table plays afterward.
 5. After an incorrect attempt, both cards remain open for the configured
    delay. They are then closed and the next table plays.
 6. While an incorrect pair is zoomed, the delay is paused. The remaining
    time is shown in both views.
 7. When a table's time limit expires, open cards are closed, the next table
    becomes active, and its timer is reset.
 8. Points are collected across all regular memories.
 9. After the last memory, all teams are shown with their scores and rankings.
    Equal scores share a rank; the ranking follows competition ranking
    (1, 1, 3).
10. In a tie, the moderator starts a tiebreaker with only the tied teams. If
    they tie again, another tiebreaker can be started.
11. The team or teams with the highest score in the completed round win.

The rules are shown as an overlay in both views and synchronized through the
shared server state.

## Build a Debian/Linux executable

Python and the build tools are required on Debian:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

Then, in the project directory:

```bash
python3 -m pip install -r requirements.txt
chmod +x build.sh
./build.sh
```

Alternatively, after setting up a Python environment:

```bash
python3 -m pip install -r requirements.txt pyinstaller
python3 build.py
```

The Linux binary is created at `dist/WeddingMemory`. The build script copies
the images next to it:

```text
dist/
├── WeddingMemory
└── images/
    ├── memory1/
    └── memory2/
```

Start it with:

```bash
./dist/WeddingMemory
```

The views can then be opened in a browser:

- Moderator: `http://127.0.0.1:5000/moderator`
- Display: `http://127.0.0.1:5000/display`

PyInstaller creates platform-specific files. The Windows executable must be
built on Windows and the Linux binary on Debian; a Windows build cannot be
used directly as a Linux executable.

`build.py` is the shared build step for both systems. It automatically uses
the correct separator for `--add-data` and creates the native file for the
current operating system. The build therefore has to be run once on Windows
and once on Debian to create both files.
