For **Spotify Ad Muter (SAM)** <br>
Version: **2.1.0** <br>
Operating System: **macOS** <br>

Last updated: **December 14, 2025**

---

# User Guide

This is a step-by-step guide on how to use Spotify Ad Muter, Sam for short, with some information about the program.

**Please keep this document for future reference.**

---

## System Requirements

Make sure you have:

- **macOS 11.0 or later**
- **Python 3.12+** recommended
- **Spotify Desktop App** (not the web app)

## How It Works (Simplified)

Sam uses AppleScript and Python to:

- Check the currently playing track in Spotify
- Detect when the track is an advertisement
- Mute Spotify using system controls
- Restore your old volume when music resumes

No files outside the app folder are modified.
Sam does not interact with your Spotify account or the internet.

---

## Pre-installation

1. **Download the latest python interpreter** at [python.org](https://www.python.org/downloads/). <br>
   Follow the installer instructions
2. **Make sure you have the Spotify** macOS Desktop app installed on your device

## After Installation

1. After unzipping the .ZIP file into a folder, you may delete the .ZIP file
2. _Optional: Name the new folder `SpotifyAdMuter` (Or even `Sam`)_
3. Inside the folder, you should see two files: <br>
    - `spotify_ad_muter.py` ⚠️ **Do not change this filename**
    - `USER_GUIDE.pdf` (this document)

### First Run

1. **Open the file `spotify_ad_muter.py` using 'Python Launcher'**
    - Double-clicking should automatically launch it
    - If not, right-click → Open With → Python Launcher
2. On first run, macOS will ask for permissions:

    - **Desktop folder access** (needed to create a shortcut file)
    - **Access to control System Events** (to know if Spotify is running)<br>
    - **Access to control Spotify** (to identify advertisements and read and control Spotify's volume)

   **Click 'Allow' for all requests**

After permissions are granted, the program begins, and **a Terminal window will open.**

Sam will automatically create **two files**:

#### ☞ `settings.json` in **the program's folder**

This file contains your configuration options, such as whether to create a shortcut file and where to place it.

#### ☞ `SAM.command` in your **Desktop folder**

This is an optional shortcut you can **double-click to run Sam** in the future.
It will be automatically generated **only if**:

- It is missing in the location specified in `settings.json` (Desktop folder, by default)
- Shortcut creation is enabled in `settings.json`
- The path specified for the shortcut location is valid

(More on these in the [Settings/Customization](#settingscustomization) section)

---

## Use

### Start/Run

You may **start Sam using any of these methods**:

1. **Double-click `SAM.command` (recommended)**
2. Open `spotify_ad_muter.py` with Python Launcher
3. Open the file in IDLE and run it **(not recommended)**:
    - File → Open... → select `spotify_ad_muter.py` (or press ⌘ + O)
    - Run → Run Module

A terminal window will appear showing a live activity log.

Spotify may be opened **before or after** starting Sam.

When an ad plays:

- **Spotify will be muted**
- (Optional) A short tone will play
- Volume will be restored when music resumes

### Stop/Terminate

Any of the following will stop the program:

- **Close the terminal window/quit terminal** and **press 'Terminate'**
- **Quit Spotify** (not just closing the Spotify window)

## Settings/Customization

Settings are located inside `settings.json`. <br>
You may edit this file using TextEdit or any text editor.

### Toggle Shortcut File Creation

1. **Open `settings.json`**
2. By default, the value next to `"create_shortcut_script_file"` is set to `true`: <br>

   ```json
   {
       "create_shortcut_script_file": true
   }
   ```

   To disable shortcut file creation, **change the value `true` to `false`**:

   ```json
   {
       "create_shortcut_script_file": false
   }
   ```

3. After turning it off, you can safely delete `SAM.command`
4. **Save the file (⌘ + S) before closing** <br>

To re-enable, change `false` back to `true`.

### Change shortcut file location

1. **Open `settings.json`**
2. By default, the value next to `"shortcut_script_file_dir"` is set to your Desktop folder: <br>
   _Example:_

   ```json
   {
       "shortcut_script_file_dir": "/Users/yourName/Desktop"
   }
   ```

   To change the location (folder) of the shortcut file, **change the value next to `"shortcut_script_file_dir"`**.
   <br><br>
   For example, if you want to change the location to `Users ▸ yourName ▸ Desktop ▸ Shortcuts`:

   ```json
   {
       "shortcut_script_file_dir": "/Users/yourName/Desktop/Shortcuts"
   }
   ```

3. **Save the file (⌘ + S) before closing**
4. Re-run the program to generate a new shortcut.
5. You may now delete the shortcut file `SAM.command` from the old location

### Turn ad alert sound on/off

1. **Open `settings.json`**
2. By default, the value next to `"ad_alert_sound"` is set to `true`

   ```json
   {
       "ad_alert_sound": true
   }
   ```

   This causes the program to play a **low half-second tone** whenever an ad starts.
   <br><br>
   To disable the ad alert sound, **change the value `true` to `false`**:

   ```json
   {
       "ad_alert_sound": false
   }
   ```

3. **Save the file (⌘ + S) before closing**
4. Rerun the program.

### Change ad alert sound volume

1. **Open `settings.json`**
2. By default, the value next to `"ad_alert_volume"` is set to `0.3`

   ```json
   {
       "ad_alert_volume": 0.3
   }
   ```
   
   To change the volume, **change the value to a number between 0 and 1**:

   ```json
   {
       "ad_alert_sound": false
   }
   ```
   ⚠️**NOTE: AVOID SETTING THE ALERT VOLUME ABOVE 0.7**, especially if you use headphones.

3. **Save the file (⌘ + S) before closing**
4. Rerun the program.

### Add an ad keyword

Ad keywords refer to keywords Sam uses to identify if a track is an ad or not.
Sam checks if the currently playing track's name contains at least one of the keywords.

To add your own keywords:

1. **Open `settings.json`**
2. By default:

   ```json
   {
       "custom_ad_keywords": []
   }
   ```

   To add keywords, type the word in the square brackets in quotes, separated by commas:

   ```json
   {
       "custom_ad_keywords": ["example", "another example"]
   }
   ```

3. **Save the file (⌘ + S) before closing**
4. Rerun the program.

### Change poll interval

The poll interval is the time, **in seconds**, between requests to Spotify when Sam collects track information, 
volume level, etc.

You might need to increase the poll interval if Spotify is not quitting properly, or if problems with Spotify are 
occurring while Sam is running. You might need to decrease the poll interval if Sam is delayed and mutes/unmutes 
Spotify too slowly.

To change the poll interval:

1. **Open `settings.json`**
2. By default:

   ```json
   {
       "poll interval": 0.3
   }
   ```

   **Avoid setting the poll interval below 0.2 seconds**, as this may cause instability with Spotify, particularly when 
   quitting the application.
   Increasing the poll interval above 0.5 seconds may reduce ad detection responsiveness and introduce additional 
   latency, though this is acceptable if slower detection is not a concern.

   ```json
   {
       "poll interval": 0.5
   }
   ```

3. **Save the file (⌘ + S) before closing**
4. Rerun the program.

---

## Uninstall

To fully remove Sam from your device:

1. **Delete the folder** containing `spotify_ad_muter.py`
2. Delete the `SAM.command` shortcut file (if present)
3. Optional: remove Automation permissions
    - System Settings → Privacy & Security → Automation
    - Disable Python / Python Launcher / Terminal

---

## Troubleshoot

### Spotify does not mute ads

- Make sure Spotify is open in the background
- Ensure macOS granted Automation permissions:
- System Settings → Privacy & Security → Automation
    - Make sure Python / Python Launcher is allowed to control Spotify

### Spotify cannot quit properly while the program is running

- This can sometimes happen if Sam tries to retrieve information from Spotify while it is trying to quit.
- Simply terminate the program before quitting Spotify
- If this happens too often, follow the steps in "[Change poll interval](#change-poll-interval)" and **increase 
  the poll interval** (a value of around 0.5 seconds is recommended)


### The shortcut file doesn't appear

- In `settings.json`, make sure `"create_shortcut_script_file": true`
- Make sure the folder path set in `settings.json` next to `"shortcut_script_file_dir"` is valid
- Ensure Sam has permission to access the specified location
- Try running `spotify_ad_muter.py` manually once

### `SAM.command` doesn't work/returns an error

This can happen if:

- You've changed the location of `spotify_ad_muter.py`
- The shortcut file is corrupted/has been changed
- The shortcut file does not have permission to access the location `spotify_ad_muter.py` is in

To fix this:

- Delete the shortcut file and regenerate the shortcut file by rerunning Sam
- Make sure Sam has permission to access the location

### Changes in `settings.json` do not take effect

- Make sure that:
  - Your changes to `settings.json` have been saved (⌘ + S)
  - `settings.json` is located in the same directory as `spotify_ad_muter.py`
  - The program was restarted after making changes
  - `settings.json` is properly formatted:
    - Curly braces (`{...}`) are correctly opened and closed
    - Setting names are enclosed in double quotes (`"..."`)
    - Commas are placed at the end of each line except the last
    - Refer to the [Settings/Cutomization](#settingscustomization) section to ensure all entries are formatted correctly

### Terminal window closes instantly

- Try running Sam from Terminal to see the error message.
- [Contact me](#bug-reportshelp) for further assistance

---

## Bug Reports/Help

If you encounter any bugs, errors, or strange behavior using the program, or if you spot mistakes in this guide: <br>
**Message me anytime** and I will help.

You can also ask questions, request features, or suggest refinements to help improve Sam!
