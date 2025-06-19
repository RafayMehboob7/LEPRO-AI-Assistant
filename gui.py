# gui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import random
import colorsys
import queue
import math # For sine wave in glowing effect

from assistant import LeproAssistant

class LeproGUI:
    """
    Manages the graphical user interface for the Lepro Chatbot.
    Features a dashboard, dark theme, animated background, and voice/text commands.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Lepro Chatbot")
        self.root.geometry("800x700") # Slightly larger window
        self.root.resizable(False, False)
        self.root.configure(bg="#2c2c2c") # Overall dark grey background

        self.canvas = tk.Canvas(root, width=800, height=700, highlightthickness=0, bg="#2c2c2c")
        self.canvas.pack(fill="both", expand=True)

        self.star_objects = []
        self.hue = 0.0 # Initial hue for background animation
        self.glow_phase = 0 # For button glowing animation

        # Threading-related variables
        self.is_listening = False
        self.is_processing_command = False
        self.listening_result_queue = queue.Queue()
        self.command_processing_queue = queue.Queue() # For results of command execution

        # Initialize assistant early for callbacks
        self.assistant = LeproAssistant(display_callback=self.display_message,
                                        typing_callback=self.typing_effect)

        # --- Setup Dashboard Screen ---
        self.dashboard_frame = tk.Frame(self.canvas, bg="#2c2c2c")
        self.dashboard_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.dashboard_label = tk.Label(self.dashboard_frame, text="Welcome to Lepro",
                                        font=("Inter", 30, "bold"), fg="#e0e0e0", bg="#2c2c2c")
        self.dashboard_label.place(relx=0.5, rely=0.3, anchor=tk.CENTER)

        self.dashboard_button = tk.Button(self.dashboard_frame, text="Talk to Lepro\nYour AI Assistant",
                                          font=("Inter", 18, "bold"), fg="white",
                                          bg="#007bff", # Default sea blue
                                          activebackground="#0056b3",
                                          relief=tk.FLAT, bd=0,
                                          command=self.show_main_interface)
        self.dashboard_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER, width=250, height=100)

        # Start initial background animation for dashboard
        self.root.after(100, self._start_initial_animations)
        self.root.after(200, self._animate_dashboard_button_glow)


    def show_main_interface(self):
        """Switches from the dashboard to the main chat interface."""
        self.dashboard_frame.destroy() # Remove dashboard

        # --- Setup Main Interface ---
        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(self.canvas, wrap=tk.WORD, font=("Inter", 12),
                                                   bg="#3a3a3a", fg="#e0e0e0", bd=0, padx=15, pady=15,
                                                   relief=tk.FLAT, insertbackground='#007bff',
                                                   selectbackground="#007bff", selectforeground="white",
                                                   highlightbackground="#007bff", highlightcolor="#007bff")
        self.chat_area.place(relwidth=0.9, relheight=0.65, relx=0.05, rely=0.04)
        self.chat_area.config(state=tk.DISABLED)

        self.chat_area.tag_config("Lepro_tag", foreground="#88c0d0", font=("Inter", 12, "bold"))
        self.chat_area.tag_config("You_tag", foreground="#a3be8c", font=("Inter", 12, "bold"))

        # Text input field
        self.text_input = tk.Entry(self.canvas, font=("Inter", 12), bg="#4a4a4a", fg="#e0e0e0",
                                   bd=2, relief=tk.FLAT, insertbackground='#007bff',
                                   highlightbackground="#007bff", highlightcolor="#007bff")
        self.text_input.place(relwidth=0.7, relheight=0.07, relx=0.05, rely=0.72)
        self.text_input.bind("<Return>", self.send_text_command)

        # Send Button
        self.send_button = tk.Button(self.canvas, text="Send", font=("Inter", 12, "bold"),
                                     bg="#007bff", fg="white", activebackground="#0056b3",
                                     activeforeground="white", relief=tk.FLAT, bd=0,
                                     command=self.send_text_command)
        self.send_button.place(relx=0.76, rely=0.72, relwidth=0.19, relheight=0.07)

        # Speech Button
        self.speech_button = tk.Button(self.canvas, text="Speech", font=("Inter", 14, "bold"),
                                       bg="#007bff", fg="white", activebackground="#0056b3",
                                       activeforeground="white", relief=tk.FLAT, bd=0,
                                       command=self.start_listening)
        self.speech_button.place(relx=0.05, rely=0.85, relwidth=0.42, relheight=0.1)

        # Stop Button
        self.stop_button = tk.Button(self.canvas, text="Stop", font=("Inter", 14, "bold"),
                                     bg="#dc3545", fg="white", activebackground="#c82333",
                                     activeforeground="white", relief=tk.FLAT, bd=0,
                                     command=self.stop_current_process)
        self.stop_button.place(relx=0.53, rely=0.85, relwidth=0.42, relheight=0.1)
        self.stop_button.config(state=tk.DISABLED) # Disabled initially

        # Start checking the queues for command results and speech recognition results
        self.root.after(100, self._check_listening_queue)
        self.root.after(100, self._check_command_processing_queue)
        self.root.after(200, self._animate_speech_button_glow) # Start glow for main interface button

        # Initial welcome message only appears after main interface shows up
        threading.Thread(target=self._initial_welcome_message, daemon=True).start()


    def _start_initial_animations(self):
        """Helper to start the background drawing and animation after a delay."""
        self._draw_gradient_and_stars()
        self._animate_background()

    def _rgb_to_hex(self, rgb):
        """Converts an RGB tuple to a hexadecimal color string."""
        return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'

    def _draw_gradient_and_stars(self):
        """
        Draws a vertical gradient background and adds static stars.
        This is the initial drawing; animation will update it.
        """
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width == 0 or height == 0:
            self.root.after(50, self._draw_gradient_and_stars)
            return

        self.canvas.delete("gradient_lines") # Clear only gradient lines, not stars for continuous effect

        # Define a base dark grey for the background
        base_color_rgb = (44, 44, 44) # #2c2c2c

        for i in range(height):
            # Calculate hue for current row for subtle color shift
            current_hue = (self.hue + (i / height) * 0.1) % 1.0
            # Blend base dark grey with a vibrant blueish-purple for the 'mixture' effect
            # Using HSV for vibrant colors, then blending with the base grey
            color_blend_hsv = colorsys.hsv_to_rgb(current_hue, 0.7, 0.6) # Vibrant mid-tone
            r_blend = int(base_color_rgb[0] * 0.4 + color_blend_hsv[0] * 0.6 * 255)
            g_blend = int(base_color_rgb[1] * 0.4 + color_blend_hsv[1] * 0.6 * 255)
            b_blend = int(base_color_rgb[2] * 0.4 + color_blend_hsv[2] * 0.6 * 255)

            # Ensure color values are within 0-255 range
            r_blend = min(255, max(0, r_blend))
            g_blend = min(255, max(0, g_blend))
            b_blend = min(255, max(0, b_blend))

            color = self._rgb_to_hex((r_blend, g_blend, b_blend))
            self.canvas.create_line(0, i, width, i, fill=color, width=1, tags="gradient_lines")

        # Draw/Update stars only if not already present, or just move them
        if not self.star_objects: # Initial creation
            for _ in range(200): # More stars for a denser feel
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(1, 3) # Smaller stars
                speed_x = random.uniform(-0.3, 0.3)
                speed_y = random.uniform(-0.3, 0.3)
                star_id = self.canvas.create_oval(x, y, x + size, y + size, fill="white", outline="white", tags="stars")
                self.star_objects.append({'id': star_id, 'x': x, 'y': y, 'size': size, 'speed_x': speed_x, 'speed_y': speed_y})
        else: # Update star positions on subsequent calls
            for star in self.star_objects:
                new_x = star['x'] + star['speed_x']
                new_y = star['y'] + star['speed_y']

                if new_x < -star['size']: new_x = width
                if new_x > width: new_x = -star['size']
                if new_y < -star['size']: new_y = height
                if new_y > height: new_y = -star['size']

                self.canvas.move(star['id'], new_x - star['x'], new_y - star['y'])
                star['x'] = new_x
                star['y'] = new_y


        # Re-stack widgets on top if they exist (main interface has them)
        # This needs to be conditional as chat_area etc. don't exist on dashboard.
        if hasattr(self, 'chat_area'):
            self.canvas.lift(self.chat_area)
            self.canvas.lift(self.text_input)
            self.canvas.lift(self.send_button)
            self.canvas.lift(self.speech_button)
            self.canvas.lift(self.stop_button)
        else: # Lift dashboard elements if still on dashboard
            self.canvas.lift(self.dashboard_frame)
            self.canvas.lift(self.dashboard_label)
            self.canvas.lift(self.dashboard_button)


    def _animate_background(self):
        """Animates the background gradient and star movement."""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width == 0 or height == 0:
            self.root.after(20, self._animate_background)
            return

        self.hue = (self.hue + 0.0008) % 1.0 # Slightly faster hue change
        self._draw_gradient_and_stars() # Redraw gradient and update stars

        self.root.after(20, self._animate_background) # Call again after 20ms

    def _animate_dashboard_button_glow(self):
        """Animates the glow effect for the dashboard button."""
        if not hasattr(self, 'dashboard_button') or not self.dashboard_button.winfo_exists():
            return # Stop animation if dashboard is gone

        # Use sine wave for pulsing glow
        brightness_factor = (math.sin(self.glow_phase) + 1) / 2 # 0 to 1
        self.glow_phase += 0.08 # Speed of glow

        # Base color (sea blue: #007bff -> RGB(0, 123, 255))
        base_r, base_g, base_b = (0, 123, 255)

        # Create a light effect for glow
        glow_r = int(base_r + (255 - base_r) * brightness_factor * 0.4) # Max 40% brighter
        glow_g = int(base_g + (255 - base_g) * brightness_factor * 0.4)
        glow_b = int(base_b + (255 - base_b) * brightness_factor * 0.4)

        glow_color = self._rgb_to_hex((glow_r, glow_g, glow_b))
        self.dashboard_button.config(bg=glow_color)

        self.root.after(50, self._animate_dashboard_button_glow) # Faster glow animation

    def _animate_speech_button_glow(self):
        """Animates the glow effect for the main interface speech button."""
        if not hasattr(self, 'speech_button') or not self.speech_button.winfo_exists():
            return # Stop animation if button is gone or interface not loaded

        # Only glow if not actively listening or processing, or if listening to indicate readiness
        if not self.is_listening and not self.is_processing_command:
            # Use sine wave for pulsing glow
            brightness_factor = (math.sin(self.glow_phase) + 1) / 2 # 0 to 1
            self.glow_phase += 0.08

            base_r, base_g, base_b = (0, 123, 255) # Sea blue

            glow_r = int(base_r + (255 - base_r) * brightness_factor * 0.4)
            glow_g = int(base_g + (255 - base_g) * brightness_factor * 0.4)
            glow_b = int(base_b + (255 - base_b) * brightness_factor * 0.4)

            glow_color = self._rgb_to_hex((glow_r, glow_g, glow_b))
            self.speech_button.config(bg=glow_color, fg="white") # Keep foreground white for readability
        elif self.is_listening:
            # Change color to indicate active listening
            self.speech_button.config(bg="#FFA500", fg="white") # Orange
        else: # processing command
            self.speech_button.config(bg="#007bff", fg="white") # Back to normal sea blue

        self.root.after(50, self._animate_speech_button_glow)


    def _initial_welcome_message(self):
        """
        Retrieves the welcome message from the assistant and displays it
        with a typing effect, then initiates the speech greeting.
        """
        # Ensure initial welcome message only triggers once main GUI is loaded
        if hasattr(self, 'chat_area'):
            welcome_text = self.assistant.get_welcome_message()
            self.typing_effect("Lepro", welcome_text)
            self.assistant.wish_me_speech()

    def display_message(self, speaker, message):
        """
        Displays a message in the chat area.
        Ensures thread-safe update by using root.after.
        """
        def _insert_message():
            # Check if chat_area exists before attempting to write to it (in case main interface not loaded)
            if hasattr(self, 'chat_area') and self.chat_area.winfo_exists():
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.insert(tk.END, f"{speaker}: ", (f"{speaker}_tag",))
                self.chat_area.insert(tk.END, message + "\n\n")
                self.chat_area.see(tk.END)
                self.chat_area.config(state=tk.DISABLED)
        self.root.after(0, _insert_message)

    def typing_effect(self, speaker, text, delay=0.01):
        """
        Simulates a typing effect by inserting characters one by one.
        Updates the chat area. Ensures thread-safe update.
        """
        def _type_char(i):
            if not (hasattr(self, 'chat_area') and self.chat_area.winfo_exists()):
                return # Stop if chat_area is not available

            if self.assistant._stop_speaking_event.is_set(): # Check if speaking was interrupted
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.delete("end-1c linestart", tk.END) # Clear partial typing
                self.chat_area.insert(tk.END, "...\n\n") # Indicate interruption
                self.chat_area.see(tk.END)
                self.chat_area.config(state=tk.DISABLED)
                return

            if i < len(text):
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.insert(tk.END, text[i])
                self.chat_area.see(tk.END)
                self.chat_area.config(state=tk.DISABLED)
                self.root.update_idletasks()
                self.root.after(int(delay * 1000), lambda: _type_char(i + 1))
            else:
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.insert(tk.END, "\n\n")
                self.chat_area.see(tk.END)
                self.chat_area.config(state=tk.DISABLED)

        def _prepare_typing_area():
            if not (hasattr(self, 'chat_area') and self.chat_area.winfo_exists()):
                return
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.insert(tk.END, f"{speaker}: ", (f"{speaker}_tag",))
            self.chat_area.config(state=tk.DISABLED)
            self.root.after(0, lambda: _type_char(0))
        self.root.after(0, _prepare_typing_area)

    def start_listening(self):
        """
        Initiates the listening process in a separate thread if not already listening.
        Updates UI for listening state.
        """
        if self.is_listening or self.is_processing_command:
            self.display_message("Lepro", "I'm currently busy. Please wait.")
            return

        self.is_listening = True
        self.speech_button.config(state=tk.DISABLED, text="Listening...", bg="#FFA500") # Orange
        self.send_button.config(state=tk.DISABLED)
        self.text_input.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL) # Enable stop button

        threading.Thread(target=self._listen_for_command, daemon=True).start()

    def _listen_for_command(self):
        """
        Internal method run in a separate thread to handle speech recognition.
        Puts the result into a queue for the main thread to process.
        """
        try:
            query = self.assistant.take_command()
            self.listening_result_queue.put(('success', query))
        except Exception as e:
            self.listening_result_queue.put(('error', str(e)))
        finally:
            self.is_listening = False # Reset flag regardless of outcome

    def _check_listening_queue(self):
        """
        Periodically checks the queue for results from the speech recognition thread.
        This runs on the main Tkinter thread.
        """
        try:
            status, query = self.listening_result_queue.get_nowait()
            if status == 'success':
                if query and query != "None":
                    self.display_message("You", query)
                    # Process the command in another thread
                    self.is_processing_command = True
                    threading.Thread(target=lambda: self._process_command_threaded(query), daemon=True).start()
                else:
                    self.display_message("Lepro", "I didn't quite catch that or listening was stopped. Could you please repeat?")
                    self.reset_buttons()
            elif status == 'error':
                self.display_message("Lepro", f"An error occurred during speech recognition: {query}")
                self.reset_buttons()
        except queue.Empty:
            pass # No results yet, continue checking
        finally:
            # Always schedule the next check
            self.root.after(100, self._check_listening_queue)

    def send_text_command(self, event=None):
        """
        Handles text input commands when 'Send' button is clicked or Enter is pressed.
        """
        if self.is_listening or self.is_processing_command:
            self.display_message("Lepro", "I'm currently busy. Please wait.")
            return

        query = self.text_input.get().strip()
        if query:
            self.display_message("You", query)
            self.text_input.delete(0, tk.END)
            self.speech_button.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.text_input.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL) # Enable stop button

            self.is_processing_command = True
            threading.Thread(target=lambda: self._process_command_threaded(query), daemon=True).start()
        else:
            self.display_message("Lepro", "Please type your command.")

    def _process_command_threaded(self, query):
        """
        Processes the recognized command (voice or text) in a separate thread.
        Puts the completion signal into a queue.
        """
        try:
            self.assistant.run_command(query)
            self.command_processing_queue.put('completed')
        except Exception as e:
            self.command_processing_queue.put(f'error: {e}')
        finally:
            # No need to set is_processing_command = False here, as the queue check handles it
            pass

    def _check_command_processing_queue(self):
        """
        Periodically checks the queue for completion signals from command processing.
        """
        try:
            result = self.command_processing_queue.get_nowait()
            if result == 'completed':
                self.display_message("Lepro", "Command executed.")
            elif result.startswith('error:'):
                error_msg = result[len('error:'):].strip()
                self.display_message("Lepro", f"Error during command execution: {error_msg}")
        except queue.Empty:
            pass
        finally:
            # Regardless of status, if a result was pulled, processing is done
            if not self.listening_result_queue.empty() or not self.command_processing_queue.empty():
                 # Only reset if *both* queues are empty, or after a specific signal
                 # This ensures buttons aren't reset too early
                 pass
            self.root.after(100, self._check_command_processing_queue) # Continue checking

        # If after checking both queues, no new task has started, reset buttons.
        # This logic needs to be careful not to reset while assistant is still speaking.
        # The assistant's speak() method is blocking its own thread, which is why we have to be careful.
        if not self.is_listening and not self.is_processing_command and self.listening_result_queue.empty() and self.command_processing_queue.empty():
            # Add a small delay before resetting to allow final speech to start
            self.root.after(500, self.reset_buttons)


    def stop_current_process(self):
        """
        Interrupts current speech recognition, command processing, or speaking.
        """
        self.display_message("Lepro", "Stopping current operation...")
        if self.is_listening:
            self.assistant.stop_listening() # Signal assistant to stop listening
            self.is_listening = False # Immediately update GUI state
            self.display_message("Lepro", "Listening interrupted.")
        if self.is_processing_command:
            # Signal assistant to stop speaking and check for stop in command logic
            self.assistant.stop_speaking()
            self.is_processing_command = False # Immediately update GUI state
            self.display_message("Lepro", "Command processing interrupted.")
        elif self.assistant.engine.isBusy(): # If just speaking without a command in progress
            self.assistant.stop_speaking()
            self.display_message("Lepro", "Speech interrupted.")

        self.reset_buttons()


    def reset_buttons(self):
        """Resets the state of the buttons and text input."""
        # Only reset if no current operations are active
        if not self.is_listening and not self.is_processing_command:
            if hasattr(self, 'speech_button') and self.speech_button.winfo_exists():
                self.speech_button.config(state=tk.NORMAL, text="Speech", bg="#007bff") # Reset to sea blue
            if hasattr(self, 'send_button') and self.send_button.winfo_exists():
                self.send_button.config(state=tk.NORMAL)
            if hasattr(self, 'text_input') and self.text_input.winfo_exists():
                self.text_input.config(state=tk.NORMAL)
                self.text_input.focus_set()
            if hasattr(self, 'stop_button') and self.stop_button.winfo_exists():
                self.stop_button.config(state=tk.DISABLED) # Disable stop button when idle