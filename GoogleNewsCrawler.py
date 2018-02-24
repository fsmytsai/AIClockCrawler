import asyncio
import aiohttp
import pymysql
import time
import os
from datetime import datetime


class GoogleNewsCrawler:
    log_absolute_path = '/Users/tsaiminyuan/NoCloudDoc/Crawler/AIClockCrawler/newslogs/'
    # log_absolute_path = '/var/crawler/AIClockCrawler/newslogs/'
    google_news_api_key = '74970d4bf19d4cf89565b65d9d45df35'
    categorys = ['general', 'business', 'entertainment',
                 'health', 'science', 'sports', 'technology']

    def __init__(self):
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.getAllGoogleNews())
        loop.close()

        tEnd = time.time()
        self.logFile.write('It cost %f sec' % (tEnd - tStart))
        self.logFile.close()

    async def getAllGoogleNews(self):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for category in self.categorys:
                tasks.append(self.getGoogleNews(session, category))
            await asyncio.gather(*tasks)

    async def getGoogleNews(self, session, category):
        self.logFile.write('開始請求 google 新聞 類別：%s\n' % (category))
        async with session.get('https://newsapi.org/v2/top-headlines?country=tw&category=%s&apiKey=%s' % (category, self.google_news_api_key)) as response:
            news_data = await response.json()

            if news_data['status'] != 'ok':
                self.logFile.write('請求 google 新聞失敗 類別：%s\n' % (category))
                return

            self.logFile.write('請求 google 新聞成功 類別：%s\n' % (category))

            for article in news_data['articles']:
                # 沒簡介及蘋果日報(簡介跟標題一樣)跳過。
                if article['description'] == None or article['description'] == '' or article['author'] == '蘋果日報':
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

                # 用分類及標題檢查新聞是否已爬過。
                text_id = self.checkDBText(category, article['title'])
                if text_id != 0:
                    self.logFile.write('text 資料已存在 textId = %d\n' % (text_id))
                    continue

                content = '標題，' + article['title'] + \
                    '。' + '簡介，' + article['description']

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

                preview_image = ''
                if article['urlToImage'] != None and 'http' in article['urlToImage']:
                    preview_image = article['urlToImage']

                text_id = self.insertText(
                    category, article['title'], article['description'], len(contents), article['url'], preview_image)

                if text_id != 0:
                    self.logFile.write(
                        '新增 text 資料成功 textId = %d category = %s\n' % (text_id, category))
                    if self.insertSounds(text_id, contents):
                        self.logFile.write(
                            '新增 sounds 資料成功 textId = %d category = %s\n' % (text_id, category))
                    else:
                        self.logFile.write(
                            '新增 sounds 資料失敗 textId = %d category = %s\n' % (text_id, category))
                else:
                    self.logFile.write(
                        '新增 text 資料失敗 category = %s\n' % (category))

    def checkDBText(self, category, title):
        self.cursor.execute(
            'select * from texts where category = \"%s\" and title = \"%s\";' % (category, title))
        db_text = self.cursor.fetchone()
        if db_text is None:
            return 0
        else:
            self.cursor.execute(
                'select * from sounds where text_id = %d;' % (db_text[0]))
            db_sounds = self.cursor.fetchall()
            if len(db_sounds) == db_text[4]:
                return db_text[0]
            else:
                self.logFile.write(
                    '音檔資料曾新增不完整 text_id = %d 將其刪除\n' % (db_text[0]))
                sql = 'delete from texts where text_id = %d;' % (db_text[0])
                self.runSQL(sql)
                os.system('rm ' + self.sound_absolute_path +
                          '%d-*' % (db_text[0]))
                return 0

    def insertText(self, category, title, description, part_count, url, preview_image):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into texts values(0, \"%s\", \"%s\", \"%s\", %d, \"%s\", \"%s\", \"%s\");' % (
            category, title, description, part_count, url, preview_image, created_at)
        is_success = self.runSQL(sql)
        if is_success:
            self.cursor.execute('SELECT LAST_INSERT_ID();')
            text_id = self.cursor.fetchone()
            return text_id[0]
        else:
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
        return is_success

    def runSQL(self, sql):
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except:
            self.logFile.write('DB ROLLBACK sql = \"%s\"\n' % (sql))
            self.db.rollback()
            return False


GoogleNewsCrawler()
