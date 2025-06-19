import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
from assistant import LeproAssistant

class LeproGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lepro Chatbot")
        self.root.geometry("750x650")
        self.root.resizable(False, False)

        # Main frame with dark grey background
        self.canvas = tk.Canvas(root, bg="#1e1e1e", width=750, height=650, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Chat area
        self.chat_area = scrolledtext.ScrolledText(
            self.canvas, wrap=tk.WORD, font=("Segoe UI", 12),
            bg="#1e1e1e", fg="white", bd=0, padx=15, pady=15,
            relief=tk.FLAT, insertbackground='white',
            selectbackground="#5ce1e6", selectforeground="black"
        )
        self.chat_area.place(relwidth=0.9, relheight=0.6, relx=0.05, rely=0.04)
        self.chat_area.config(state=tk.DISABLED)

        # Tag colors for user and bot messages
        self.chat_area.tag_config("Lepro_tag", foreground="#5ce1e6", font=("Segoe UI", 12, "bold"))
        self.chat_area.tag_config("You_tag", foreground="#a3be8c", font=("Segoe UI", 12, "bold"))

        # Text input field
        self.text_input = tk.Entry(self.canvas, font=("Segoe UI", 12), bg="#2b2b2b", fg="white",
                                   bd=2, relief=tk.FLAT, insertbackground='white')
        self.text_input.place(relwidth=0.65, relheight=0.07, relx=0.05, rely=0.68)

        # Send button (glowing blue style)
        self.send_button = tk.Button(self.canvas, text="Send", font=("Segoe UI", 12, "bold"),
                                     bg="#00bfff", fg="white", activebackground="#00e6e6",
                                     activeforeground="white", relief=tk.FLAT, bd=4)
        self.send_button.place(relx=0.72, rely=0.68, relwidth=0.23, relheight=0.07)

        # Talk button (glowing blue style)
        self.talk_button = tk.Button(self.canvas, text="Talk to Lepro", font=("Segoe UI", 14, "bold"),
                                     bg="#00bfff", fg="white", activebackground="#00e6e6",
                                     activeforeground="white", relief=tk.FLAT, bd=4)
        self.talk_button.place(relx=0.05, rely=0.78, relwidth=0.4, relheight=0.08)

        # Exit button (with red glow on active)
        self.exit_button = tk.Button(self.canvas, text="Exit", font=("Segoe UI", 14, "bold"),
                                     bg="#00bfff", fg="white", activebackground="#cc0000",
                                     activeforeground="white", relief=tk.FLAT, bd=4, command=self.root.quit)
        self.exit_button.place(relx=0.55, rely=0.78, relwidth=0.4, relheight=0.08)

        # Initialize assistant logic with callbacks
        self.assistant = LeproAssistant(display_callback=self.display_message,
                                        typing_callback=self.typing_effect)

        # Event bindings
        self.text_input.bind("<Return>", self.send_text_command)
        self.send_button.config(command=self.send_text_command)
        self.talk_button.config(command=self.start_listening)

        # For listening thread and queue
        self.is_listening = False
        self.listening_result_queue = queue.Queue()

        # Welcome message and listening checker
        self.root.after(300, self._initial_welcome_message)
        self.root.after(400, self._check_listening_queue)

    def _initial_welcome_message(self):
        welcome = self.assistant.get_welcome_message()
        self.typing_effect("Lepro", welcome)
        self.assistant.wish_me_speech()

    def display_message(self, speaker, message):
        def _insert():
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.insert(tk.END, f"{speaker}: ", (f"{speaker}_tag",))
            self.chat_area.insert(tk.END, message + "\n\n")
            self.chat_area.see(tk.END)
            self.chat_area.config(state=tk.DISABLED)
        self.root.after(0, _insert)

    def typing_effect(self, speaker, text, delay=0.02):
        def _type_char(i):
            if i < len(text):
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.insert(tk.END, text[i])
                self.chat_area.see(tk.END)
                self.chat_area.config(state=tk.DISABLED)
                self.root.after(int(delay * 1000), lambda: _type_char(i + 1))
            else:
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.insert(tk.END, "\n\n")
                self.chat_area.config(state=tk.DISABLED)

        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"{speaker}: ", (f"{speaker}_tag",))
        self.chat_area.config(state=tk.DISABLED)
        self.root.after(0, lambda: _type_char(0))

    def send_text_command(self, event=None):
        query = self.text_input.get().strip()
        if query:
            self.display_message("You", query)
            self.text_input.delete(0, tk.END)
            self.disable_inputs()
            threading.Thread(target=lambda: self._process_command_threaded(query), daemon=True).start()
        else:
            self.display_message("Lepro", "Please type your command.")

    def start_listening(self):
        if self.is_listening:
            self.display_message("Lepro", "I'm already listening. Please speak now.")
            return

        self.is_listening = True
        self.disable_inputs()
        self.talk_button.config(text="Listening...")
        threading.Thread(target=self._listen_for_command, daemon=True).start()

    def _listen_for_command(self):
        try:
            query = self.assistant.take_command()
            self.listening_result_queue.put(('success', query))
        except Exception as e:
            self.listening_result_queue.put(('error', str(e)))
        finally:
            self.is_listening = False

    def _check_listening_queue(self):
        try:
            status, query = self.listening_result_queue.get_nowait()
            if status == 'success' and query and query != "None":
                self.display_message("You", query)
                threading.Thread(target=lambda: self._process_command_threaded(query), daemon=True).start()
            elif status == 'error':
                self.display_message("Lepro", f"Error: {query}")
            else:
                self.display_message("Lepro", "Didn't catch that. Please try again.")
        except queue.Empty:
            pass
        self.root.after(100, self._check_listening_queue)

    def _process_command_threaded(self, query):
        try:
            self.assistant.run_command(query)
        except Exception as e:
            self.display_message("Lepro", f"Error: {e}")
        finally:
            self.root.after(0, self.reset_buttons)

    def disable_inputs(self):
        self.talk_button.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.text_input.config(state=tk.DISABLED)

    def reset_buttons(self):
        self.talk_button.config(state=tk.NORMAL, text="Talk to Lepro")
        self.send_button.config(state=tk.NORMAL)
        self.text_input.config(state=tk.NORMAL)
        self.text_input.focus_set()

if __name__ == '__main__':
    root = tk.Tk()
    app = LeproGUI(root)
    root.mainloop()
