# assistant.py
import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import smtplib
import random
import re
import time

class LeproAssistant:
    def __init__(self, display_callback=None, typing_callback=None):
        """Initialize voice engine, callbacks, jokes and riddles."""
        self.display_callback = display_callback
        self.typing_callback = typing_callback

        self.engine = pyttsx3.init('sapi5')
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)

        self.jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call fake spaghetti? An impasta!",
            "Why did the math book look sad? Because it had too many problems.",
        ]

        self.riddles = [
            {"q": "What has keys but can't open locks?", "a": "A piano"},
            {"q": "What can travel around the world while staying in the corner?", "a": "A stamp"},
        ]

    def speak(self, text):
        """Type + speak response."""
        if self.typing_callback:
            self.typing_callback("Lepro", text, delay=0.03)
            time.sleep(len(text) * 0.03 + 0.3)
        self.engine.say(text)
        self.engine.runAndWait()

    def get_welcome_message(self):
        return "Hello! I'm Lepro, your AI friend. How can I help you today?"

    def wish_me_speech(self):
        hour = datetime.datetime.now().hour
        if hour < 12:
            greet = "Good morning"
        elif hour < 18:
            greet = "Good afternoon"
        else:
            greet = "Good evening"
        self.speak(f"{greet}! I'm ready to assist you.")

    def take_command(self):
        """Capture voice command from user."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.display_callback("Lepro", "Listening...")
            recognizer.pause_threshold = 1
            try:
                audio = recognizer.listen(source, timeout=5)
                query = recognizer.recognize_google(audio, language='en-in')
                return query.lower()
            except sr.WaitTimeoutError:
                self.speak("No speech detected. Try again.")
            except sr.UnknownValueError:
                self.speak("Sorry, I couldn't understand.")
            except sr.RequestError:
                self.speak("Internet issue or API down.")
        return "None"

    def run_command(self, query):
        """Route commands based on query content."""
        if 'wikipedia' in query:
            self.search_wikipedia(query)

        elif 'open youtube' in query:
            self.open_website("YouTube", "https://youtube.com")

        elif 'open google' in query:
            self.open_website("Google", "https://google.com")

        elif 'stackoverflow' in query:
            self.open_website("Stack Overflow", "https://stackoverflow.com")

        elif 'play song' in query or 'spotify' in query:
            self.play_on_spotify(query)

        elif 'calculate' in query:
            self.handle_calculation(query)

        elif 'time' in query:
            self.tell_time()

        elif 'joke' in query:
            self.speak(random.choice(self.jokes))

        elif 'tricky' in query or 'riddle' in query:
            r = random.choice(self.riddles)
            self.speak(r["q"])

        elif 'open code' in query:
            self.open_vs_code()

        elif 'email to' in query:
            self.speak("Feature under development. Email sending isn't configured.")

        elif 'exit' in query or 'quit' in query or 'bye' in query:
            self.speak("Goodbye! Take care.")
            os._exit(0)

        else:
            self.speak("Sorry, I didn't understand that.")

    def search_wikipedia(self, query):
        """Search and read Wikipedia summary."""
        self.speak("Searching Wikipedia...")
        topic = query.replace("wikipedia", "").strip()
        if not topic:
            self.speak("What should I search for?")
            return
        try:
            summary = wikipedia.summary(topic, sentences=2)
            self.speak(f"According to Wikipedia, {summary}")
        except Exception:
            self.speak("No result found or too many matches.")

    def open_website(self, name, url):
        """Open any website."""
        self.speak(f"Opening {name}")
        webbrowser.open(url)

    def play_on_spotify(self, query):
        self.speak("Which song?")
        song = self.take_command()
        if song != "None":
            url = f"https://open.spotify.com/search/{song.replace(' ', '%20')}"
            webbrowser.open(url)
            self.speak(f"Playing {song} on Spotify")

    def handle_calculation(self, query):
        """Extract and calculate arithmetic expressions."""
        match = re.search(r'calculate (.+)', query)
        if match:
            expression = match.group(1)
            expression = re.sub(r'[^\d\+\-\*/\.]', '', expression)
            try:
                result = eval(expression)
                self.speak(f"The result is {result}")
            except Exception as e:
                self.speak("Sorry, calculation failed.")
        else:
            self.speak("Please say something like 'calculate 5 plus 3'.")

    def tell_time(self):
        time_now = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The time is {time_now}")

    def open_vs_code(self):
        """Try to open Visual Studio Code."""
        path = "C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
        try:
            os.startfile(path)
            self.speak("Opening VS Code")
        except:
            self.speak("Can't find VS Code at that path.")
