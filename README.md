# Zack — Personal AI Voice Assistant

A JARVIS-style voice assistant for Windows with conversation memory, 
proactive check-ins, trading tools, gaming automation, and a live HUD.

## Features
- Wake word "Zack" or double-clap to activate
- Real conversational AI, not just commands
- System control: volume, brightness, shutdown, screenshots
- Task manager, Pomodoro timer, class schedule
- Trade journal for forex/trading
- Spotify control
- Game mode auto-optimization
- Screen recording via Windows Game Bar
- Global news summaries
- Code snippet library and error explainer

## Requirements
- Windows 10 or 11
- Python 3.10 or higher
- A working microphone

## Installation

### 1. Install Python
Download from https://www.python.org/downloads/  
During install, check "Add Python to PATH".

### 2. Download this project
Click the green "Code" button above, click "Download ZIP", extract it 
anywhere on your PC (e.g. Desktop).

### 3. Open a terminal in the folder
Open the extracted folder, click the address bar, type `cmd`, press Enter.

### 4. Install dependencies
pip install -r requirements.txt
If `pyaudio` fails:
pip install pipwin

pipwin install pyaudio

### 5. Set up your config
Copy `zack_config.example.json` and rename the copy to `zack_config.json`.
Open it and fill in your own values (see Configuration section below).

### 6. Set your API keys
Create a file named `.env` in the same folder with:
NVIDIA_API_KEY=your_key_here

MEDIASTACK_KEY=your_key_here
Get a free NVIDIA key at https://build.nvidia.com  
Get a free Mediastack key at https://mediastack.com

### 7. Run it
python zack.py

## Configuration

Open `zack_config.json` and customize:
- `weather_city`: your city name
- `tasks_file`: where your to-do list saves
- `spotify_client_id` / `spotify_client_secret`: from https://developer.spotify.com/dashboard
- `game_triggers`: executable names of games you want auto-optimization for

## Usage

Say "Zack" then your command. Examples:
- "Zack, what's the weather"
- "Zack, add task finish homework"
- "Zack, start pomodoro"
- "Zack, what can you do" (full feature list)

## Troubleshooting

**Zack doesn't wake up when I say his name**  
Lower mic sensitivity or recalibrate. See the Issues tab for common fixes.

**No sound from Zack**  
Check Windows Sound settings, Communications tab, disable "Reduce volume of other apps".

**Spotify gives an error**  
Delete the `.cache` file in this folder and try again.

## License
MIT — free to use, modify, and share.
