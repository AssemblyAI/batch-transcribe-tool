import os
import time
import requests
import json

api_token = os.environ.get('ASSEMBLYAI_API_TOKEN')

def read_file(fname, chunk_size=5242880, sleep=0):
    with open(fname, 'rb') as _file:
        while True:
            time.sleep(sleep)
            data = _file.read(chunk_size)
            if not data:
                break
            yield data


def upload(fname, sleep=0, chunk_size=5242880*2):
    headers = {'authorization': api_token}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                             headers=headers,
                             data=read_file(fname, sleep=sleep, chunk_size=chunk_size))

    if 'upload_url' not in response.json():
        print('UPLOAD ERROR', response.json())
        return
    return response.json()['upload_url']


def transcribe(speech_file, language_code='en', word_boost=None, boost_param=None,
               punctuate=True, format_text=True, dual_channel=False, redact_pii=False,
               redact_pii_policies=None, redact_pii_sub='entity_name', webhook_url=''):

    url = "https://api.assemblyai.com/v2/transcript"
    staging = "https://api.staging.assemblyai-labs.com/v2/transcript"

    audio_url = upload(speech_file)

    if audio_url is None:
        return
    
    payload = {
        "audio_url": audio_url,
        "punctuate": punctuate,
        "format_text": format_text,
        "language_code": language_code,

        # ADD YOUR PARAMETERS HERE
        # "entity_detection": True,
        # "auto_highlights": True,
        # "content_safety": True,
        # "iab_categories": True,
        # "summarization": True,
        # "summary_model": "informative",
        # "summary_type": "paragraph",
        # "speaker_labels": True
        # "dual_channel": dual_channel,
        # "webhook_url": webhook_url,
        # "disfluencies": True
        # "redact_pii": redact_pii,
        # "redact_pii_audio": redact_pii,
        # "redact_pii_policies": None if not redact_pii_policies else redact_pii_policies.split(","),
        # "redact_pii_sub": redact_pii_sub,
    }

    if word_boost is not None:
        word_boost = word_boost.split(",")
        boost_param = boost_param
        payload['word_boost'] = word_boost

        if boost_param is not None:
            payload['boost_param'] = boost_param

    headers = {'authorization': api_token}

    response = requests.post(url, json=payload, headers=headers)
    response_json = response.json()
    status = response_json.get('status')
    id = response_json.get('id')
    print('ASSEMBLYAI TRANSCRIPT ID', id)

    if status is None:
        print(response.json())
        return
    
    starttime = time.time()
    while status not in ["completed", "error"]:
        response = requests.get(url + "/%s" % id, headers=headers)
        response_json = response.json()
        status = response_json.get('status')

        time.sleep(3)

    donetime = time.time()

    if status == "error":
        print('TRANSCRIPT ERROR', response_json['error'])
        return

    # Use start and end timestamps from filename to offset word timestamps
    if len(speech_file.split('-')) > 1:
        start_ts = int(float(speech_file.split('-')[1])*1000)
        for word in response_json['words']:
            word['start'] += start_ts
            word['end'] += start_ts
    
    return response_json