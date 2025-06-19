# assistant.py

# Import necessary libraries
import pyttsx3  # For text-to-speech conversion: enables the bot to "speak" its responses.
import speech_recognition as sr  # For converting speech to text: allows the bot to "listen" to user commands.
import \
    datetime  # For working with dates and times: used to determine the current time for greetings and to provide the time.
import wikipedia  # For searching information on Wikipedia: allows the bot to fetch summaries from Wikipedia.
import \
    webbrowser  # For opening web pages in a browser: used to open URLs like YouTube, Google, Spotify, and Stack Overflow.
import \
    os  # For interacting with the operating system: enables actions like opening applications (e.g., VS Code) or forcefully exiting the program.
import smtplib  # For sending emails using SMTP (Simple Mail Transfer Protocol): provides functionality to send emails.
import random  # For generating random numbers or selecting random items: used for picking jokes and tricky questions.
import time  # For time-related functions: primarily used for pausing execution (e.g., for typing effects).
import re  # For regular expressions: used in the calculation function to parse and clean mathematical expressions.
import \
    threading  # For managing concurrent operations: crucial for preventing the GUI from freezing during blocking operations like speech recognition or text-to-speech, and for signalling interruptions.

# Import configurations from a separate file
# This is good practice for separating sensitive data (like email credentials) from the main code.
from config import EMAIL_ADDRESS, EMAIL_PASSWORD


