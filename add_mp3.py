#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import os
import requests
import time
import logging

import config


def parse(line):
    pattern = r'</span>([\w\s\.?\-?]+)<br'
    result = re.search(pattern, line)
    if result:
        word = result.group(1)
        if len(word.split()) > 1:
            pattern = r'^to (\w+)$'
            result = re.match(pattern, word)
            if result:
                word = result.group(1)
        return word
    else:
        raise Exception('Error in regexp?\n{}'.format(line))


def mp3_save(response, word, audio_format):
    with open(os.path.join(MEDIA_FOLDER, '{}.{}'.format(word, audio_format)), 'wb') as fh:
        for chunk in response:
            fh.write(chunk)
    return True


def download_from_google(word):
    print('Try downloading from Google')
    if len(word.split()) > 1:
        return False
    google_url = 'https://ssl.gstatic.com/dictionary/static/sounds/de/0/'
    url = google_url + word + '.mp3'
    try:
        response = requests.get(url, stream=True)
    except requests.ConnectionError as exp:
        print('Some HTTP problems, {}'.format(exp))
        return False
    except requests.Timeout as exp:
        print('HTTP timeout, {}'.format(exp))
        return False
    if response.status_code == 200:
        if mp3_save(response, word, 'mp3'):
            print("Download from Google was successful.\nSaving result.")
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
    try:
        response = requests.post(ms_url_auth, headers=headers)
    except requests.ConnectionError as exp:
        print('Some HTTP problems, {}'.format(exp))
        return False
    except requests.Timeout as exp:
        print('HTTP timeout, {}'.format(exp))
        return False
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
    global MS_AUTH_TOKEN
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

    try:
        response = requests.post(ms_url_tts, data=body, headers=headers, stream=True)
    except requests.ConnectionError as exp:
        print('Some HTTP problems, {}'.format(exp))
        return False
    except requests.Timeout as exp:
        print('HTTP timeout, {}'.format(exp))
        return False
    if response.status_code == 200:
        print("Download from MS was successful.\nSaving result.")
        if mp3_save(response, word, 'wav'):
            return True
    elif response.status_code == 403:
        time.sleep(60)
        print('Get 403 from ms voice recognition, retry auth')
        MS_AUTH_TOKEN = ms_auth()
        if MS_AUTH_TOKEN:
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
    if os.path.isfile(os.path.join(MEDIA_FOLDER, '{}.mp3'.format(word))):
        print('File exists')
        return 'mp3'
    elif os.path.isfile(os.path.join(MEDIA_FOLDER, '{}.wav'.format(word))):
        print('File exists')
        return 'wav'
    else:
        print('File not exists in library\nDownloading...')
        audio_file_extension = download_mp3(word)
        if audio_file_extension:
            return audio_file_extension
        else:
            return False


if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError as exp:
        print('Please, run program with argument:\n{} filename'.format(sys.argv[0]))
        exit(1)
    ANKI_PATH = config.conf['anki']['path']
    MEDIA_FOLDER = os.path.join(ANKI_PATH, 'collection.media')
    MS_KEY = config.conf['ms']['ms_key1']
    MS_KEY = config.conf['ms']['ms_key1']
    MS_AUTH_TOKEN = ms_auth()

    with open(filename, 'r') as fh, open(filename + '.new', 'a') as new_fh, open(filename + '.seek', 'a+') as seek_fh:
        seek_fh.seek(0)
        position = seek_fh.readline()
        try:
            position = int(position)
            fh.seek(position)
            print('Move to new position {}'.format(position))
        except ValueError as exp:
            pass
        for line in fh:
            try:
                word = parse(line)
            except Exception as e:
                logging.warning(e)
                continue
            seek_fh.seek(0)
            seek_fh.truncate()
            seek_fh.write(str(fh.tell() - len(line)) + '\n')
            print('============================\n{}'.format(word))
            extension = mp3(word)
            if extension:
                new_fh.write('[sound:' + word + '.' + extension + ']' + line)
                seek_fh.seek(0)
                seek_fh.truncate()
                seek_fh.write(str(fh.tell()) + '\n')
        os.remove(filename + '.seek')
