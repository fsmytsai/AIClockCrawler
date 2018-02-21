import requests
import pymysql
import time
import os
import sys
import json
from xml.etree import ElementTree
from datetime import datetime


class PromptToSpeech:
    # log_absolute_path = '/Users/tsaiminyuan/NoCloudDoc/Crawler/AIClockCrawler/pts_logs/'
    # sound_absolute_path = '/Users/tsaiminyuan/Documents/LaravelProject/LaravelAIClock/public/sounds/'
    log_absolute_path = '/var/crawler/AIClockCrawler/pts_logs/'
    sound_absolute_path = '/var/www/LaravelAIClock/public/sounds/'
    bing_speech_api_key = '151812742a7b48c5aa9f3192cac54c4b'
    result = {'is_success': False, 'data': {}}

    def __init__(self, day, hour, minute, sencond, speaker):
        self.day = day
        self.hour = hour
        self.minute = minute
        self.sencond = sencond
        self.speaker = speaker

        oldmask = os.umask(000)
        os.makedirs(self.log_absolute_path + '%s' %
                    (datetime.now().strftime('%Y-%m-%d')), 0o777, True)
        os.umask(oldmask)
        self.logFile = open(self.log_absolute_path + '%s.txt' %
                            (datetime.now().strftime('%Y-%m-%d/%H-%M-%S')), 'w', encoding='utf-8')

        tStart = time.time()

        self.db = pymysql.connect(
            '127.0.0.1', 'tsaihau', 'hausung1998', 'ai_clock', charset='utf8mb4')
        self.cursor = self.db.cursor()
        self.getBingSpeechAPIToken()

        tEnd = time.time()
        self.logFile.write('It cost %f sec' % (tEnd - tStart))

        print(json.dumps(self.result))
        self.logFile.close()

    def getBingSpeechAPIToken(self):
        headers = {'Ocp-Apim-Subscription-Key': self.bing_speech_api_key}
        response = requests.post(
            'https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers)
        if response.status_code != 200:
            self.logFile.write('取得 token 失敗\n')
            return
        self.access_token = response.text
        self.getPromptSpeech()

    def getPromptSpeech(self):
        title = ''
        if self.day > 0:
            title += '%d天' % (self.day)
        if self.hour > 0:
            title += '%d小時' % (self.hour)
        if self.minute > 0:
            title += '%d分鐘' % (self.minute)
        if self.sencond > 0 and title == '':
            title += '%d秒' % (self.sencond)

        if title == '':
            return

        title += '後響鈴'

        text_id = self.checkDBText(title)
        if text_id != 0:
            return

        text_id = self.insertText(title, 'prompt', 1, '', '')
        if text_id != 0:
            self.result['data'] = {'text_id': text_id, 'part_count': 1}
            if self.insertSounds(text_id, [title]) == False:
                return
            self.downloadSpeech(text_id, 0, title)

    def checkDBText(self, title):
        self.cursor.execute(
            'select * from texts where speaker = \"%s\" and title = \"%s\";' % (self.speaker, title))
        db_text = self.cursor.fetchone()
        if db_text is None:
            return 0
        else:
            self.cursor.execute(
                'select * from sounds where text_id = %d;' % (db_text[0]))
            db_sounds = self.cursor.fetchall()
            if len(db_sounds) == db_text[5]:
                self.logFile.write('已存在 text_id = %d\n' % (db_text[0]))

                isReDownload = False

                for sound in db_sounds:
                    if(os.path.exists('%s%d-%d.wav' % (self.sound_absolute_path, sound[0], sound[1])) == False):
                        self.logFile.write('補音檔 text_id = %d part_no = %d\n' %
                                           (sound[0], sound[1]))
                        isReDownload = True
                        self.downloadSpeech(sound[0], sound[1], sound[2])

                if isReDownload == False:
                    self.result['is_success'] = True
                self.result['data'] = {'text_id': db_text[0],
                                       'part_count': db_text[5]}

                return db_text[0]
            else:
                self.logFile.write(
                    '音檔資料曾新增不完整 text_id = %d 將其刪除\n' % (db_text[0]))
                sql = 'delete from texts where text_id = %d;' % (db_text[0])
                self.runSQL(sql)
                os.system('rm ' + self.sound_absolute_path +
                          '%d-*' % (db_text[0]))
                return 0

    def insertText(self, title, description, part_count, url, preview_image):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into texts values(0, \"%s\", \"%s\", \"%s\", \"%s\", %d, \"%s\", \"%s\", \"%s\");' % (
            self.speaker, 'prompt', title, description, part_count, url, preview_image, created_at)
        is_success = self.runSQL(sql)
        if is_success:
            self.cursor.execute('SELECT LAST_INSERT_ID();')
            text_id = self.cursor.fetchone()
            return text_id[0]
        else:
            self.logFile.write('insertText failed\n')
            return 0

    def insertSounds(self, text_id, contents):
        sql = 'insert into sounds values'
        for i in range(0, len(contents)):
            sql += '(%d, %d, \"%s\")' % (
                text_id, i, contents[i])

            if i != len(contents) - 1:
                sql += ','
            else:
                sql += ';'

        is_success = self.runSQL(sql)
        if is_success == False:
            self.logFile.write(
                'insertSounds failed text_id = %d\n' % (text_id))
        return is_success

    def downloadSpeech(self, text_id, part_no, content):
        headers = {'Content-type': 'application/ssml+xml',
                   'X-Microsoft-OutputFormat': 'riff-16khz-16bit-mono-pcm',
                   'Authorization': 'Bearer ' + self.access_token}

        body = ElementTree.Element('speak', version='1.0')
        body.set('xml:lang', 'en-us')
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('xml:lang', 'en-us')
        voice.set('xml:gender', 'Female')
        voice.set(
            'name', 'Microsoft Server Speech Text to Speech Voice (zh-TW, ' + self.speaker + ')')
        voice.text = content

        os.makedirs(self.sound_absolute_path, exist_ok=True)

        response = requests.post('https://speech.platform.bing.com/synthesize',
                                 data=ElementTree.tostring(body), headers=headers)
        sound = response.content
        with open('%s%d-%d.wav' % (self.sound_absolute_path, text_id, part_no), 'wb') as f:
            if response.status_code != 200:
                self.logFile.write('error text_id = %d part_no = %d status_code = %d\n' %
                                   (text_id, part_no, response.status_code))
                time.sleep(1)
                self.downloadSpeech(text_id, part_no, content)
            else:
                f.write(sound)
                self.logFile.write('新音檔 %d-%d\n' % (text_id, part_no))
                self.result['is_success'] = True

    def runSQL(self, sql):
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except:
            self.logFile.write('DB ROLLBACK sql = \"%s\"\n' % (sql))
            self.db.rollback()
            return False


"""
arg1 = day 天數
arg2 = hour 0~23 小時
arg3 = minute 0~59 分鐘
arg4 = second 0~59 秒數
arg5 = speaker 0=Yating, Apollo 1=HanHanRUS 2=Zhiwei, Apollo
"""
if len(sys.argv) > 5:
    try:
        day = int(sys.argv[1])
        hour = int(sys.argv[2])
        minute = int(sys.argv[3])
        second = int(sys.argv[4])
        spk = int(sys.argv[5])
    except:
        print('輸入錯誤')

    speaker = ['Yating, Apollo', 'HanHanRUS', 'Zhiwei, Apollo']

    if 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60 and 0 <= spk < 3:
        PromptToSpeech(day, hour, minute, second, speaker[spk])
    else:
        print('輸入錯誤')
else:
    print('輸入錯誤')
