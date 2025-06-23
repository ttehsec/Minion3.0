import tkinter as tk
import random
import os
import readline
import base64 
import binascii
import re
import subprocess
from tkinter import messagebox
from tkinter import filedialog
import shlex
import threading
from tkinter import ttk
import sys
import platform
import importlib.util
import signal
import time
from tkinter import messagebox, scrolledtext
import datetime
import psutil
from tkinter import simpledialog
import shutil
from tkinter.scrolledtext import ScrolledText 
import json
import urllib.parse
import codecs




# Global variable to track the running process
current_process = None
smb_process = None
wordlist_process = None
cracking_process = None
cupp_process = None
error_shown = False 
hashid_process = None
hash_identifier_process = None
metadata_process = None
log_analysis_process = None




    
#System and Tools Check


def tool_exists(tool_name):
    """Verifies if the tool is installed by checking its system path"""
    result = subprocess.run(["which", tool_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return bool(result.stdout.strip())  # Returns True if path is found

def check_system():
    """Silently verifies Python version, required tools, essential packages, and system updates"""

    # Step 1: Verify Python Version
    required_python = (3, 6)  # Minimum required version
    current_python = sys.version_info[:2]

    if current_python < required_python:
        return f"❌ Python {required_python[0]}.{required_python[1]} or higher is required. Detected: Python {current_python[0]}.{current_python[1]}"

    # Step 2: Check Required Tools
    required_tools = ["john", "hydra", "crackmapexec", "hashcat", "cupp"]
    missing_tools = [tool for tool in required_tools if not tool_exists(tool)]

    if missing_tools:
        return f"❌ Missing tools: {', '.join(missing_tools)}. Ensure they are installed and accessible from the system PATH."

    # Step 3: Check Essential Python Packages
    required_packages = ["tkinter", "subprocess"]
    missing_packages = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]

    if missing_packages:
        return f"❌ Missing Python packages: {', '.join(missing_packages)}. Install them using `pip install <package>`."

    # Step 4: Verify Tool Versions (silent check)
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except FileNotFoundError:
            return f"❌ {tool} is missing. Install it before running the program."

    return None  # No issues detected, program can run


def autocomplete_path(event):
    """Suggests file paths when user types and presses Tab"""
    typed_text = tool_option_entry.get()

    # Split into directory and partial filename
    directory, partial = os.path.split(typed_text)
    directory = directory if directory else "."  # Default to current directory

    try:
        files = os.listdir(directory)  # Get directory files
        matches = [os.path.join(directory, f) for f in files if f.startswith(partial)]  # Filter by typed text

        if matches:
            tool_option_entry.delete(0, tk.END)
            tool_option_entry.insert(tk.END, matches[0])  # Insert first match
    except FileNotFoundError:
        pass  # Ignore missing directories




#****Logging, Reporting, and Notes****


LOG_FILE = "minion_command_log.txt"  # Define log file
SESSION_FILE = "last_session.txt"  # File to store session name
ARCHIVE_DIR = "archived_logs"  # Folder to move old logs

log_enabled = False  # Default: Logging disabled
session_name = ""  # Global session name variable
ARCHIVE_SESSION_DIR = "archived_sessions"  # Folder for backed-up logs
NOTES_FILE = "user_notes.txt"


def ask_logging_preference():
    """Ask user if they want to enable command logging and allow continuing a previous session."""
    global log_enabled, session_name

    response = messagebox.askyesno("Minion Logging", "Would you like Minion to log all executed commands?")
    log_enabled = response  # Store user preference

    previous_session_name = load_previous_session()  # Store previous session name before changing it

    if log_enabled:
        session_name = previous_session_name if previous_session_name else "Unnamed Session"

        if previous_session_name:
            continue_session = messagebox.askyesno("Previous Session Found", f"Would you like to continue session '{previous_session_name}'?")
            if not continue_session:
                session_name = simpledialog.askstring("Session Name", "Enter a new session name:")
                if not session_name:  # ✅ Prevents `None` values
                    session_name = "Unnamed Session"

                # ✅ Ensure `previous_session_name` is valid before calling clear_log()
                if previous_session_name:
                    clear_log(previous_session_name)  # ✅ Only called if valid

                save_session_name(session_name)  # Save new session name
        else:
            session_name = simpledialog.askstring("Session Name", "Enter a session name for this logging session:")
            if not session_name:  # ✅ Prevents `None` values
                session_name = "Unnamed Session"

            # ✅ Ensure `previous_session_name` is valid before calling clear_log()
            if previous_session_name:
                clear_log(previous_session_name)  # ✅ Only called if valid

            save_session_name(session_name)  # Save new session name

        with open(LOG_FILE, "a") as log:
            log.write(f"\n==== Minion Session '{session_name}' Started ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ====\n")


def save_session_name(session_name):
    """Stores the current session name to a file safely."""
    if session_name is None:
        session_name = "Unnamed Session"  #  Prevent `None` from being saved

    with open(SESSION_FILE, "w") as file:
        file.write(session_name)



def load_previous_session():
    """Retrieves the last used session name if available."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as file:
            return file.read().strip()
    return None


def log_command(command):
    """Logs executed commands without printing to the terminal."""
    if log_enabled:
        if not command or command.strip() == "None":
            return  # Prevent logging empty or None values

        exclude_list = ["run_hydra", "run_hashcat", "run_crackmap", "run_john"]
        if command in exclude_list:
            return  # Skip logging for unwanted commands

        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log_entry = f"{timestamp} [Session: {session_name}] {command}\n"

        with open(LOG_FILE, "a") as log:
            log.write(log_entry)
            log.flush()
            os.fsync(log.fileno())

        # Remove print statement to prevent logging in terminal
        # print(f"📝 Logged Command: {command}")  # ❌ Commented out



def view_log():
    """Displays a scrollable window with all logged commands, allowing users to search for specific commands."""
    log_window = tk.Toplevel(root)
    log_window.title("Command Log")
    log_window.attributes('-topmost', True)  # Bring window to front

    # Label for dropdown
    dropdown_label = tk.Label(log_window, text="📂 Select an archived session log to view:")
    dropdown_label.pack()

    # Create a dropdown menu for archived logs (Ensuring no errors if empty)
    archive_list = get_archived_sessions()
    selected_archive = tk.StringVar()
    selected_archive.set("Choose a session" if archive_list else "No archives found")

    dropdown = tk.OptionMenu(log_window, selected_archive, selected_archive.get(), *archive_list)
    dropdown.pack(pady=5)

    # Search bar setup
    search_label = tk.Label(log_window, text="🔍 Search for a command:")
    search_label.pack()
    search_entry = tk.Entry(log_window)
    search_entry.pack(pady=5)
    search_button = tk.Button(log_window, text="Search", command=lambda: search_logs(log_text, search_entry.get()))
    search_button.pack(pady=5)

    # Scrollable log text box
    log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, width=80, height=25)
    log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Function to load the latest log file
    def load_current_log():
        """Refreshes the current session log before displaying."""
        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("Log Viewer", "⚠ No log file found. Logging may be disabled.")
            return
        with open(LOG_FILE, "r") as log:
            log_text.config(state=tk.NORMAL)
            log_text.delete("1.0", tk.END)
            log_text.insert(tk.END, log.read())
            log_text.config(state=tk.DISABLED)  

    # Function to load selected archived session log
    def load_selected_log():
        archive_name = selected_archive.get()
        if archive_name and archive_name not in ["Choose a session", "No archives found"]:
            archive_path = os.path.join(ARCHIVE_SESSION_DIR, archive_name)
            if os.path.exists(archive_path):
                with open(archive_path, "r") as log:
                    log_text.config(state=tk.NORMAL)
                    log_text.delete("1.0", tk.END)
                    log_text.insert(tk.END, log.read())
                    log_text.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Error", "⚠ Selected archive file does not exist.")

    # ✅ Display latest log on startup
    load_current_log()

    # ✅ Buttons with clear labels
    load_current_button = tk.Button(log_window, text="🔍 View Current Session Log", command=load_current_log)
    load_current_button.pack(pady=5)

    load_archive_button = tk.Button(log_window, text="📂 Load Archived Log", command=load_selected_log)
    load_archive_button.pack(pady=5)




def search_logs(log_widget, keyword):
    """Search for a specific command in the displayed log."""
    log_text = log_widget.get("1.0", tk.END)  # Get full log content
    results = [line for line in log_text.split("\n") if keyword.lower() in line.lower()]

    # Show results or notify user if no matches
    log_widget.config(state=tk.NORMAL)
    log_widget.delete("1.0", tk.END)
    if results:
        log_widget.insert(tk.END, "\n".join(results))
    else:
        log_widget.insert(tk.END, "⚠ No matching commands found.")
    log_widget.config(state=tk.DISABLED)




# Define Cleared Logs Directory
CLEARED_LOGS_DIR = "cleared_logs"
os.makedirs(CLEARED_LOGS_DIR, exist_ok=True)  # Ensure folder exists

def clear_log(previous_session_name="default_session"):
    """Moves cleared logs to the correct archive directory instead of cleared_logs."""

    if not os.path.exists(LOG_FILE):
        messagebox.showinfo("Clear Log", "⚠ No log file found.")
        return

    # Ensure archive directory exists
    if not os.path.exists(ARCHIVE_SESSION_DIR):
        os.makedirs(ARCHIVE_SESSION_DIR)

    # Move existing log to ARCHIVE_SESSION_DIR (correct folder)
    backup_name = f"session_{previous_session_name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    backup_path = os.path.join(ARCHIVE_SESSION_DIR, backup_name)  # Store in the correct archive folder

    shutil.move(LOG_FILE, backup_path)
    messagebox.showinfo("Logs Archived", f"✅ Session log moved to: {backup_path}")

    # Create a fresh new log file after clearing
    with open(LOG_FILE, "w") as log:
        log.write(f"\n==== Minion Session '{previous_session_name}' Started ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ====\n")



def archive_old_logs():
    """Moves logs older than 7 days to the 'archived_logs' folder instead of deleting them."""
    if not os.path.exists(LOG_FILE):
        messagebox.showinfo("Archive Logs", "⚠ No log file found.")
        return

    # Ensure archive directory exists
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

    # Check last modified date
    file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
    days_old = (datetime.datetime.now() - file_mod_time).days

    if days_old >= 7:  # Archive logs older than 7 days
        archive_path = os.path.join(ARCHIVE_DIR, f"archived_log_{file_mod_time.strftime('%Y-%m-%d')}.txt")
        shutil.move(LOG_FILE, archive_path)
        messagebox.showinfo("Logs Archived", f"✅ Log file moved to archive: {archive_path}")

    else:
        messagebox.showinfo("Archive Logs", "✅ No logs older than 7 days detected.")

def get_archived_sessions():
    """Retrieves archived session logs from the archive folder."""
    if not os.path.exists(ARCHIVE_SESSION_DIR):
        os.makedirs(ARCHIVE_SESSION_DIR)  # Create archive folder if missing
        return []

    return sorted([f for f in os.listdir(ARCHIVE_SESSION_DIR) if f.startswith("session_")])


# Initialize Logging Setup
ask_logging_preference()  # Prompt user for logging preferences upon startup



# Define Notes Directory
NOTES_DIR = "saved_notes"
os.makedirs(NOTES_DIR, exist_ok=True)  # Ensures the folder exists

def view_notes():
    """Displays a window where users can edit and save the current note instead of creating a new one."""
    notes_window = tk.Toplevel(root)
    notes_window.title("User Notes")
    notes_window.attributes('-topmost', True)

    tk.Label(notes_window, text="📝 Minion Notes:", font=("Arial", 12, "bold"), fg="white", bg="#0A192F").pack(pady=5)

    # Dropdown to Select a Saved Note
    tk.Label(notes_window, text="📂 Select a note to edit:", fg="white", bg="#0A192F").pack()
    
    saved_notes = os.listdir(NOTES_DIR)  # List existing notes
    selected_note = tk.StringVar()
    selected_note.set("Choose a note")

    dropdown = tk.OptionMenu(notes_window, selected_note, "Choose a note", *saved_notes)
    dropdown.pack(pady=5)

    # Search Bar Setup Inside Notes Window
    search_label = tk.Label(notes_window, text="🔍 Search Notes:", fg="white", bg="#0A192F")
    search_label.pack()

    search_entry = tk.Entry(notes_window)
    search_entry.pack(pady=5)

    search_button = tk.Button(notes_window, text="Search", command=lambda: search_notes(notes_text, search_entry.get(), notes_text.get("1.0", tk.END)), bg="#1565C0", fg="white")
    search_button.pack(pady=5)


    # Scrollable Notes Entry Box
    notes_text = ScrolledText(notes_window, wrap=tk.WORD, width=80, height=25, bg="#333333", fg="white", font=("Courier", 12))
    notes_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Function to Load Selected Note
    def load_note():
        note_name = selected_note.get()
        if note_name and note_name != "Choose a note":
            with open(os.path.join(NOTES_DIR, note_name), "r") as file:
                notes_text.delete("1.0", tk.END)
                notes_text.insert("1.0", file.read())
            current_file.set(note_name)  # Tracks the current note file

    # Track Current File (Default None)
    current_file = tk.StringVar()
    current_file.set("")

    #  Function to Save Changes to Current Note
    def save_note():
        """Saves changes to the current note instead of creating a new file."""
        note_name = current_file.get()

        # Ensure user selects or names a note
        if not note_name or note_name == "":
            note_name = simpledialog.askstring("Save Note", "Enter a name for this note:", parent=notes_window)
            if not note_name:
                return

        # Ensure '.txt' is only added once
        if not note_name.endswith(".txt"):
            note_name += ".txt"

        file_path = os.path.join(NOTES_DIR, note_name)

        # Overwrite existing file instead of creating new
        with open(file_path, "w") as file:
            file.write(notes_text.get("1.0", tk.END).strip())

        current_file.set(note_name)  # Keeps track of the active note

        # Ensure dropdown updates properly
        if note_name not in saved_notes:
            saved_notes.append(note_name)
            dropdown["menu"].add_command(label=note_name, command=lambda: selected_note.set(note_name))

        messagebox.showinfo("Notes Saved", f"✅ '{note_name}' has been updated!", parent=notes_window)

    def search_notes(notes_widget, keyword, full_text):
        """Search for a specific word or phrase without losing the full note."""
        notes_widget.config(state=tk.NORMAL)
        notes_widget.delete("1.0", tk.END)  # Reset notes view before searching
        notes_widget.insert("1.0", full_text)  # Restore full text first

        # Highlight matching words instead of deleting text
        if keyword:
            start_index = "1.0"
            while True:
                start_index = notes_widget.search(keyword, start_index, stopindex=tk.END, nocase=True)
                if not start_index:
                    break
                end_index = f"{start_index}+{len(keyword)}c"
                notes_widget.tag_add("highlight", start_index, end_index)
                notes_widget.tag_config("highlight", background="yellow", foreground="black")
                start_index = end_index

        # Keep window visible after saving
        notes_window.lift()
        notes_window.focus_force()

    #Buttons for Loading & Saving Notes
    button_frame = tk.Frame(notes_window)
    button_frame.pack(pady=5)

    tk.Button(button_frame, text="📂 Load Note", command=load_note, width=10, height=2, bg="#3E3E3E", fg="white").pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="💾 Save Note", command=save_note, width=10, height=2, bg="#1565C0", fg="white").pack(side=tk.LEFT, padx=5)



#***Cheat Sheet Function****

# Define Cheat Sheet Directory
CHEAT_SHEET_FILE = "cheatsheet.json"  # External file storage
if not os.path.exists(CHEAT_SHEET_FILE):
    with open(CHEAT_SHEET_FILE, "w") as f:
        json.dump({}, f)  # Creates an empty cheat sheet file if missing

def load_cheat_sheet():
    """Loads cheat sheet data from JSON file."""
    try:
        with open(CHEAT_SHEET_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}  # Prevent crashes if the file is malformed

def open_cheat_sheet():
    """Opens a Cheat Sheet window for users to browse, search, and select categories."""
    cheat_sheet_window = tk.Toplevel(root)
    cheat_sheet_window.title("Cheat Sheet")
    cheat_sheet_window.attributes('-topmost', True)

    tk.Label(cheat_sheet_window, text="📖 Minion Cheat Sheet:", font=("Arial", 12, "bold"), fg="white", bg="#0A192F").pack(pady=5)

    # Dropdown to Select Cheat Sheet Category
    cheat_data = load_cheat_sheet()
    categories = list(cheat_data.keys())

    selected_category = tk.StringVar()
    selected_category.set("Choose a category")

    dropdown = tk.OptionMenu(cheat_sheet_window, selected_category, "Choose a category", *categories)
    dropdown.pack(pady=5)

    # Search Bar
    tk.Label(cheat_sheet_window, text="🔍 Search Cheat Sheet:", fg="white", bg="#0A192F").pack()
    search_entry = tk.Entry(cheat_sheet_window)
    search_entry.pack(pady=5)

    search_button = tk.Button(cheat_sheet_window, text="Search", command=lambda: search_cheat_sheet(cheat_text, search_entry.get(), cheat_data), bg="#1565C0", fg="white")
    search_button.pack(pady=5)

    # Scrollable Cheat Sheet Text Box
    cheat_text = ScrolledText(cheat_sheet_window, wrap=tk.WORD, width=80, height=25, bg="#333333", fg="white", font=("Courier", 12))
    cheat_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    tk.Button(cheat_sheet_window, text="📂 Show Category", 
          command=lambda: display_cheat_sheet(cheat_text, selected_category.get(), cheat_data),
          width=15, bg="#2196F3", fg="white").pack(pady=5)


    
    def display_cheat_sheet(widget, category, data):
        """Displays commands under the selected category in a structured format."""
        widget.delete("1.0", tk.END)

        # Ensure category exists
        if category in data:
            widget.insert(tk.END, f"📂 {category}\n")  # Display category heading
            for command, description in data[category].items():
                widget.insert(tk.END, f"  🔹 {command}: {description}\n")  # Proper indentation
            widget.insert(tk.END, "\n")  # Space after category
        else:
            widget.insert(tk.END, "⚠ No category selected or invalid category.\n")

        # Apply formatting for readability
        widget.tag_config("category", font=("Arial", 11, "bold"))




    def search_cheat_sheet(widget, query, data):
        """Searches for commands inside cheat sheet and groups results by category."""
        widget.delete("1.0", tk.END)
        found = False

        for category, commands in data.items():
            # Collect matching commands within the category
            category_matches = [f"  🔹 {cmd}: {desc}" for cmd, desc in commands.items() if query.lower() in cmd.lower() or query.lower() in desc.lower()]

            if category_matches:
                widget.insert(tk.END, f"📂 {category}\n")  # Display category only once
                widget.insert(tk.END, "\n".join(category_matches) + "\n\n")  # Display matching commands with spacing
                found = True

        if not found:
            widget.insert(tk.END, "⚠ No matching results found.\n")

        # Apply basic formatting for readability
        widget.tag_config("category", font=("Arial", 11, "bold"))





    def clear_cheat_sheet():
        """Resets cheat sheet view to default."""
        cheat_text.delete("1.0", tk.END)
        search_entry.delete(0, tk.END)

    # Buttons for Functionality
    button_frame = tk.Frame(cheat_sheet_window)
    button_frame.pack(pady=5)

    
    tk.Button(button_frame, text="❌ Clear", command=clear_cheat_sheet, width=10, bg="#B71C1C", fg="white").pack(side=tk.LEFT, padx=5)





#*****Terminal Function****

def open_terminal():
    """Opens an interactive shell while reminding users to close it properly."""
    
    # ✅ Show pop-up alert before launching terminal
    messagebox.showinfo(
        "Closing Terminal",
        "⚠️ Reminder: Please type 'exit' instead of clicking 'X' to close the terminal to avoid errors."
    )

    # ✅ Ensure proper cleanup setup
    if os.name != "nt":  # Linux/macOS
        os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
        subprocess.Popen(["x-terminal-emulator"], start_new_session=True)
    else:  # Windows
        subprocess.Popen(["cmd.exe"], shell=True, start_new_session=True)



    def execute_command():
        """Runs commands inside a separate subprocess."""
        command = command_entry.get().strip()
        if not command:
            terminal_output.insert(tk.END, "⚠ No command entered.\n")
            terminal_output.update()
            return

        terminal_output.insert(tk.END, f"$ {command}\n")
        terminal_output.update()
        command_entry.delete(0, tk.END)  # ✅ Clears input after execution

        def run_cmd():
            try:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for line in iter(process.stdout.readline, ''):
                    terminal_output.insert(tk.END, line)
                    terminal_output.update()
                process.stdout.close()
                process.wait()
            except Exception as e:
                terminal_output.insert(tk.END, f"⚠ Error: {str(e)}\n")
                terminal_output.update()

        # ✅ Run command asynchronously to prevent GUI freezing
        threading.Thread(target=run_cmd, daemon=True).start()

    # ✅ Bind "Enter" key to execute commands
    #command_entry.bind("<Return>", lambda event: execute_command())




#****NMAP Function****
         

def run_command(command):
    """Execute command with progress tracking and dynamic time estimation."""
    global current_process, progress_var

    log_command(command)
    nmap_clear_output()
    nmap_output_text.insert(tk.END, f"Running: {command}\n\n")
    nmap_output_text.update()

    estimated_time = estimate_scan_time(command)  # Get estimated time dynamically

    try:
        current_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        # Pass `command` when starting progress tracking thread
        threading.Thread(target=nmap_update_progress_tracker, args=(command, estimated_time), daemon=True).start()

        # Start output streaming
        threading.Thread(target=stream_command_output, args=(current_process,), daemon=True).start()

    except Exception as e:
        nmap_output_text.insert(tk.END, f"Error: {str(e)}\n")



def nmap_update_progress_tracker(command, estimated_time):
    """Tracks Nmap scan progress dynamically and stops precisely when the scan completes."""
    global current_process

    if not current_process:  # Prevent 'NoneType' errors
        return  

    start_time = time.time()  # Capture scan start time
    progress_samples = []  # Store elapsed times for dynamic adjustment

    while current_process and current_process.poll() is None:  # Ensure current_process is valid before polling
        elapsed_time = time.time() - start_time

        # Dynamically refine estimated time based on scan speed
        if elapsed_time > 5:
            progress_samples.append(elapsed_time)
            estimated_time = max(refine_estimated_time(progress_samples, command), elapsed_time)  # Avoid underestimation

        remaining_time = max(estimated_time - elapsed_time, 0)  # Prevent negative countdown
        progress = min(int((elapsed_time / estimated_time) * 100), 100)  #Keep progress within 100%

        progress_var.set(progress)

        if progress_bar:
            progress_bar.update_idletasks()

        '''#Overwrite previous progress message
        nmap_output_text.delete("end-2l", "end")
        nmap_output_text.insert(tk.END, f"\n⏳ Progress: {progress}% completed... ({int(remaining_time // 60)}m {int(remaining_time % 60)}s left)")'''
        nmap_output_text.update_idletasks()

        time.sleep(5)  # Adjust update speed based on scan response

    # Ensure tracker stops *exactly* when Nmap finishes
    if current_process:  # Avoid calling `.wait()` on `NoneType`
        current_process.wait()

    progress_var.set(100)
    nmap_output_text.insert(tk.END, "\n✅ Scan completed!\n")
    nmap_output_text.update_idletasks()



def estimate_scan_time(command):
    """Estimates scan time dynamically based on Nmap scan type and speed (-T1 to -T5)."""
    base_time = 15  # Base estimate for simple scans

    # Adjust based on scan options
    if "-p-" in command:  # Scanning all ports
        base_time += 20
    if "-A" in command or "-sC" in command or "-sV" in command:  # Aggressive & script scanning
        base_time += 30

    # Adjust based on scan speed (`-T1` to `-T5`)
    if "-T1" in command:  # 🐢 Very slow (stealthy)
        base_time *= 2.5
    elif "-T2" in command:  # 🐌 Slow
        base_time *= 1.8
    elif "-T3" in command:  # ⚡ Normal
        base_time *= 1.2
    elif "-T4" in command:  # 🚀 Fast
        base_time *= 0.8
    elif "-T5" in command:  # 🔥 Very fast
        base_time *= 0.5

    return max(base_time, 5)  # Ensure a reasonable minimum time


def refine_estimated_time(progress_samples, command):
    """Refines estimated scan time based on real-time response speed and scan type."""
    avg_time = sum(progress_samples) / len(progress_samples) if progress_samples else 10  # Average speed

    # Modify estimate further based on scan complexity
    scan_factor = estimate_scan_time(command) / 30  # Normalize against base timing
    refined_time = avg_time * scan_factor

    return max(refined_time, 5)  # Ensure reasonable time


def nmap_cancel_scan():
    """Stops the scan if the user clicks cancel."""
    global current_process
    if current_process:
        current_process.kill()  #Forcefully stop the process
        current_process = None
        progress_var.set(0)
        nmap_output_text.insert(tk.END, "\n❌ Scan canceled.\n")
        nmap_output_text.update_idletasks()



def stream_command_output(process):
    """Reads process output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        nmap_output_text.insert(tk.END, line)
        nmap_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Scan Complete", "✅ Nmap scan finished successfully!")
    progress_var.set(100)  # Set progress bar to complete



def nmap_clear_output():
    """ Clear scan results """
    nmap_output_text.delete("1.0", tk.END)
    nmap_manual_entry.delete(0, tk.END)  # Clear manual command input
    nmap_ip_entry.delete(0, tk.END)  # Clear IP input
    
def run_manual_scan():
    """ Execute custom Nmap command from user input """
    nmap_custom_command = nmap_manual_entry.get().strip()
    if not nmap_custom_command:
        messagebox.showwarning("Invalid Input", "Please enter a valid Nmap command.")
        return
    run_command(nmap_custom_command)


# *****SMB Functions*****

def run_smb(command, full_enum=False):
    """Runs SMB commands while showing a warning only for full enumeration scans."""
    global smb_process

    if full_enum:
        continue_scan = messagebox.askyesno(
            "Full Enumeration Warning",
            "⚠️ This scan may take a while. Please allow it to complete before continuing.\n\n"
            "Estimated scan time: **5-10 minutes** (depending on target size).\n\n"
            "You will be notified once the scan is finished.\n\n"
            "Do you want to proceed?"
        )

        if not continue_scan:
            messagebox.showinfo("Scan Canceled", "The SMB enumeration scan was canceled.")
            return

    log_command(command)
    smb_output_text.delete("1.0", tk.END)
    smb_output_text.insert(tk.END, f"Running: {command}\n\n")
    smb_output_text.update()

    try:
        smb_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # Start progress tracking in a separate thread
        threading.Thread(target=smb_update_progress_tracker, daemon=True).start()

        # Stream output without blocking
        threading.Thread(target=stream_smb_output, args=(smb_process,), daemon=True).start()

    except Exception as e:
        smb_output_text.insert(tk.END, f"Error: {str(e)}\n")


stop_event = threading.Event()  # Global stop event

def smb_update_progress_tracker():
    """Tracks scan progress but stops immediately if scan is completed or canceled."""
    estimated_time = 600  # Approx 10 minutes
    interval = estimated_time // 10  # Update every 60 seconds

    for i in range(10):
        if stop_event.is_set() or smb_process is None:  # Stop if scan finishes
            smb_output_text.insert(tk.END, "\n⏳ Scan progress has been forcibly halted.\n")
            smb_output_text.update_idletasks()
            return  # Exit loop when process ends

        time.sleep(interval)
        smb_output_text.insert(tk.END, f"\n⏳ Progress: {((i+1)*10)}% completed...\n")
        smb_output_text.update_idletasks()

    smb_output_text.insert(tk.END, "\n✅ Scan nearing completion...\n")
    smb_output_text.update_idletasks()


def stream_smb_output(process):
    """Reads and updates SMB output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        smb_output_text.insert(tk.END, line)
        smb_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Scan Complete", "✅ SMB enumeration scan finished successfully!")


'''def smb_manual_scan():
    """ Execute custom Nmap command from user input """
    smb_custom_command = smb_manual_entry.get().strip()
    if not smb_custom_command:
        messagebox.showwarning("Invalid Input", "Please enter a valid SMB command.")
        return
    run_smb(smb_custom_command)'''

def smb_clear_output():
    """ Clear scan results """
    smb_output_text.delete("1.0", tk.END)
    smb_ip_entry.delete(0, tk.END) 
    smb_share_entry.delete(0, tk.END) 
    smb_user_entry.delete(0, tk.END) 
    smb_pass_entry.delete(0, tk.END) 
    smb_command_entry.delete(0, tk.END) 


def connect_smb():
    """Runs custom SMB commands entered by the user."""
    smb_ip = smb_ip_entry.get().strip()
    smb_share = smb_share_entry.get().strip()
    smb_user = smb_user_entry.get().strip()
    smb_pass = smb_pass_entry.get().strip()

    # Validate user input fields (Ensuring IP & Share are provided)
    if not smb_ip or not smb_share or not smb_user:
        messagebox.showwarning("Missing Input", "Please fill IP, Share, and User before connecting.")
        return

    # Validate custom command entry
    try:
        smb_command = smb_command_entry.get().strip()
    except NameError:
        messagebox.showerror("Error", "Custom SMB command entry is missing from the GUI.")
        return

    # Execute SMB command (Switch to --no-pass if password is missing)
    if smb_pass:
        command_to_run = f"smbclient -N -U '{smb_user}%{smb_pass}' //{smb_ip}/{smb_share} -c '{smb_command if smb_command else 'ls'}'"
    else:
        command_to_run = f"smbclient --no-pass //{smb_ip}/{smb_share} -c '{smb_command if smb_command else 'ls'}'"

    run_smb(command_to_run)  # Execute the command via SMB handler


def smbmap_connect_smb():
    """ Runs custom SMB commands entered by the user """
    smb_ip = smb_ip_entry.get().strip()
    smb_share = smb_share_entry.get().strip()
    smb_user = smb_user_entry.get().strip()
    smb_pass = smb_pass_entry.get().strip()
    
    # Validate user input fields
    if not smb_ip:
        messagebox.showwarning("Missing Input", "Please fill Target IP before connecting.")
        return

    # Validate custom command entry
    try:
        smb_command = smb_command_entry.get().strip()
    except NameError:
        messagebox.showerror("Error", "Custom SMB command entry is missing from the GUI.")
        return

    # Execute the custom command or default to 'ls'
    command_to_run = f"smbmap -H {smb_ip}"

    run_smb(command_to_run)  # Pass command to output handler


def smb_run_custom_command():
    """Runs the user-defined SMB command with live output streaming."""

    # Retrieve SMB command from user input
    custom_command = smb_command_entry.get().strip()

    # Ensure the command exists before proceeding
    if not custom_command:
        messagebox.showwarning("Missing Input", "Please enter a command to run.")
        return

    # Define `command` before logging
    command = custom_command  # Set `command` as the user-inputted SMB command
    log_command(command)  # ✅ Now it won't throw a NameError

    global smb_process
    smb_output_text.delete("1.0", tk.END)
    smb_output_text.insert(tk.END, f"Running: {command}\n\n")
    smb_output_text.update()

    try:
        # Start process with real-time output handling
        smb_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        # Read output line by line **without freezing**
        for line in smb_process.stdout:
            smb_output_text.insert(tk.END, line)
            smb_output_text.update()  # Keeps the GUI responsive

        smb_process.stdout.close()
        smb_process.wait()
        smb_process = None  # Reset after completion

        messagebox.showinfo("Scan Complete", "SMB command executed successfully!")

    except Exception as e:
        smb_output_text.insert(tk.END, f"Error: {str(e)}\n")



def smb_connect_cme():
    """Runs CrackMapExec SMB scan and streams output into the GUI."""
    smb_ip = smb_ip_entry.get().strip()
    smb_user = smb_user_entry.get().strip()
    smb_pass = smb_pass_entry.get().strip()

    # Validate user input fields
    if not smb_ip or not smb_user or not smb_pass:
        messagebox.showwarning("Missing Input", "Please enter SMB IP, username, and password.")
        return

    # Handle password formatting dynamically
    password_wrapper = '"' if all(c.isalnum() for c in smb_pass) else "'"
    formatted_password = f"{password_wrapper}{smb_pass}{password_wrapper}"

    # Construct CrackMapExec command
    command_to_run = f'crackmapexec smb {smb_ip} -u "{smb_user}" -p {formatted_password} --shares'

    run_smb(command_to_run)  # Pass command to the SMB execution function


def smb_cancel_scan():
    """Stops SMB scan and ensures background progress tracking stops immediately."""
    global smb_process

    if smb_process:
        smb_output_text.insert(tk.END, "\n❌ SMB scan canceled.\n")
        smb_output_text.update_idletasks()

        try:
            smb_process.send_signal(signal.SIGINT)  # Send Ctrl+C first
            smb_process.terminate()
            smb_process.kill()  # Force stop process
        except Exception as e:
            smb_output_text.insert(tk.END, f"\n⚠️ Error stopping process: {str(e)}\n")

        smb_process = None  

    # Stop progress tracking immediately
    stop_event.set()  # ✅ Stop all active tracking threads

    smb_output_text.insert(tk.END, "\n✅ Scan progress fully halted.\n")
    smb_output_text.update_idletasks()



def stop_smb_progress():
    """Completely halts scan progress updates by force-stopping background threads."""
    global smb_process

    smb_process = None  # Reset process tracking
    smb_output_text.delete("1.0", tk.END)  # Clear progress updates
    smb_output_text.insert(tk.END, "\n⏳.\n")
    smb_output_text.update_idletasks()

    # Stop all active threads running progress updates
    for thread in threading.enumerate():
        if "smb_update_progress_tracker" in thread.name:
            thread._stop()


def monitor_smb_processes():
    """Checks if any SMB-related or Enum4Linux processes are still running and displays them."""
    active_processes = [proc.info for proc in psutil.process_iter(attrs=["pid", "name"]) if "enum4linux" in proc.info["name"]]

    if active_processes:
        smb_output_text.insert(tk.END, "\n⚠️ Active SMB processes detected:\n")
        for proc in active_processes:
            smb_output_text.insert(tk.END, f"🔍 PID: {proc['pid']} | Process: {proc['name']}\n")
        smb_output_text.insert(tk.END, "\nYou can manually terminate these processes if needed.\n")
    else:
        smb_output_text.insert(tk.END, "\n✅ No active SMB-related processes detected.\n")

    smb_output_text.update_idletasks()

def cleanup_smb_processes():
    """Automatically removes any remaining Enum4Linux processes after cancellation."""
    remaining_processes = [proc.info["pid"] for proc in psutil.process_iter(attrs=["pid", "name"]) if "enum4linux" in proc.info["name"]]

    if remaining_processes:
        smb_output_text.insert(tk.END, "\n⚠️ Some Enum4Linux processes are still running. Attempting cleanup...\n")
        smb_output_text.update_idletasks()
        
        for pid in remaining_processes:
            psutil.Process(pid).kill()  # Force terminate

        smb_output_text.insert(tk.END, "\n✅ Cleanup complete! All lingering processes have been terminated.\n")
    else:
        smb_output_text.insert(tk.END, "\n✅ No remaining processes detected.\n")

    smb_output_text.update_idletasks()
    


# *****Gobuster Functions*****

def gobuster_select_wordlist(entry_widget):
    """ Opens file browser to select a wordlist for Gobuster """
    file_path = filedialog.askopenfilename(
        title="Select Gobuster Wordlist",
        filetypes=[("Wordlist Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)

def run_gobuster():
    """Executes Gobuster with correct flags, ensuring proper port and protocol selection."""
    
    # Get user inputs
    target = gobuster_ip_entry.get().strip()
    wordlist = gobuster_wordlist_entry.get().strip()
    mode = gobuster_mode_entry.get().strip().lower()
    threads = gobuster_threads_entry.get().strip()
    output_file = gobuster_output_entry.get().strip()
    port = gobuster_port_entry.get().strip()
    protocol = gobuster_protocol_entry.get().strip().lower()

    # Validate mode
    if not target or not wordlist or mode not in ["dir", "dns", "s3", "gcs", "vhost", "fuzz", "tftp"]:
        messagebox.showerror("Input Error", "⚠ Missing Target, Wordlist, or Mode (Must be dir, dns, s3, etc.).")
        return  

    # Validate protocol selection for directory mode
    if mode == "dir" and protocol not in ["http", "https"]:
        messagebox.showerror("Input Error", "⚠ For 'dir' mode, specify either http or https.")
        return

    global current_process
    if current_process:
        current_process.terminate()
        current_process = None

    # ✅ Use `-d` for DNS mode, otherwise use `-u` with protocol & port
    if mode == "dns":
        cmd = f"gobuster {mode} -d {target} -w {wordlist}"
    else:
        port_option = f":{port}" if port else ""
        cmd = f"gobuster {mode} -u {protocol}://{target}{port_option}/ -w {wordlist}"

    if threads:
        cmd += f" -t {threads}"
    if output_file:
        cmd += f" -o {output_file}"

    gobuster_output_text.delete("1.0", tk.END)
    gobuster_output_text.insert(tk.END, f"Running: {cmd}\n\n")
    gobuster_output_text.update()

    try:
        current_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        threading.Thread(target=gobuster_stream_command_output, args=(current_process,), daemon=True).start()
        threading.Thread(target=gobuster_update_progress, args=(current_process,), daemon=True).start()  # ✅ Start progress tracker

    except Exception as e:
        gobuster_output_text.insert(tk.END, f"Error: {str(e)}\n")

def gobuster_update_progress(process):
    """Tracks Gobuster scan progress dynamically."""
    while process.poll() is None:  # Ensure process is still running
        line = process.stdout.readline()
        if not line:
            break  # Stop reading if stream is empty

        if "Progress:" in line:
            progress_percent = extract_progress(line)
            progress_var.set(progress_percent)

        gobuster_output_text.insert(tk.END, line)
        gobuster_output_text.update_idletasks()

        time.sleep(2)  # Adjust update interval for smooth tracking

    process.stdout.close()
    process.wait()
    progress_var.set(100)  #  Ensure progress hits 100% when scan completes


def extract_progress(line):
    """Extracts progress percentage from Gobuster output."""
    parts = line.split("Progress: ")
    if len(parts) > 1:
        progress_info = parts[1].split(" ")[0]  # Extract numeric percentage
        try:
            return int(float(progress_info.replace("%", "")))  # Convert percentage
        except ValueError:
            return 0
    return 0

def gobuster_cancel_scan():
    """Stops the Gobuster scan if the user clicks cancel."""
    global current_process
    if current_process:
        current_process.kill()
        current_process = None
        progress_var.set(0)
        gobuster_output_text.insert(tk.END, "\n❌ Scan canceled.\n")
        gobuster_output_text.update_idletasks()

def gobuster_clear_output():
    """Clears Gobuster scan results."""
    gobuster_output_text.delete("1.0", tk.END)
    gobuster_ip_entry.delete(0, tk.END)
    gobuster_wordlist_entry.delete(0, tk.END)
    gobuster_mode_entry.delete(0, tk.END)
    gobuster_threads_entry.delete(0, tk.END)
    gobuster_output_entry.delete(0, tk.END)
    gobuster_port_entry.delete(0, tk.END)
    gobuster_protocol_entry.delete(0, tk.END)
    progress_var.set(0)  # ✅ Reset progress bar

def gobuster_stream_command_output(process):
    """Streams Gobuster's output, including progress, directly into the GUI."""
    while process.poll() is None:  # ✅ Ensure process is still running
        line = process.stdout.readline()
        if not line:
            break  # ✅ Stop if the stream is empty

        # ✅ Insert progress updates exactly as Gobuster displays them
        gobuster_output_text.insert(tk.END, line)
        gobuster_output_text.update_idletasks()

        time.sleep(1)  # ✅ Adjust update interval for smoother tracking

    process.stdout.close()
    process.wait()
    messagebox.showinfo("Scan Complete", "✅ Gobuster scan finished successfully!")







# **Wordlist Function**

def select_save_location():
    save_path = filedialog.asksaveasfilename(title="Select Save Location", defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if save_path:
        save_location_entry.delete(0, tk.END)
        save_location_entry.insert(0, save_path)

def run_wordlist():
    """ Execute Hashcat wordlist modification and save to user-defined location """
    global wordlist_process
    wordlist_output_text.delete("1.0", tk.END)  # Clear previous output

    wordlist = wordlist_entry.get().strip()
    rulefile = rulefile_entry.get().strip()
    save_location = save_location_entry.get().strip()

    if not wordlist or not rulefile or not save_location:
        messagebox.showwarning("Invalid Input", "Please select a wordlist, rule file, and save location.")
        return

    cmd = f"hashcat --stdout {wordlist} -r {rulefile} > \"{save_location}\""
    log_command(command)
    

    try:
        wordlist_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in iter(wordlist_process.stdout.readline, ''):
            wordlist_output_text.insert(tk.END, line)
            wordlist_output_text.update()

        wordlist_process.stdout.close()
        wordlist_process.wait()
        messagebox.showinfo("Process Complete", f"Wordlist modification saved to: {save_location}")

        wordlist_process = None

    except Exception as e:
        wordlist_output_text.insert(tk.END, f"Error: {str(e)}\n")

def select_wordlist():
    """ Allow user to browse for a wordlist file """
    file_path = filedialog.askopenfilename(title="Select Wordlist File")
    wordlist_entry.delete(0, tk.END)
    wordlist_entry.insert(0, file_path)

def select_rulefile():
    """ Allow user to browse for a Hashcat rule file """
    file_path = filedialog.askopenfilename(title="Select Hashcat Rule File")
    rulefile_entry.delete(0, tk.END)
    rulefile_entry.insert(0, file_path)



def ignore_ctrl_z(signal_received, frame):
    """Prevents Ctrl+Z from suspending the process"""
    print("\n⚠️ Warning: Ctrl+Z is disabled. Ctrl+C will interrupt and restart Minion. To close Minion properly, use the Exit option or click the X button in the GUI")

signal.signal(signal.SIGTSTP, ignore_ctrl_z)  # Disable Ctrl+Z


def execute_cupp():
    """Runs CUPP interactively with correct input handling and interruption control."""
    global cupp_process

    try:
        # Start CUPP with interactive input handling
        cupp_process = subprocess.Popen(
            ["cupp", "-i"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )

        while True:
            output_line = cupp_process.stdout.readline().strip()
            if not output_line and cupp_process.poll() is not None:
                break  #  Stop reading when CUPP completes

            print(output_line)  #  Redirect to GUI if needed

            #  Detect expected input prompts (ends with ":") and correctly send user input
            if output_line.endswith(":"):
                try:
                    user_input = input(f"{output_line} ")  # GUI can replace this input collection

                    if user_input.lower() == "exit":  #  Allow safe termination
                        cupp_process.terminate()
                        break  

                    cupp_process.stdin.write((user_input or "") + "\n")  # Ensure enter sends an empty response
                    cupp_process.stdin.flush()

                except KeyboardInterrupt:  #  Prevent Minion from misinterpreting Ctrl+C as input
                    print("⚠ CUPP interrupted. Exiting safely...")
                    cupp_process.terminate()
                    break  

        cupp_process.stdout.close()
        cupp_process.wait()

        #  Ensure CUPP fully terminates after execution
        if cupp_process.poll() is None:
            os.kill(cupp_process.pid, signal.SIGTERM)

        cupp_process = None  # Free resources properly
        messagebox.showinfo("CUPP Complete", "✅ CUPP process finished successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"⚠️ CUPP execution failed: {str(e)}")




# Function to Run CUPP with Confirmation
def run_cupp():
    """Opens CUPP in an external terminal while suppressing Qt warnings."""
    confirm = messagebox.askyesno("CUPP Execution", "⚠ CUPP will open in a separate terminal.\n\nDo you want to continue?")
    if not confirm:
        messagebox.showinfo("CUPP Canceled", "CUPP execution was canceled.")
        return

    try:
        if sys.platform.startswith("linux"):
            subprocess.Popen(["x-terminal-emulator", "-e", "bash -c 'QT_LOGGING_RULES=\"*=false\" cupp -i; exec bash'"])
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", "-a", "Terminal", "--args", "cupp", "-i"])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["cmd.exe", "/c", "start cupp -i"], shell=True)
        else:
            messagebox.showerror("Error", "⚠ CUPP execution failed: Unsupported OS")

    except Exception as e:
        messagebox.showerror("Error", f"⚠ CUPP execution failed: {str(e)}")



# Function to Stop CUPP


def stop_cupp():
    """Gracefully stops CUPP without crashing the system."""
    global cupp_process

    if cupp_process:
        try:
            cupp_process.terminate()  # Attempt graceful termination
            cupp_process.wait(timeout=5)  # Allow CUPP to exit smoothly

            if cupp_process.poll() is None:  # If still running, force kill
                os.kill(cupp_process.pid, signal.SIGTERM)  # Use SIGTERM (safer than SIGKILL)

            cupp_process = None  # Free up resources
            messagebox.showinfo("CUPP Canceled", "🚫 CUPP was successfully stopped without system impact!")
        except Exception as e:
            messagebox.showerror("Error", f"⚠️ CUPP cancel failed: {str(e)}")



def segment_wordlist():
    """Splits username list into batches while confirming filenames before saving."""
    file_path = wordlist_entry.get().strip()  # Get selected wordlist file
    save_location = save_location_entry.get().strip()  # Get user-selected save location (including filename)

    if not file_path or not save_location:
        messagebox.showwarning("Invalid Input", "Please select a Wordlist and Save Location.")
        return

    # Extract user-provided filename (remove extension if present)
    user_filename = os.path.basename(save_location).replace('.txt', '').strip()

    # Convert save location to folder path
    save_folder = os.path.dirname(save_location)

    # Ensure save directory exists
    os.makedirs(save_folder, exist_ok=True)

    print(f"✅ Processing file: {file_path}")  # Debugging info
    print(f"✅ Saving batches to folder: {save_folder}")  # Debugging info

    # Load wordlist and sort usernames
    try:
        with open(file_path, "r") as f:
            usernames = sorted(set(f.read().splitlines()))  # Remove duplicates & sort
    except Exception as e:
        messagebox.showerror("Error", f"⚠️ Could not read wordlist file: {str(e)}")
        return

    username_count = len(usernames)

    if username_count == 0:
        messagebox.showerror("Error", "⚠️ The selected wordlist appears to be empty. Please check the file.")
        return

    # Adjust batch size dynamically based on wordlist size
    if username_count > 1000:
        batch_size = max(username_count // 10, 100)
    elif username_count > 500:
        batch_size = max(username_count // 5, 50)
    else:
        batch_size = 20 if username_count > 40 else max(username_count // 2, 10)

    print(f"✅ Splitting into batches of {batch_size} entries")  # Debugging info

    batch_files = []
    preview_list = []  # Stores filenames for preview

    for i in range(0, username_count, batch_size):
        batch_number = str(i // batch_size + 1).zfill(2)  # Zero-pad batch numbers (01, 02, etc.)
        batch_filename = f"{user_filename}_batch_{batch_number}.txt"
        batch_file = os.path.join(save_folder, batch_filename)

        preview_list.append(batch_filename)  # ✅ Add batch filename to preview list

    # Show confirmation popup before saving
    preview_message = "The following batch files will be created:\n\n" + "\n".join(preview_list)
    confirm = messagebox.askyesno("Confirm Batch Creation", preview_message + "\n\nProceed with saving?")
    
    if not confirm:
        messagebox.showinfo("Batching Canceled", "Batch creation was canceled by the user.")
        return

    # Proceed with saving after confirmation
    for batch_filename in preview_list:
        batch_file = os.path.join(save_folder, batch_filename)
        batch = usernames[:batch_size]
        usernames = usernames[batch_size:]  # Remove saved usernames

        try:
            with open(batch_file, "w") as f:
                f.write("\n".join(batch))

            batch_files.append(batch_file)
            print(f"✅ Created batch file: {batch_file}")  # Debugging info

        except Exception as e:
            messagebox.showerror("Error", f"⚠️ Could not write batch file {batch_file}: {str(e)}")
            return

    messagebox.showinfo("Batching Complete", f"✅ Username batches saved in: {save_folder}")
    print("✅ Batching complete!")  # Debugging info



#Password Cracking

def start_crack(crack_function):
    """Runs password-cracking in a separate thread while ensuring user input errors display correctly."""
    global cracking_process

    if cracking_process:
        return  

    command = crack_function.__name__  

    # Allow input validation while preventing terminal logs
    if command not in ["run_hydra", "run_hashcat", "run_crackmap", "run_john", "custom_crack"]:  
        log_command(command)  
        print(f"🚀 Starting: {command}")  

    try:
        crack_thread = threading.Thread(target=crack_function, daemon=True)
        crack_thread.start()
    except Exception as e:
        if "showerror" in str(e):
            messagebox.showerror("Execution Error", f"⚠️ Failed to execute {command}. Please check input values.")  # Restore user error messages
            return




def stop_crack():
    """Stops cracking safely"""
    global cracking_process
    if cracking_process:
        cracking_process.terminate()
        messagebox.showinfo("Scan Stopped", "Password cracking has been halted.")

def cracking_clear_output():
    """ Clear scan results and entry """
    cracking_output_text.delete("1.0", tk.END)
    cracking_ip_entry.delete(0, tk.END) 
    hash_file_entry.delete(0, tk.END) 
    tool_option_entry.delete(0, tk.END)
    protocol_entry.delete(0, tk.END)
    user_wordlist_entry.delete(0, tk.END)
    password_wordlist_entry.delete(0, tk.END)
    hashcat_command_entry.delete(0, tk.END)

def cracking_cancel_scan():
    """Safely stops any running password-cracking process (Hydra, John, Hashcat, CrackMapExec) asynchronously."""
    def cancel_cracking():
        global cracking_process

        if cracking_process:
            try:
                # Attempt graceful termination first
                cracking_process.terminate()
                cracking_process.wait(timeout=5)

                # If process is still running, force kill
                if cracking_process.poll() is None:
                    os.kill(cracking_process.pid, signal.SIGKILL)

                # Kill any lingering password-cracking processes asynchronously
                subprocess.Popen("pkill -f 'hydra'", shell=True)
                subprocess.Popen("pkill -f 'john'", shell=True)
                subprocess.Popen("pkill -f 'hashcat'", shell=True)
                subprocess.Popen("pkill -f 'crackmapexec'", shell=True)

                cracking_process = None  # Free resources properly
                cracking_output_text.insert(tk.END, "\n🚫 Cracking process canceled by user. All tools stopped.\n")
                cracking_output_text.update()

                # Run `messagebox.showinfo()` inside the main thread to prevent GUI freeze
                root.after(0, lambda: messagebox.showinfo("Cracking Canceled", "All password-cracking processes have been successfully stopped!"))

            except Exception as e:
                cracking_output_text.insert(tk.END, f"\n⚠️ Error stopping cracking process: {str(e)}\n")
                cracking_output_text.update()

    # Run cancellation **in a non-blocking separate thread** to prevent UI blocking
    threading.Thread(target=cancel_cracking, daemon=True).start()



def cracking_select_hash_file(entry_widget):
    """ Opens file browser to select a hash file """
    file_path = filedialog.askopenfilename(
        title="Select Hash File",
        filetypes=[("Hash Files", "*.hash"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)


def run_hashid():
    """Executes HashID to identify hash type with enhanced format options."""
    global hashid_process

    # Get user-selected hash from the hash file entry
    hash_value = hash_file_entry.get().strip()

    if not hash_value:
        messagebox.showerror("Input Error", "⚠ Please enter a hash value before running HashID.")
        return  

    # Update GUI to indicate process has started
    cracking_output_text.delete("1.0", tk.END)
    cracking_output_text.insert(tk.END, "Processing... Please wait.\n")
    cracking_output_text.update()

    # Construct HashID command
    cmd = f"hashid {hash_value} -e -m -j"
    log_command(cmd) 

    try:
        hashid_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        threading.Thread(target=stream_hashid_output, args=(hashid_process,), daemon=True).start()

    except Exception as e:
        cracking_output_text.insert(tk.END, f"Error: {str(e)}\n")

    #stream_output(cracking_process)

def stream_hashid_output(process):
    """Reads HashID output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        cracking_output_text.insert(tk.END, line)
        cracking_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Process Complete", "✅ HashID analysis finished successfully!")


def run_hash_identifier():
    """Executes Hash-Identifier to determine hash type."""
    global hash_identifier_process

    # Get user-selected hash from the hash file entry
    hash_value = hash_file_entry.get().strip()

    if not hash_value:
        messagebox.showerror("Input Error", "⚠ Please enter a hash value before running Hash-Identifier.")
        return  

    # Update GUI to indicate process has started
    cracking_output_text.delete("1.0", tk.END)
    cracking_output_text.insert(tk.END, "Processing... Please wait.\n")
    cracking_output_text.update()

    # Construct Hash-Identifier command
    cmd = f"hash-identifier {hash_value}"
    log_command(cmd) 

    try:
        hash_identifier_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        threading.Thread(target=stream_hash_identifier_output, args=(hash_identifier_process,), daemon=True).start()

    except Exception as e:
        cracking_output_text.insert(tk.END, f"Error: {str(e)}\n")

def stream_hash_identifier_output(process):
    """Reads Hash-Identifier output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        cracking_output_text.insert(tk.END, line)
        cracking_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Process Complete", "✅ Hash-Identifier analysis finished successfully!")

    




def cracking_user_wordlist(entry_widget):
    """ Opens file browser to select a wordlist """
    file_path = filedialog.askopenfilename(
        title="Select Wordlist File",
        filetypes=[("Text Files", "*.txt"), ("List Files", "*.list"), ("Wordlist Files", "*.lst")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)


def check_cracking_status(tool_name):
    """Monitors whether the cracking tool is still running"""
    while cracking_process and cracking_process.poll() is None:
        cracking_status_label.config(text=f"{tool_name} Status: 🔄 Running...", fg="green")
        cracking_status_label.update()
        time.sleep(60)  # Update every 60 seconds
    cracking_status_label.config(text=f"{tool_name} Status: ✅ Completed!", fg="blue")
    cracking_status_label.update()





def cracking_pass_wordlist(entry_widget):
    """ Opens file browser to select a wordlist """
    file_path = filedialog.askopenfilename(
        title="Select Wordlist File",
        filetypes=[("Text Files", "*.txt"), ("List Files", "*.list"), ("Wordlist Files", "*.lst")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)


def custom_crack():
    """Executes user-defined custom cracking options while ensuring zero terminal logging."""
    global cracking_process

    command = tool_option_entry.get().strip()  

    # Ensure logging is completely suppressed
    if not command:
        messagebox.showerror("Input Error", "⚠ Please enter a valid command.")
        return  

    # Prevent terminal logging explicitly
    if command not in ["run_hydra", "run_hashcat", "run_crackmap", "run_john", "custom_crack"]:
        log_command(command)  

    try:
        cracking_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

        status_thread = threading.Thread(target=lambda: check_cracking_status("Custom Cracking"), daemon=True)
        status_thread.start()

        

    except Exception as e:
        messagebox.showerror("Execution Error", f"⚠️ Error running custom cracking command: {str(e)}")





def run_john():
    """Runs John the Ripper with user-selected wordlist and hash file"""
    global cracking_process


    wordlist = password_wordlist_entry.get().strip()
    hash_file = hash_file_entry.get().strip()

    if not wordlist or not hash_file:
        messagebox.showerror("Input Error", "Please select both a password wordlist and a hash file before running.")
        return

    # Update GUI to indicate the process has started
    cracking_output_text.delete("1.0", tk.END)
    cracking_output_text.insert(tk.END, "Processing... Please wait.\n")
    cracking_output_text.update()

    # Run John the Ripper
    cmd = f"john --wordlist={wordlist} {hash_file}"
    log_command(cmd)
    cracking_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    status_thread = threading.Thread(target=lambda: check_cracking_status("John the Ripper"), daemon=True)
    status_thread.start()


    stream_output(cracking_process)  # Display live output



def run_hydra():
    """Runs Hydra with correct user/password flags, optional port, and protocol."""
    
    # Get user inputs
    cracking_ip = cracking_ip_entry.get().strip()
    user_input = user_wordlist_entry.get().strip()
    password_input = password_wordlist_entry.get().strip()
    protocol = protocol_entry.get().strip()
    port = cracking_port_entry.get().strip()  # Added optional port entry

    # Collect missing inputs for single error message
    missing_fields = []
    if not cracking_ip: missing_fields.append("IP Address")
    if not user_input: missing_fields.append("Username/Wordlist")
    if not password_input: missing_fields.append("Password/Wordlist")
    if not protocol: missing_fields.append("Protocol")

    if missing_fields:
        print("🚨 ERROR: Showing messagebox.showerror() for missing fields")
        messagebox.showerror("Input Error", f"⚠ Missing required inputs: {', '.join(missing_fields)}.")
        return  

    global cracking_process
    if cracking_process:
        print("🔄 Stopping previous Hydra process before starting new one")
        cracking_process.terminate()
        cracking_process = None

    # **Include the port flag (-s <port>) only if the user provides one**
    port_option = f"-s {port}" if port else ""  

    # Determine correct user/password flags
    user_flag = "-L" if os.path.isfile(user_input) else "-l"
    password_flag = "-P" if os.path.isfile(password_input) else "-p"

    # **Updated command with optional port**
    cmd = f"hydra {port_option} {user_flag} {user_input} {password_flag} {password_input} {protocol}://{cracking_ip} -V"

    if not cmd.strip():
        print("⚠ Command is empty, stopping execution.")
        return  

    print("📝 Logging command:", cmd)
    log_command(cmd)  

    cracking_output_text.delete("1.0", tk.END)
    cracking_output_text.insert(tk.END, f"Executing: {cmd}\n")
    cracking_output_text.update()

    if cracking_process:
        print("🔄 Terminating existing process to prevent duplicates")
        cracking_process.terminate()
        cracking_process = None  

    cracking_process = subprocess.Popen(cmd.strip(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    if cracking_process.poll() is not None:
        print("⚠ Process failed to start, stopping execution.")
        cracking_process = None  
        return  

    print("🚀 Starting Hydra status updater thread")
    status_thread = threading.Thread(target=lambda: check_cracking_status("Hydra"), daemon=True)
    status_thread.start()

    stream_output(cracking_process)


def run_crackmap():
    """Runs CrackMapExec with user-selected wordlist, password list, IP, protocol, and optional port."""

    # Get user-selected inputs
    cracking_ip = cracking_ip_entry.get().strip()
    protocol = protocol_entry.get().strip()
    user_wordlist = user_wordlist_entry.get().strip()
    password_wordlist = password_wordlist_entry.get().strip()
    port = cracking_port_entry.get().strip()  #  Added optional port field

    if not protocol or not cracking_ip or not user_wordlist or not password_wordlist:
        messagebox.showerror("Input Error", "Please enter a protocol, IP, user or wordlist, and password or wordlist before running.")
        return

    # **Include the port flag only if the user provides one**
    port_option = f"--port {port}" if port else ""  

    # **Updated command construction to handle optional port**
    cmd = f"crackmapexec {protocol} {cracking_ip} {port_option} -u {user_wordlist} -p {password_wordlist}"

    status_thread = threading.Thread(target=lambda: update_cme_status("CrackMapExec"), daemon=True)
    status_thread.start()

    global cracking_process
    cracking_output_text.delete("1.0", tk.END)  # Clear previous output
    cracking_output_text.insert(tk.END, f"Running: {cmd}\n\n")
    cracking_output_text.update()
    log_command(cmd)

    # **Ensure proper execution with valid formatting**
    cracking_process = subprocess.Popen(cmd.strip(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stream_output(cracking_process)  # Live output streaming

  

def update_cme_status(tool_name):
    """Updates CrackMapExec progress indicator every 60 seconds."""
    while cracking_process and cracking_process.poll() is None:
        cracking_status_label.config(text=f"🔄 {tool_name} is still running...", fg="green")
        cracking_status_label.update()
        time.sleep(60)  # Wait 60 seconds before updating again
    cracking_status_label.config(text=f"✅ {tool_name} process has completed!", fg="blue")
    cracking_status_label.update()
    cracking_output_text.insert(tk.END, f"\n⚡ Status: {tool_name} has completed execution.\n")
    cracking_output_text.update()




def run_hashcat():
    """Runs Hashcat with user-defined command input"""
    global cracking_process

    cmd = hashcat_command_entry.get().strip()  # Get full user input
    status_thread = threading.Thread(target=lambda: check_cracking_status("Hashcat"), daemon=True)
    status_thread.start()


    if not cmd:
        messagebox.showerror("Input Error", "Please enter a valid Hashcat command.")
        return

    cracking_output_text.delete("1.0", tk.END)
    cracking_output_text.insert(tk.END, f"Running: {cmd}\n\n")
    cracking_output_text.update()
    log_command(cmd)

    cracking_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stream_output(cracking_process)





def stream_output(process):    
    cracking_output_text.delete("1.0", tk.END)  # Clear previous output

    while True:
        output_line = process.stdout.readline()
        if not output_line and process.poll() is not None:
            break  # Stops when the process finishes

        cracking_output_text.insert(tk.END, output_line)
        cracking_output_text.see(tk.END)  # Auto-scroll
        cracking_output_text.update()  # Refresh GUI

    # Ensure process is fully closed before showing completion message
    process.stdout.close()
    process.wait()
    
    root.after(0, lambda: messagebox.showinfo("Scan Complete", "Password Cracking has finished Processing"))




#****Forensics Functions****

def forensics_select_metadata_file(entry_widget):
    """ Opens file browser for selecting a metadata extraction target. """
    file_path = filedialog.askopenfilename(
        title="Select File for Metadata Extraction",
        filetypes=[("All Files", "*.*")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)

def run_forensics_metadata_extraction():
    """Runs ExifTool to extract metadata and display results in the GUI."""
    global metadata_process
    
    # Get selected file path
    file_path = metadata_file_entry.get().strip()
    
    if not file_path:
        messagebox.showerror("Input Error", "⚠ Please select a file before extracting metadata.")
        return  

    # Update GUI to indicate process has started
    forensics_output_text.delete("1.0", tk.END)
    forensics_output_text.insert(tk.END, "Processing... Extracting metadata...\n")
    forensics_output_text.update()

    # Construct ExifTool command
    cmd = f"exiftool {file_path}"
    log_command(cmd)
    
    try:
        metadata_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        threading.Thread(target=stream_metadata_output, args=(metadata_process,), daemon=True).start()

    except Exception as e:
        forensics_output_text.insert(tk.END, f"Error: {str(e)}\n")


def run_forensics_file_type():
    """Runs the `file` command to identify file type, logs it, and displays results."""
    global metadata_process
    
    # Get selected file path
    file_path = metadata_file_entry.get().strip()
    
    if not file_path:
        messagebox.showerror("Input Error", "⚠ Please select a file before running file type analysis.")
        return  

    # Update GUI to indicate process has started
    forensics_output_text.delete("1.0", tk.END)
    forensics_output_text.insert(tk.END, "Processing... Identifying file type...\n")
    forensics_output_text.update()

    # Construct `file` command
    cmd = f"file {file_path}"

    # Log the command used
    log_command(cmd)

    try:
        file_type_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        threading.Thread(target=stream_file_type_output, args=(file_type_process,), daemon=True).start()

    except Exception as e:
        forensics_output_text.insert(tk.END, f"Error: {str(e)}\n")


def run_forensics_binwalk():
    """Runs Binwalk to analyze files for embedded data, logs the command, and displays results."""
    global metadata_process
    
    # Get selected file path
    file_path = metadata_file_entry.get().strip()
    
    if not file_path:
        messagebox.showerror("Input Error", "⚠ Please select a file before running Binwalk.")
        return  

    # Update GUI to indicate process has started
    forensics_output_text.delete("1.0", tk.END)
    forensics_output_text.insert(tk.END, "Processing... Running Binwalk analysis...\n")
    forensics_output_text.update()

    # Construct Binwalk command
    cmd = f"binwalk {file_path}"

    # Log the command used
    log_command(cmd)

    try:
        binwalk_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        threading.Thread(target=stream_binwalk_output, args=(binwalk_process,), daemon=True).start()

    except Exception as e:
        forensics_output_text.insert(tk.END, f"Error: {str(e)}\n")

def stream_binwalk_output(process):
    """Reads Binwalk output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        forensics_output_text.insert(tk.END, line)
        forensics_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Process Complete", "✅ Binwalk analysis completed successfully!")



def stream_file_type_output(process):
    """Reads file type output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        forensics_output_text.insert(tk.END, line)
        forensics_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Process Complete", "✅ File type analysis completed successfully!")


def stream_metadata_output(process):
    """Reads ExifTool output asynchronously to prevent GUI freeze."""
    for line in iter(process.stdout.readline, ''):
        forensics_output_text.insert(tk.END, line)
        forensics_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Process Complete", "✅ Metadata extraction completed successfully!")

def forensics_clear_output():
    """Clears Forensics output."""
    forensics_output_text.delete("1.0", tk.END)
    metadata_file_entry.delete(0, tk.END)


def run_forensics_log_custom_pipeline():
    """Safely assembles and executes a custom CLI pipeline using grep, cut, awk, sort, and uniq."""
    global log_analysis_process

    file_path = log_file_entry.get().strip()
    grep_input = grep_entry.get().strip()
    delim_choice = cut_delim_var.get().strip().lower()
    custom_cut_delim = custom_delim_entry.get().strip()
    cut_fields = cut_fields_entry.get().strip()
    awk_input = awk_entry.get().strip()
    sort_option = sort_option_entry.get().strip()
    uniq_option = uniq_option_entry.get().strip()


    if not file_path:
        messagebox.showerror("Input Error", "⚠ Please select a log file before running analysis.")
        return

    # Normalize known delimiters
    delim_map = {
        "space": " ",
        "tab": "\\t",
        "comma": ",",
        "colon": ":",
        "pipe": "|"
    }
    if delim_choice == "custom":
        cut_delim = custom_cut_delim.strip().replace('"', '').replace("'", '')
    else:
        cut_delim = delim_map.get(delim_choice, "")

    # Begin building the command
    cmd_parts = [f"cat \"{file_path}\""]

    if grep_input:
        cmd_parts.append(f"grep \"{grep_input}\"")
    if cut_fields:
        if cut_delim:
            cmd_parts.append(f"cut -d \"{cut_delim}\" -f {cut_fields}")
        else:
            cmd_parts.append(f"cut -f {cut_fields}")
    if awk_input:
        awk_safe = awk_input.replace("'", "'\\''")
        cmd_parts.append(f"awk '{awk_safe}'")

        #awk_clean = awk_input.replace('"', '\\"')
        #cmd_parts.append(f"awk \"{awk_clean}\"")
    if sort_option:
        cmd_parts.append(f"sort {sort_option}")
    else:
        cmd_parts.append("sort")
    if uniq_option:
        cmd_parts.append(f"uniq {uniq_option}")

    # Final assembled command
    cmd = " | ".join(cmd_parts)

    # Log + show command
    log_command(cmd)
    forensics_log_output_text.delete("1.0", tk.END)
    forensics_log_output_text.insert(tk.END, f"Running Pipeline:\n{cmd}\n\n")
    forensics_log_output_text.update()

    try:
        log_analysis_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        threading.Thread(target=stream_log_analysis_output, args=(log_analysis_process,), daemon=True).start()
    except Exception as e:
        forensics_log_output_text.insert(tk.END, f"Error: {str(e)}\n")



def update_cut_delim_field(*args):
    if cut_delim_var.get().lower() == "custom":
        custom_delim_entry.pack(pady=2)
    else:
        custom_delim_entry.pack_forget()

    cut_delim_var.trace("w", update_cut_delim_field)


def export_log_analysis_output():
    """Allows user to export the current output to a text file."""
    output = forensics_output_text.get("1.0", tk.END).strip()

    if not output:
        messagebox.showwarning("No Output", "⚠ There is no output to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Save Log Analysis Output"
    )

    if file_path:
        try:
            with open(file_path, 'w') as file:
                file.write(output)
            messagebox.showinfo("Success", f"✅ Output saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{str(e)}")





def forensics_select_log_file(entry_widget):
    """ Opens file browser for selecting a log file. """
    file_path = filedialog.askopenfilename(
        title="Select Log File",
        filetypes=[("Log Files", "*.log"), ("All Files", "*.*")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)

def stream_log_analysis_output(process):
    """Reads CLI output asynchronously and streams it into the GUI."""
    for line in iter(process.stdout.readline, ''):
        forensics_log_output_text.insert(tk.END, line)
        forensics_log_output_text.update_idletasks()

    process.stdout.close()
    process.wait()

    messagebox.showinfo("Process Complete", "✅ Log pipeline finished running!")

def forensics_log_clear_output():
    """Clears Forensics log output."""
    forensics_log_output_text.delete("1.0", tk.END)
    log_file_entry.delete(0, tk.END)




#**Minion SmartDecode**

def decode_atbash(text):
    def translate(char):
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            return chr(base + (25 - (ord(char) - base)))
        return char

    return ''.join(translate(c) for c in text)

def decode_caesar(text, shift):
    decoded = ''
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            decoded += chr((ord(char) - base - shift) % 26 + base)
        else:
            decoded += char
    return decoded

def decode_rail_fence(text):
    even = text[::2]
    odd = text[1::2]
    decoded = ''.join(e + o for e, o in zip(even, odd))
    if len(even) > len(odd):
        decoded += even[-1]
    return decoded




def sanitize_and_score(decoded):
    """Returns a score and possibly sanitized output based on printable content ratio."""
    printable_ratio = sum(32 <= ord(c) < 127 for c in decoded) / max(len(decoded), 1)
    if printable_ratio < 0.5:
        return 1, "⚠ Output appears to be non-printable or binary."
    elif printable_ratio < 0.85:
        return 2, decoded  # mixed
    else:
        return 3, decoded  # clean text


def detect_all_bases_ranked(input_string):
    """Detects encoding formats and returns results ranked by readability and reliability."""
    input_string = input_string.strip()
    results = []

    # Dash-separated Decimal ASCII (e.g. 84-104-101)
    if re.fullmatch(r'(?:\d{1,3}-)*\d{1,3}', input_string):
        try:
            chars = [chr(int(n)) for n in input_string.split('-')]
            decoded = ''.join(chars)
            score, output = sanitize_and_score(decoded)
            results.append(("Decimal ASCII (Dash-Separated)", output, score))
        except Exception:
            results.append(("Decimal ASCII (Dash-Separated)", "⚠ Unable to decode numbers to characters.", 0))

    # Only proceed with cipher-style decoders if it's alphabetic text
    if re.fullmatch(r'[A-Za-z\s]+', input_string):
        # Atbash Cipher
        decoded = decode_atbash(input_string)
        score, output = sanitize_and_score(decoded)
        if decoded != input_string:
            results.append(("Atbash Cipher", output, score))

        # Caesar Ciphers
        for shift in [3, 13, -3]:
            decoded = decode_caesar(input_string, shift)
            if decoded != input_string:
                label = f"Caesar Cipher (Shift {shift})"
                score, output = sanitize_and_score(decoded)
                results.append((label, output, score))

        # ROT13
        decoded = codecs.encode(input_string, 'rot_13')
        if decoded != input_string:
            score, output = sanitize_and_score(decoded)
            results.append(("ROT13", output, score))

        # Rail Fence Cipher (depth 2)
        if len(input_string) >= 4:
            decoded = decode_rail_fence(input_string)
            score, output = sanitize_and_score(decoded)
            if decoded != input_string:
                results.append(("Rail Fence Cipher (depth 2)", output, score))

    # Binary
    if re.fullmatch(r'[01\s]+', input_string):
        try:
            bits = ''.join(input_string.split())
            chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
            decoded = ''.join(chars)
            score, output = sanitize_and_score(decoded)
            results.append(("Binary", output, score))
        except Exception:
            results.append(("Binary", "⚠ Unable to decode (invalid binary format).", 0))

    # Octal ASCII (e.g. 110 145 154 154 157)
    if re.fullmatch(r'(?:[0-7]{1,3}\s+)*[0-7]{1,3}', input_string):
        try:
            octets = input_string.split()
            chars = [chr(int(o, 8)) for o in octets]
            decoded = ''.join(chars)
            score, output = sanitize_and_score(decoded)
            results.append(("Octal ASCII", output, score))
        except Exception:
            results.append(("Octal ASCII", "⚠ Unable to decode octal values.", 0))

    # Decimal ASCII (space-separated)
    if re.fullmatch(r'(?:\d{1,3}\s+)*\d{1,3}', input_string):
        try:
            chars = [chr(int(n)) for n in input_string.split()]
            decoded = ''.join(chars)
            score, output = sanitize_and_score(decoded)
            results.append(("Decimal ASCII", output, score))
        except Exception:
            results.append(("Decimal ASCII", "⚠ Unable to decode decimal values.", 0))

    # Hexadecimal
    if re.fullmatch(r'(0x)?[0-9a-fA-F]+', input_string):
        try:
            decoded = bytes.fromhex(input_string.replace("0x", "")).decode('utf-8', errors='replace')
            score, output = sanitize_and_score(decoded)
            results.append(("Hexadecimal", output, score))
        except Exception:
            pass

    # Base32
    if re.fullmatch(r'[A-Z2-7=]+', input_string, re.IGNORECASE):
        try:
            decoded = base64.b32decode(input_string, casefold=True).decode('utf-8', errors='replace')
            score, output = sanitize_and_score(decoded)
            results.append(("Base32", output, score))
        except Exception:
            pass

    # Base64
    if re.fullmatch(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', input_string):
        try:
            decoded = base64.b64decode(input_string, validate=True).decode('utf-8', errors='replace')
            score, output = sanitize_and_score(decoded)
            results.append(("Base64", output, score))
        except Exception:
            pass

    # Base85
    try:
        decoded = base64.a85decode(input_string).decode('utf-8', errors='replace')
        score, output = sanitize_and_score(decoded)
        results.append(("Base85 (Ascii85)", output, score))
    except Exception:
        pass

    # URL Encoding
    if '%' in input_string:
        try:
            decoded = urllib.parse.unquote(input_string)
            score, output = sanitize_and_score(decoded)
            results.append(("URL Encoded", output, score))
        except Exception:
            pass

    # Bacon Cipher
    if re.fullmatch(r'([ABab]{5}\s*)+', input_string):
        try:
            bacon_map = {
                'AAAAA':'A','AAAAB':'B','AAABA':'C','AAABB':'D','AABAA':'E','AABAB':'F','AABBA':'G',
                'AABBB':'H','ABAAA':'I','ABAAB':'K','ABABA':'L','ABABB':'M','ABBAA':'N','ABBAB':'O',
                'ABBBA':'P','ABBBB':'Q','BAAAA':'R','BAAAB':'S','BAABA':'T','BAABB':'U',
                'BABAA':'W','BABAB':'X','BABBA':'Y','BABBB':'Z'
            }
            clean = re.sub(r'\s+', '', input_string.upper())
            chunks = [clean[i:i+5] for i in range(0, len(clean), 5)]
            decoded = ''.join(bacon_map.get(chunk, '?') for chunk in chunks)
            score, output = sanitize_and_score(decoded)
            results.append(("Bacon Cipher", output, score))
        except Exception:
            results.append(("Bacon Cipher", "⚠ Could not decode Bacon Cipher input.", 0))

    # NATO Phonetic Alphabet
    nato_map = {
        "ALFA": "A", "ALPHA": "A", "BRAVO": "B", "CHARLIE": "C", "DELTA": "D",
        "ECHO": "E", "FOXTROT": "F", "GOLF": "G", "HOTEL": "H", "INDIA": "I",
        "JULIETT": "J", "JULIET": "J", "KILO": "K", "LIMA": "L", "MIKE": "M",
        "NOVEMBER": "N", "OSCAR": "O", "PAPA": "P", "QUEBEC": "Q", "ROMEO": "R",
        "SIERRA": "S", "TANGO": "T", "UNIFORM": "U", "VICTOR": "V", "WHISKEY": "W",
        "XRAY": "X", "X-RAY": "X", "YANKEE": "Y", "ZULU": "Z"
    }
    words = re.split(r'[\s\-]+', input_string.upper())
    if all(word in nato_map for word in words):
        decoded = ''.join(nato_map[word] for word in words)
        score, output = sanitize_and_score(decoded)
        results.append(("NATO Phonetic Alphabet", output, score))

    # Base58 (best guess only)
    base58_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    if all(c in base58_chars for c in input_string):
        results.append(("Possibly Base58", "⚠ Decoding not attempted.", 0))

    # Fallback
    if not results:
        results.append(("Unknown or invalid encoding", "", 0))

    # Sort and return by score
    ranked = sorted(results, key=lambda x: x[2], reverse=True)
    return ranked

#**Deep Decode**    

try:
    with open("/usr/share/dict/words", "r") as f:
        english_words = set(word.strip().lower() for word in f if len(word.strip()) >= 3)
except FileNotFoundError:
    english_words = set()

def count_wordlist_hits(text):
    words = [w.lower() for w in text.split() if w.isalpha()]
    return sum(1 for w in words if w in english_words)


def decode_with_chains(input_string, max_depth=3, min_score=2):
    """
    Attempts to decode input recursively using top-ranked decoders.
    Follows multiple decoder branches with score >= min_score.
    """
    visited = set()
    trace_paths = []

    def recurse_chain(current_input, depth, path):
        if depth > max_depth or current_input in visited:
            return
        visited.add(current_input)

        results = detect_all_bases_ranked(current_input)
        for enc, decoded, score in results:
            if score >= min_score and decoded != current_input:
                path_copy = path + [(enc, decoded)]
                trace_paths.append(path_copy)
                recurse_chain(decoded, depth + 1, path_copy)

    recurse_chain(input_string, 1, [])
    
    # Pick longest or most readable trace
   
    best_trace = max(trace_paths, key=lambda t: (len(t), sum(32 <= ord(ch) < 127 for ch in t[-1][1])), default=[])
    return best_trace



def is_likely_readable(text):
    printable_ratio = sum(32 <= ord(c) < 127 for c in text) / max(len(text), 1)
    word_count = len([w for w in text.split() if len(w) >= 4 and w.isalpha()])
    return printable_ratio > 0.95 and word_count >= 3




def run_full_chain_detection():
    user_input = forensics_base_input_entry.get().strip()
    forensics_base_output_text.delete("1.0", tk.END)

    if not user_input:
        forensics_base_output_text.insert(tk.END, "⚠ No input provided.\n")
        return

    paths = decode_combinatorially(user_input)

    if not paths:
        forensics_base_output_text.insert(tk.END, "⚠ No valid decoding paths found.\n")
        return

    # Display all paths
    for i, path in enumerate(paths, 1):
        forensics_base_output_text.insert(tk.END, f"🔎 Path {i}\n")
        for step, (method, result) in enumerate(path, 1):
            forensics_base_output_text.insert(tk.END, f"[Step {step}] {method}\n{result}\n\n")
        forensics_base_output_text.insert(tk.END, "—" * 40 + "\n")

    # After displaying, now evaluate final steps of all paths
    def score_result(result):
        printable = sum(32 <= ord(c) < 127 for c in result) / max(len(result), 1)
        words = [w for w in result.split() if len(w) >= 4 and w.isalpha()]
        return printable * len(words)

    best_score = 0
    #best_path = None
    best_result = ""
    best_index = None
    best_step_index = None

    for i, path in enumerate(paths, 1):
        if not path:
            continue
        method, result = path[-1]
        score = count_wordlist_hits(result)
        if score > best_score:
            best_score = score
            best_path = path
            best_result = result
            best_index = i
            best_step_index = len(path)

    # Add visual highlight + popup
    if best_result:
        messagebox.showinfo(
            "✅ Human-Readable Output Found",
            f"Best result found at:\nPath {best_index}, Step {best_step_index}\n\n{best_result}"
        )
        forensics_base_output_text.insert(
            tk.END,
            f"\n🎯 Most human-readable output found at Path {best_index}, Step {best_step_index}:\n✅ {best_result}\n"
        )
    else:
        messagebox.showwarning(
            "⚠ No Readable Output",
            "No clearly readable output found."
        )
        forensics_base_output_text.insert(
            tk.END,
            "\n⚠ No clearly readable output found.\n"
        )





def decode_combinatorially(input_string, max_depth=4, min_score=2, delay=0.01):
    """
    Recursively explores all decoding paths with score >= min_score,
    building full traces, avoiding loops, and optionally delaying between steps.
    """
    visited = set()
    all_paths = []

    def recurse(current_input, depth, path):
        if depth > max_depth or current_input in visited:
            return
        visited.add(current_input)

        results = detect_all_bases_ranked(current_input)
        for method, decoded, score in results:
            if score >= min_score and decoded != current_input:
                new_path = path + [(method, decoded)]
                all_paths.append(new_path)
                time.sleep(delay)
                recurse(decoded, depth + 1, new_path)

    recurse(input_string, 1, [])
    return all_paths


# *Run Detection*

def run_base_detection():
    user_input = forensics_base_input_entry.get().strip()
    forensics_log_output_text.delete("1.0", tk.END)

    if not user_input:
        forensics_log_output_text.insert(tk.END, "⚠ No input provided.\n")
        return

    results = detect_all_bases_ranked(user_input)

    for enc, decoded, score in results:
        marker = "✓" if score >= 3 else "•"
        forensics_base_output_text.insert(tk.END, f"[{marker} {enc}]\n{decoded}\n\n")

# Export Output
def export_base_output():
    content = forensics_base_output_text.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("Nothing to Save", "⚠ There is no output to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")],
        title="Save Base Detection Output"
    )

    if file_path:
        with open(file_path, 'w') as f:
            f.write(content)
        messagebox.showinfo("Saved", f"✅ Output saved to:\n{file_path}")


def forensics_base_clear_output():
    """Clears the Forensics base detection output and input file entry."""
    forensics_base_output_text.delete("1.0", tk.END)
    forensics_base_input_entry.delete(0, tk.END)











#****Switch***** 
def switch_to_frame(frame_to_show):
    """ Ensure only the selected menu is visible and force UI refresh """
    main_menu_frame.pack_forget()
    nmap_menu_frame.pack_forget()
    smb_menu_frame.pack_forget()
    wordlist_menu_frame.pack_forget()
    cracking_menu_frame.pack_forget()
    core_security_menu_frame.pack_forget()
    core_security_submenu_scanner_frame.pack_forget()
    gobuster_menu_frame.pack_forget()
    forensics_menu_frame.pack_forget()
    forensics_submenu_frame.pack_forget()
    forensics_metadata_frame.pack_forget()
    forensics_log_frame.pack_forget()
    forensics_base_frame.pack_forget()
    

    frame_to_show.pack(fill="both", expand=True)
    root.update()  # Forces the UI to redraw


# ****GUI Setup*****
root = tk.Tk()
root.title("Minion Security Toolkit")
root.geometry("1200x800")  # Ensure program starts large
root.minsize(1200, 800)    # Prevent crash due to resizing
root.configure(bg="#0A192F")  # Dark theme for better readability
root.attributes('-topmost', True)  # Keep GUI on top
progress_var = tk.IntVar(root)


# **Main Menu Frame**


main_menu_frame = tk.Frame(root, bg="#0A192F")  # Set background explicitly
tk.Label(main_menu_frame, text="MINION", font=("Arial", 30, "bold"), fg="#FFC107", bg="#0A192F").pack(pady=10)
tk.Label(main_menu_frame, text="Created by TTEH", font=("Arial", 10), fg="#CCCCCC", bg="#0A192F").pack()
tk.Label(main_menu_frame, text="Legal Disclaimer: Usage of Minion for attacking targets without prior mutual consent is illegal...", fg="#FFA726", font=("Arial", 8), bg="#0A192F").pack()

main_log_menu_nav_buttons_frame = tk.Frame(main_menu_frame, bg="#0A192F")
main_log_menu_nav_buttons_frame.pack(pady=20)
tk.Button(main_log_menu_nav_buttons_frame, text="View Log", command=view_log, width=10, height=2, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(main_log_menu_nav_buttons_frame, text="View Notes", command=view_notes, width=10, height=2, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(main_menu_frame, text="Cheat Sheet", command=open_cheat_sheet, width=20, height=2, bg="#3E3E3E", fg="white").pack(pady=5)
tk.Button(main_log_menu_nav_buttons_frame, text="Open Terminal", command=open_terminal, width=10, height=2, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(main_log_menu_nav_buttons_frame, text="Clear Log", command=clear_log, width=10, height=2, bg="#B71C1C", fg="white").pack(side=tk.LEFT, padx=5)

main_selection_menu_nav_frame = tk.Frame(main_menu_frame, bg="#0A192F")
main_selection_menu_nav_frame.pack(pady=10)
tk.Button(main_selection_menu_nav_frame, text="Core Offensive Security", command=lambda: switch_to_frame(core_security_menu_frame), width=20, height=2, bg="#FFD700", fg="black").pack(side=tk.LEFT, padx=5)
tk.Button(main_selection_menu_nav_frame, text="Forensics", command=lambda: switch_to_frame(forensics_menu_frame), width=20, height=2, bg="#FFD700", fg="black").pack(side=tk.LEFT, padx=5)

#tk.Button(main_menu_frame, text="Core Offensive Security", command=lambda: switch_to_frame(core_security_menu_frame), width=25, height=2, bg="#FFD700", fg="black").pack(pady=10)


# **** Core Offensive Security Menu Frame ****
core_security_menu_frame = tk.Frame( bg="#0A192F")

tk.Label(core_security_menu_frame, text="Core Offensive Security", font=("Arial", 30, "bold"), fg="#FFD700", bg="#0F1B37").pack(pady=15)

# Navigation buttons inside Core Offensive Security menu
tk.Button(core_security_menu_frame, text="Scanning", command=lambda: switch_to_frame(core_security_submenu_scanner_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(core_security_menu_frame, text="Create Wordlist", command=lambda: switch_to_frame(wordlist_menu_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(core_security_menu_frame, text="Cracking", command=lambda: switch_to_frame(cracking_menu_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(core_security_menu_frame, text="Back to Main Menu", command=lambda: switch_to_frame(main_menu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(pady=10)


# **** Core Security Submenu (Scanners) ****
core_security_submenu_scanner_frame = tk.Frame(bg="#0A192F")
tk.Label(core_security_submenu_scanner_frame, text="Scanner Tools", font=("Arial", 30, "bold"), fg="#FFD700", bg="#0F1B37").pack(pady=15)

# **Navigation buttons for scanner tools**
tk.Button(core_security_submenu_scanner_frame, text="Nmap Scanner", command=lambda: switch_to_frame(nmap_menu_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(core_security_submenu_scanner_frame, text="SMB Scanner", command=lambda: switch_to_frame(smb_menu_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(core_security_submenu_scanner_frame, text="Gobuster Scanner", command=lambda: switch_to_frame(gobuster_menu_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)

# **Back to Core Security Menu**
tk.Button(core_security_submenu_scanner_frame, text="Core Security Menu", command=lambda: switch_to_frame(core_security_menu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(pady=10)

# **** Forensics Menu Frame ****
forensics_menu_frame = tk.Frame(root, bg="#0A192F")
tk.Label(forensics_menu_frame, text="Forensics", font=("Arial", 30, "bold"), fg="#FFD700", bg="#0F1B37").pack(pady=15)

# **Navigation button leading to the Forensics Submenu**
tk.Button(forensics_menu_frame, text="Forensics Tools", command=lambda: switch_to_frame(forensics_submenu_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)


# **** Forensics Submenu (Grouped Tools) ****
forensics_submenu_frame = tk.Frame(bg="#0A192F")
tk.Label(forensics_submenu_frame, text="Forensics Tools Selection", font=("Arial", 30, "bold"), fg="#FFD700", bg="#0F1B37").pack(pady=15)

# **Grouped Forensics Tools**
tk.Button(forensics_submenu_frame, text="Extracting", command=lambda: switch_to_frame(forensics_metadata_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(forensics_submenu_frame, text="Log Analysis", command=lambda: switch_to_frame(forensics_log_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
tk.Button(forensics_submenu_frame, text="Minion SmartDecode", command=lambda: switch_to_frame(forensics_base_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)
#tk.Button(forensics_submenu_frame, text="Cryptography", command=lambda: switch_to_frame(forensics_crypto_frame), width=20, height=2, bg="#1E88E5", fg="white").pack(pady=5)

# **Back to Forensics Menu**
tk.Button(forensics_submenu_frame, text="Forensics Menu", command=lambda: switch_to_frame(forensics_menu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(pady=10)
# **Back to Main Menu**
tk.Button(forensics_menu_frame, text="Back to Main Menu", command=lambda: switch_to_frame(main_menu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(pady=10)




#tk.Label(main_menu_frame, text="Exploit Development & Execution", font=("Arial", 25, "bold"), fg="#00FFFF", bg="#121212").pack(pady=15)


tk.Button(main_menu_frame, text="Exit", command=root.quit, width=50, height=2, bg="#FFA726", fg="white").pack(pady=8)


main_menu_frame.pack()

# **Scanner Frame**
nmap_menu_frame = tk.Frame(root, bg="#0A192F")
nmap_menu_frame.pack_propagate(False)

smb_menu_frame = tk.Frame(root, bg="#0A192F")
smb_menu_frame.pack_propagate(False)

wordlist_menu_frame = tk.Frame(root, bg="#0A192F")
wordlist_menu_frame.pack_propagate(False)

cracking_menu_frame = tk.Frame(root, bg="#0A192F")
cracking_menu_frame.pack_propagate(False)

gobuster_menu_frame = tk.Frame(root, bg="#0A192F")
gobuster_menu_frame.pack_propagate(False)

#**Forensics Frame**
forensics_metadata_frame = tk.Frame(root, bg="#0A192F")
forensics_metadata_frame.pack_propagate(False)

forensics_binwalk_frame = tk.Frame(root, bg="#0A192F")
forensics_binwalk_frame.pack_propagate(False)

forensics_log_frame = tk.Frame(root, bg="#0A192F")
forensics_log_frame.pack_propagate(False)

forensics_base_frame = tk.Frame(root, bg="#0A192F")
forensics_base_frame.pack_propagate(False)





# **Output Display Top Banner**
tk.Label(nmap_menu_frame, text="Nmap Scanner", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(nmap_menu_frame, text="Scan Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()
tk.Label(smb_menu_frame, text="SMB Scanner", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(smb_menu_frame, text="Scan Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()
tk.Label(gobuster_menu_frame, text="Gobuster Scanner", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(gobuster_menu_frame, text="Scan Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()
tk.Label(wordlist_menu_frame, text="Hashcat Wordlist Modifier", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=12)

tk.Label(cracking_menu_frame, text="Cracking", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(cracking_menu_frame, text="Scan Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()

tk.Label(forensics_metadata_frame, text="Forensics", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(forensics_metadata_frame, text="Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()

tk.Label(forensics_log_frame, text="Log Analysis", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(forensics_log_frame, text="Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()

tk.Label(forensics_base_frame, text="Minion SmartDecode", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(forensics_base_frame, text="Results:", font=("Arial", 14, "bold"), fg="#FFFFFF", bg="#0A192F").pack()

# **Output Display Top Banner**

# Nmap Output
nmap_output_text = tk.Text(nmap_menu_frame, height=15, width=200, bg="#0A192F", fg="#FFFFFF")
nmap_output_text.pack(fill="both", expand=True, padx=10, pady=10)
nmap_output_text.config(font=("Courier", 12))

# SMB Output
smb_output_text = tk.Text(smb_menu_frame, height=15, width=200, bg="#0A192F", fg="#FFFFFF")
smb_output_text.pack(fill="both", expand=True, padx=5, pady=5)
smb_output_text.config(font=("Courier", 12))  # Set terminal-style font

#Gobuster Output
gobuster_output_text = tk.Text(gobuster_menu_frame, height=15, width=200, bg="#0A192F", fg="white")
gobuster_output_text.pack(fill="both", expand=True, padx=10, pady=10)
gobuster_output_text.config(font=("Courier", 12))

# Wordlist Output Display
wordlist_output_text = tk.Text(wordlist_menu_frame, height=15, width=80, bg="#0A192F", fg="#FFFFFF")
wordlist_output_text.pack(fill="both", expand=True, padx=10, pady=10)

#Password Cracking Tools Output

cracking_output_text = tk.Text(cracking_menu_frame, height=15, width=200, bg="#0A192F", fg="#FFFFFF")
cracking_output_text.pack(fill="both", expand=True, padx=10, pady=10)
cracking_output_text.config(font=("Courier", 12))


#Forensics Output
forensics_output_text = tk.Text(forensics_metadata_frame, height=15, width=200, bg="#0A192F", fg="#FFFFFF")
forensics_output_text.pack(fill="both", expand=True, padx=10, pady=10)
forensics_output_text.config(font=("Courier", 12))

forensics_log_output_text = tk.Text(forensics_log_frame, height=15, width=200, bg="#0A192F", fg="#FFFFFF")
forensics_log_output_text.pack(fill="both", expand=True, padx=10, pady=10)
forensics_log_output_text.config(font=("Courier", 12))

forensics_base_output_text = tk.Text(forensics_base_frame, height=15, width=200, bg="#0A192F", fg="#FFFFFF")
forensics_base_output_text.pack(fill="both", expand=True, padx=10, pady=10)
forensics_base_output_text.config(font=("Courier", 12))

forensics_base_frame


# **IP Entry Fields for Each Scanner**
#nmap
nmap_ip_entry = tk.Entry(nmap_menu_frame, width=50)
nmap_ip_entry.pack(pady=5)

#smb
smb_ip_entry = tk.Entry(smb_menu_frame, width=50)
smb_ip_entry.pack()

#gobuster
tk.Label(gobuster_menu_frame, text="Enter Target (IP/URL/Domain):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_ip_entry = tk.Entry(gobuster_menu_frame, width=50)
gobuster_ip_entry.pack()

cracking_ip_entry = tk.Entry(cracking_menu_frame, width=50)
cracking_ip_entry.pack()



# **Grouped Scan Options**

# Nmap Section
tk.Label(nmap_menu_frame, text="Enter Target IP:", font=("Arial", 12), fg="#64B5F6", bg="#0A192F").pack()

tk.Label(nmap_menu_frame, text="🔵 Basic Scan → Performs a quick stealth SYN scan (-sS -p-) across all ports", font=("Arial", 14, "bold"), fg="#64B5F6", bg="#0A192F").pack()
tk.Button(nmap_menu_frame, text="Stealth Scan (Full Ports)", command=lambda: run_command(f"nmap -n -sS -p- --min-rate=5000 {nmap_ip_entry.get()}"), width=50, height=2, bg="#2196F3", fg="white").pack(pady=5)

tk.Label(nmap_menu_frame, text="🟠 Script Scan → Runs default Nmap scripts (-sV -sC -p-) on all ports. ", font=("Arial", 14, "bold"), fg="#FF9800", bg="#0A192F").pack()
tk.Button(nmap_menu_frame, text="Service & Script Scan (Full Ports)", command=lambda: run_command(f"nmap -n -sV -sC -p- --min-rate=5000 {nmap_ip_entry.get()}"), width=50, height=2, bg="#FF9800", fg="white").pack(pady=5)

tk.Label(nmap_menu_frame, text="🔴 Script with Detection → Uses aggressive scanning (-A -p-), enabling OS detection, version scanning, default scripts, and traceroute analysis. *High-noise*", font=("Arial", 14, "bold"), fg="#D32F2F", bg="#0A192F").pack()
tk.Button(nmap_menu_frame, text="Advanced Recon Scan", command=lambda: run_command(f"nmap -A -p- -T4 {nmap_ip_entry.get()}"), width=50, height=2, bg="#D32F2F", fg="white").pack(pady=5)



# **Manual Scan Option**

tk.Label(nmap_menu_frame, text="🔹 Custom Nmap Command:", font=("Arial", 14, "bold")).pack()
nmap_manual_entry = tk.Entry(nmap_menu_frame, width=50)
nmap_manual_entry.pack(pady=5)  


progress_var = tk.IntVar()
progress_label = tk.Label(nmap_menu_frame, text="Scanning Progress", font=("Arial", 12), fg="white", bg="#0A192F").pack(pady=5)
progress_bar = ttk.Progressbar(nmap_menu_frame, maximum=100, variable=progress_var, length=300)
progress_bar.pack(pady=5)


nmap_nav_buttons_frame = tk.Frame(nmap_menu_frame, bg="#0A192F")
nmap_nav_buttons_frame.pack(pady=10)

tk.Button(nmap_nav_buttons_frame, text="Run Custom Scan", command=run_manual_scan, width=15, height=2, bg="#673AB7", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(nmap_nav_buttons_frame, text="Cancel Scan", command=nmap_cancel_scan, width=15, height=2, bg="#D32F2F", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(nmap_nav_buttons_frame, text="Clear", command=nmap_clear_output, width=15, height=2, bg="#757575", fg="white").pack(pady=5)

nmap_nav_back_buttons_frame = tk.Frame(nmap_menu_frame, bg="#0A192F")
nmap_nav_back_buttons_frame.pack(pady=10)

tk.Button(nmap_nav_back_buttons_frame, text="Scanning Tools Menu", command=lambda: switch_to_frame(core_security_submenu_scanner_frame), width=50, height=2, bg="#00897B", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(nmap_nav_back_buttons_frame, text="Core Offensive Security Menu", command=lambda: switch_to_frame(core_security_menu_frame), width=50, height=2, bg="#FFD700", fg="white").pack(side=tk.LEFT, padx=5)



# *****SMB Section*****
tk.Label(smb_menu_frame, text="Enter Target IP:", font=("Arial", 12), fg="#64B5F6", bg="#0A192F").pack()
tk.Label(smb_menu_frame, text="🔵 List Shares", font=("Arial", 14, "bold"), fg="#64B5F6", bg="#0A192F").pack()


listshares_nav_buttons_frame = tk.Frame(smb_menu_frame, bg="#0A192F")
listshares_nav_buttons_frame.pack(pady=10)
tk.Button(listshares_nav_buttons_frame, text="List Shares", command=lambda: run_smb(f"smbclient -N -L \\\\\\\\{smb_ip_entry.get()}\\\\"), width=20, height=2, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

tk.Button(listshares_nav_buttons_frame, text="Full Enumeration", command=lambda: run_smb(f"enum4linux -a {smb_ip_entry.get()}", full_enum=True), width=20, height=2, bg="#D32F2F", fg="white").pack(side=tk.LEFT, padx=5)


# SMB Connection Section
tk.Label(smb_menu_frame, text="🔴 Connect to SMB", font=("Arial", 14, "bold"), fg="#64B5F6", bg="#0A192F").pack()
tk.Label(smb_menu_frame, text="Enter Share:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
smb_share_entry = tk.Entry(smb_menu_frame, width=50, bg="#333333", fg="white")
smb_share_entry.pack(pady=3)

tk.Label(smb_menu_frame, text="Enter User:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
smb_user_entry = tk.Entry(smb_menu_frame, width=50, bg="#333333", fg="white")
smb_user_entry.pack(pady=3)

tk.Label(smb_menu_frame, text="Enter Password:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
smb_pass_entry = tk.Entry(smb_menu_frame, width=50, bg="#333333", fg="white", show="*")  # Mask password input
smb_pass_entry.pack(pady=3)

# Add an entry box for custom SMB commands
tk.Label(smb_menu_frame, text="Custom SMB Command: ", font=("Arial", 12, "bold"), fg="white", bg="#0A192F").pack()
smb_command_entry = tk.Entry(smb_menu_frame, width=50, font=("Arial", 12, "bold"), bg="#333333", fg="white")
smb_command_entry.pack(pady=3)

#SMB Nav For Command
smbcommand_nav_buttons_frame = tk.Frame(smb_menu_frame, bg="#0A192F")
smbcommand_nav_buttons_frame.pack(pady=10)
tk.Button(smbcommand_nav_buttons_frame, text="Run Custom Command", command=smb_run_custom_command, width=20, height=2, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(smbcommand_nav_buttons_frame, text="Connect via SMBclient", command=connect_smb, width=20, height=2, bg="#2E7D32", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(smbcommand_nav_buttons_frame, text="Connect via CrackMapExec", command=smb_connect_cme, width=20, height=2, bg="#2E7D32", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(smbcommand_nav_buttons_frame, text="Connect via smbmap", command=smbmap_connect_smb, width=20, height=2, bg="#2E7D32", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(smbcommand_nav_buttons_frame, text="Cancel SMB Scan", command=smb_cancel_scan, width=20, height=2, bg="#D32F2F", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(smbcommand_nav_buttons_frame, text="Clear", command=smb_clear_output, width=20, height=2, bg="#757575", fg="white").pack(side=tk.LEFT, padx=5)

# Back to Main Menu Button
smb_nav_back_buttons_frame = tk.Frame(smb_menu_frame, bg="#0A192F")
smb_nav_back_buttons_frame.pack(pady=10)
tk.Button(smb_nav_back_buttons_frame, text="Back to Scanning Menu", command=lambda: switch_to_frame(core_security_submenu_scanner_frame), width=50, height=2, bg="#00897B", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(smb_nav_back_buttons_frame, text="Core Offensive Security Menu", command=lambda: switch_to_frame(core_security_menu_frame), width=50, height=2, bg="#FFD700", fg="white").pack(side=tk.LEFT, padx=5)


# *****Gobuster Section*****

# Gobuster Mode Selection
tk.Label(gobuster_menu_frame, text="Gobuster Mode:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_mode_entry = tk.Entry(gobuster_menu_frame, width=50, bg="#333333", fg="white")
gobuster_mode_entry.pack()

# Gobuster Protocol Selection
tk.Label(gobuster_menu_frame, text="Protocol (http/https):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_protocol_entry = tk.Entry(gobuster_menu_frame, width=50, bg="#333333", fg="white")
gobuster_protocol_entry.pack()

# Gobuster Port Selection
tk.Label(gobuster_menu_frame, text="Port (Optional):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_port_entry = tk.Entry(gobuster_menu_frame, width=50, bg="#333333", fg="white")
gobuster_port_entry.pack()

# Gobuster Wordlist Selection
tk.Label(gobuster_menu_frame, text="Select Wordlist:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_wordlist_entry = tk.Entry(gobuster_menu_frame, width=50, bg="#333333", fg="white")
gobuster_wordlist_entry.pack()
tk.Button(gobuster_menu_frame, text="Browse", command=lambda: gobuster_select_wordlist(gobuster_wordlist_entry), width=20, height=2, bg="#1565C0", fg="white").pack(pady=5)

# Gobuster Threads Entry
tk.Label(gobuster_menu_frame, text="Threads:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_threads_entry = tk.Entry(gobuster_menu_frame, width=50, bg="#333333", fg="white")
gobuster_threads_entry.pack()

# Gobuster Output File Entry
tk.Label(gobuster_menu_frame, text="Output File (Optional):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
gobuster_output_entry = tk.Entry(gobuster_menu_frame, width=50, bg="#333333", fg="white")
gobuster_output_entry.pack(pady=3)

# Action Buttons
gobuster_nav_buttons_frame = tk.Frame(gobuster_menu_frame, bg="#0A192F")
gobuster_nav_buttons_frame.pack(pady=10)
tk.Button(gobuster_nav_buttons_frame, text="Run Gobuster Scan", command=run_gobuster, width=20, height=2, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(gobuster_nav_buttons_frame, text="Cancel Scan", command=gobuster_cancel_scan, width=20, height=2, bg="#D32F2F", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(gobuster_nav_buttons_frame, text="Clear", command=gobuster_clear_output, width=20, height=2, bg="#757575", fg="white").pack(side=tk.LEFT, padx=5)

# Back Buttons
gobuster_nav_back_buttons_frame = tk.Frame(gobuster_menu_frame, bg="#0A192F")
gobuster_nav_back_buttons_frame.pack(pady=10)
tk.Button(gobuster_nav_back_buttons_frame, text="Back to Scanning Menu", command=lambda: switch_to_frame(core_security_submenu_scanner_frame), width=35, height=2, bg="#00897B", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(gobuster_nav_back_buttons_frame, text="Core Offensive Security Menu", command=lambda: switch_to_frame(core_security_menu_frame), width=35, height=2, bg="#FFD700", fg="white").pack(side=tk.LEFT, padx=5)




#*****Create Wordlist*****

# Wordlist Modification
wordlist_menu_frame = tk.Frame(root, bg="#0A192F")  # Navy Blue Background

tk.Label(wordlist_menu_frame, text="Wordlist Modifier & Generator", font=("Arial", 16, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=5)

tk.Label(wordlist_menu_frame, text="Select Wordlist:", font=("Arial", 12), fg="#FFFFFF", bg="#0A192F").pack(pady=5)
wordlist_entry = tk.Entry(wordlist_menu_frame, width=50, bg="#333333", fg="white")  # Darker input field
wordlist_entry.pack()
tk.Button(wordlist_menu_frame, text="Browse", command=select_wordlist, width=50, height=2, bg="#1565C0", fg="white").pack(pady=5)

tk.Label(wordlist_menu_frame, text="Select Rule File:", font=("Arial", 12), fg="#FFFFFF", bg="#0A192F").pack(pady=5)
rulefile_entry = tk.Entry(wordlist_menu_frame, width=50, bg="#333333", fg="white")
rulefile_entry.pack()
tk.Button(wordlist_menu_frame, text="Browse", command=select_rulefile, width=50, height=2, bg="#1565C0", fg="white").pack(pady=5)

tk.Label(wordlist_menu_frame, text="Select Save Location:", font=("Arial", 12), fg="#FFFFFF", bg="#0A192F").pack(pady=5)
save_location_entry = tk.Entry(wordlist_menu_frame, width=50, bg="#333333", fg="white")
save_location_entry.pack()
tk.Button(wordlist_menu_frame, text="Browse", command=select_save_location, width=50, height=2, bg="#1565C0", fg="white").pack(pady=5)

tk.Button(wordlist_menu_frame, text="Create A Modified Wordlist", command=run_wordlist, width=50, height=2, bg="#FF9800", fg="white").pack(pady=8)  # Orange for action

tk.Label(wordlist_menu_frame, text="Optimize Wordlist for Faster Cracking", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#0A192F").pack(pady=15)
tk.Button(wordlist_menu_frame, text="Batch Wordlist for Speed", command=segment_wordlist, width=50, height=1, bg="#1565C0", fg="white").pack(pady=15)

tk.Label(wordlist_menu_frame, text="To Create Highly Personalized Password Wordlists: Try CUPP", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#0A192F").pack(pady=10)
tk.Button(wordlist_menu_frame, text="Run Common User Passwords Profiler", command=run_cupp, width=50, height=1, bg="#1565C0", fg="white").pack(pady=10)


# Back to Main Menu Button
tk.Button(wordlist_menu_frame, text="Core Offensive Security Menu", command=lambda: switch_to_frame(core_security_menu_frame), width=50, height=2, bg="#FFD700", fg="white").pack(pady=8)  # Red for exit/navigation



# ******Password Cracking Menu*****

tk.Label(cracking_menu_frame, text="Enter IP Address:", font=("Arial", 12), fg="#64B5F6", bg="#0A192F").pack()

# Entry for general cracking tool options


# Entry for hash file selection
tk.Label(cracking_menu_frame, text="Enter Hash or File:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
hash_file_entry = tk.Entry(cracking_menu_frame, width=50, bg="#333333", fg="white")
hash_file_entry.pack()
cracking_nav_hash_buttons_frame = tk.Frame(cracking_menu_frame, bg="#0A192F")
cracking_nav_hash_buttons_frame.pack(pady=10)
tk.Button(cracking_nav_hash_buttons_frame, text="Browse Hash File", command=lambda: cracking_select_hash_file(hash_file_entry), width=20, height=1, bg="#757575", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(cracking_nav_hash_buttons_frame, text="Run HashID", command=run_hashid, width=20, height=1, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(cracking_nav_hash_buttons_frame, text="Hash-Identifier", command=run_hash_identifier, width=20, height=1, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)



# Frame for Protocol & Port Entries (Ensures Proper Layout)
protocol_ports_nav_buttons_frame = tk.Frame(cracking_menu_frame, bg="#0A192F")
protocol_ports_nav_buttons_frame.pack(pady=10)

# Protocol Label & Entry
protocol_frame = tk.Frame(protocol_ports_nav_buttons_frame, bg="#0A192F")
protocol_frame.pack(side=tk.LEFT, padx=5)

tk.Label(protocol_frame, text="Enter Protocol:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
protocol_entry = tk.Entry(protocol_frame, width=25, bg="#333333", fg="white")
protocol_entry.pack()

# Port Label & Entry
cracking_port_frame = tk.Frame(protocol_ports_nav_buttons_frame, bg="#0A192F")
cracking_port_frame.pack(side=tk.LEFT, padx=5)

tk.Label(cracking_port_frame, text="Enter Port (if not using default:)", font=("Arial", 12), fg="white", bg="#0A192F").pack()
cracking_port_entry = tk.Entry(cracking_port_frame, width=25, bg="#333333", fg="white")
cracking_port_entry.pack()


# Entry for user wordlist selection
tk.Label(cracking_menu_frame, text="User or Wordlist:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
user_wordlist_entry = tk.Entry(cracking_menu_frame, width=50, bg="#333333", fg="white")
user_wordlist_entry.pack(pady=5)
tk.Button(cracking_menu_frame, text="Browse User Wordlist", command=lambda: cracking_user_wordlist(user_wordlist_entry), width=50, height=1, bg="#757575", fg="white").pack()

# Entry for password wordlist selection
tk.Label(cracking_menu_frame, text="Password or Wordlist:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
password_wordlist_entry = tk.Entry(cracking_menu_frame, width=50, bg="#333333", fg="white")
password_wordlist_entry.pack(pady=5)
tk.Button(cracking_menu_frame, text="Browse Password Wordlist", command=lambda: cracking_pass_wordlist(password_wordlist_entry), width=50, height=1, bg="#757575", fg="white").pack()

tk.Label(cracking_menu_frame, text="Manual Cracking:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
tool_option_entry = tk.Entry(cracking_menu_frame, width=50, bg="#333333", fg="white", font="bold")
tool_option_entry.pack()
tool_option_entry.bind("<Tab>", autocomplete_path)  # Enable inline file path completion

tk.Label(cracking_menu_frame, text="Hashcat Command:", font=("Arial", 12), fg="white", bg="#0A192F").pack()
hashcat_command_entry = tk.Entry(cracking_menu_frame, width=50)
hashcat_command_entry.pack(pady=5)

tools_nav_buttons_frame = tk.Frame(cracking_menu_frame, bg="#0A192F")
tools_nav_buttons_frame.pack(pady=10)

tk.Button(tools_nav_buttons_frame, text="John the Ripper", command=lambda: start_crack(run_john), width=20, height=1, bg="#1565C0", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(tools_nav_buttons_frame, text="Hydra", command=lambda: start_crack(run_hydra), width=20, height=1, bg="#1565C0", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(tools_nav_buttons_frame, text="CrackMapExec", command=lambda: start_crack(run_crackmap), width=20, height=1, bg="#1565C0", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(tools_nav_buttons_frame, text="Hashcat", command=lambda: start_crack(run_hashcat), width=20, height=1, bg="#1565C0", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(tools_nav_buttons_frame, text="Manual Cracking Options", command=lambda: start_crack(custom_crack), width=20, height=1, bg="#1565C0", fg="white").pack(side=tk.LEFT, padx=5)

cracking_status_label = tk.Label(cracking_menu_frame, text="Status: ⏳ Waiting for execution...", font=("Arial", 12), fg="yellow", bg="#0A192F")
cracking_status_label.pack()


# **Action Buttons**
#nmap
'''tk.Button(nmap_menu_frame, text="Cancel Scan", command=cancel_scan, width=50, height=2, bg="#f44336", fg="white").pack(pady=5)'''


#smb
'''tk.Button(smb_menu_frame, text="Cancel Scan", command=cancel_scan, width=50, height=2, bg="#f44336", fg="white").pack(pady=5)'''



#Password Cracking

nav_buttons_frame = tk.Frame(cracking_menu_frame, bg="#0A192F")
nav_buttons_frame.pack(pady=10)
tk.Button(nav_buttons_frame, text="Clear", command=cracking_clear_output, width=20, height=1, bg="#FF5722", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(nav_buttons_frame, text="Cancel Scan", command=cracking_cancel_scan, width=20, height=1, bg="#D32F2F", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(nav_buttons_frame, text="Core Offensive Security Menu", command=lambda: switch_to_frame(core_security_menu_frame), width=30, height=1, bg="#FFD700", fg="white").pack(side=tk.LEFT, padx=5)


#****Forensics****

# **Extract Metadata Menu**

tk.Label(forensics_metadata_frame, text="Extract Metadata", font=("Arial", 25, "bold"), fg="#64B5F6", bg="#0A192F").pack(pady=8)
tk.Label(forensics_metadata_frame, text="Select File:", font=("Arial", 14), fg="#FFFFFF", bg="#0A192F").pack()

# *File Selection Entry*
metadata_file_entry = tk.Entry(forensics_metadata_frame, width=50, bg="#333333", fg="white")
metadata_file_entry.pack()

# *Browse Button*
tk.Button(forensics_metadata_frame, text="Browse", command=lambda: forensics_select_metadata_file(metadata_file_entry), width=20, height=2, bg="#1565C0", fg="white").pack(pady=5)


# *Action Buttons*
forensics_nav_buttons_frame = tk.Frame(forensics_metadata_frame, bg="#0A192F")
forensics_nav_buttons_frame.pack(pady=10)

tk.Button(forensics_nav_buttons_frame, text="Identify File Type", command=run_forensics_file_type, width=20, height=2, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_buttons_frame, text="Exiftool", command=run_forensics_metadata_extraction, width=20, height=2, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_buttons_frame, text="Binwalk", command=run_forensics_binwalk, width=20, height=2, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)

forensics_nav_clear_back_frame = tk.Frame(forensics_metadata_frame, bg="#0A192F")
forensics_nav_clear_back_frame.pack(pady=10)

tk.Button(forensics_nav_clear_back_frame, text="Clear Output", command=forensics_clear_output, width=20, height=2, bg="#757575", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_clear_back_frame, text="Back to Forensics Menu", command=lambda: switch_to_frame(forensics_submenu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(side=tk.LEFT, padx=5)


# **Log Analysis**


# *Log File Selection Label*
tk.Label(forensics_log_frame, text="Select Log File:", font=("Arial", 14), fg="white", bg="#0A192F").pack()

# *Log File Entry Field*
log_file_entry = tk.Entry(forensics_log_frame, width=60, bg="#333333", fg="white")
log_file_entry.pack(pady=2)

# *Browse Button*
tk.Button(forensics_log_frame, text="Browse", command=lambda: forensics_select_log_file(log_file_entry), width=20, height=2, bg="#1565C0", fg="white").pack(pady=5)


# --- GREP ---
tk.Label(forensics_log_frame, text="Grep (optional):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
grep_entry = tk.Entry(forensics_log_frame, width=60, bg="#333333", fg="white")
grep_entry.pack(pady=2)

# --- CUT ---

tk.Label(forensics_log_frame, text="Cut delimiter:", font=("Arial", 12), fg="white", bg="#0A192F").pack()

cut_delim_var = tk.StringVar()
cut_delim_var.set("space")  # default

cut_delim_menu = tk.OptionMenu(forensics_log_frame, cut_delim_var, "space", "tab", "comma", "colon", "pipe", "custom")
cut_delim_menu.config(width=20, bg="#333333", fg="white")
cut_delim_menu.pack(pady=2)

# Custom delimiter entry (initially hidden unless "custom" is selected)
custom_delim_entry = tk.Entry(forensics_log_frame, width=10, bg="#333333", fg="white")
custom_delim_entry.pack(pady=2)
custom_delim_entry.pack_forget()

tk.Label(forensics_log_frame, text="Cut field(s) (e.g. 1 or 2,3):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
cut_fields_entry = tk.Entry(forensics_log_frame, width=30, bg="#333333", fg="white")
cut_fields_entry.pack(pady=2)


# --- AWK ---
tk.Label(forensics_log_frame, text="Awk expression: (e.g. {print $1} or {print $1,$2,$3} )", font=("Arial", 12), fg="white", bg="#0A192F").pack()
awk_entry = tk.Entry(forensics_log_frame, width=70, bg="#333333", fg="white")
awk_entry.pack(pady=2)

# --- SORT ---
tk.Label(forensics_log_frame, text="Sort option (e.g. -n -r):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
sort_option_entry = tk.Entry(forensics_log_frame, width=30, bg="#333333", fg="white")
sort_option_entry.pack(pady=2)

# --- UNIQ ---
tk.Label(forensics_log_frame, text="Uniq option (e.g. -c -d -u):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
uniq_option_entry = tk.Entry(forensics_log_frame, width=30, bg="#333333", fg="white")
uniq_option_entry.pack(pady=2)

forensics_nav_log_buttons_frame = tk.Frame(forensics_log_frame, bg="#0A192F")
forensics_nav_log_buttons_frame.pack(pady=10)

# --- Run Button ---
tk.Button(forensics_nav_log_buttons_frame, text="Run Custom Pipeline", command=run_forensics_log_custom_pipeline, width=20, height=2, bg="#29B6F6", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_log_buttons_frame, text="Save Output to File", command=export_log_analysis_output, width=20, height=2, bg="#43A047", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_log_buttons_frame, text="Clear Output", command=forensics_log_clear_output, width=20, height=2, bg="#757575", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_log_buttons_frame, text="Back to Forensics Menu", command=lambda: switch_to_frame(forensics_submenu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(side=tk.LEFT, padx=5)


# **Minion SmartDecode**

# *Entry field for encoded input*
tk.Label(forensics_base_frame, text="Encoded input (e.g. Base64, Hex, URL):", font=("Arial", 12), fg="white", bg="#0A192F").pack()
forensics_base_input_entry = tk.Entry(forensics_base_frame, width=100, bg="#1C1C1C", fg="white", font=("Courier", 12))
forensics_base_input_entry.pack(padx=10, pady=(5, 10))

forensics_nav_base_decode_buttons_frame = tk.Frame(forensics_base_frame, bg="#0A192F")
forensics_nav_base_decode_buttons_frame.pack(pady=10)

tk.Button(forensics_nav_base_decode_buttons_frame, text="Detect Encoding", command=run_base_detection, width=20, height=2, bg="#1E88E5", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_base_decode_buttons_frame, text="Deep Decode 🔎", command=run_full_chain_detection, width=20).pack(side=tk.LEFT, padx=5)


forensics_nav_base_buttons_frame = tk.Frame(forensics_base_frame, bg="#0A192F")
forensics_nav_base_buttons_frame.pack(pady=10)

tk.Button(forensics_nav_base_buttons_frame, text="Clear", command=forensics_base_clear_output, width=20, height=2, bg="#29B6F6", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_base_buttons_frame, text="Save Output", command=export_base_output, width=20, height=2, bg="#43A047", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(forensics_nav_base_buttons_frame, text="Back to Forensics Menu", command=lambda: switch_to_frame(forensics_submenu_frame), width=20, height=2, bg="#B71C1C", fg="white").pack(side=tk.LEFT, padx=5)






#tk.Button(forensics_log_frame, text="Run Custom Pipeline", command=run_forensics_log_custom_pipeline, width=20, height=2, bg="#29B6F6", fg="white").pack()









# Run system check before starting GUI
if __name__ == "__main__":
    error_message = check_system()

    if error_message:
        print(error_message)  # Alert user only if something is wrong
    else:
        while True:
            try:
                root.mainloop()  # Starts the GUI
                break  # If successful, exit loop
            except KeyboardInterrupt:
                print("\n⚠️ GUI interrupted! Restarting...")
                continue  # Loops back to prevent full termination
