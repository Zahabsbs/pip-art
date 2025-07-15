import sys
import time
import subprocess
import threading
import os
import random
import json
from pathlib import Path
import requests
import tempfile
import toml

from term_image.image import from_file
from term_image.exceptions import TermImageError
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn

# --- Configuration ---
# The GitHub repository where the art gallery is stored.
# This serves as the DEFAULT if no config file is found.
DEFAULT_ART_GALLERY_REPO = "Zahabsbs/pip-art-gallery"
REQUEST_TIMEOUT = 10 # Seconds to wait for a response from GitHub

# --- Fallback Art ---
# If the online gallery can't be reached, this local image will be shown.
FALLBACK_IMAGE_PATH = Path(__file__).parent / "images" / "images.jpg"
FALLBACK_METADATA = {
    "title": "MonkaS",
    "author": "Pepe the Frog",
    "description": "This is a local fallback image. When you feel anxious about long-running commands."
}

def get_config():
    """
    Looks for a config file (~/.pip-art.toml), loads it, and returns the config.
    Returns a dictionary with configuration settings.
    """
    config_path = Path.home() / ".pip-art.toml"
    config = {"gallery_repo": DEFAULT_ART_GALLERY_REPO} # Start with default

    if config_path.is_file():
        try:
            user_config = toml.load(config_path)
            # Overwrite default if the key exists in user's config
            if "gallery_repo" in user_config:
                config["gallery_repo"] = user_config["gallery_repo"]
        except toml.TomlDecodeError:
            # Handle cases where the TOML file is malformed
            _print_error_box(f"Warning: Could not parse config file at {config_path}. Using defaults.")
            pass # Keep using default config

    return config

def _print_error_box(message):
    """Prints a message inside a formatted rich Panel."""
    console = Console()
    console.print(Panel(Text(message, justify="center"), title="[bold red]Error[/bold red]", border_style="red"))


