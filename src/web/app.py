#!/usr/bin/env python3
import os
import json
import uuid
import secrets
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file, jsonify

from .. import video_upload_workflow

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = Path(os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads')))
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

# Create upload folder if it doesn't exist
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video_file' not in request.files:
        flash('No video file part')
        return redirect(request.url)
    
    video_file = request.files['video_file']
    
    if video_file.filename == '':
        flash('No video selected')
        return redirect(request.url)
    
    if not allowed_file(video_file.filename):
        flash(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}')
        return redirect(request.url)
    
    # Create a unique folder for this upload
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    session_folder = UPLOAD_FOLDER / session_id
    session_folder.mkdir(exist_ok=True)
    
    # Save OpenAI API key
    openai_api_key = request.form.get('openai_api_key', '')
    with open(session_folder / 'openai_api_key.txt', 'w') as f:
        f.write(openai_api_key)
    os.environ['OPENAI_API_KEY'] = openai_api_key
    
    # Save YouTube client secrets
    if 'client_secrets' in request.files:
        client_secrets_file = request.files['client_secrets']
        if client_secrets_file.filename != '':
            client_secrets_file.save(session_folder / 'client_secrets.json')
    
    # Save YouTube token if provided
    if 'token_pickle' in request.files:
        token_pickle_file = request.files['token_pickle']
        if token_pickle_file.filename != '':
            token_pickle_file.save(session_folder / 'token.pickle')
    
    # Save thumbnail if provided
    if 'thumbnail' in request.files:
        thumbnail_file = request.files['thumbnail']
        if thumbnail_file.filename != '':
            thumbnail_file.save(session_folder / 'thumbnail.png')
    
    # Save the uploaded video
    video_path = session_folder / 'input_video.mp4'
    video_file.save(video_path)
    
    # Redirect to the processing page
    return redirect(url_for('process_video'))

@app.route('/process', methods=['GET', 'POST'])
def process_video():
    session_id = session.get('session_id')
    if not session_id:
        flash('No active upload session')
        return redirect(url_for('index'))
    
    session_folder = UPLOAD_FOLDER / session_id
    if not session_folder.exists():
        flash('Upload session not found')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Check if the user wants to skip color editing
        skip_color_edit = 'skip_color_edit' in request.form
        
        # Start processing the video
        input_video = str(session_folder / 'input_video.mp4')
        
        # Change to the session directory to work with the uploaded files
        original_dir = os.getcwd()
        os.chdir(str(session_folder))
        
        try:
            # Step 1: Color edit the video (unless skipped)
            output_video = Path("output.mp4")
            if skip_color_edit:
                print("Color editing step skipped. Using input video for subsequent steps.")
                output_video = Path(input_video)
                # Save info that color editing was skipped
                with open('color_edit_skipped.txt', 'w') as f:
                    f.write('true')
            else:
                video_upload_workflow.color_edit_video(input_video, output_video)
            
            # Step 2: Transcribe the video
            output_srt = Path("output.srt")
            video_upload_workflow.transcribe_video(output_video, output_srt)
            
            # Step 3: Generate chapters and suggested titles
            chapters_json = Path("chapters_and_suggested_titles.json")
            video_upload_workflow.generate_chapters(output_srt, chapters_json)
            
            # Step 4: Extract chapter markers and suggested titles
            chapters, titles = video_upload_workflow.extract_chapters_and_titles(chapters_json)
            
            # Save chapters and titles for the next step
            with open('chapters.txt', 'w') as f:
                f.write(chapters)
            
            with open('titles.json', 'w') as f:
                json.dump(titles, f)
            
            # Redirect to title selection page
            return redirect(url_for('select_title'))
        
        except Exception as e:
            flash(f"Error during processing: {str(e)}")
            return redirect(url_for('index'))
        finally:
            os.chdir(original_dir)
    
    return render_template('process.html')

@app.route('/select_title', methods=['GET', 'POST'])
def select_title():
    session_id = session.get('session_id')
    if not session_id:
        flash('No active upload session')
        return redirect(url_for('index'))
    
    session_folder = UPLOAD_FOLDER / session_id
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        with open(session_folder / 'final_title.txt', 'w') as f:
            f.write(title)
        
        # Get chapters from file
        chapters_text = (session_folder / 'chapters.txt').read_text()
        
        # Save description with chapters
        with open(session_folder / 'description.txt', 'w') as f:
            f.write(chapters_text)
        
        return redirect(url_for('edit_description'))
    
    try:
        with open(session_folder / 'titles.json', 'r') as f:
            titles = json.load(f)
    except:
        titles = ["No titles were generated"]
    
    return render_template('select_title.html', titles=titles)

@app.route('/edit_description', methods=['GET', 'POST'])
def edit_description():
    session_id = session.get('session_id')
    if not session_id:
        flash('No active upload session')
        return redirect(url_for('index'))
    
    session_folder = UPLOAD_FOLDER / session_id
    
    if request.method == 'POST':
        description = request.form.get('description', '')
        with open(session_folder / 'description.txt', 'w') as f:
            f.write(description)
        
        return redirect(url_for('confirm_upload'))
    
    try:
        description = (session_folder / 'description.txt').read_text()
    except:
        description = ""
    
    return render_template('edit_description.html', description=description)

@app.route('/confirm', methods=['GET', 'POST'])
def confirm_upload():
    session_id = session.get('session_id')
    if not session_id:
        flash('No active upload session')
        return redirect(url_for('index'))
    
    session_folder = UPLOAD_FOLDER / session_id
    
    if request.method == 'POST':
        original_dir = os.getcwd()
        os.chdir(str(session_folder))
        
        try:
            # Get the final title
            final_title = (session_folder / 'final_title.txt').read_text()
            
            # Check if color edit was skipped
            color_edit_skipped = (session_folder / 'color_edit_skipped.txt').exists()
            
            # Use the appropriate video path based on whether color edit was skipped
            if color_edit_skipped:
                video_path = str(session_folder / 'input_video.mp4')
            else:
                video_path = str(session_folder / 'output.mp4')
                
            # Upload the video
            video_upload_workflow.upload_video(final_title, video_path)
            
            flash('Video successfully uploaded to YouTube!')
        except Exception as e:
            flash(f"Error during upload: {str(e)}")
        finally:
            os.chdir(original_dir)
        
        return redirect(url_for('download_results'))
    
    try:
        title = (session_folder / 'final_title.txt').read_text()
        description = (session_folder / 'description.txt').read_text()
    except:
        title = ""
        description = ""
    
    return render_template('confirm.html', title=title, description=description)

@app.route('/download')
def download_results():
    session_id = session.get('session_id')
    if not session_id:
        flash('No active upload session')
        return redirect(url_for('index'))
    
    session_folder = UPLOAD_FOLDER / session_id
    
    files = {}
    for file in ['output.mp4', 'output.srt', 'chapters_and_suggested_titles.json', 'description.txt']:
        file_path = session_folder / file
        if file_path.exists():
            files[file] = True
        else:
            files[file] = False
    
    return render_template('download.html', files=files, session_id=session_id)

@app.route('/download/<session_id>/<filename>')
def download_file(session_id, filename):
    file_path = UPLOAD_FOLDER / session_id / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found')
        return redirect(url_for('download_results'))

@app.route('/api/status/<session_id>')
def get_process_status(session_id):
    session_folder = UPLOAD_FOLDER / session_id
    
    status = {
        'color_edit': (session_folder / 'output.mp4').exists(),
        'transcription': (session_folder / 'output.srt').exists(),
        'chapters': (session_folder / 'chapters_and_suggested_titles.json').exists(),
        'titles_extracted': (session_folder / 'titles.json').exists(),
        'description': (session_folder / 'description.txt').exists(),
        'title_selected': (session_folder / 'final_title.txt').exists()
    }
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
