#!/usr/bin/env python3
"""
This script processes a video through several steps:
  1. Color edits the video.
  2. Transcribes the video.
  3. Generates chapters and suggested titles.
  4. Extracts chapters and suggested titles.
  5. Lets the user choose and optionally edit a title.
  6. Creates a description file and allows editing.
  7. Asks for confirmation (unless --yes is provided).
  8. Uploads the video to YouTube.

It requires the commands: uvx. Make sure these are installed.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def check_required_commands():
    """Check that all required external commands are available."""
    required_cmds = ["uvx"]
    for cmd in required_cmds:
        if shutil.which(cmd) is None:
            print(f"Error: {cmd} is not installed. Please install it and try again.", file=sys.stderr)
            sys.exit(1)

def run_command(command, description=""):
    """
    Run a command with subprocess.run.
    
    Args:
        command (list): The command and its arguments as a list.
        description (str): A short description of what the command does.
    """
    if description:
        print(description)
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as err:
        print(f"Error while running: {' '.join(command)}", file=sys.stderr)
        sys.exit(err.returncode)

def color_edit_video(input_video: str, output_video: Path, volume_threshold="0.002"):
    """Perform color editing on the video if output file does not already exist."""
    print("=== Step 1: Color-edit the video ===")
    if output_video.exists():
        print(f"{output_video} already exists, skipping color-edit step.")
    else:
        cmd = [
            "color_edit",
            "--input", input_video,
            "--output", str(output_video),
            "--volume_threshold", volume_threshold
        ]
        run_command(cmd, "Running color edit...")
        print(f"Color editing complete: {output_video} is available.")
    print()

def transcribe_video(input_video: Path, output_srt: Path):
    """Transcribe the video if transcription file does not already exist."""
    print("=== Step 2: Transcribe the video ===")
    if output_srt.exists():
        print(f"{output_srt} already exists, skipping transcription step.")
    else:
        cmd = [
            "whisper",
            "--output_format", "srt",
            "--task", "transcribe",
            str(input_video)
        ]
        run_command(cmd, "Transcribing video...")

        # whisper puts the output in a file named <input_video>.srt.
        # Move it to the desired output path
        srt_file = input_video.with_suffix(".srt")
        if srt_file.exists():
            srt_file.rename(output_srt)
        else:
            print(f"Error: Transcription output {srt_file} not found.", file=sys.stderr)
            sys.exit(1)
        print(f"Transcription complete: {output_srt} is available.")
    print()

def generate_chapters(input_srt: Path, output_json: Path):
    """Generate chapters and suggested titles from the transcript."""
    print("=== Step 3: Generate chapters and suggested titles ===")
    if output_json.exists():
        print(f"{output_json} already exists, skipping chapters generation step.")
    else:
        cmd = [
            "yt_chapter_maker",
            "--input", str(input_srt),
            "--output", str(output_json)
        ]
        run_command(cmd, "Generating chapters and titles...")
        print(f"Chapters and titles are available in {output_json}.")
    print()

def extract_chapters_and_titles(json_file: Path):
    """
    Extract chapters and suggested titles from the JSON output.
    
    Returns:
        tuple: (chapters as str, list of suggested titles)
    """
    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    chapters = data.get("chapters", "")
    titles = data.get("suggested_titles", [])
    return chapters, titles

def select_and_edit_title(titles):
    """
    Let the user choose a title from the suggested list and optionally edit it.
    
    Args:
        titles (list): A list of suggested titles.
    
    Returns:
        str: The final title to use.
    """
    print("=== Step 5: Choose and edit a title ===")
    
    # Print all suggested titles with numbers
    print("Suggested titles:")
    for i, title in enumerate(titles, 1):
        print(f"{i}. {title}")
    print()
    
    # Let user select a title by number
    while True:
        try:
            selection = input("Enter the number of your preferred title (or 0 to enter a custom title): ")
            selection = int(selection.strip())
            
            if selection == 0:
                selected_title = input("Enter your custom title: ").strip()
                break
            elif 1 <= selection <= len(titles):
                selected_title = titles[selection - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(titles)}, or 0 for custom title.")
        except ValueError:
            print("Please enter a valid number.")
    
    print(f"Selected title: {selected_title}")
    
    # Let user edit the selected title if desired
    input_title = input("Edit title (press Enter to keep the above): ").strip()
    final_title = input_title if input_title else selected_title
    print(f"Final title: {final_title}")
    print()
    return final_title

def edit_description(chapters):
    """
    Create a description file with chapter markers and let the user edit it.
    
    Returns:
        Path: The path to the description file.
    """
    description_file = Path("description.txt")
    # Write the chapters to description.txt
    description_file.write_text(chapters, encoding="utf-8")
    print("=== Step 6: Create and edit the description ===")
    print(f"A description file ({description_file}) with chapter markers has been created.")
    
    # Open the user's preferred editor (default to nano if not set)
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(description_file)])
    
    print("Final description:")
    print(description_file.read_text(encoding="utf-8"))
    print()
    return description_file

def confirm_upload(final_title, description_file, skip_confirmation):
    """
    Display a review before upload and ask the user for confirmation.
    
    Args:
        final_title (str): The final title chosen.
        description_file (Path): The description file.
        skip_confirmation (bool): If True, skip the confirmation step.
    """
    if skip_confirmation:
        return
    print("=== Review Before Upload ===")
    print("Title:", final_title)
    print("Description:")
    print(description_file.read_text(encoding="utf-8"))
    print()
    confirm = input("Proceed with upload? (y/N): ").strip()
    if confirm.lower() != "y":
        print("Upload cancelled.")
        sys.exit(0)

def upload_video(final_title, video_path):
    """Upload the video using the provided title and associated files."""
    print("=== Step 8: Uploading video to YouTube ===")
    cmd = [
        "yt_upload",
        "--video", str(video_path),
        "--transcript", "output.srt",
        "--description", "description.txt",
        "--thumbnail", "thumbnail.png",
        "--title", final_title
    ]
    run_command(cmd, "Uploading video...")
    print("Upload complete!")

def main():
    parser = argparse.ArgumentParser(
        description="Process a video: color-edit, transcribe, generate chapters/titles, and upload to YouTube."
    )
    parser.add_argument("input_video", help="Path to the input video file (e.g., input_video.mp4)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation before upload")
    parser.add_argument("--skip-color-edit", action="store_true", help="Skip the color editing step")
    parser.add_argument("--volume-threshold", default="0.002", help="Volume threshold for color editing")
    args = parser.parse_args()

    check_required_commands()

    input_video = args.input_video
    skip_confirmation = args.yes
    skip_color_edit = args.skip_color_edit
    volume_threshold = args.volume_threshold

    # Step 1: Color edit the video.
    output_video = Path("output.mp4")
    if skip_color_edit:
        print("=== Step 1: Color-edit the video ===")
        print(f"Color editing step skipped. Using input video for subsequent steps.")
        output_video = Path(input_video)
        print()
    else:
        color_edit_video(input_video, output_video, volume_threshold)

    # Step 2: Transcribe the video.
    output_srt = Path("output.srt")
    transcribe_video(output_video, output_srt)

    # Step 3: Generate chapters and suggested titles.
    chapters_json = Path("chapters_and_suggested_titles.json")
    generate_chapters(output_srt, chapters_json)

    # Step 4: Extract chapter markers and suggested titles.
    chapters, titles = extract_chapters_and_titles(chapters_json)
    print("=== Step 4: Extract chapter markers and suggested titles ===")
    print("Chapters:")
    print(chapters)
    print()
    print("Suggested Titles:")
    for t in titles:
        print(t)
    print()

    # Step 5: Choose and edit a title.
    final_title = select_and_edit_title(titles)

    # Step 6: Create and edit the description.
    description_file = edit_description(chapters)

    # Step 7: Confirmation before upload.
    confirm_upload(final_title, description_file, skip_confirmation)

    # Step 8: Upload the video.
    upload_video(final_title, output_video)

if __name__ == "__main__":
    main()
