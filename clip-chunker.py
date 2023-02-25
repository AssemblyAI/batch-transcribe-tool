"""
This script takes an input audio file, splits it into clips of a specified length, and batch transcribes the clips with AssemblyAI.

Usage: python clip-chunker.py <path_to_input_file> <clip_length_in_seconds (optional, default=120 seconds)>
"""

from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_silence
import json, os
import concurrent.futures
import requests
import assembly
import time
import sys

"""
Helper function to clip audio at the given start and end timestamps and store at {output_file} path
"""
def clip_audio(audio, output_file, start, end):
    # Convert start and end timestamps from seconds to milliseconds
    start_ms = start * 1000
    end_ms = end * 1000
    
    # Get the audio in the specified range
    clipped = audio[start_ms:end_ms]
    
    # Save the clipped audio to a new file
    start = time.time()
    print('started clipping')
    clipped.export(output_file, format=output_file.split(".")[-1])
    end = time.time()
    print('CLIPPING TIME:', end-start)
    return clipped

"""
This function chunks the original audio file into clips of {clip_length} seconds

This method uses a VAD to detect silences in the audio to optimize the clipping (i.e. to avoid clipping in the middle of a sentence)

Clips are stored in the output directory with the naming convention: clipped-{start}-{end}.mp3
"""
def chunk_audio(audio, clip_length, output_folder, min_clip_length = 90):
    
    if clip_length < min_clip_length:
        print('Clip length must be greater than min clip length!')
        sys.exit()

    # Determine the loudness of the audio file
    dBFS=audio.dBFS
   
    window_start = 0
    window_end = window_start + clip_length

    metadata = []

    # Use a sliding window to clip the audio
    while (window_end <= audio.duration_seconds):
        print('WINDOW START', window_start, 'WINDOW END', window_end)
        print('Started detecting silences')

        # PyDub documentation for this method can be found here: https://github.com/jiaaro/pydub/blob/master/pydub/silence.py
        silences = detect_silence(audio[window_start * 1000:window_end * 1000], min_silence_len=500, silence_thresh=dBFS-16)
        
        print('Finished detecting silences')

        # If there are no silences in the window, increase the window size for the clip and continue
        if len(silences) == 0:
            window_end += clip_length
            continue
        
        last_silence = silences[-1]

        start, stop = last_silence

        # Calculate the middle of the last silence in add silence padding
        middle = start + ((stop - start) / 2)
        
        clip_start = window_start
        clip_end = window_start + (middle/1000)

        # If the clip is too short, increase the window size for the clip and continue
        if (clip_end-clip_start < min_clip_length):
            window_end += clip_length
            continue

        clip_audio(audio, f"{output_folder}/clipped-{clip_start}-{clip_end}.mp3", clip_start, clip_end)
        metadata.append({
            "start": clip_start,
            "end": clip_end
        })

        window_start = clip_end
        window_end = window_start + clip_length

    # Clip remaining audio
    clip_start = window_start
    clip_end = audio.duration_seconds
    clip_audio(audio, f"{output_folder}/clipped-{clip_start}-{clip_end}.mp3", clip_start, clip_end)
    metadata.append({
        "start": clip_start,
        "end": clip_end
    })

    open ("metadata.json", "w").write(json.dumps(metadata))

"""
This function batch transcribes all the clips in the given folder using AssemblyAI's transcription API

Set your concurrency limit using the {max_workers} parameter
"""
def batch_transcribe(clips_folder, max_workers=60):
    with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
        results = [executor.submit(assembly.transcribe, (os.path.join(clips_folder, f))) for f in os.listdir(clips_folder) if f.endswith('.mp3')]
        hugeWordArr = []
        for future in concurrent.futures.as_completed(results):
            result = future.result()
            # print(result['words'])

            # if there are words in the result, append to the word array
            if result and 'words' in result:
                hugeWordArr += result['words']
        
        # stich together all word arrays and sort by start time
        sortedWords = sorted(hugeWordArr, key=lambda x: x['start'], reverse=False)
        open ("words-chopped.json", "w").write(json.dumps({'words':sortedWords}))

if len(sys.argv) < 2:
    print('Missing file path!')
    print('Usage: python clip-chunker.py <path_to_input_file> <clip_length_in_seconds (optional, default = 120 seconds)>')
    sys.exit()

path_to_input_file = sys.argv[1]
clip_length = 120
if len(sys.argv) > 2:
    clip_length = int(sys.argv[2])

try:
    audio = AudioSegment.from_file(path_to_input_file)
except:
    print('Invalid file path!')
    print('Usage: python clip-chunker.py <path_to_input_file> <clip_length_in_seconds (optional, default = 120 seconds)>')
    sys.exit()

try:
    os.mkdir('output')
except:
    print('folder exists')

folder = './output'

start = time.time()
chunk_audio(audio, clip_length, folder)
end = time.time()
print('TOTAL CHUNKING TIME:', end-start)

start = time.time()
batch_transcribe(folder)
end = time.time()
print('TOTAL PARALLEL TRANSCRIPTION TIME:', end-start)

''' 
Uncomment this section to transcribe the full audio file to compare turnaround time
'''
# start = time.time()
# result = assembly.transcribe(path_to_input_file)
# # print(result['words'])
# open ("fulltranscript-full.json", "w").write(result['text'])
# open ("words-full.json", "w").write(json.dumps({'words':result['words']}))
# end = time.time()
# print('TOTAL FULL AUDIO TIME:', end-start)