def fetch_random_art_from_gallery(temp_dir):
    """
    Fetches a list of available art from the GitHub gallery, downloads a
    random image and its metadata to a temporary directory.
    
    On network failure, returns a path to a local fallback image.
    Returns a tuple: (Path_to_image | Error_string, metadata_dict)
    """
    config = get_config()
    art_gallery_repo = config.get("gallery_repo", DEFAULT_ART_GALLERY_REPO)
    
    # If the gallery repo is not configured (still the placeholder), use the fallback.
    if art_gallery_repo == "YOUR_USERNAME/YOUR_REPO":
        return FALLBACK_IMAGE_PATH, FALLBACK_METADATA

    gallery_api_url = f"https://api.github.com/repos/{art_gallery_repo}/contents/images"
        
    try:
        # Show a loading message while fetching the gallery list
        console = Console()
        with console.status("🎨 Fetching gallery list..."):
            response = requests.get(gallery_api_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raise an exception for bad status codes
        
        files = response.json()
        if not isinstance(files, list):
             return "Invalid response from GitHub API: expected a list of files.", {}

        image_files = [
            f for f in files 
            if isinstance(f, dict) and f.get('type') == 'file' and f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]

        if not image_files:
            # If the gallery is empty, don't show an error, just use the fallback.
            return FALLBACK_IMAGE_PATH, FALLBACK_METADATA

        # Select a random image file object
        random_image_data = random.choice(image_files)
        random_image_name = random_image_data['name']
        
        base_name, _ = os.path.splitext(random_image_name)
        json_name = f"{base_name}.json"

        # Find the corresponding JSON file data in the initial list
        json_file_data = next((f for f in files if f['name'] == json_name), None)

        # Download the image
        image_url = random_image_data.get('download_url')
        if not image_url:
            return f"Could not find download URL for '{random_image_name}'.", {}

        temp_image_path = Path(temp_dir) / random_image_name
        
        # Use rich.progress to show a download bar
        with Progress(
            TextColumn("[bold blue]Downloading: {task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task(random_image_name, start=False)
            
            with requests.get(image_url, stream=True, timeout=REQUEST_TIMEOUT) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                progress.update(task, total=total_size)
                
                progress.start_task(task)
                with open(temp_image_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

        # Download metadata if it exists
        metadata = {}
        if json_file_data and json_file_data.get('download_url'):
            json_url = json_file_data['download_url']
            try:
                json_response = requests.get(json_url, timeout=REQUEST_TIMEOUT)
                json_response.raise_for_status()
                metadata = json_response.json()
            except (requests.exceptions.RequestException, json.JSONDecodeError):
                # If metadata fails, we can proceed without it.
                # It's not critical.
                pass
        
        return temp_image_path, metadata

    except (requests.exceptions.RequestException, requests.exceptions.Timeout, KeyError, IndexError, TypeError, json.JSONDecodeError):
        # On any network or data error, return the local fallback art. It's more user-friendly.
        return FALLBACK_IMAGE_PATH, FALLBACK_METADATA


def load_art_from_file(image_path):
    """
    Loads an image from a local file path and prepares it for display.
    """
    try:
        # Create a term-image object, setting a fixed height.
        art_object = from_file(image_path, height=40)
        return art_object
    except TermImageError as e:
        # Instead of returning a string, we print a formatted error.
        # This prevents the art display thread from crashing.
        _print_error_box(f"Art image at '{image_path}' could not be processed.")
        return None
    except FileNotFoundError:
        _print_error_box(f"Art image file not found at: '{image_path}'")
        return None


def display_art(art_object, metadata, stop_event):
    """
    Displays art in the terminal's alternate screen buffer to avoid flickering
    and preserve the user's command history.
    """
    console = Console()
    
    if isinstance(art_object, str):
        # Even errors should be displayed cleanly without messing up the terminal
        print("\x1b[?1049h\x1b[?25l", end="") # Enter alternate screen
        try:
            _print_error_box(art_object)
            stop_event.wait()
        finally:
            print("\x1b[?1049l\x1b[?25h", end="") # Leave alternate screen
        return

    if not art_object:
        stop_event.wait() # Nothing to display, just wait for command
        return

    # --- Prepare Metadata Text ---
    title = metadata.get('title', 'Untitled')
    description = f"\"{metadata.get('description', 'This piece of art is waiting for its story.')}\""
    author = f"Art by: {metadata.get('author', 'Unknown')}"
    
    metadata_panel = Panel(
        Text(f"{description}\n{author}", justify="center"),
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        expand=False
    )
    
    # Enter alternate screen buffer and hide cursor
    print("\x1b[?1049h\x1b[?25l", end="")

    try:
        # We need the last frame for animated GIFs to redraw after the loop.
        last_frame = None

        if not art_object.is_animated:
            # --- STATIC IMAGE ---
            # Draw the art and text once, then show a spinner while waiting.
            print("\x1b[H", end="")  # Move cursor to home position
            print(str(art_object))
            console.print(metadata_panel)
            
            # Show a status spinner while the command runs in the background.
            with console.status("[bold yellow]Running your command...", spinner="dots"):
                stop_event.wait() # Wait for the command to finish
        else:
            # --- ANIMATED IMAGE ---
            # Loop through frames, redrawing with a manual spinner.
            frame_iterator = iter(art_object)

            # Pre-render the panel to a string to speed up the animation loop
            with console.capture() as capture:
                console.print(metadata_panel)
            metadata_text = capture.get()

            spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner_idx = 0

            while not stop_event.is_set():
                try:
                    frame = next(frame_iterator)
                    last_frame = frame
                except StopIteration:
                    frame_iterator = iter(art_object)  # Loop the animation
                    continue
                
                # Prepare the spinner line for this frame
                spinner_char = spinner_frames[spinner_idx % len(spinner_frames)]
                spinner_idx += 1
                
                # Use rich formatting for the spinner line
                spinner_line = f"\n  {spinner_char} [bold yellow]Running your command...[/bold yellow]"
                with console.capture() as capture:
                    console.print(spinner_line)
                spinner_text_formatted = capture.get()

                full_frame_output = str(frame) + metadata_text + spinner_text_formatted
                
                # Move cursor to home, then print, overwriting the previous frame.
                print("\x1b[H", end="")
                print(full_frame_output, end="", flush=True)
                
                # Wait for the frame's duration, checking event for faster shutdown
                if stop_event.wait(timeout=frame.duration if frame.duration > 0 else 0.05):
                    break  # Exit loop if event is set
        
        # After the command finishes, the spinner is gone (or needs to be removed).
        # We redraw the screen in a clean final state before showing the prompt.
        if art_object.is_animated:
            # For animated GIFs, the spinner was drawn manually, so we must clear
            # the screen and redraw the last frame to remove it.
            print("\x1b[H\x1b[J", end="") # Clear screen and move to home
            if last_frame:
                print(str(last_frame))
            else: # Fallback in case the loop never ran
                print(str(art_object))
            console.print(metadata_panel)

        # The command has now finished. The art (or last frame of it) is still on screen.
        # Print a final message below the art and wait for the user to press Enter.
        console.print(Panel(
            Text("✨ Command finished! ✨\nPress Enter to continue...", justify="center"),
            border_style="green"
        ))
        input()

    finally:
        # Leave alternate screen buffer, show cursor, and restore the terminal.
        print("\x1b[?1049l\x1b[?25h", end="")


def run_command(command, stop_event, result_container):
    """
    Runs the given command in the background, captures its output,
    stores the exit code, and sets the stop_event when it completes.
    """
    try:
        # Use shell=True only for string-based commands (from -c flag).
        # It's safer and more reliable for list-based commands to use shell=False.
        use_shell = isinstance(command, str)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=use_shell,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        stdout, stderr = process.communicate()
        exit_code = process.returncode

        result_container["exit_code"] = exit_code
        if stdout:
            result_container["stdout"] = stdout
        if stderr:
            result_container["stderr"] = stderr

    except Exception as e:
        result_container["exit_code"] = 1 # Generic failure
        result_container["error_message"] = str(e)
    finally:
        stop_event.set()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("Usage: pip-art [-c] <command-to-run>")
        print("\nDisplays terminal art while the specified command runs.")
        print("Pass the command directly, or use -c for commands with complex quoting.")
        print("\nExamples:")
        print("  pip-art pip install numpy")
        print("  pip-art -c \"echo 'Hello World'\"")
        sys.exit(1)

    # Handle '-c' flag for passing command as a single string
    if sys.argv[1] == '-c':
        if len(sys.argv) < 3:
            _print_error_box("Error: The '-c' flag requires a command string to be provided.")
            sys.exit(1)
        command_to_run = sys.argv[2] # The command is the third argument
    else:
        # If no '-c' is used, treat all following arguments as the command
        command_to_run = sys.argv[1:]

    command_result = {} # To store the exit code from the thread

    art_object = None # Default to None
    metadata = {}
    
    # Use a temporary directory for downloaded art
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path_or_error, metadata = fetch_random_art_from_gallery(temp_dir)

        # If fetching was successful, load the image from the temporary file
        if isinstance(image_path_or_error, Path):
            art_object = load_art_from_file(image_path_or_error)
        else: # If there was an error string
            art_object = image_path_or_error # Pass the error string to display_art
    
    stop_event = threading.Event()
    
    display_thread = threading.Thread(
        target=display_art,
        args=(art_object, metadata, stop_event),
    )
    command_thread = threading.Thread(
        target=run_command,
        args=(command_to_run, stop_event, command_result),
    )

    display_thread.start()
    command_thread.start()

    command_thread.join()
    display_thread.join()
    
    # After closing the alternate screen, print the final status.
    exit_code = command_result.get("exit_code")
    error_message = command_result.get("error_message")
    stdout = command_result.get("stdout")
    stderr = command_result.get("stderr")

    console = Console()
    if exit_code == 0:
        console.print(Panel(
            Text("✅ Success! The command completed without errors.", justify="center"),
            title="[bold green]Status Report[/bold green]",
            border_style="green"
        ))
    elif exit_code is not None:
        error_text = f"❌ Failed! The command finished with exit code {exit_code}."
        if error_message:
            error_text += f"\n\n[bold yellow]Reason:[/bold yellow]\n{error_message}"
        if stderr:
            error_text += f"\n\n[bold]Error Output (stderr):[/bold]\n{stderr}"
        if stdout:
            error_text += f"\n\n[bold]Standard Output (stdout):[/bold]\n{stdout}"

        console.print(Panel(
            Text(error_text, justify="left"),
            title="[bold red]Status Report[/bold red]",
            border_style="red"
        ))
        console.print("[yellow]Note: Original command output was captured above. Run without 'pip-art' to interact directly.[/yellow]")


if __name__ == "__main__":
    main() 