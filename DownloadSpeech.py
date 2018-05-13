import asyncio
import aiohttp
import pymysql
import time
import os
import sys
import json
from xml.etree import ElementTree
from datetime import datetime
from GetChinesePlace import getChinesePlace


class DownloadSpeech:
    # sound_absolute_path = '/Users/tsaiminyuan/Documents/LaravelProject/LaravelAIClock/public/sounds/'
    sound_absolute_path = '/var/www/LaravelAIClock/public/sounds/'
    bing_speech_api_key = 'a5ef00ba301349219a6c25263b59f82d'
    real_speaker = ['Yating, Apollo', 'HanHanRUS', 'Zhiwei, Apollo']
    download_count = 0
    downloaded_count = 0
    need_download_count = 0

    def __init__(self, text_id_list_str, speaker):
        self.text_id_list = text_id_list_str.split(',')
        self.speaker = speaker
        if len(self.text_id_list) > 13:
            print(0)
            return
        self.db = pymysql.connect(
            '127.0.0.1', 'tsaihau', 'hausung1998', 'ai_clock', charset='utf8mb4')
        self.cursor = self.db.cursor()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.getBingSpeechAPIToken())
        loop.close()
        if self.downloaded_count == self.need_download_count:
            print(1)
        else:
            print(0)

    async def getBingSpeechAPIToken(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                'Ocp-Apim-Subscription-Key': self.bing_speech_api_key}
            async with session.post('https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers) as response:
                if response.status != 200:
                    return
                self.access_token = await response.text()
                await self.getSpeechs(session)

    async def getSpeechs(self, session):
        tasks = []

        for text_id in self.text_id_list:
            content_list = self.getContentList(text_id)

            for i in range(0, len(content_list)):
                if os.path.exists('%s%s-%d-%d.wav' % (self.sound_absolute_path, text_id, i, self.speaker)) != True:
                    self.need_download_count += 1
                    tasks.append(self.downloadSpeech(
                        session, text_id, i, content_list[i]))

        await asyncio.gather(*tasks)

    def getContentList(self, text_id):
        self.cursor.execute(
            'select * from sounds where text_id = %d;' % (int(text_id)))
        db_sounds = self.cursor.fetchall()
        content_list = []
        for db_sound in db_sounds:
            content_list.append(db_sound[2])

        return content_list

    async def downloadSpeech(self, session, text_id, part_no, content):
        self.download_count += 1
        if self.download_count > 80:
            return

        headers = {'Content-type': 'application/ssml+xml',
                   'X-Microsoft-OutputFormat': 'riff-16khz-16bit-mono-pcm',
                   'Authorization': 'Bearer ' + self.access_token}

        body = ElementTree.Element('speak', version='1.0')
        body.set('xml:lang', 'en-us')
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('xml:lang', 'en-us')
        voice.set('xml:gender', 'Female')
        voice.set(
            'name', 'Microsoft Server Speech Text to Speech Voice (zh-TW, ' + self.real_speaker[self.speaker] + ')')
        voice.text = content

        os.makedirs(self.sound_absolute_path, exist_ok=True)

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            if response.status != 200:
                print(response.status)
                await asyncio.sleep(1.0)
                await self.downloadSpeech(session, text_id, part_no, content)
            else:
                sound = await response.read()
                with open('%s%s-%d-%d.wav' % (self.sound_absolute_path, text_id, part_no, self.speaker), 'wb') as f:
                    f.write(sound)
                    self.downloaded_count += 1

    def runSQL(self, sql):
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except:
            self.db.rollback()
            return False


"""
arg1 = text_id_list_str
arg2 = speaker 0=Yating, Apollo 1=HanHanRUS 2=Zhiwei, Apollo
"""
if len(sys.argv) > 2:
    try:
        speaker = int(sys.argv[2])
    except:
        print('輸入錯誤')

    text_id_list_str = sys.argv[1]

    if len(text_id_list_str) > 0:
        DownloadSpeech(text_id_list_str, speaker)
    else:
        print('輸入錯誤')
else:
    print('輸入錯誤')
