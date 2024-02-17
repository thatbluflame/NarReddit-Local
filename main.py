import ffmpeg
import stable_whisper
from html2image import Html2Image
from openai import OpenAI
from jinja2 import Template
from gtts import gTTS

import os
import random

# temp
TTS_TITLE_PATH = 'tts/ttsTitle.mp3'
TTS_DESCRIPTION_PATH = 'tts/ttsDescription.mp3'
VIDEO_FOLDER_PATH = 'background_videos/minecraft'
SUBTITLES_PATH = 'subtitles.srt'
OUTPUT_VIDEO_PATH = 'final.mp4'
# Open AI
OPENAI_API_KEY = 'API-KEY'
GPT_MODEL = "gpt-3.5-turbo"
# Intro Card
INTRO_CARD_TEMPLATE_HTML = "intro_card_template/template.html"
INTRO_CARD_TEMPLATE_CSS = "intro_card_template/index.css"
TITLE_IMAGE_PATH = "titleCard.png"
LOGO_PATH = 'intro_card_template/logo.png'
USERNAME = 'USERNAME'
COMMENT_SVG_PATH = 'intro_card_template/comment.svg'
UPVOTE_SVG_PATH = 'intro_card_template/upvote.svg'
VIEWS_SVG_PATH = 'intro_card_template/views.svg'
# ffmpeg
VCODEC='libx264'
THREADS=4

# Generate Video
def generate_video(title_text, description_text):
    # Modify Text with GPT
    #title_text = get_tts_ready_text(title_text)
    #description_text = get_tts_ready_text(description_text)
    
    # Generate Image Card
    generate_title_card(INTRO_CARD_TEMPLATE_HTML, title_text, LOGO_PATH, USERNAME, TITLE_IMAGE_PATH)

    # Generate TTS .mp3
    gtts_synthesize_text(title_text, TTS_TITLE_PATH)
    gtts_synthesize_text(description_text, TTS_DESCRIPTION_PATH)

    # Generate Subtitle .srt
    whisper_transcribe(TTS_TITLE_PATH, TTS_DESCRIPTION_PATH, SUBTITLES_PATH)

    video = process_video(TTS_TITLE_PATH, TTS_DESCRIPTION_PATH, TITLE_IMAGE_PATH, SUBTITLES_PATH)

    # Merge Title & Description Audio
    mergedAudio = merge_audio(TTS_TITLE_PATH, TTS_DESCRIPTION_PATH)

    # Merge Video & Audio
    merge_video_audio(video, mergedAudio, OUTPUT_VIDEO_PATH)

def get_tts_ready_text(text):
    instructions = "Correct grammar mistakes. Don't alter curse words or swearing. Replace slashes and dashes with the appropriate word. Add punctuation as necessary for smooth speech flow. Only respond with the modified (or unmodified if no changes were made) text. Do not include any other information: "
    client = OpenAI(
    api_key=OPENAI_API_KEY,
    )
    return client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": instructions + text,
        }
    ],
    model=GPT_MODEL,
)

def generate_title_card(html_template_path, title_text, profile_picture_path, username, output_path):
    # Read Template
    with open(html_template_path, "r") as f:
        template = Template(f.read())

    # Render HTML template with data
    title_card_html = template.render(titleText=title_text, profilePicturePath='logo.png', username=username)

    # Load Images
    hti = Html2Image(size=(850,500))
    hti.load_file(profile_picture_path)
    hti.load_file(COMMENT_SVG_PATH)
    hti.load_file(UPVOTE_SVG_PATH)
    hti.load_file(VIEWS_SVG_PATH)
    # Take "screenshot" from Title Card
    hti.screenshot(html_str=title_card_html, css_file=INTRO_CARD_TEMPLATE_CSS, save_as=output_path)

def gtts_synthesize_text(text, output_file):
    tts = gTTS(text, lang='en', tld='us')
    tts.save(output_file)

def whisper_transcribe(tts_title_path, tts_description_path, srt_output_path):
    # Transcribing Audio and generating .srt with max duration per Line of 1 sec
    model = stable_whisper.load_model('base.en')
    result = model.transcribe(tts_description_path, regroup=True)
    (
        result
        .split_by_duration(1)
    )
    result.to_srt_vtt(srt_output_path, strip=True, word_level=False, segment_level=True)

    offset = get_audio_duration(tts_title_path)
    offset_srt_time(srt_output_path, srt_output_path, offset)

def offset_srt_time(input_file, output_file, offset_seconds):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if '-->' in line:
            parts = line.strip().split(' --> ')
            start_time, end_time = parts[0], parts[1]
            start_time = add_time_offset(start_time, offset_seconds)
            end_time = add_time_offset(end_time, offset_seconds)
            new_line = f"{start_time} --> {end_time}\n"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(output_file, 'w') as f:
        f.writelines(new_lines)

