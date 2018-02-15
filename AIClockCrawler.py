import asyncio
import aiohttp
import pymysql
import time
import os
import sys
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from datetime import datetime


class AIClockCrawler:
    log_absolute_path = './logs/'
    sound_absolute_path = './sounds/'
    google_news_api_key = '74970d4bf19d4cf89565b65d9d45df35'
    bing_speech_api_key = '151812742a7b48c5aa9f3192cac54c4b'
    result = {'is_success': False, 'news_ids': []}

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
        if len(self.result['news_ids']) == 11:
            self.result['is_success'] = True
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
        async with session.get('https://newsapi.org/v2/top-headlines?country=tw&category=%s&apiKey=%s' % (self.category, self.google_news_api_key)) as response:
            news_data = await response.json()

            if news_data['status'] != 'ok':
                self.logFile.write('請求 google 新聞失敗\n')
                return

            tasks = []
            datas = []

            article_count = 0
            for article in news_data['articles']:
                if article['description'] == None or article['author'] == '蘋果日報':
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
                    self.result['news_ids'].append(news_id)

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
            if len(db_sounds) == db_news[5]:
                self.logFile.write('已存在 news_id = %d\n' % (db_news[0]))

                for sound in db_sounds:
                    if(os.path.exists('%s%d-%d.wav' % (self.sound_absolute_path, sound[0], sound[1])) == False):
                        self.logFile.write('補音檔 news_id = %d part_no = %d\n' %
                                           (sound[0], sound[1]))
                        await self.downloadSpeech(session, sound[0], sound[1], sound[2])

                if isTime:
                    self.result['news_ids'].append(db_news[0])
                else:
                    self.result['news_ids'].append(db_news[0])

                return db_news[0]
            else:
                self.logFile.write(
                    '音檔資料曾新增不完整 news_id = %d 將其刪除\n' % (db_news[0]))
                sql = 'delete from news where news_id = %d;' % (db_news[0])
                self.runSQL(sql)
                os.system('rm ' + self.sound_absolute_path +
                          '%d-*' % (db_news[0]))
                return 0

    def insertNews(self, title, description, part_count):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into news values(0, \"%s\", \"%s\", \"%s\", \"%s\", %d, \"%s\");' % (
            self.speaker, self.category, title, description, part_count, created_at)
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
            sql += '(%d, %d, \"%s\")' % (
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

        os.makedirs(self.sound_absolute_path, exist_ok=True)

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            sound = await response.read()
            with open('%s%d-%d.wav' % (self.sound_absolute_path, news_id, part_no), 'wb') as f:
                if response.status != 200:
                    self.logFile.write('error news_id = %d part_no = %d status = %d\n' %
                                       (news_id, part_no, response.status))
                    await asyncio.sleep(1.0)
                    await self.downloadSpeech(session, news_id, part_no, content)
                else:
                    f.write(sound)
                    self.logFile.write('新音檔 %d-%d\n' % (news_id, part_no))

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
arg4 = category 0=general 1=business 2=entertainment 3=health 4=science 5=sports 6=technology
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
                'health', 'science', 'sports', 'technology']

    if 0 <= hour < 24 and 0 <= minute < 59 and 0 <= spk < 3 and 0 <= ctg < 7:
        AIClockCrawler(hour, minute, speaker[spk], category[ctg])
    else:
        print('輸入錯誤')
else:
    print('輸入錯誤')
