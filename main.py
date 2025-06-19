# main.py
import tkinter as tk
from gui import LeproGUI

def main():
    """Starts the chatbot application."""
    root = tk.Tk()
    app = LeproGUI(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say("Starting Lepro")
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[Warning] Could not initialize speech engine: {e}")

    main()
