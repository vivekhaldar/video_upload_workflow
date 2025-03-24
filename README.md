
# Video Processing Pipeline

This repository contains a Python script that automates a video processing pipeline. The script performs the following tasks:

1. **Color Edit:** Applies a color editing filter to the input video.
2. **Transcription:** Transcribes the color-edited video using OpenAI's Whisper.
3. **Chapter Generation:** Generates chapters and suggested titles based on the transcription.
4. **Title Selection:** Lets you select and optionally edit a title using `fzf`.
5. **Description Editing:** Creates a description file with chapter markers and opens it in your preferred editor.
6. **Confirmation:** Provides a review step (with an option to skip) before the final upload.
7. **Upload:** Uploads the video to YouTube along with the transcript, description, and thumbnail.

## Requirements

Before running the script, make sure you have the following installed:

- **Python 3.6+**
- **uvx** – along with its required plugins:
  - [color_edit](https://github.com/vivekhaldar/color_edit)
  - [yt_chapter_maker](https://github.com/vivekhaldar/yt_chapter_maker)
  - [yt_upload](https://github.com/vivekhaldar/yt_upload)

Also, ensure your `$EDITOR` environment variable is set to your preferred text editor (defaults to `nano` if not set).


## Usage

The script is intended to be run from the command line. Its basic syntax is:

```bash
uvx --from git+https://github.com/vivekhaldar/video_upload_workflow video_upload_workflow input_video.mp4
```

For the step that uploads to YouTube, the following credentials are expected in the current directory:
- `client_secrets.json` for using the YouTube upload API
- `token.pickle` as the saved credential for your specific YouTube channel

The tool also expects `thumbnail.png` in the current directory.

## Workflow Details

1. **Color Edit:**  
   Checks if `output.mp4` exists. If not, it applies the color editing filter to the input video.

2. **Transcription:**  
   Transcribes the color-edited video into `output.srt`.

3. **Chapter Generation:**  
   Generates chapters and suggested titles and saves them in `chapters_and_suggested_titles.json`.

4. **Extraction:**  
   Extracts and displays chapter markers and suggested titles from the JSON file.

5. **Title Selection:**  
   Choose a title from the suggestions, with an option to edit.

6. **Description Editing:**  
   Creates `description.txt` with chapter markers and opens it in your editor for further customization.

7. **Confirmation:**  
   Reviews the final title and description. If you run without the `--yes` flag, you'll be prompted to confirm before upload.

8. **Upload:**  
   Uploads the video to YouTube along with the transcript, description, and thumbnail.

