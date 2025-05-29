import os
import threading
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pyttsx3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AUDIO_FOLDER'] = 'static/audio'
app.secret_key = 'your_secret_key'

# Глобальные переменные для управления TTS
engine = None
playback_thread = None
current_file = None

def init_tts():
    global engine
    engine = pyttsx3.init()
    # Выбираем голос IVONA MAXIM
    for voice in engine.getProperty('voices'):
        if 'IVONA' in voice.name and 'Maxim' in voice.name:
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 150)  # Скорость речи

def text_to_speech(text, filename):
    output_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    return output_path

def play_audio():
    global engine
    if engine:
        engine.startLoop(False)
        engine.iterate()
        while engine.isBusy():
            engine.iterate()
        engine.endLoop()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect('/')
    file = request.files['file']
    if file.filename == '':
        return redirect('/')
    if file and file.filename.endswith('.txt'):
        filename = str(uuid.uuid4()) + '.txt'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return redirect(url_for('player', filename=filename))
    return redirect('/')

@app.route('/player/<filename>')
def player(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    audio_filename = f"{os.path.splitext(filename)[0]}.wav"
    audio_path = text_to_speech(text, audio_filename)
    
    return render_template(
        'player.html',
        text=text,
        audio_file=os.path.basename(audio_path),
        filename=filename
    )

@app.route('/control/<action>/<filename>')
def control(action, filename):
    global playback_thread, current_file
    
    if action == 'play':
        if playback_thread and playback_thread.is_alive():
            return 'Already playing', 400
            
        current_file = filename
        playback_thread = threading.Thread(target=play_audio)
        playback_thread.start()
        return 'Playing'
    
    elif action == 'stop' and engine:
        engine.stop()
        return 'Stopped'
    
    return 'Invalid action', 400

@app.route('/static/audio/<path:filename>')
def audio_files(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
    init_tts()
    app.run(host='0.0.0.0', port=5050, threaded=True)