def add_time_offset(time_str, offset):
    h, m, s_ms = map(float, time_str.replace(',', '.').split(':'))
    total_seconds = h * 3600 + m * 60 + s_ms
    total_seconds += offset
    new_h = int(total_seconds // 3600)
    total_seconds %= 3600
    new_m = int(total_seconds // 60)
    new_s_ms = total_seconds % 60
    return f"{new_h:02d}:{new_m:02d}:{new_s_ms:06.3f}".replace('.', ',')

def process_video(title_audio_path, description_audio_path, title_image_path, subtitles_path, start_time=None, background_video_path=None):
    # Get duration of Audios
    title_audio_duration = get_audio_duration(title_audio_path)
    description_audio_duration = get_audio_duration(description_audio_path)

    #Merge Title and Description
    merged_audio_duration = title_audio_duration + description_audio_duration

    # Choose random Video if not specified
    if background_video_path is None:
      background_video_path = random_background_video()

    video_probe = ffmpeg.probe(background_video_path)
    video_stream = get_video_stream(video_probe)
    video_duration = float(video_stream['duration'])

    if start_time is None:
      start_time = random_start_time(video_duration, merged_audio_duration)

    video = ffmpeg.input(background_video_path, stream_loop=-1)
    video = video.trim(start=start_time, end=start_time + merged_audio_duration + 0.3)
    video = video.setpts('PTS-STARTPTS')

    # Calculate new dimensions only when necessary
    new_width, new_height = None, None
    if video_stream['width'] != 9 or video_stream['height'] != 16:
        new_width, new_height = get_new_dimensions(video_stream)
    video = ffmpeg.filter_(video, 'crop', new_width, new_height)

    # Get Image Stream of Title Image
    image_stream = get_image_stream(title_image_path, new_width)

    #Overlay Image
    video = ffmpeg.overlay(
        video, image_stream, x='(W-w)/2', y='(H-h)/2', enable=f'between(t,0,{title_audio_duration})')

    if subtitles_path is not None and os.path.isfile(subtitles_path):
            # Set style for the subtitles
            style = "FontName=Londrina Solid,FontSize=20,PrimaryColour=&H00ffffff,OutlineColour=&H00000000," \
                    "BackColour=&H80000000,Bold=1,Italic=0,Alignment=10"
            video = ffmpeg.filter_(
                video, 'subtitles', subtitles_path, force_style=style)
    return video

def random_background_video():
    # Check if the folder exists
    if not os.path.isdir(VIDEO_FOLDER_PATH):
        print(f"Error: '{VIDEO_FOLDER_PATH}' is not a valid directory.")
        return None
    
    # Get a list of all files in the folder
    video_files = [f for f in os.listdir(VIDEO_FOLDER_PATH) if os.path.isfile(os.path.join(VIDEO_FOLDER_PATH, f))]
    
    # Check if there are any video files in the folder
    if not video_files:
        print(f"No video files found in '{VIDEO_FOLDER_PATH}'.")
        return None
    
    # Choose a random video file
    random_video = random.choice(video_files)
    
    # Return the path to the randomly chosen video file
    return os.path.join(VIDEO_FOLDER_PATH, random_video)

def random_start_time(videoDuration, audioDuration):
    # Calculate the maximum start time for the video
    max_start_time = max(0, videoDuration - audioDuration)
    
    # Choose a random start time within the valid range
    random_start_time = random.uniform(0, max_start_time)
    
    return random_start_time

def get_audio_duration(audio_path):
    probe = ffmpeg.probe(audio_path)
    return float(probe['streams'][0]['duration'])
    
def merge_video_audio(video, audio, output_video_path):
    output = ffmpeg.output(video, audio, output_video_path,
                               vcodec=VCODEC, threads=THREADS)
    output = ffmpeg.overwrite_output(output)
    ffmpeg.run(output)

def get_video_stream(videoProbe):
    return next((stream for stream in videoProbe['streams'] if stream['codec_type'] == 'video'), None)

def get_new_dimensions(videoStream):
    width = int(videoStream['width'])
    height = int(videoStream['height'])
    if width / height > 9 / 16:  # wider than 9:16, crop sides
        return int(height * (9 / 16)), height
    else:  # narrower than 9:16, crop top and bottom
        return width, int(width * (16 / 9))

def merge_audio(titleAudioPath, descriptionAudioPath):
    titleAudio = ffmpeg.input(titleAudioPath)
    descriptionAudio = ffmpeg.input(descriptionAudioPath)
    # Concatenate the title and content audio files
    audio_stream = ffmpeg.concat(
        titleAudio, descriptionAudio, v=0, a=1)
    return audio_stream

def get_image_stream(titleImagePath, videoNewWidth):
    # If an image file is provided, overlay it for the first 5 seconds
    if titleImagePath is not None:
        image_stream = ffmpeg.input(titleImagePath)
        videoWidth = min(1080, videoNewWidth)
        imageWidth = min(864, int(videoWidth*0.8))
        # Scale the image to match the video's dimensions if needed
        image_stream = image_stream.filter_('scale', imageWidth, -1)
        return image_stream

def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        # Remove newline characters ("\n")
        text = text.replace('\n', '')
    return text

    

# Example usage
generate_video(read_text_file('title-text.txt'), read_text_file('description-text.txt'))
