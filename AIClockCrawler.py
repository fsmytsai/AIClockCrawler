import asyncio
import aiohttp
import pymysql
import time
import os
import sys
import json
from xml.etree import ElementTree
from datetime import datetime


class AIClockCrawler:
    # log_absolute_path = '/Users/tsaiminyuan/NoCloudDoc/Crawler/AIClockCrawler/logs/'
    # sound_absolute_path = '/Users/tsaiminyuan/Documents/LaravelProject/LaravelAIClock/public/sounds/'
    log_absolute_path = '/var/crawler/AIClockCrawler/logs/'
    sound_absolute_path = '/var/www/LaravelAIClock/public/sounds/'
    google_news_api_key = '74970d4bf19d4cf89565b65d9d45df35'
    bing_speech_api_key = '151812742a7b48c5aa9f3192cac54c4b'
    result = {'is_success': False, 'data': []}

    def __init__(self, hour, minute, speaker, category):
        self.hour = hour
        self.minute = minute
        self.speaker = speaker
        self.category = category
        os.makedirs(self.log_absolute_path + '%s' %
                    (datetime.now().strftime('%Y-%m-%d')), exist_ok=True)
        self.logFile = open(self.log_absolute_path + '%s.txt' %
                            (datetime.now().strftime('%Y-%m-%d/%H-%M-%S')), 'w')

        tStart = time.time()

        self.db = pymysql.connect(
            '127.0.0.1', 'tsaihau', 'hausung1998', 'ai_clock', charset='utf8mb4')
        self.cursor = self.db.cursor()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.getBingSpeechAPIToken())
        loop.close()

        tEnd = time.time()
        self.logFile.write('It cost %f sec' % (tEnd - tStart))

        request_data_len = 1

        if self.category != '-1':
            request_data_len += 10

        if len(self.result['data']) == request_data_len:
            self.result['is_success'] = True
        print(json.dumps(self.result))
        self.logFile.close()

    async def getBingSpeechAPIToken(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                'Ocp-Apim-Subscription-Key': self.bing_speech_api_key}
            async with session.post('https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers) as response:
                if response.status != 200:
                    self.logFile.write('取得 token 失敗\n')
                    return
                self.access_token = await response.text()
                await self.getTimeSpeech(session)
                if self.category != '-1':
                    await self.getGoogleNews(session)

    async def getTimeSpeech(self, session):
        title = '嗨，現在時間' + str(self.hour) + '點'
        if self.minute == 0:
            title += '整'
        else:
            title += str(self.minute) + '分'

        if self.hour in range(4, 12):
            title += '，早上好'
        elif self.hour in range(12, 14):
            title += '，午安'
        elif self.hour in range(14, 18):
            title += '，下午好'
        elif self.hour in range(18, 24):
            title += '，晚上好'

        text_id = await self.checkDBText(session, title)
        if text_id != 0:
            return

        text_id = self.insertText(title, 'time', 1)
        if text_id != 0:
            self.result['data'].append({'text_id': text_id, 'part_count': 1})
            if self.insertSounds(text_id, [title]) == False:
                return
            await self.downloadSpeech(session, text_id, 0, title)

    async def getGoogleNews(self, session):
        async with session.get('https://newsapi.org/v2/top-headlines?country=tw&category=%s&apiKey=%s' % (self.category, self.google_news_api_key)) as response:
            news_data = await response.json()

            if news_data['status'] != 'ok':
                self.logFile.write('請求 google 新聞失敗\n')
                return

            tasks = []
            datas = []

            article_count = 0
            for article in news_data['articles']:
                # 10篇新聞結束。
                if article_count == 10:
                    break

                # 沒簡介及蘋果日報(簡介跟標題一樣)跳過。
                if article['description'] == None or article['author'] == '蘋果日報':
                    continue

                # 簡介結尾是 '…' 或不是 '。' 則找到最後一個 '。' 當簡介結尾，如果沒找到 '。' 則跳過。
                if article['description'][-1] == '…' or article['description'][-1] != '。':
                    last_period_index = article['description'].rfind('。')
                    if last_period_index == -1:
                        continue
                    article['description'] = article['description'][0:last_period_index + 1]

                # 將 '：' 換成 '說，' ，並去除空格跟換行。
                article['title'] = article['title'].replace('：', '說，')
                article['title'] = article['title'].replace(' ', '')
                article['title'] = article['title'].replace('\n', '')
                article['description'] = article['description'].replace(
                    '：', '說，')
                article['description'] = article['description'].replace(
                    ' ', '')
                article['description'] = article['description'].replace(
                    '\n', '')

                # 用標題檢查新聞是否已爬過。
                text_id = await self.checkDBText(session, article['title'])
                if text_id != 0:
                    article_count += 1
                    continue

                # content = '第' + str(self.index) + '則新聞，標題，' + article['title'] + \
                #     '。' + '簡介，' + article['description']

                content = '標題，' + article['title'] + \
                    '。' + '簡介，' + article['description']

                article_count += 1

                contents = []
                part_content = content
                while len(part_content) > 100:
                    last_comma_index = part_content[0:100].rfind('，')
                    last_period_index = part_content[0:100].rfind('。')
                    if last_comma_index > last_period_index:
                        last_index = last_comma_index
                    else:
                        last_index = last_period_index
                    contents.append(part_content[0:last_index])
                    part_content = part_content[last_index +
                                                1:len(part_content)]

                contents.append(part_content)

                text_id = self.insertText(
                    article['title'], article['description'], len(contents))

                if text_id != 0:
                    self.result['data'].append({'text_id': text_id,
                                                'part_count': len(contents)})

                    if self.insertSounds(text_id, contents) == False:
                        continue

                    for i in range(0, len(contents)):
                        task = asyncio.ensure_future(self.downloadSpeech(
                            session, text_id, i, contents[i]))
                        tasks.append(task)

            await asyncio.gather(*tasks)

    async def checkDBText(self, session, title):
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

                for sound in db_sounds:
                    if(os.path.exists('%s%d-%d.wav' % (self.sound_absolute_path, sound[0], sound[1])) == False):
                        self.logFile.write('補音檔 text_id = %d part_no = %d\n' %
                                           (sound[0], sound[1]))
                        await self.downloadSpeech(session, sound[0], sound[1], sound[2])

                self.result['data'].append({'text_id': db_text[0],
                                            'part_count': db_text[5]})

                return db_text[0]
            else:
                self.logFile.write(
                    '音檔資料曾新增不完整 text_id = %d 將其刪除\n' % (db_text[0]))
                sql = 'delete from texts where text_id = %d;' % (db_text[0])
                self.runSQL(sql)
                os.system('rm ' + self.sound_absolute_path +
                          '%d-*' % (db_text[0]))
                return 0

    def insertText(self, title, description, part_count):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into texts values(0, \"%s\", \"%s\", \"%s\", \"%s\", %d, \"%s\");' % (
            self.speaker, self.category, title, description, part_count, created_at)
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

    async def downloadSpeech(self, session, text_id, part_no, content):
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

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            sound = await response.read()
            with open('%s%d-%d.wav' % (self.sound_absolute_path, text_id, part_no), 'wb') as f:
                if response.status != 200:
                    self.logFile.write('error text_id = %d part_no = %d status = %d\n' %
                                       (text_id, part_no, response.status))
                    await asyncio.sleep(1.0)
                    await self.downloadSpeech(session, text_id, part_no, content)
                else:
                    f.write(sound)
                    self.logFile.write('新音檔 %d-%d\n' % (text_id, part_no))

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
arg1 = hour 0~23 小時
arg2 = minute 0~59 分鐘
arg3 = speaker 0=Yating, Apollo 1=HanHanRUS 2=Zhiwei, Apollo
arg4 = category -1=no news 0=general 1=business 2=entertainment 3=health 4=science 5=sports 6=technology
"""
if len(sys.argv) > 4:
    try:
        hour = int(sys.argv[1])
        minute = int(sys.argv[2])
        spk = int(sys.argv[3])
        ctg = int(sys.argv[4])
    except:
        print('輸入錯誤')

    speaker = ['Yating, Apollo', 'HanHanRUS', 'Zhiwei, Apollo']
    category = ['general', 'business', 'entertainment',
                'health', 'science', 'sports', 'technology', '-1']

    if 0 <= hour < 24 and 0 <= minute < 59 and 0 <= spk < 3 and -1 <= ctg < 7:
        AIClockCrawler(hour, minute, speaker[spk], category[ctg])
    else:
        print('輸入錯誤')
else:
    print('輸入錯誤')
