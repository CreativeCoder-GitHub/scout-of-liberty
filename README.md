# Scout of Liberty
<img src="https://raw.githubusercontent.com/shaurya-sharma-dev/scout-of-liberty/refs/heads/main/demo-img.png" width="45%" />
Scout of Liberty is a 2D retro-style platformer game made using Python. It is set in the 1770s during the American Revolution. The player is a fictional scout for the Sons of Liberty. The desktop version of Scout of Liberty was made for Windows and may not work on other operating systems. However, there is a web version you can play right now at https://shaurya-sharma-dev.github.io/scout-of-liberty/ or host locally on any device with Python. The web version also has integrated mobile support.  

All disclosures for 3rd-party libraries and assets used in this game are located in the DISCLOSURE.md file.

All `*.py` files and the `pyscript-config.json` file located in this repository are licensed under the MIT license found in `LICENSE.md` in the repository root.

## Dependencies
The Python package dependencies are stated in the `requirements.txt` file. pygame-ce also requires the Simple DirectMedia Layer (SDL) Library (which itself requires freetype to render fonts).

<b>SDL and FreeType Dependencies</b>
- SDL >= 2.0.14
- SDL_mixer >= 2.0.4
- SDL_image >= 2.0.4
- SDL_ttf >= 2.0.15
- FreeType >= 2.9.1

## Quickstart for Desktop Version
1. Download Python 3.12, if you don't already have it. (Make sure it is the correct version!)
2. Open a terminal and navigate to the folder with all of the project code files.
3. Run `pip install --no-deps -r requirements.txt`. On some platforms, you may have to run `pip3 install --no-deps -r requirements.txt` instead.
    - If the command fails on Linux and triggers an `externally-managed-environment` error, you should create and activate a virtual environment before re-running the command.
    - To create and activate a virtual environment, run the following:<br>
    `python3 -m venv venv      # Create a virtual environment named 'venv'`<br>
    `source venv/bin/activate  # Activate the virtual environment named  'venv'`
4. Run `python main.py` or `python3 main.py` (depends on platform) in order to run the game.

## Quickstart for Web Version
1. Download Python 3.12, if you don't already have it. (Make sure it is the correct version!)
2. Open a terminal and navigate to the folder with all of the project code files.
3. Run `python -m http.server` or `python3 -m http.server` (depends on platform) in order to host the web version locally (installing the dependencies is not needed since PyScript does that in the browser). Make sure that port 8000 is open before running the command.
4. Open localhost:8000 to play the game!

## Controls
- WASD/Arrow Keys/Joystick - Movement
- Space Bar/Joystick Up - Jump
- Left Click/Tap Screen - Attack

## References
The following references were used for the historical information in the game:
- https://www.history.com/articles/boston-tea-party
- https://www.ebsco.com/research-starters/history/paul-reveres-midnight-ride
- https://www.battlefields.org/learn/articles/who-were-sons-liberty
- https://www.americanrevolution.org/sons-of-liberty/
- https://www.battlefields.org/learn/revolutionary-war/battles/yorktown
