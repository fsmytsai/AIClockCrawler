import asyncio
import aiohttp
import pymysql
import time
import os
import sys
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from datetime import datetime


class NewsClockCrawler:
    absolute_path = './'
    google_news_api_key = '74970d4bf19d4cf89565b65d9d45df35'
    bing_speech_api_key = '151812742a7b48c5aa9f3192cac54c4b'
    result = []

    def __init__(self, hour, minute, speaker):
        self.hour = hour
        self.minute = minute
        self.speaker = speaker
        self.logFile = open(self.absolute_path + 'logs/%s.txt' %
                            (datetime.now().strftime('%Y-%m-%d %H-%M-%S')), 'w')

        tStart = time.time()

        self.db = pymysql.connect(
            '127.0.0.1', 'tsaihau', 'hausung1998', 'news_clock', charset='utf8mb4')
        self.cursor = self.db.cursor()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.getBingSpeechAPIToken())
        loop.close()

        tEnd = time.time()
        self.logFile.write('It cost %f sec' % (tEnd - tStart))
        print(self.result)
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
                await self.getGoogleNews(session)

    async def getTimeSpeech(self, session):
        title = '嗨，現在時間' + str(self.hour) + '點' + str(self.minute) + '分，早上好'
        news_id = await self.checkDBNews(session, title, '時間', True)
        if news_id != 0:
            return
        news_id = self.insertNews(title, '時間', 1)
        if news_id != 0:
            self.result.append(news_id)
            if self.insertSounds(news_id, [title]) == False:
                return
            await self.downloadSpeech(session, news_id, 0, title)

    async def getGoogleNews(self, session):
        async with session.get('https://newsapi.org/v2/top-headlines?country=tw&apiKey=' + self.google_news_api_key) as response:
            news_data = await response.json()

            if news_data['status'] != 'ok':
                self.logFile.write('請求 google 新聞失敗\n')
                return

            tasks = []
            datas = []

            article_count = 0
            for article in news_data['articles']:
                if article['description'] == None:
                    continue

                if article_count == 10:
                    break

                article_count += 1

                news_id = await self.checkDBNews(
                    session, article['title'], article['description'], False)
                if news_id != 0:
                    continue

                # content = '第' + str(self.index) + '則新聞，標題，' + article['title'] + \
                #     '。' + '簡介，' + article['description']

                content = '標題，' + article['title'] + \
                    '。' + '簡介，' + article['description']

                content = content.replace('：', '說，')

                if content[-1] == '…' or content[-1] != '。':
                    last_period_index = content.rfind('。')
                    content = content[0:last_period_index + 1]

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

                news_id = self.insertNews(
                    article['title'], article['description'], len(contents))

                if news_id != 0:
                    self.result.append(news_id)

                    if self.insertSounds(news_id, contents) == False:
                        continue

                    for i in range(0, len(contents)):
                        task = asyncio.ensure_future(self.downloadSpeech(
                            session, news_id, i, contents[i]))
                        tasks.append(task)

            await asyncio.gather(*tasks)

    async def checkDBNews(self, session, title, description, isTime):
        self.cursor.execute(
            'select * from news where speaker = \"%s\" and title = \"%s\";' % (self.speaker, title))
        db_news = self.cursor.fetchone()
        if db_news is None:
            return 0
        else:
            self.cursor.execute(
                'select * from sounds where news_id = %d;' % (db_news[0]))
            db_sounds = self.cursor.fetchall()
            if len(db_sounds) == db_news[4]:
                self.logFile.write('已存在 news_id = %d\n' % (db_news[0]))

                for sound in db_sounds:
                    if sound[3] == 0:
                        self.logFile.write('補音檔 news_id = %d part_no = %d\n' %
                                           (sound[0], sound[1]))
                        await self.downloadSpeech(session, sound[0], sound[1], sound[2])

                if isTime:
                    self.result.append(db_news[0])
                else:
                    self.result.append(db_news[0])

                return db_news[0]
            else:
                self.logFile.write(
                    '音檔資料曾新增不完整 news_id = %d 將其刪除\n' % (db_news[0]))
                sql = 'delete from news where news_id = %d;' % (db_news[0])
                self.runSQL(sql)
                os.system('rm ' + self.absolute_path +
                          'sounds/%d-*' % (db_news[0]))
                return 0

    def insertNews(self, title, description, part_count):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into news values(0, \"%s\", \"%s\", \"%s\", %d, \"%s\");' % (
            self.speaker, title, description, part_count, created_at)
        is_success = self.runSQL(sql)
        if is_success:
            self.cursor.execute('SELECT LAST_INSERT_ID();')
            news_id = self.cursor.fetchone()
            return news_id[0]
        else:
            self.logFile.write('insertNews failed\n')
            return 0

    def insertSounds(self, news_id, contents):
        sql = 'insert into sounds values'
        for i in range(0, len(contents)):
            sql += '(%d, %d, \"%s\", 0)' % (
                news_id, i, contents[i])

            if i != len(contents) - 1:
                sql += ','
            else:
                sql += ';'

        is_success = self.runSQL(sql)
        if is_success == False:
            self.logFile.write(
                'insertSounds failed news_id = %d\n' % (news_id))
        return is_success

    async def downloadSpeech(self, session, news_id, part_no, content):
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

        uri = self.absolute_path + 'sounds/'

        # 建立資料夾
        os.makedirs(uri, exist_ok=True)

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            sound = await response.read()
            with open('%s%d-%d.wav' % (uri, news_id, part_no), 'wb') as f:
                if response.status != 200:
                    self.logFile.write('error news_id = %d part_no = %d status = %d\n' %
                                       (news_id, part_no, response.status))
                    await asyncio.sleep(1.0)
                    await self.downloadSpeech(session, news_id, part_no, content)
                else:
                    f.write(sound)
                    self.successDownloadSound(news_id, part_no)

    def successDownloadSound(self, news_id, part_no):
        sql = "update sounds set is_success_dl = 1 where news_id = %d and part_no = %d;" % (
            news_id, part_no)
        is_success = self.runSQL(sql)
        if is_success == False:
            self.logFile.write('update is_success_dl failed news_id = %d part_no = %d\n' %
                               (news_id, part_no))

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
arg1 = 0~23 小時
arg2 = 0~59 分鐘
arg3 = speaker 0=Yating, Apollo 1=HanHanRUS 2=Zhiwei, Apollo
"""
if len(sys.argv) > 3:
    try:
        hour = int(sys.argv[1])
        minute = int(sys.argv[2])
        spk = int(sys.argv[3])
    except:
        print('輸入錯誤')

    speaker = ['Yating, Apollo', 'HanHanRUS', 'Zhiwei, Apollo']

    if 0 < hour < 24 and 0 < minute < 59:
        NewsClockCrawler(hour, minute, speaker[spk])
    else:
        print('輸入錯誤')
else:
    print('輸入錯誤')
