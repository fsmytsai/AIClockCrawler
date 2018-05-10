import pymysql
import json
import requests
import sys
from datetime import datetime
from GetChinesePlace import getChinesePlace


class WeatherCrawler:
    google_place_api_key = 'AIzaSyBxDEN5xNm3zsgMKnWxflTYVTpMLDM9dIo'

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

        self.db = pymysql.connect(
            '127.0.0.1', 'tsaihau', 'hausung1998', 'ai_clock', charset='utf8mb4')
        self.cursor = self.db.cursor()

        weather_text_id = self.getYahooWeather()

        print(weather_text_id)

    def getYahooWeather(self):
        response = requests.get('https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20u=%22c%22%20and%20%20woeid%20in%20(SELECT%20woeid%20FROM%20geo.places%20WHERE%20text=%22(' +
                                str(self.latitude) + ',' + str(self.longitude) + ')%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys')
        weather_data = response.json()
        if weather_data['query']['count'] == 0:
            return 0

        english_region = weather_data['query']['results']['channel']['location']['region']
        english_city = weather_data['query']['results']['channel']['location']['city']

        chinese_region, chinese_city = getChinesePlace(
            english_region, english_city)

        if chinese_city == '':
            chinese_city = self.getChineseCity(english_city)

        title = ''
        if datetime.now().hour >= 20:
            forecast = weather_data['query']['results']['channel']['item']['forecast'][1]
            day = '明天'
        else:
            forecast = weather_data['query']['results']['channel']['item']['forecast'][0]
            day = '今天'

        code = int(forecast['code'])

        if code in [32, 33, 34]:
            title += '%s%s天氣晴朗' % (day, chinese_city)
        elif code in [36]:
            title += '%s%s天氣很熱' % (day, chinese_city)
        elif code in [2, 23]:
            title += '%s%s風很大，出門在外請小心' % (day, chinese_city)
        elif code in [3, 4, 9, 10, 11, 12, 37, 38, 39, 40, 45, 47]:
            title += '%s%s會下雨，出門記得帶把傘' % (day, chinese_city)
        elif code in [5, 6, 7, 41, 42, 43, 46]:
            title += '%s%s會下雪，出門記得帶把傘' % (day, chinese_city)
        elif code in [8, 35]:
            title += '%s%s會下冰雹，出門記得帶把傘' % (day, chinese_city)
        elif code in [25]:
            title += '%s%s天氣很冷' % (day, chinese_city)
        elif code in [26, 44]:
            title += '%s%s是陰天' % (day, chinese_city)
        elif code in [27, 28, 29, 30]:
            title += '%s%s多雲' % (day, chinese_city)

        title += '，氣溫最低%d度，最高%d度' % (
            int(forecast['low']), int(forecast['high']))

        title += '，當前氣溫%d度' % (
            int(weather_data['query']['results']['channel']['item']['condition']['temp']))

        if int(forecast['low']) < 15:
            title += '，請注意保暖'

        if chinese_region != '':
            air_quality_str = self.getAirQualityStr(chinese_region)
            if air_quality_str != '':
                title += air_quality_str

        text_id = self.checkWeatherText(title)
        if text_id != 0:
            return text_id

        text_id = self.insertWeatherText(title, 'weather')
        if text_id != 0:
            if self.insertWeatherSound(text_id, title) == False:
                return 0

        return text_id

    def getChineseCity(self, english_city):
        response = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json?&query=%s&language=zh-TW&key=%s' %
                                (english_city, self.google_place_api_key))
        place_data = response.json()
        if len(place_data['results']) > 0:
            return place_data['results'][0]['name']
        else:
            return ''

    def getAirQualityStr(self, chinese_region):
        response = requests.get(
            'https://pm25.lass-net.org/data/last-all-epa.json')
        air_quality_data = response.json()
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

    def checkWeatherText(self, title):
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
                sql = 'delete from texts where text_id = %d;' % (db_text[0])
                self.runSQL(sql)
                return 0
            return db_text[0]

    def insertWeatherText(self, title, description):
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'insert into texts values(0, \"\", \"%s\", \"%s\", 1, \"\", \"\", \"%s\");' % (
            title, description, created_at)
        is_success = self.runSQL(sql)
        if is_success:
            self.cursor.execute('SELECT LAST_INSERT_ID();')
            text_id = self.cursor.fetchone()
            return text_id[0]
        else:
            return 0

    def insertWeatherSound(self, text_id, content):
        sql = 'insert into sounds values(%d, 0, \"%s\");' % (text_id, content)
        is_success = self.runSQL(sql)
        return is_success

    def runSQL(self, sql):
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except:
            self.db.rollback()
            return False


"""
arg2 = latitude 緯度 -90~90 1000=無需天氣
arg3 = longitude 經度 -180~180
"""
if len(sys.argv) > 2:
    try:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])
    except:
        print('輸入錯誤')

    WeatherCrawler(latitude, longitude)
else:
    print('輸入錯誤')
