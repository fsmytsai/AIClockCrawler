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
    google_place_api_key = 'AIzaSyBxDEN5xNm3zsgMKnWxflTYVTpMLDM9dIo'
    bing_speech_api_key = '6cecb861c41b4b1681e5efb3780c3679'
    real_speaker = ['Yating, Apollo', 'HanHanRUS', 'Zhiwei, Apollo']
    results = []
    download_count = 0

    def __init__(self, hour, minute, speaker, category, news_count, latitude, longitude):
        self.hour = hour
        self.minute = minute
        self.speaker = speaker
        self.category = category
        self.news_count = news_count
        self.latitude = latitude
        self.longitude = longitude

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
        loop.run_until_complete(self.getBingSpeechAPIToken())
        loop.close()

        tEnd = time.time()
        self.logFile.write('Download Count = %d\n' % (self.download_count))
        self.logFile.write('It cost %f sec' % (tEnd - tStart))

        print(json.dumps(self.results))
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
                if self.latitude != 1000:
                    await self.getYahooWeather(session)
                if self.category != '-1':
                    await self.getNews(session)

    async def getTimeSpeech(self, session):
        title = '嗨，現在時間' + str(self.hour) + '點'
        if self.minute == 0:
            title += '整'
        else:
            title += str(self.minute) + '分'

        if self.hour in range(4, 12):
            title += '，早安'
        elif self.hour in range(12, 14):
            title += '，午安'
        elif self.hour in range(14, 18):
            title += '，下午好'
        elif self.hour in range(18, 24):
            title += '，晚上好'

        text_id = await self.checkTimeOrWeatherText(session, title)
        if text_id != 0:
            return

        text_id = self.insertTimeOrWeatherText(title, 'time')
        if text_id != 0:
            self.results.append({'text_id': text_id, 'part_count': 1})
            if self.insertTimeOrWeatherSound(text_id, title) == False:
                return
            await self.downloadSpeech(session, text_id, 0, title)

    async def getYahooWeather(self, session):
        async with session.get('https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20u=%22c%22%20and%20%20woeid%20in%20(SELECT%20woeid%20FROM%20geo.places%20WHERE%20text=%22(' + str(self.latitude) + ',' + str(self.longitude) + ')%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys') as response:
            weather_data = await response.json()
            if weather_data['query']['count'] == 0:
                self.logFile.write('請求 yahoo 天氣失敗\n')
                return

            english_region = weather_data['query']['results']['channel']['location']['region']

            chinese_region = await self.getChineseRegion(session, english_region)

            title = ''
            if datetime.now().hour >= 20:
                forecast = weather_data['query']['results']['channel']['item']['forecast'][1]
                day = '明天'
            else:
                forecast = weather_data['query']['results']['channel']['item']['forecast'][0]
                day = '今天'

            code = int(forecast['code'])

            if code in [32, 33, 34]:
                title += '%s%s天氣晴朗' % (day, chinese_region)
            elif code in [36]:
                title += '%s%s天氣很熱' % (day, chinese_region)
            elif code in [2, 23]:
                title += '%s%s風很大，出門在外請小心' % (day, chinese_region)
            elif code in [3, 4, 9, 10, 11, 12, 37, 38, 39, 40, 45, 47]:
                title += '%s%s會下雨，出門記得帶把傘' % (day, chinese_region)
            elif code in [5, 6, 7, 41, 42, 43, 46]:
                title += '%s%s會下雪，出門記得帶把傘' % (day, chinese_region)
            elif code in [8, 35]:
                title += '%s%s會下冰雹，出門記得帶把傘' % (day, chinese_region)
            elif code in [25]:
                title += '%s%s天氣很冷' % (day, chinese_region)
            elif code in [26, 44]:
                title += '%s%s是陰天' % (day, chinese_region)
            elif code in [27, 28, 29, 30]:
                title += '%s%s多雲' % (day, chinese_region)

            title += '，氣溫最低%d度，最高%d度' % (
                int(forecast['low']), int(forecast['high']))

            title += '，當前氣溫%d度' % (
                int(weather_data['query']['results']['channel']['item']['condition']['temp']))

            if int(forecast['low']) < 15:
                title += '，請注意保暖'

            if chinese_region != '':
                air_quality_str = await self.getAirQualityStr(session, chinese_region)
                if air_quality_str != '':
                    title += air_quality_str

            text_id = await self.checkTimeOrWeatherText(session, title)
            if text_id != 0:
                return

            text_id = self.insertTimeOrWeatherText(title, 'weather')
            if text_id != 0:
                self.results.append(
                    {'text_id': text_id, 'part_count': 1})
                if self.insertTimeOrWeatherSound(text_id, title) == False:
                    return
                await self.downloadSpeech(session, text_id, 0, title)

    async def getChineseRegion(self, session, english_region):
        async with session.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%f,%f&keyword=%s&rankby=distance&language=zh-TW&key=%s' % (self.latitude, self.longitude, english_region, self.google_place_api_key)) as response:
            place_data = await response.json()
            if len(place_data['results']) > 0:
                place_data['results'][0]['name'] = place_data['results'][0]['name'].replace(
                    '台', '臺')
                return place_data['results'][0]['name']
            else:
                self.logFile.write('getChineseRegion Failed\n')
                return ''

    async def getAirQualityStr(self, session, chinese_region):
        async with session.get('https://pm25.lass-net.org/data/last-all-epa.json') as response:
            air_quality_data = await response.json()
            max = 0
            min = 500
            for air_quality in air_quality_data['feeds']:
                if chinese_region in air_quality['County']:
                    if 'AQI' in air_quality:
                        if air_quality['AQI'] > max:
                            max = air_quality['AQI']
                        if air_quality['AQI'] < min:
                            min = air_quality['AQI']

            if max == 0 and min == 500:
                self.logFile.write('getAirQualityData Failed\n')
                return ''

            air_quality_str = '。空氣品質指數維%d到%d' % (min, max)
            if max <= 50:
                air_quality_str += '，狀態良好'
            elif max <= 100:
                air_quality_str += '，狀態普通'
            elif max <= 150:
                air_quality_str += '，不適於敏感人群，建議戴上口罩再出門'
            elif max <= 200:
                air_quality_str += '，狀態很差，建議戴上口罩再出門'
            else:
                air_quality_str += '，狀態非常差，建議不要出門'
            return air_quality_str

    async def getNews(self, session):
        tasks = []
        news_list = self.getNewsList()

        for news in news_list:
            self.results.append(news)

            content_list = self.getContentList(news['text_id'])

            for i in range(0, len(content_list)):
                if os.path.exists('%s%d-%d-%d.wav' % (self.sound_absolute_path, news['text_id'], i, self.speaker)):
                    self.logFile.write('音檔已存在 %d-%d-%d\n' %
                                       (news['text_id'], i, self.speaker))
                else:
                    tasks.append(self.downloadSpeech(
                        session, news['text_id'], i, content_list[i]))

        await asyncio.gather(*tasks)

    def getNewsList(self):
        self.cursor.execute(
            'select * from texts where category = \"%s\" order by text_id desc limit %d;' % (self.category, self.news_count))
        db_texts = self.cursor.fetchall()
        news_list = []
        for db_text in db_texts:
            news_list.append({'text_id': db_text[0],
                              'part_count': db_text[4]})

        return news_list

    def getContentList(self, text_id):
        self.cursor.execute(
            'select * from sounds where text_id = %d;' % (text_id))
        db_sounds = self.cursor.fetchall()
        content_list = []
        for db_sound in db_sounds:
            content_list.append(db_sound[2])

        return content_list

    async def checkTimeOrWeatherText(self, session, title):
        self.cursor.execute(
            'select * from texts where title = \"%s\";' % (title))
        db_text = self.cursor.fetchone()
        if db_text is None:
            return 0
        else:
            self.cursor.execute(
                'select * from sounds where text_id = %d;' % (db_text[0]))
            db_sound = self.cursor.fetchone()
            if db_sound is None:
                self.logFile.write(
                    '音檔資料曾新增不完整 text_id = %d 將其刪除\n' % (db_text[0]))
                sql = 'delete from texts where text_id = %d;' % (db_text[0])
                self.runSQL(sql)
                os.system('rm ' + self.sound_absolute_path +
                          '%d-*' % (db_text[0]))
                return 0
            else:
                self.logFile.write('已存在 text_id = %d\n' % (db_text[0]))

                if os.path.exists('%s%d-%d-%d.wav' % (self.sound_absolute_path, db_sound[0], db_sound[1], self.speaker)) == False:
                    self.logFile.write('補音檔 text_id = %d part_no = %d speaker = %d\n' %
                                       (db_sound[0], db_sound[1], self.speaker))
                    await self.downloadSpeech(session, db_sound[0], db_sound[1], db_sound[2])

                self.results.append({'text_id': db_text[0],
                                     'part_count': db_text[4]})

                return db_text[0]

    def insertTimeOrWeatherText(self, title, description):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into texts values(0, \"\", \"%s\", \"%s\", 1, \"\", \"\", \"%s\");' % (
            title, description, created_at)
        is_success = self.runSQL(sql)
        if is_success:
            self.cursor.execute('SELECT LAST_INSERT_ID();')
            text_id = self.cursor.fetchone()
            return text_id[0]
        else:
            self.logFile.write('insertText failed\n')
            return 0

    def insertTimeOrWeatherSound(self, text_id, content):
        sql = 'insert into sounds values(%d, 0, \"%s\");' % (text_id, content)
        is_success = self.runSQL(sql)
        return
        if is_success == False:
            self.logFile.write(
                'insertTimeOrWeatherSound failed text_id = %d\n' % (text_id))
        return is_success

    async def downloadSpeech(self, session, text_id, part_no, content):
        self.logFile.write('開始下載 %d-%d-%d\n' %
                           (text_id, part_no, self.speaker))

        self.download_count += 1
        if self.download_count > 80:
            self.logFile.write('超出下載量限制\n')
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
            sound = await response.read()
            with open('%s%d-%d-%d.wav' % (self.sound_absolute_path, text_id, part_no, self.speaker), 'wb') as f:
                if response.status != 200:
                    self.logFile.write('error text_id = %d part_no = %d speaker = %d status = %d\n' %
                                       (text_id, part_no, self.speaker, response.status))
                    await asyncio.sleep(1.0)
                    await self.downloadSpeech(session, text_id, part_no, content)
                else:
                    f.write(sound)
                    self.logFile.write('下載完成 %d-%d-%d\n' %
                                       (text_id, part_no, self.speaker))

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
arg5 = news_count 6~10
arg6 = latitude 緯度 -90~90 1000=無需天氣
arg7 = longitude 經度 -180~180
"""
if len(sys.argv) > 7:
    try:
        hour = int(sys.argv[1])
        minute = int(sys.argv[2])
        speaker = int(sys.argv[3])
        ctg = int(sys.argv[4])
        news_count = int(sys.argv[5])
        latitude = float(sys.argv[6])
        longitude = float(sys.argv[7])
    except:
        print('輸入錯誤')

    category = ['general', 'business', 'entertainment',
                'health', 'science', 'sports', '-1']

    if 0 <= hour < 24 and 0 <= minute < 60 and 0 <= speaker < 3 and -1 <= ctg < 6 and 6 <= news_count <= 10:
        AIClockCrawler(
            hour, minute, speaker, category[ctg], news_count, latitude, longitude)
    else:
        print('輸入錯誤')
else:
    print('輸入錯誤')
