import openai
import os
import csv
from time import sleep
import hashlib

def init_openai():
    '''Initializes OpenAI API'''
    key = ''
    if os.path.isfile('key/key.txt'):
        key = open('key/key.txt', 'r').read().strip()
    
    openai.api_key = key

def get_processed():
    '''Returns a list of files that have already been processed'''
    
    # Create processed_files directory if it doesn't exist
    if not os.path.exists('processed_files'):
        os.makedirs('processed_files')
    
    # If processed.txt exists, returns a list of files that have been processed
    if os.path.isfile('processed_files/processed.txt'):
        with open('processed_files/processed.txt', 'r') as f:
            return f.read().strip().splitlines()
    
    # Otherwise creates a new file and returns an empty list
    else:
        open('processed_files/processed.txt', 'w').close()
        return []
    
def get_new_audio(processed: list):
    '''Returns a list of audio files that have not been processed'''
    
    # Create audio directory if it doesn't exist
    if not os.path.exists('audio'):
        os.makedirs('audio')
    
    allowed_filetypes = ('flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm')
    
    # Returns a list of audio files that have not been processed
    return [f for f in os.listdir('audio') if os.path.isfile(os.path.join('audio', f)) and f not in processed and f.endswith(allowed_filetypes)]

def process_audio(audio_files: list):
    '''Transcribe and process audio files'''
    
    # Creates transcripts directory if it doesn't exist
    if not os.path.exists('transcripts'):
        os.makedirs('transcripts')
    
    record_processed(audio_files) # Records processed audio files
    
    # Creates transcripts.csv if it doesn't exist
    if not os.path.isfile('transcripts/transcripts.csv'):
        with open('transcripts/transcripts.csv', 'w', newline='') as f:
            transcripts = csv.writer(f, delimiter=';')
            transcripts.writerow(['Filename', 'Filetype', 'MD5', 'Filepath', 'Filesize', 'Created', 'Accessed', 'Modified', 'Transcript'])
        
    # Transcribes all new audio files into transcripts folder
    with open('transcripts/transcripts.csv', 'a', newline='') as f:
        transcripts = csv.writer(f, delimiter = ';')
        for i in range(len(audio_files)):
            print('Transcribing audio file', i+1, 'of', len(audio_files))
            transcript = transcribe_audio(audio_files[i]).replace(';', '')
            if not transcript:
                continue
            row = create_row(audio_files[i], transcript)
            transcripts.writerow(row)

def create_row(audio_file: str, transcript: str):
    '''Creates a row for the transcripts.csv file'''
    filepath = os.path.join('audio', audio_file)
    filesize = os.path.getsize(filepath)
    ctime = os.path.getctime(filepath)
    atime = os.path.getatime(filepath)
    mtime = os.path.getmtime(filepath)
    bytes = open(filepath, 'rb').read()
    md5 = hashlib.md5(bytes).hexdigest()
    filetype = os.path.splitext(audio_file)[1][1:].upper()
    return [audio_file, filetype, md5, filepath, filesize, ctime, atime, mtime, transcript]
    

def transcribe_audio(audio_file: str):
    '''Transcribes the new audio file and saves to transcripts folder'''
    filepath = 'audio/' + audio_file
    tries = 3
    errors = []
    while tries > 0:
        try:
            frb = open(filepath, 'rb')
            transcript = openai.Audio.transcribe('whisper-1', frb)
            return transcript['text']
        except Exception as e:
            print('Error:', e)
            errors.append('Attempt ' + str(4-tries) + ' Failed: ' + str(e))
            sleep(2)
            print('Retrying...')
            tries -= 1
    if not os.path.exists('errors'):
        os.makedirs('errors')
    with open('errors/' + audio_file + '.txt', 'w') as f:
        f.write('\n'.join(errors))
    return None
    
def record_processed(audio_files: list):
    '''Records processed audio files in processed.txt if any'''
    
    # returns if no new audio files
    if not audio_files:
        return
    
    # Appends newly processed audio files to processed.txt
    with open('processed_files/processed.txt', 'a') as f:
        f.write('\n'.join(audio_files) + '\n')
     
def main():
    '''Transcribes all new audio files in the audio folder'''
    
    init_openai() # Gets OpenAI API key
    processed = get_processed() # Gets list of processed audio files
    new_audio = get_new_audio(processed) # get unprocessed audio files
    
    # Transcribes all new audio files if any
    print('Transcribing', len(new_audio), 'new audio files...')
    process_audio(new_audio)
    print('Finished Transcription!')

if __name__ == '__main__':
    main()
