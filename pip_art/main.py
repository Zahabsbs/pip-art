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

from term_image.image import from_file
from term_image.exceptions import TermImageError
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

# --- Configuration ---
# The GitHub repository where the art gallery is stored.
# The tool will fetch images from the 'images' directory of this repo.
# IMPORTANT: This must be a public repository.
# TO CHANGE: Replace "YOUR_USERNAME/YOUR_REPO" with your actual GitHub username and repository name.
ART_GALLERY_REPO = "YOUR_USERNAME/YOUR_REPO"
GALLERY_API_URL = f"https://api.github.com/repos/{ART_GALLERY_REPO}/contents/images"
REQUEST_TIMEOUT = 10 # Seconds to wait for a response from GitHub

# --- Fallback Art ---
# If the online gallery can't be reached, this local image will be shown.
FALLBACK_IMAGE_PATH = Path(__file__).parent / "images" / "images.jpg"
FALLBACK_METADATA = {
    "title": "Gallery Not Found",
    "author": "pip-art",
    "description": "Could not fetch art from the online gallery. Showing a local friend instead."
}

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
    try:
        response = requests.get(GALLERY_API_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        files = response.json()
        if not isinstance(files, list):
             return "Invalid response from GitHub API: expected a list of files.", {}

        image_files = [
            f for f in files 
            if isinstance(f, dict) and f.get('type') == 'file' and f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]

        if not image_files:
            return "No compatible images found in the online gallery.", {}

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

        image_response = requests.get(image_url, timeout=REQUEST_TIMEOUT)
        image_response.raise_for_status()
        
        temp_image_path = Path(temp_dir) / random_image_name
        with open(temp_image_path, 'wb') as f:
            f.write(image_response.content)

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

    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        # On any network-related error (404, timeout, no connection),
        # return the local fallback art instead of an error message.
        return FALLBACK_IMAGE_PATH, FALLBACK_METADATA
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return "Invalid or unexpected data from GitHub API.", {}


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
        if not art_object.is_animated:
            # --- STATIC IMAGE ---
            # Draw the art and text once, then just wait for the event. No loops.
            print("\x1b[H", end="")  # Move cursor to home position
            print(str(art_object))
            console.print(metadata_panel)
            stop_event.wait()
        else:
            # --- ANIMATED IMAGE ---
            # Loop through frames, redrawing by overwriting the previous frame.
            frame_iterator = iter(art_object)

            # Pre-render the panel to a string to speed up the animation loop
            with console.capture() as capture:
                console.print(metadata_panel)
            metadata_text = capture.get()

            while not stop_event.is_set():
                try:
                    frame = next(frame_iterator)
                except StopIteration:
                    frame_iterator = iter(art_object)  # Loop the animation
                    continue

                full_frame_output = str(frame) + metadata_text
                
                # Move cursor to home, then print, overwriting the previous frame.
                print("\x1b[H", end="")
                print(full_frame_output, end="", flush=True)
                
                # Wait for the frame's duration, checking event for faster shutdown
                if stop_event.wait(timeout=frame.duration if frame.duration > 0 else 0.05):
                    break  # Exit loop if event is set

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


def run_command(command, stop_event):
    """
    Runs the given command in the background with its output suppressed,
    and sets the stop_event when it completes.
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.wait()
    finally:
        # Ensure the event is always set, even if the command fails
        stop_event.set()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("Usage: pip-art <command-to-run>")
        print("\nDisplays terminal art while the specified command runs.")
        print("Art is fetched from a community gallery on GitHub.")
        print("\nExample: pip-art pip install numpy")
        sys.exit(1)

    command_to_run = sys.argv[1:]

    art_object = None # Default to None
    metadata = {}
    
    # Use a temporary directory for downloaded art
    with tempfile.TemporaryDirectory() as temp_dir:
        # Show a loading message while fetching
        print("🎨 Fetching a random piece of art from the gallery...")
        
        image_path_or_error, metadata = fetch_random_art_from_gallery(temp_dir)

        # If fetching was successful, load the image from the temporary file
        if isinstance(image_path_or_error, Path):
            art_object = load_art_from_file(image_path_or_error)
        else:
            # Otherwise, the error message itself is the "art"
            # The display function will know how to format it.
            art_object = image_path_or_error
        
        stop_event = threading.Event()
        
        art_thread = threading.Thread(target=display_art, args=(art_object, metadata, stop_event))
        art_thread.start()

        command_thread = threading.Thread(target=run_command, args=(command_to_run, stop_event))
        command_thread.start()

        command_thread.join()
        art_thread.join()


if __name__ == "__main__":
    main() 