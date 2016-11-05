#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import os
import requests
import time

import config


def parse(line):
    pattern = r'<span style=\"color: #aaa;\">[\(\)\w\.?\s?]+</span> ' \
              r'([\w\s\.?\-?]+)<br/>'
    result = re.search(pattern, line)
    if result:
        return result.group(1)
    else:
        print('Error in regexp?\n{}'.format(line))
        return False


def mp3_save(response, format):
    with open(MEDIA_FOLDER + '/' + word + '.' + format, 'wb') as fh:
        for chunk in response:
            fh.write(chunk)
    return True


def download_from_google(word):
    print('Try downloading from Google')
    if len(word.split()) > 1:
        pattern = r'^to (\w+)$'
        result = re.match(pattern, word)
        if result:
            word = result.group(1)
        else:
            return False
    google_url = 'https://ssl.gstatic.com/dictionary/static/sounds/de/0/'
    url = google_url + word + '.mp3'
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        if mp3_save(response, 'mp3'):
            return True
        else:
            print('Can\'t save file')
            return False
    else:
        print(response.status_code)
        return False


def ms_auth():
    ms_url_auth = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
    headers = {"Content-type": "application/x-www-form-urlencoded", "Content-Length": '0',
               "Ocp-Apim-Subscription-Key": MS_KEY}
    response = requests.post(ms_url_auth, headers=headers)
    if response.status_code == 200:
        return response.content
    elif response.status_code == 429:
        print('Too many requests, sleeping for 60 sec')
        time.sleep(60)
        ms_auth()
    else:
        print('Can\'t get ms auth token\n{}'.format(response.status_code))
        return False


def download_from_ms(word):
    print('Try downloading from Microsoft')

    ms_auth_token = MS_AUTH_TOKEN
    ms_url_tts = 'https://speech.platform.bing.com/synthesize'

    body = "<speak version='1.0' xml:lang='en-us'><voice xml:lang='en-us' xml:gender='Female' " \
           "name='Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)'>" + \
           word + "</voice></speak>"

    headers = {"Content-type": "application/ssml+xml",
               "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
               "Authorization": "Bearer " + ms_auth_token,
               "X-Search-AppId": "07D3234E49CE426DAA29772419F436CA",
               "X-Search-ClientID": "1ECFAE91408841A480F00935DC390960",
               "User-Agent": "TTSForPython"}

    response = requests.post(ms_url_tts, data=body, headers=headers)
    if response.status_code == 200:
        if mp3_save(response, 'wav'):
            return True
    elif response.status_code == 403:
        time.sleep(60)
        print('Get 403 from ms voice recognition, retry auth')
        global MS_AUTH_TOKEN
        MS_AUTH_TOKEN = ms_auth()
        download_mp3(word)
    elif response.status_code == 503:
        print('Some problem in MS\nStatus code is {}'.format(response.status_code))
        return False
    else:
        print('Can\'t generate ms voice\n{}'.format(response.status_code))


def download_mp3(word):
    if download_from_google(word):
        return 'mp3'
    elif download_from_ms(word):
        return 'wav'
    else:
        return False


def mp3(word):
    print('Check existing mp3s')
    if os.path.isfile(MEDIA_FOLDER + '/' + word + '.mp3'):
        return 'mp3'
    elif os.path.isfile(MEDIA_FOLDER + '/' + word + '.wav'):
        return 'wav'
    else:
        print('File not exists in library\nDownloading...')
        audio_file = download_mp3(word)
        if audio_file:
            return audio_file
        else:
            return False


if __name__ == '__main__':
    filename = sys.argv[1]
    ANKI_PATH = config.conf['anki']['path']
    MEDIA_FOLDER = ANKI_PATH + 'collection.media'
    MS_KEY = config.conf['ms']['ms_key1']
    MS_AUTH_TOKEN = ms_auth()

    # TODO
    # save file position if program was break and start with this position

    with open(filename, 'r') as fh, open(filename + '.new', 'a') as new_fh:
        for line in fh:
            word = parse(line)
            print('Word = {}'.format(word))
            extension = mp3(word)
            new_fh.write('[sound:' + word + '.' + extension + ']' + line)
