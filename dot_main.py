from click import command
import speech_recognition as sr
import shutil
import os
import webbrowser
import subprocess
import datetime
import psutil
from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import quote_plus
import pyjokes
from sqlalchemy import text
import wikipedia
import pywhatkit
import requests
import pyttsx3
from gtts import gTTS
import tempfile
import random
import logging
import pyautogui
import re
import pywhatkit as kit
import time
import threading



WAKE_WORD_RESPONSES = ["hey dot", "hello dot", "you there dot", "dot", "hey", "hello"]
EXIT_RESPONSES = [ "exit dot", "exit", "quit dot", "quit", "bye", "bye bye",
                  "goodbye", "bye dot", "bye bye dot", "goodbye dot", "terminate", "terminate dot"]
NEWS_API_KEY = "5998fb29280642e5bb77357123c49bb4"
WEATHER_API_KEY = "71997cfa812d069c21911cfe80cebb67"
CLOSE_APP_KEYWORDS = ["close application", "terminate application"]


class VirtualAssistant:
    def __init__(self):
        self.sites = [
            ["youtube", "https://www.youtube.com"],
            ["instagram", "https://www.instagram.com"],
            ["google", "https://www.google.com"],
            ["wikipedia", "https://www.wikipedia.com"]
        ]
        self.active = True
        self.recognizer = sr.Recognizer()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.current_task = None
        self.task_data = {}
        self.jokes = pyjokes
        self.wikipedia = wikipedia
        self.pywhatkit = pywhatkit
        self.mode = "text"  # Default mode is text
        self.interrupt_flag = False  # Used for interrupting ongoing commands
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Set speech rate (speed)
        self.engine.setProperty('voice','com.apple.speech.synthesis.voice.samantha')  # Example for macOS, change accordingly
        # self.engine.setProperty('voice', female_voice_id)
        self.voice = self.get_female_voice()
        self.use_gtts = True  # Start by assuming GTTS will be used

    def get_female_voice(self):
        """Configure pyttsx3 to use a female voice."""
        voices = self.engine.getProperty('voices')
        # Check for a female voice
        for voice in voices:
            if 'female' in voice.name.lower() :
                self.engine.setProperty('voice',voice.id)
                return voice.id
        # Default to the first available voice if no female voice is found


    def normalize(self, text: str) -> str:
        text = text.lower().strip()

        replacements = {
            "please": "",
            "could you": "",
            "can you": "",
            "would you": "",
            "dot": "",
        }

        for k, v in replacements.items():
            text = text.replace(k, v)

        return text.strip()

    def check_internet(self) -> bool:
        """Check internet connectivity."""
        try:
            response = requests.get("http://www.google.com", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False

    def _speak_async(self, text: str):
        if self.use_gtts:
            try:
                tts = gTTS(text=text, lang='en-IN')
                with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_file:
                    tts.save(temp_file.name)
                    os.system(f"afplay {temp_file.name}")
            except Exception:
                self.use_gtts = False
                self._speak_async(text)
        else:
            try:
                self.engine.setProperty('voice', self.voice)
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                self.use_gtts = True
                self._speak_async(text)

    def say(self, text: str) -> None:
        # 1️⃣ Update GUI immediately
        if hasattr(self, "gui_callback") and callable(self.gui_callback):
            self.gui_callback(text)

        # 2️⃣ Print immediately
        print(f"Assistant: {text}")

        # 3️⃣ Speak in background (NON-BLOCKING)
        speech_thread = threading.Thread(
            target=self._speak_async,
            args=(text,),
            daemon=True
        )
        speech_thread.start()




    def display_text(self, text: str) -> None:
        """Print the text to console."""
        print(f"Assistant: {text}")

    def get_welcome_response(self) -> str:
        responses = [
            "Hello Boss! How can I assist you today?",
            "Hi there! What can I do for you?",
            "Hey boss! What can I help you with today?",
            "Hello boss! I'm here to help. What do you need?"
        ]
        return random.choice(responses)

    def get_exit_response(self) -> str:
        responses = [
            "Goodbye sir! Have a great day!",
            "Exiting now. Take care sir!",
            "See you later sir!",
            "Goodbye sir! Let me know if you need anything else."
        ]
        return random.choice(responses)

    # def listen_for_wake_word(self) -> None:
    #     with sr.Microphone() as source:
    #         self.recognizer.adjust_for_ambient_noise(source)
    #         self.display_text("Listening for wake word...")
    #         while self.active:
    #             try:
    #                 audio = self.recognizer.listen(source)
    #                 query = self.recognizer.recognize_google(audio, language="en-IN").lower()
    #                 if any(wake_word in query for wake_word in WAKE_WORD_RESPONSES):
    #                     self.say(self.get_welcome_response())
    #                     self.process_commands()
    #             except sr.UnknownValueError:
    #                 pass
    #             except sr.WaitTimeoutError:
    #                 pass
    #             except Exception as e:
    #                 self.say(f"An unexpected error occurred: {e}")

    def take_command(self, text_input: str = None, timeout: int = 10) -> str:
        if text_input:
            return text_input.lower()

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=timeout)
                query = self.recognizer.recognize_google(audio, language="en-IN").lower()
                return query
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print("Mic error:", e)
            return ""




    def process_commands(self) -> None:
        if not self.check_internet():
            self.use_gtts = False
        while self.active:
            if self.interrupt_flag:  # If interrupt signal is triggered, stop current command execution
                self.say("Command interrupted.")
                self.interrupt_flag = False
                continue

            if self.mode == "voice":
                command = input("Enter command: ").lower()
            else:
                command = self.take_command()

            if any(keyword in command for keyword in EXIT_RESPONSES):
                self.say(self.get_exit_response())
                self.active = True
                return

            if "switch to voice" in command:
                self.mode = "voice"
                self.say("Switching to voice input.")
                continue
            elif "switch to text" in command:
                self.mode = "text"
                self.say("Switching to text input.")
                continue
            elif "stop" in command:
                self.interrupt_flag = True
                self.say("Stopping current operation.")
                continue

            # Handle other commands
            self.execute_command(command)


    def open_application(self, app_name: str) -> None:
        try:
            result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
            if result.returncode == 0:
                self.say(f"Certainely boss Opening {app_name}...")
            else:
                self.say(f"Failed to open {app_name}. Error: {result.stderr.strip()}")
                print(result.stderr)  # Print detailed error information
        except FileNotFoundError:
            self.say(f"Application {app_name} not found.")
        except subprocess.CalledProcessError as e:
            self.say(f"Error occurred: {e}")
        except Exception as e:
            self.say(f"An unexpected error occurred: {e}")
            print(e)  # Print detailed error information

    def close_application(self, app_name: str) -> None:
        try:
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'], check=True)
            self.say(f"Closing {app_name}...")
        except FileNotFoundError:
            self.say(f"Application {app_name} not found.")
        except subprocess.CalledProcessError:
            self.say(f"Unable to close {app_name}.")
        except Exception as e:
            self.say(f"An unexpected error occurred while closing the application: {e}")
            print(e)  # Print detailed error information for debugging

    def open_website(self, site_name: str) -> None:
        site_name = site_name.strip().lower()

            # Directly open if it's a valid URL
        if site_name.startswith("www.") or site_name.startswith("http"):
            full_url = site_name if site_name.startswith("http") else f"https://{site_name}"
            self.say(f"Opening {full_url}...")
            webbrowser.open(full_url)
        else:
                # Map of common website names to URLs
            site_map = {
                "google": "https://www.google.com",
                "instagram": "https://www.instagram.com",
                "youtube": "https://www.youtube.com",
                    # Add more mappings as needed
                }

            if site_name in site_map:
                self.say(f"Opening {site_name}...")
                webbrowser.open(site_map[site_name])
            else:
                self.say(f"Unable to find website {site_name}.")

    def close_website(self, site_name: str) -> None:
        try:
            result = subprocess.run(
                ["osascript", "-e",
                    f'tell application "Google Chrome" to close (windows whose name contains "{site_name}")'],
                check=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.say(f"Closing {site_name}...")
            else:
                self.say(
                    f"Could not close {site_name}. It might not be open or the name might not match the window title.")
        except subprocess.CalledProcessError:
            self.say(f"Unable to close {site_name}. An error occurred while trying to close the window.")
        except Exception as e:
            self.say(f"An unexpected error occurred while closing the website: {e}")
            print(e)  # Print detailed error information for debugging

    def set_brightness(self, percentage: int) -> None:
        try:
            if 0 <= percentage <= 100:
                result = subprocess.run(["brightness", str(percentage / 100.0)], capture_output=True, text=True)
                if result.returncode == 0:
                    self.say(f"Brightness set to {percentage}%.")
                else:
                    self.say(f"Failed to set brightness. Error: {result.stderr.strip()}")
            else:
                self.say("Brightness percentage must be between 0 and 100.")
        except FileNotFoundError:
            self.say("Brightness command not found. Please ensure the brightness utility is installed.")
        except Exception as e:
            self.say(f"An unexpected error occurred while setting brightness: {e}")
            print(e)  # Print detailed error information

    def set_volume(self, level: str) -> None:
        try:
            volume_level = int(level)
            if 0 <= volume_level <= 100:
                self.say(f"Setting volume to {volume_level}%")
                os.system(f"osascript -e 'set volume output volume {volume_level}'")
            else:
                self.say("Please provide a volume level between 0 and 100.")
        except ValueError:
            self.say("An unexpected error occurred: Please provide a valid number for volume.")

    def search_youtube_channel(self, channel_name: str) -> None:
        query = quote_plus(channel_name)
        url = f"https://www.youtube.com/results?search_query={query}"
        self.say(f"Searching YouTube for {channel_name}...")
        webbrowser.open(url)

    def search_instagram_account(self, account_name: str) -> None:
        query = quote_plus(account_name)
        url = f"https://www.instagram.com/{query}/"
        self.say(f"Searching Instagram for {account_name}...")
        webbrowser.open(url)

    def get_battery_status(self) -> str:
        battery = psutil.sensors_battery()
        if battery is None:
            return "Battery status not available."
        charging = "charging" if battery.power_plugged else "not charging"
        return f"Battery is at {battery.percent}%, {charging}."

    def search_web(self, query: str) -> None:
        self.say(f"Searching the web for {query}...")
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(url)

    def get_news(self, topic: str = None) -> None:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
        if topic:
            url += f"&q={quote_plus(topic)}"
        self.say(f"Fetching news for {topic if topic else 'top headlines'}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "ok":
                self.say(f"Could not retrieve news: {data.get('message', 'Unknown error')}")
                return
            articles = data.get("articles", [])
            if not articles:
                self.say("No news articles found.")
                return
            self.say(f"Here are the top 3 headlines:")
            for i, article in enumerate(articles[:3], 1):
                self.say(f"Headline {i}: {article['title']}")
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP error while fetching news: {e}")
            self.say("An error occurred while fetching news.")
        except Exception as e:
            logging.error(f"Unexpected error while fetching news: {e}")
            self.say("An unexpected error occurred.")

    def get_weather(self, location: str) -> None:
        self.say(f"Fetching weather for {location}...")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={quote_plus(location)}&appid={WEATHER_API_KEY}&units=metric"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("cod") != 200:
                self.say(f"Could not retrieve weather data: {data.get('message', 'Unknown error')}")
                return
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            self.say(f"The weather in {location} is {weather} with a temperature of {temp}°C.")
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP error while fetching weather data: {e}")
            self.say("An error occurred while fetching weather data.")
        except Exception as e:
            logging.error(f"Unexpected error while fetching weather data: {e}")
            self.say("An unexpected error occurred.")

    def tell_joke(self) -> None:
        joke = self.jokes.get_joke()
        self.say(f"Here's a joke for you: {joke}")

    def set_reminder(self, reminder: str, time: datetime.datetime) -> None:
        self.scheduler.add_job(lambda: self.say(reminder), 'date', run_date=time)
        self.say(f"Reminder set for {time}.")

    def set_alarm(self, alarm_time: str) -> None:
        try:
            # Support for different time formats
            alarm_time = alarm_time.strip().lower().replace(".", "")
            alarm_time = datetime.datetime.strptime(alarm_time, "%I:%M %p")
            self.say(f"Alarm set for {alarm_time.strftime('%I:%M %p')}.")
        except ValueError as e:
            self.say(f"An unexpected error occurred: {e}")

    def add_calendar_event(self, title: str, start_time: datetime.datetime, end_time: datetime.datetime,description: str) -> None:
        try:
            subprocess.run([
                "osascript", "-e",
                f'declare calendar "{title}" start time "{start_time.strftime("%Y-%m-%d %H:%M:%S")}" end time "{end_time.strftime("%Y-%m-%d %H:%M:%S")}" description "{description}"'
            ], check=True)
            self.say(f"Event '{title}' added to your calendar.")
        except subprocess.CalledProcessError:
            self.say("Failed to add event to calendar.")
        except Exception as e:
            self.say(f"An unexpected error occurred while adding the calendar event: {e}")
            print(e)  # Print detailed error information

    def open_file_or_folder(self, name: str) -> None:
        """Open a file or folder based on the name provided. Searches in common directories if the name is not a full path."""
        # Replace 'dot' with '.' in the filename
        name = name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        # Define common directories to search
        common_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/")
        ]

        # Search for the file or folder in the common directories
        found = False
        for directory in common_directories:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                try:
                    subprocess.run(["open", path], check=True)
                    self.say(f"Opening {path}...")
                    found = True
                    break
                except Exception as e:
                    self.say(f"An error occurred while trying to open {path}: {e}")
                    print(e)  # Print detailed error information for debugging

        if not found:
            self.say(f"Sorry, the file or folder {name} does not exist.")

    def search_files(self, search_criteria: str) -> None:
        """Search for files with specific criteria."""
        if not search_criteria:
            self.say("Please provide the search criteria.")
            search_criteria = self.listen()  # Listen for search criteria
        search_criteria = search_criteria.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot",
                                                                                                                  ".")

        found_files = []
        for directory in [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents"),
                          os.path.expanduser("~/Downloads"), os.path.expanduser("~/")]:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if search_criteria in file:
                        found_files.append(os.path.join(root, file))
                for folder in dirs:
                    if search_criteria in folder:
                        found_files.append(os.path.join(root, folder))

        if found_files:
            self.say(f"Found {len(found_files)} matching files or folders:")
            for file in found_files:
                self.say(file)
        else:
            self.say(f"No files or folders found with criteria '{search_criteria}'.")

    def create_file_or_folder(self, name: str, file: bool = False) -> None:
        """Create a new file or folder based on the name provided."""
        if not name:
            self.say(f"Please provide the name of the {'file' if file else 'folder'} you would like to create.")
            name = self.listen()  # Listen for the file/folder name
        # Replace 'dot' with '.' in the filename or folder name
        name = name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        # Determine the path for creation
        common_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/")
        ]

        path_created = False
        for directory in common_directories:
            path = os.path.join(directory, name)
            if not os.path.exists(path):
                try:
                    if file:
                        with open(path, 'w') as f:
                            pass  # Create an empty file
                    else:
                        os.makedirs(path)  # Create a directory
                    self.say(f"{'File' if file else 'Folder'} created at {path}.")
                    path_created = True
                    break
                except Exception as e:
                    self.say(f"An error occurred while trying to create {path}: {e}")
                    print(e)  # Print detailed error information for debugging

        if not path_created:
            self.say(f"Sorry, could not create the file or folder {name}.")

    def rename_file_or_folder(self, old_name: str = None) -> None:
        """Rename a file or folder conversationally."""

        if not old_name:
            self.say("Which file or folder would you like to rename?")
            old_name = self.listen()  # Listen for the old name

        # Replace 'dot' with '.' in the filenames or folder names
        old_name = old_name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        # Now ask for the new name
        self.say(f"What would you like to rename {old_name} into?")
        new_name = self.listen()  # Listen for the new name

        new_name = new_name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        # Determine the path for renaming
        common_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/")
        ]

        renamed = False
        for directory in common_directories:
            old_path = os.path.join(directory, old_name)
            new_path = os.path.join(directory, new_name)

            if os.path.exists(old_path):
                try:
                    os.rename(old_path, new_path)
                    self.say(f"{old_name} renamed to {new_name}.")
                    renamed = True
                    break
                except Exception as e:
                    self.say(f"An error occurred while renaming: {e}")
                    print(e)  # Print detailed error information for debugging

        if not renamed:
            self.say(f"Sorry, could not rename {old_name}.")

    def move_file_or_folder(self, src_name: str, dest_name: str) -> None:
        """Move a file or folder to a new location."""
        if not src_name:
            self.say("Which file or folder would you like to move?")
            src_name = self.listen()  # Listen for the source name

        # Replace 'dot' with '.' in the filenames or folder names
        src_name = src_name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")
        # Now ask for the destination
        self.say(f"Where would you like to move {src_name} to?")
        dest_name = self.listen()  # Listen for the destination
        dest_name = dest_name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        # Determine the paths
        common_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/")
        ]

        moved = False
        for directory in common_directories:
            src_path = os.path.join(directory, src_name)
            dest_path = os.path.join(directory, dest_name)

            if os.path.exists(src_path):
                try:
                    shutil.move(src_path, dest_path)
                    self.say(f"Moved to {dest_name}.")
                    moved = True
                    break
                except Exception as e:
                    self.say(f"An error occurred while moving: {e}")
                    print(e)  # Print detailed error information for debugging

        if not moved:
            self.say(f"Sorry, could not move {src_name}.")

    def copy_file_or_folder(self, src_name: str, dest_name: str) -> None:
        """Copy a file or folder to a new location."""
        # Replace 'dot' with '.' in the filenames or folder names
        src_name = src_name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")
        dest_name = dest_name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        # Determine the paths
        common_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/")
        ]

        copied = False
        for directory in common_directories:
            src_path = os.path.join(directory, src_name)
            dest_path = os.path.join(directory, dest_name)

            if os.path.exists(src_path):
                try:
                    shutil.copy(src_path, dest_path)
                    self.say(f"Copied to {dest_name}.")
                    copied = True
                    break
                except Exception as e:
                    self.say(f"An error occurred while copying: {e}")
                    print(e)  # Print detailed error information for debugging

        if not copied:
            self.say(f"Sorry, could not copy {src_name}.")

    def delete_file_or_folder(self, name: str, is_folder: bool = False) -> None:
        """Delete a file or folder."""
        if not name:
            self.say(f"Which {'folder' if is_folder else 'file'} would you like to delete?")
            name = self.listen()  # Listen for the file/folder name
        # Replace 'dot' with '.' in the filenames or folder names
        name = name.replace(" dot ", ".").replace(" dot", ".").replace("dot ", ".").replace("dot", ".")

        self.say(f"Are you sure you want to delete {name}? Please say 'yes' to confirm or 'no' to cancel.")
        confirmation = self.listen()
        if "yes" in confirmation.lower():

         # Determine the path for deletion
         common_directories = [
             os.path.expanduser("~/Desktop"),
             os.path.expanduser("~/Documents"),
             os.path.expanduser("~/Downloads"),
             os.path.expanduser("~/")
         ]

         deleted = False
         for directory in common_directories:
             path = os.path.join(directory, name)

             if os.path.exists(path):
                 try:
                     if is_folder:
                         shutil.rmtree(path)
                     else:
                         os.remove(path)
                     self.say(f"Deleted {name}.")
                     deleted = True
                     break
                 except Exception as e:
                     self.say(f"An error occurred while deleting: {e}")
                     print(e)  # Print detailed error information for debugging

         if not deleted:
             self.say(f"Sorry, could not delete {name}.")
        else:
            self.say(f"Deletion of {name} cancelled.")

    def take_screenshot(self):
        # Get the path to the user's desktop
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        # Get the current time for a unique screenshot name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_path = os.path.join(desktop_dir, f"screenshot_{timestamp}.png")

        # Capture screenshot and save it to the desktop
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            result = f"Screenshot saved on your Desktop as {screenshot_path}"
            self.say(result)  # Use the say method to speak the result
            return result
        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            self.say(error_message)
            return error_message

    def toggle_wifi(self, state: str) -> None:
        try:
            if state == "on":
                subprocess.run(["networksetup", "-setairportpower", "Wi-Fi", "on"], check=True)
                self.say("Turning Wi-Fi on...")
            elif state == "off":
                subprocess.run(["networksetup", "-setairportpower", "Wi-Fi", "off"], check=True)
                self.say("Turning Wi-Fi off...")
        except subprocess.CalledProcessError as e:
            self.say(f"An error occurred while trying to toggle Wi-Fi: {e}")
            print(e)
        except Exception as e:
            self.say(f"An unexpected error occurred: {e}")
            print(e)

    def toggle_bluetooth(self, state: str) -> None:
        """Turn Bluetooth on or off."""
        if state == "on":
            command = "blueutil --power 1"
            response_text = "Turning Bluetooth on..."
        elif state == "off":
            command = "blueutil --power 0"
            response_text = "Turning Bluetooth off..."
        else:
            self.say("Invalid state for Bluetooth. Use 'on' or 'off'.")
            return

        try:
            subprocess.run(command, shell=True, check=True)
            self.say(response_text)
        except Exception as e:
            self.say(f"An error occurred while toggling Bluetooth: {e}")

    def send_whatsapp_message_instantly(self, phone_no, message):
        try:
            # Get the current time and add a small delay for sending the message
            now = time.localtime()
            hour = now.tm_hour
            minute = now.tm_min + 1  # Schedule for one minute later

            # Send WhatsApp message with a scheduled time
            kit.sendwhatmsg(phone_no, message, hour, minute, wait_time=10, tab_close=True)
            print(f'Message sent to {phone_no} successfully!')
        except Exception as e:
            print(f"Error in sending message: {e}")



    def execute_command(self, command: str) -> None:
        """Executes the user's command."""
        command = self.normalize(command)
        try:
            if "open application" in command:#1
                app_name = command.replace("open application", "").strip()
                self.open_application(app_name)
            elif "close application" in command:#2
                app_name = command.replace("close application", "").strip()
                self.close_application(app_name)
            elif "open website" in command:#3
                site_name = command.replace("open website", "").strip()
                self.open_website(site_name)
            elif "close website" in command:#4
                site_name = command.replace("close website", "").strip()
                self.close_website(site_name)
            elif "set reminder" in command:#5
                reminder_info = command.split("set reminder", 1)[-1].strip()
                self.say(f"Reminder set for {reminder_info}.")
            elif "set alarm" in command:#6
                alarm_time = command.split("set alarm at", 1)[-1].strip()
                self.set_alarm(alarm_time)
            elif "add calendar event" in command:#7
                event_info = command.split("add calendar event", 1)[-1].strip()
                self.add_calendar_event(event_info)
            elif "tell me a joke" in command:#8
                self.tell_joke()
            elif "set brightness" in command:#9
                try:
                    percentage = int(command.split()[-1])
                    self.set_brightness(percentage)
                except ValueError:
                    self.say("Please specify a valid brightness percentage.")
            elif "set volume" in command:#10
                try:
                    level = command.split()[-1]
                    self.set_volume(level)
                except ValueError:
                    self.say("Please specify a valid volume level.")
            elif "search web for" in command:#11
                search_query = command.replace("search web for", "").strip()
                self.search_web(search_query)
            elif "get weather for" in command:#12
                location = command.replace("get weather for", "").strip()
                self.get_weather(location)
            elif "get news" in command:#13
                topic = command.replace("get news on", "").replace("get news about","").strip() if "on" in command or "about" in command else None
                self.get_news(topic)
            elif "search youtube for" in command:#14
                channel_name = command.replace("search youtube channel", "").strip()
                self.search_youtube_channel(channel_name)
            elif "search instagram account" in command:#15
                account_name = command.replace("search instagram account", "").strip()
                self.search_instagram_account(account_name)
            elif "battery status" in command:#16
                status = self.get_battery_status()
                self.say(status)
            elif "open file" in command or "open folder" in command:#17
                name = command.replace("open file", "").replace("open folder", "").strip()
                self.open_file_or_folder(name)
            elif "create file" in command:#18
                name = command.replace("create file", "").strip()
                self.create_file_or_folder(name, file=True)
            elif "create folder" in command:#19
                name = command.replace("create folder", "").strip()
                self.create_file_or_folder(name, file=False)
            elif "rename" in command:#20
                parts = command.replace("rename", "").strip().split(" to ")
                if len(parts) == 2:
                    old_name, new_name = parts
                    self.rename_file_or_folder(old_name, new_name)
            elif "move" in command:#21
                parts = command.replace("move", "").strip().split(" to ")
                if len(parts) == 2:
                    src_name, dest_name = parts
                    self.move_file_or_folder(src_name, dest_name)
            elif "copy" in command:#22
                parts = command.replace("copy", "").strip().split(" to ")
                if len(parts) == 2:
                    src_name, dest_name = parts
                    self.copy_file_or_folder(src_name, dest_name)
            elif "delete" in command:#23
                name = command.replace("delete", "").strip()
                is_folder = "folder" in command
                self.delete_file_or_folder(name, is_folder)
            elif "search for" in command:#24
                search_criteria = command.replace("search for", "").strip()
                self.search_files(search_criteria)
            elif "take a screenshot" in command.lower():
                result = self.take_screenshot()
            elif"hello" in command.lower():
                print("Hello boss!")
            elif "turn wi-fi" in command:
                state = command.split("turn wi-fi ")[-1].strip()
                if state in ["on", "off"]:
                    self.toggle_wifi(state)
                else:
                    self.say("Invalid state for Wi-Fi. Please specify 'on' or 'off'.")
            elif "turn bluetooth" in command:
                state = command.split("turn bluetooth")[-1].strip()
                self.toggle_bluetooth(state)
            elif "send whatsapp message" in command:
                    # Use regex to extract phone number and message
                    pattern = r"send whatsapp message to\s*(\+?\d[\s\d]*)\s*(.*)"
                    match = re.search(pattern, command, re.IGNORECASE)

                    if match:
                        phone_no = match.group(1).replace(" ", "")  # Extract and clean phone number
                        message = match.group(2).strip()  # Extract message

                        # Always add country code +91 if it doesn't start with a '+'
                        if not phone_no.startswith("+"):
                            phone_no = f"+91{phone_no}"

                        # Send the WhatsApp message
                        self.send_whatsapp_message_instantly(phone_no, message)
                    else:
                        print("Invalid command format.")
        except Exception as e:
            self.display_text(f"An unexpected error occurred: {e}")



if __name__ == "__main__":
    va = VirtualAssistant()
    va.process_commands()