class LeproAssistant:
    """
    Core assistant logic including speech synthesis, recognition,
    and command execution. This class encapsulates all the backend
    functionality of the chatbot, interacting with external APIs and system resources.
    """

    def __init__(self, display_callback=None, typing_callback=None):
        """
        Initializes the LeproAssistant with the text-to-speech engine,
        speech recognition, and GUI interaction callbacks.

        Args:
            display_callback (function): A function provided by the GUI to display general messages.
                                         This is used to show bot responses in the chat area.
            typing_callback (function): A function provided by the GUI to simulate a typing effect
                                        for the bot's messages, enhancing user experience.
        """
        # Initialize the text-to-speech engine using pyttsx3.
        # 'sapi5' is a Microsoft Speech API specific to Windows.
        self.engine = pyttsx3.init('sapi5')

        # Retrieve available voices from the system.
        voices = self.engine.getProperty('voices')
        try:
            # Attempt to set the voice to a female voice. On most Windows systems,
            # voices[1] corresponds to a female voice (e.g., Microsoft Zira).
            self.engine.setProperty('voice', voices[1].id)
        except IndexError:
            # Fallback if the specific voice (index 1) is not found on the system.
            print("Warning: Female voice (index 1) not found. Using default voice.")
            if voices:
                # Use the first available voice as a fallback.
                self.engine.setProperty('voice', voices[0].id)
            else:
                # If no voices are found at all, print an error.
                print("Error: No voices found on this system.")

        # Store the callback functions provided by the GUI for displaying messages
        # and simulating typing. These are essential for the bot to interact with the UI.
        self.display_callback = display_callback
        self.typing_callback = typing_callback

        # Events for signalling stopping of speech or listening.
        # `threading.Event` objects are used for inter-thread communication.
        # `_stop_speaking_event`: Set when the user wants to interrupt the bot's speech.
        # `_stop_listening_event`: Set when the user wants to interrupt the microphone listening.
        self._stop_speaking_event = threading.Event()
        self._stop_listening_event = threading.Event()

        # Initialize the SpeechRecognition Recognizer.
        # This object is responsible for processing audio input.
        self.recognizer = sr.Recognizer()

        # Predefined lists of jokes and tricky questions for the bot to use.
        self.jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised."
        ]

        self.tricky_questions = [
            {"question": "What has an eye, but cannot see?", "answer": "A needle"},
            {"question": "What is full of holes but still holds water?", "answer": "A sponge"},
            {"question": "What question can you never answer yes to?", "answer": "Are you asleep yet?"},
            {"question": "What has to be broken before you can use it?", "answer": "An egg"},
            {"question": "What is always in front of you but can’t be seen?", "answer": "The future"},
            {"question": "What has cities, but no houses; forests, but no trees; and water, but no fish?",
             "answer": "A map"},
        ]

    def speak(self, text):
        """
        Converts text to speech using pyttsx3 and updates the GUI.
        This method includes a typing effect simulation and ensures the bot's speech
        can be interrupted by the stop command.

        Args:
            text (str): The text message that the assistant will speak aloud.
        """
        # Clear the stop speaking event before starting new speech.
        # This is crucial so that a stop signal from a previous action doesn't
        # immediately stop the *new* speech being generated.
        self._stop_speaking_event.clear()

        # Check if a typing callback is provided (i.e., if connected to a GUI).
        if self.typing_callback:
            # Call the GUI's typing effect to simulate the bot "typing" its response.
            self.typing_callback("Lepro", text, delay=0.03)
            # Introduce a small delay to allow the typing animation to be visible
            # before the actual speech begins. The delay is capped to prevent excessive waits
            # for very long texts.
            time.sleep(min(2, len(text) * 0.03 + 0.5))

        # Queue the text for the pyttsx3 engine to synthesize and speak.
        self.engine.say(text)
        # Block the current thread until the queued utterance is finished speaking
        # or until `self.engine.stop()` is called from another thread (e.g., by the stop button).
        self.engine.runAndWait()

        # Note on Interruption: `runAndWait()` can be stopped by `engine.stop()`.
        # However, if the text is very short, `runAndWait()` might complete before
        # a stop signal can be processed. For highly granular interruption,
        # a different TTS library or direct audio stream management might be required.

    def stop_speaking(self):
        """
        Immediately stops the current text-to-speech output.
        This is called by the GUI's 'Stop' button.
        """
        # Set the `_stop_speaking_event` to signal any ongoing speech processes to halt.
        self._stop_speaking_event.set()
        # Force the pyttsx3 engine to stop any current utterances.
        self.engine.stop()

    def wish_me_speech(self):
        """
        Delivers a time-based greeting (Good Morning, Good Afternoon, Good Evening)
        to the user via speech.
        """
        hour = int(datetime.datetime.now().hour)  # Get the current hour (0-23).
        greeting = ""
        # Determine the appropriate greeting based on the hour.
        if hour < 12:
            greeting = "Good Morning!"
        elif hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"
        # Speak the composed greeting.
        self.speak(f"{greeting} I am Lepro Sir. Please tell me how may I help you.")

    def take_command(self):
        """
        Listens for the user's voice command using the system microphone
        and Google Speech Recognition API. This method is blocking while listening.
        It includes features for ambient noise adjustment and handling various
        speech recognition errors.

        Returns:
            str: The recognized command converted to lowercase. Returns "None" if
                 no speech is detected, an error occurs during recognition, or
                 listening is explicitly stopped.
        """
        # Clear the stop listening event before starting a new listening session.
        # This ensures that a previous stop signal doesn't prematurely halt the new session.
        self._stop_listening_event.clear()

        # Use the system's default microphone as the audio source for the recognizer.
        with sr.Microphone() as source:
            if self.display_callback:
                # Inform the user in the GUI that the bot is now listening.
                self.display_callback("Lepro", "Listening... Please speak now.")

            # Set the minimum length of silence (in seconds) that the recognizer
            # will consider to be the end of a phrase.
            self.recognizer.pause_threshold = 1
            # Set the energy threshold. This helps the recognizer determine what parts
            # of the audio stream are actual speech versus background noise.
            self.recognizer.energy_threshold = 300

            # Adjust for ambient noise to improve recognition accuracy.
            # The recognizer listens for a short duration (1 second) to
            # calibrate itself to the background noise levels.
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                if self.display_callback:
                    self.display_callback("Lepro", "Calibrated. Listening for command...")
            except Exception as e:
                # Handle errors during microphone calibration.
                if self.display_callback:
                    self.display_callback("Lepro", f"Could not calibrate microphone: {e}")
                print(f"Microphone calibration error: {e}")

            audio = None
            try:
                # Listen to the audio stream from the microphone. This is a blocking call.
                # `timeout`: If no speech is detected for this duration, a `sr.WaitTimeoutError` is raised.
                # `phrase_time_limit`: Maximum duration (in seconds) of a continuous phrase.
                #                     Speech beyond this limit will be ignored for the current phrase.
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                # If no speech is detected within the specified timeout.
                self.speak("No speech detected.")
                return "None"
            except Exception as e:
                # Catch any other unexpected errors that might occur during the listening phase.
                self.speak(f"An error occurred while listening: {e}")
                return "None"

        # After audio has been captured, check if a stop listening event was set.
        # This handles cases where the user clicked 'Stop' while `listen()` was waiting.
        if self._stop_listening_event.is_set():
            self.speak("Listening stopped.")
            return "None"

        try:
            if self.display_callback:
                # Inform the user that the bot is now processing the captured audio.
                self.display_callback("Lepro", "Recognizing speech...")
            # Use Google Speech Recognition to convert the captured audio into text.
            # 'en-in' specifies Indian English as the recognition language.
            query = self.recognizer.recognize_google(audio, language='en-in')
            return query.lower()  # Return the recognized text in lowercase for easier command matching.
        except sr.UnknownValueError:
            # This exception is raised if Google Speech Recognition cannot understand the audio.
            self.speak("Sorry, I couldn't understand your audio. Please try again.")
            return "None"
        except sr.RequestError as e:
            # This exception is raised if there's a problem connecting to or receiving
            # results from the Google Speech Recognition service (e.g., no internet, API issues).
            self.speak(f"Could not request results from speech recognition service; {e}")
            return "None"
        except Exception as e:
            # Catch any other unexpected errors that might occur during the recognition process.
            self.speak(f"An unexpected error occurred during speech recognition: {e}")
            return "None"

    def stop_listening(self):
        """
        Signals the ongoing listening process (if any) to stop.
        This is called by the GUI's 'Stop' button.
        """
        # Set the `_stop_listening_event` to signal the listening thread to halt.
        self._stop_listening_event.set()
        # Note: This event acts as a signal. The `recognizer.listen()` method
        # itself is blocking and doesn't immediately stop. The signal will be
        # processed after `listen()` returns (e.g., after a timeout or a phrase end).

    def calculate(self, expression):
        """
        Evaluates a simple mathematical expression provided as a string.
        It sanitizes the input to only allow basic arithmetic operations.

        Args:
            expression (str): The mathematical expression string (e.g., "5 + 3 * 2").

        Returns:
            str: The result of the calculation as a string, or an error message
                 if the expression is invalid or an error occurs.
        """
        # Use regular expressions to clean the input expression.
        # Only digits, basic operators (+, -, *, /), decimal points, and spaces are allowed.
        expression = re.sub(r'[^\d+\-*/. ]', '', expression)
        try:
            # `eval()` evaluates the string as a Python expression.
            # While convenient for simple calculators, `eval()` can be a security risk
            # if used with untrusted input without strict sanitization, as it can execute arbitrary code.
            # Here, the input is heavily sanitized, reducing the risk for this specific use case.
            result = eval(expression)
            return str(result)  # Convert the numerical result back to a string.
        except (SyntaxError, ZeroDivisionError, TypeError) as e:
            # Catch common mathematical errors like invalid syntax or division by zero.
            return f"Sorry, I couldn't calculate that. Error: {e}"
        except Exception as e:
            # Catch any other unexpected errors during calculation.
            return f"An unexpected error occurred during calculation: {e}"

    def run_command(self, query):
        """
        Processes the recognized user command (from voice or text input) and
        executes the corresponding action. This method contains the core logic
        for the bot's functionalities (e.g., searching, opening apps, emailing).
        It also checks for stop signals before and during command execution.

        Args:
            query (str): The normalized (lowercase) command string received from the user.
        """
        # Check if a stop signal was issued for speaking or listening just before
        # command execution. If so, abort the command.
        if self._stop_speaking_event.is_set() or self._stop_listening_event.is_set():
            self.stop_speaking()  # Ensure any partial speech is stopped.
            self.speak("Command execution stopped.")
            return

        # --- Extensive Command Handling Logic ---
        # Each `elif` block handles a specific type of user command.

        if 'wikipedia' in query:
            self.speak('Searching Wikipedia...')
            # Remove the keyword "wikipedia" to get the actual search term.
            query = query.replace("wikipedia", "").strip()
            if not query:
                # If the user just said "Wikipedia", prompt for a specific search term.
                self.speak("What do you want to search on Wikipedia?")
                query = self.take_command()  # Listen for the follow-up command.
                if query == "None":
                    self.speak("No search query provided. Aborting Wikipedia search.")
                    return
            try:
                # Use the wikipedia library to get a summary.
                # `sentences=3` limits the summary to three sentences.
                results = wikipedia.summary(query, sentences=3)
                self.speak(f"According to Wikipedia, {results}")
            except wikipedia.exceptions.PageError:
                # Handle cases where the Wikipedia page does not exist.
                self.speak("Sorry, I could not find anything on Wikipedia for that query.")
            except wikipedia.exceptions.DisambiguationError as e:
                # Handle ambiguous queries where multiple Wikipedia pages match.
                self.speak(
                    f"Your query is ambiguous. Please be more specific. Possible options include: {', '.join(e.options[:3])}")
            except Exception as e:
                # Catch any other errors during Wikipedia search.
                self.speak(f"An error occurred while searching Wikipedia: {e}")

        elif 'open youtube' in query:
            self.speak("Opening YouTube.")
            # Extract search query if present (e.g., "open youtube and search for cats").
            search_query = query.replace("open youtube and search for", "").replace("open youtube and search",
                                                                                    "").strip()
            if search_query:
                # Open YouTube directly to a search results page.
                webbrowser.open(f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}")
                self.speak(f"Searching YouTube for {search_query}")
            else:
                # Open the YouTube homepage.
                webbrowser.open("https://www.youtube.com")

        elif 'open google' in query:
            self.speak("Opening Google.")
            # Extract search query if present.
            search_query = query.replace("open google and search for", "").replace("open google and search", "").strip()
            if search_query:
                # Open Google directly to a search results page.
                webbrowser.open(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
                self.speak(f"Searching Google for {search_query}")
            else:
                # Open the Google homepage.
                webbrowser.open("https://www.google.com")

        elif 'open stackoverflow' in query:
            self.speak("Opening Stack Overflow.")
            webbrowser.open("https://stackoverflow.com")  # Open Stack Overflow website.

        elif 'play song on spotify' in query or 'play music on spotify' in query:
            self.speak("Sure, what song would you like me to play on Spotify?")
            song_name = self.take_command()  # Listen for the song name.
            if song_name and song_name != "None":
                # Open Spotify's web player search for the specified song.
                search_url = f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}"
                webbrowser.open(search_url)
                self.speak(f"Searching Spotify for {song_name}.")
            else:
                self.speak("I didn't get the song name. Please try again.")

        elif 'the time' in query:
            # Get the current time and format it as HH:MM AM/PM.
            str_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"Sir, the time is {str_time}.")

        elif 'open code' in query or 'open vs code' in query:
            self.speak("Opening Visual Studio Code.")
            # IMPORTANT: This path needs to be updated by the user to their actual VS Code executable location.
            code_path = "C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
            try:
                os.startfile(code_path)  # Use `os.startfile` to launch an executable.
            except FileNotFoundError:
                self.speak(
                    "Sorry, I could not find Visual Studio Code at the specified path. Please check the path in my code.")
            except Exception as e:
                self.speak(f"An error occurred while opening VS Code: {e}")

        elif 'email to rafay' in query:
            self.speak("What should I say in the email?")
            content = self.take_command()  # Listen for the email content.
            if content and content != "None":
                to = "mahboobrafay@gmail.com"  # Define the recipient's email address.
                try:
                    self.send_email(to, content)  # Call the helper function to send the email.
                    self.speak("Email has been sent!")
                except Exception as e:
                    self.speak(
                        f"Sorry, I am not able to send this email. Error: {e}. Please ensure your email settings are correct in config.py.")
            else:
                self.speak("No content provided for the email. Aborting email.")

        elif 'tell me a joke' in query:
            joke = random.choice(self.jokes)  # Select a random joke from the predefined list.
            self.speak(joke)

        elif 'ask me a tricky question' in query:
            tricky_qa = random.choice(self.tricky_questions)  # Select a random tricky question.
            self.speak(tricky_qa["question"])
            # Current implementation only asks the question. To make it interactive,
            # you would need to add a follow-up listening phase and logic to check the user's answer.

        elif 'calculate' in query:
            # Use `re.search` to find the mathematical expression after the word "calculate".
            expression_match = re.search(r'calculate (.+)', query)
            if expression_match:
                expression = expression_match.group(1)  # Extract the captured expression.
                result = self.calculate(expression)  # Call the calculate function.
                self.speak(f"The result is {result}.")
            else:
                self.speak(
                    "What do you want me to calculate? Please state the full expression, for example: 'calculate 5 plus 3'")

        elif 'exit' in query or 'quit' in query or 'bye' in query:
            self.speak("Goodbye, Sir! Have a great day!")
            os._exit(0)  # Forcefully exit the Python application. This is typically used in threaded environments.

        else:
            # Default response if the command is not understood.
            self.speak("I didn't understand that command. Please say it again or try a different command.")

    def send_email(self, to, content):
        """
        Sends an email using the SMTP protocol via Gmail's servers.
        Requires `EMAIL_ADDRESS` and `EMAIL_PASSWORD` from `config.py`.

        Args:
            to (str): The recipient's email address.
            content (str): The body content of the email.
        """
        # Establish a secure SMTP connection to Gmail's server on port 587.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Upgrade the connection to a secure TLS encrypted connection.

        # Log in to the sender's email account using credentials from config.py.
        # For security, consider using Gmail App Passwords if 2-Factor Authentication is enabled.
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        # Send the email from the sender's address to the recipient with the specified content.
        server.sendmail(EMAIL_ADDRESS, to, content)

        server.quit()  # Close the SMTP connection.