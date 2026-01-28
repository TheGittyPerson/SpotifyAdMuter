"""
Spotify Ad Muter (SAM) is a module meant to automatically detect Spotify
advertisements on macOS and mute Spotify for the entire duration of the ad
when installed, preventing the user from hearing ads while the program is
running.

Sam works by:
- Monitoring Spotify’s playback state through AppleScript.
- Detecting when an advertisement begins (via track metadata).
- Instantly lowering Spotify’s volume to 0, even if the user tries to raise it.
- Playing an optional alert tone when an ad is detected.
- Restoring the user's previous volume as soon as music resumes.
- Automatically generating a user-configurable shortcut (.command) script.
- Saving preferences to a JSON settings file. 

Additional features:
- Waits for Spotify to launch before starting detection.
- Handles unexpected Spotify crashes or exits gracefully.
- Provides a live log output with timestamps for debugging.
- Creates a shortcut .COMMAND executable file for ease of use .

This script is intended to run continuously in a terminal and guarantees that
Spotify advertisements remain fully muted at all times.
"""

import subprocess
import sys
import math
import wave
import struct
import os
import json
import traceback
from pathlib import Path
from datetime import datetime
from time import sleep


class SpotifyAdMuter:
    """Spotify Ad Muter (SAM).

    A macOS-only utility that, when SpotifyAdMuter.run() is called,
    continuously monitors Spotify playback and automatically mutes
    Spotify advertisements while preserving the user's original volume
    settings.

    Attributes:
        VERSION (str):
            Current version string of the application.

        JSON_SETTINGS_NAME (str):
            Filename of the JSON settings file.

        JSON_SETTINGS_PATH (pathlib.Path):
            Absolute path to the JSON settings file.

        SHORTCUT_SCRIPT_NAME (str):
            Filename of the generated shortcut executable shell script.

        settings (dict):
            Parsed configuration loaded from the JSON settings file.

        create_shortcut_is_on (bool):
            Whether automatic shortcut script creation is enabled.

        shortcut_script_path (pathlib.Path):
            Filesystem path where the `.command` shortcut script is
            created.

        ad_alert_sound_is_on (bool):
            Whether an alert tone is played when an advertisement is
            detected.

        ad_alert_volume (float):
            Volume multiplier used when generating the ad alert tone.

        custom_ad_keywords (list[str]):
            User-defined keywords used to identify advertisements.

        poll_interval (float):
            Time delay between polls, in seconds.
    """

    VERSION = "2.1.0"
    JSON_SETTINGS_NAME = "settings.json"
    JSON_SETTINGS_PATH = Path(__file__).resolve().parent / JSON_SETTINGS_NAME
    SHORTCUT_SCRIPT_NAME = "SAM.command"

    def __init__(self):
        """Initialize SpotifyAdMuter class attributes."""

        self.settings = self._get_json_settings()

        self.create_shortcut_is_on = (
            self.settings.get("create_shortcut_script_file", True)
        )
        self.shortcut_script_path = (
            Path(
                self.settings.get(
                    "shortcut_script_file_dir",
                    Path(os.path.expanduser("~/Desktop"))
                )
            )
            / self.SHORTCUT_SCRIPT_NAME
        )
        self.ad_alert_sound_is_on = self.settings.get("ad_alert_sound", True)
        self.ad_alert_volume = self.settings.get("ad_alert_volume", 0.3)
        self.custom_ad_keywords = self.settings.get("custom_ad_keywords", [])
        self.poll_interval = self.settings.get("poll_interval", 0.3)
        
        self.IDLE_RAMP_RATE = 0.005
        self.MAX_POLL_MULTIPLIER = 30

    def run(self):
        """Run Spotify Ad Muter (SAM)."""
        try:
            if not self._is_macos():
                self._log("\nSorry :( Sam only works on macOS!")
                sys.exit(0)

            print(
                "\n\033[1m\033[32m"
                + "\n🎧 Spotify Ad Muter (SAM) started 🎶🎵"
                + "\033[0m"
            )
            print(f"[Version {self.VERSION}]")
            print(
                "\033[1m"
                + "\n*❖* ——————————————— ACTIVITY LOG ——————————————— *❖*"
                + "\033[0m"
            )

            self._check_shortcut_script()

            self._log("Sam is waiting for Spotify...")

            ad_was_current = False

            # Wait for Spotify to open
            precount = 0
            while not self._spotify_is_running():
                sleep(self._get_delay(precount, self.poll_interval))
                precount += 1

            # Read initial state
            previously_playing = self._spotify_is_playing()
            previous_volume = self._get_spotify_volume()
            ad_is_current_track = self._ad_is_track()

            # Start of program — print correct initial message
            if not previously_playing:
                self._log("No music playing. Sam is waiting for music to play...")
            else:
                self._log(
                    "Music started! Sam will mute Spotify when ads are playing."
                )

            # SPECIAL: If program starts on an ad AND it is playing
            # → treat this as “ad started”
            if ad_is_current_track and previously_playing:
                self._log(f"🔇 Ad detected — muting Spotify.")
                # Save current volume (even if 0)
                previous_volume = self._get_spotify_volume()

                # Mute Spotify
                self._set_spotify_volume(0)

                # Play tone
                if self.ad_alert_sound_is_on:
                    self._play_tone()

                ad_was_current = True
            
            count = 0
            while True:
                sleep(self._get_delay(count, self.poll_interval))
                count += 1

                if not self._spotify_is_running():
                    sleep(1)
                    # Double-check to avoid race-condition during quit
                    if not self._spotify_is_running():
                        self._log("\n🚪 Spotify closed. Sam is going to sleep...")
                        break

                playing = self._spotify_is_playing()
                ad_is_current = self._ad_is_track()

                # ────────────────────────────────────────────────
                # 1. Handle play/pause messages
                #    (NOT ad-related; this always fires correctly)
                # ────────────────────────────────────────────────
                if playing != previously_playing:
                    if not playing:
                        self._log(
                            "No music playing. Sam is waiting for music to play...")
                    else:
                        self._log("Music started! Sam will mute Spotify when "
                                  "ads are playing")
                        count = 0
                    previously_playing = playing

                # If Spotify is NOT playing, do NOT apply ad logic yet
                if not playing:
                    continue

                # ────────────────────────────────────────────────
                # 2. AD STARTS
                # ────────────────────────────────────────────────
                try:
                    if ad_is_current:

                        # Handle only-once-on-ad-start events
                        if not ad_was_current:
                            self._log("🔇 Ad detected — muting Spotify.")
                            # Save the volume at the moment ad began
                            previous_volume = self._get_spotify_volume()

                            self._set_spotify_volume(0)

                            if self.ad_alert_sound_is_on:
                                self._play_tone()

                            ad_was_current = True

                            # Always force mute during ads
                            if self._get_spotify_volume() != 0:
                                self._set_spotify_volume(0)
                                self._play_tone()

                    # ────────────────────────────────────────────────
                    # 3. AD ENDS
                    # ────────────────────────────────────────────────
                    if not ad_is_current and ad_was_current:
                        self._log("🔊 Ad ended and music resumed "
                                  f"— restoring volume to {previous_volume}")

                        # Restore the volume user had before ad started
                        self._set_spotify_volume(previous_volume)

                        ad_was_current = False
                except RuntimeError as e:
                    self._err(
                        "Something went wrong while Sam was getting "
                        "Spotify music data or volume level.",
                        f"Error message: {e}"
                    )
                    sys.exit(1)

        except KeyboardInterrupt:
            print("\n*❖* —————————————————————————————— *❖*")
            self._log("User ended the program. Sam is going to sleep...")
            sys.exit(0)
        except Exception as e:
            self._err(
                "Something went wrong...",
                f"Error summary: {e}",
                traceback.format_exc()
            )
            sys.exit(1)
        finally:
            print("\nProgram finished.")

    # ##########################################################################
    # //////////////////////////// INTERNAL METHODS ////////////////////////////
    # ##########################################################################

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ---------------- HELPER (STATIC) METHODS ----------------
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @staticmethod
    def _run_as(script) -> str:
        """Run AppleScript and return stdout."""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    @staticmethod
    def _log(message: str, newline: bool = True) -> None:
        """Print log message with formatted timestamp."""
        if newline:
            print(f"\n{message} "
                  f"\033[37m[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\033[0m")
        else:
            print(f"{message} "
                  f"\033[37m["
                  + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                  + "]\033[0m")
    
    def _get_delay(self, count: int, base: float) -> float:
        """
        Gradually increase poll delay during inactivity,
        capped to avoid excessive latency.
        """
        multiplier = min(
            1 + count * self.IDLE_RAMP_RATE, self.MAX_POLL_MULTIPLIER
        )
        return base * multiplier
    
    @staticmethod
    def _err(
            message: str,
            *desc: str,
            restart: bool = True
    ) -> None:
        """Print formatted error message with timestamp."""
        print("\n*!* —————————————————————————————— *!*")
        print(
            f"❌ \033[1m\033[31m" + "ERROR!" + "\033[0m: "
            + message
        )

        print()
        for d in desc:
            print(d)

        print()
        if restart:
            print("Try restarting the program.")
        print("If the error persists, consider reporting this issue.")
        print("*!* —————————————————————————————— *!*\n")

    @staticmethod
    def _is_macos() -> bool:
        """Return whether running on macOS."""
        return sys.platform == "darwin"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ---------------- SETTINGS/SHORTCUT INITIALIZATION METHODS ----------------
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_json_settings(self) -> dict:
        """Fetch 'settings.json' contents and return parsed config.

        Create a default 'settings.json' file if it does not exist and
        return fetched configuration.
        """
        try:
            with open(self.JSON_SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            shortcut_dir = os.path.expanduser("~/Desktop")
            json_dict = {
                "create_shortcut_script_file": True,
                "shortcut_script_file_dir": shortcut_dir,
                "ad_alert_sound": True,
                "ad_alert_volume": 0.3,
                "custom_ad_keywords": [],
                "poll_interval": 0.3,
            }
            with open(self.JSON_SETTINGS_PATH, 'w') as f:
                json.dump(json_dict, f, indent=4)
            return json_dict
        except Exception as e:
            self._err(
                "Something went wrong while creating 'settings.json'...",
                f"Error summary: {e}",
                traceback.format_exc()
            )
            return {
                "create_shortcut_script_file": True,
                "shortcut_script_file_dir": os.path.expanduser("~/Desktop"),
                "ad_alert_sound": True,
                "ad_alert_volume": 0.3,
                "custom_ad_keywords": [],
                "poll_interval": 0.3,
            }

    def _check_shortcut_script(self) -> None:
        """Search device's Desktop folder for shortcut script file.

        Search the device's Desktop folder for 'SAM.command' shortcut
        script and create it if it doesn't exist.
        """
        if self.shortcut_script_path.exists() or not self.create_shortcut_is_on:
            return
        else:
            try:
                self._create_shortcut_script()
            except FileNotFoundError:
                return

            script_dir = self.shortcut_script_path.parent
            self._log("\033[1mSam made an executable shortcut automatically "
                      f"created in {script_dir}. \033[0mYou can now double-click "
                      "'SAM.command' to run the program.")
            print("\n*❖* —————————————————————————————— *❖*")

    def _create_shortcut_script(self) -> None:
        """Create shortcut executable script in device Desktop folder."""
        this_file_path = os.path.abspath(__file__)

        script_contents = f'#!/bin/bash\nexec {sys.executable} "{this_file_path}"'

        try:
            with open(self.shortcut_script_path, "w") as f:
                f.write(script_contents)
        except FileNotFoundError:
            self._err(
                "Unable to create shortcut script file...",
                "Please ensure the directory specified in 'settings.json' is valid.",
                restart=False
            )
            raise FileNotFoundError

        try:
            os.chmod(self.shortcut_script_path, 0o755)
        except Exception as e:
            self._err(
                "Unable to make shortcut script file executable...",
                f"Error summary: {e}",
                traceback.format_exc(),
            )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ---------------- SPOTIFY STATE AND TRACK FETCH METHODS ----------------
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _spotify_is_running(self) -> bool:
        """Return whether Spotify is running."""
        script = ('tell application "System Events" '
                  'to (name of processes) contains "Spotify"')
        return self._run_as(script) == "true"

    def _spotify_is_playing(self) -> bool:
        """Return whether Spotify is playing."""
        script = '''
        tell application "Spotify"
            if player state is playing then
                return true
            else
                return false
            end if
        end tell
        '''
        return self._run_as(script) == "true"

    def _get_current_track_info(self) -> tuple[str, str, str, int]:
        """Return the currently playing Spotify track info.

        Returns the current playing song name, artist, album, and duration.
        """

        script = r'''
            tell application "Spotify"
                try
                    set trackName to name of current track
                    set trackArtist to artist of current track
                    set trackAlbum to album of current track
                    set trackDur to duration of current track

                    set jsonText to "{"
                    set jsonText to jsonText & "\"name\":\"" & trackName & "\","
                    set jsonText to jsonText & "\"artist\":\"" & trackArtist & "\","
                    set jsonText to jsonText & "\"album\":\"" & trackAlbum & "\","
                    set jsonText to jsonText & "\"duration\":" & trackDur
                    set jsonText to jsonText & "}"

                    return jsonText
                on error
                    return "{\"error\":true}"
                end try
            end tell
            '''

        out = self._run_as(script)

        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            return "ERR", "ERR", "ERR", 0

        if data.get("error"):
            return "ERR", "ERR", "ERR", 0

        return (
            data["name"],
            data["artist"],
            data["album"],
            int(data["duration"]),
        )

    def _ad_is_track(self) -> bool:
        """Return whether an advertisement is playing on Spotify.

        Determine whether the currently playing track is an ad or not
        by checking if the returned name and artist strings are empty
        and the duration is less than 45 seconds. Or, if the track title
        contains any word from the defined list of ad keywords.
        """
        name, artist, album, duration = self._get_current_track_info()

        # This sometimes occurs when the user manually selects another track
        # or playlist on Spotify and skips the current track, causing Spotify
        # to momentarily return an error when trying to get track info, so
        # this error can be ignored.
        if (name, artist, album, duration) == ('ERR', 'ERR', 'ERR', 0):
            return False

        if album == "" and artist == "" and duration < 45000:
            return True

        custom_keywords = [k.lower() for k in self.custom_ad_keywords]

        name_lower = name.lower()
        ad_keywords = ["advertisement", "sponsored"] + custom_keywords

        return any(keyword in name_lower for keyword in ad_keywords)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ---------------- VOLUME CONTROL METHODS ----------------
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_spotify_volume(self) -> int:
        """Fetch Spotify volume and return integer out of 100.

        On an error where the volume cannot be fetched, an error
        message is printed and the volume is assumed to be 50.
        """
        script = 'tell application "Spotify" to return sound volume'
        try:
            return int(self._run_as(script))
        except RuntimeError as e:
            self._err(
                "Something went wrong while fetching Spotify volume...",
                f"Error message: {e}",
                "\nAssuming volume is 50.",
                restart=False
            )
            return 50

    def _set_spotify_volume(self, x: int) -> None:
        """Set Spotify's volume to x."""
        script = f'tell application "Spotify" to set sound volume to {int(x)}'
        self._run_as(script)

    def _play_tone(self, freq=180, duration=0.3) -> None:
        """Play, by default, a 180 Hz sine wave for 0.3 seconds.

        Create a .WAV file and delete immediately after playing.
        """
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        file_path = Path("tone_tmp.wav")
        volume = self.ad_alert_volume

        try:
            with wave.open(str(file_path), "w") as f:
                f.setparams((1, 2, sample_rate, num_samples, "NONE",
                             "not compressed"))
                for i in range(num_samples):
                    sample = volume * math.sin(2 * math.pi * freq
                                               * (i / sample_rate))
                    f.writeframes(struct.pack('<h', int(sample * 32767)))
        except struct.error as e:
            self._err(
                "Something went wrong while playing ad alert tone...",
                f"Error message: {e}",
                "\nPlease ensure the volume specified in 'settings.json' is valid",
                restart=False,
            )
            return

        subprocess.run(["afplay", str(file_path)])

        os.remove(str(file_path))


if __name__ == "__main__":
    sam = SpotifyAdMuter()
    sam.run()
