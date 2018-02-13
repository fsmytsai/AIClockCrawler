import asyncio
import aiohttp
import time
import os
from bs4 import BeautifulSoup
from xml.etree import ElementTree


class NewsClockCrawler:
    google_news_api_key = '74970d4bf19d4cf89565b65d9d45df35'
    bing_speech_api_key = '151812742a7b48c5aa9f3192cac54c4b'

    def __init__(self):
        tStart = time.time()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.getGoogleNews())
        loop.close()

        tEnd = time.time()
        print('It cost %f sec' % (tEnd - tStart))

    async def getGoogleNews(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                'Ocp-Apim-Subscription-Key': self.bing_speech_api_key}
            async with session.post('https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers) as response:
                if response.status != 200:
                    print('取得 token 失敗')
                    return
                self.access_token = await response.text()

                async with session.get('https://newsapi.org/v2/top-headlines?country=tw&apiKey=' + self.google_news_api_key) as response:
                    news_data = await response.json()

                    if news_data['status'] != 'ok':
                        print('請求 google 新聞失敗')
                        return

                    tasks = []
                    index = 0
                    for article in news_data['articles']:
                        if article['description'] == None:
                            article['description'] = '這篇新聞沒有描述。'

                        text = '標題，' + article['title'] + \
                            '。' + '簡介，' + article['description']

                        text = text.replace('：', '說，')
                        index2 = 0
                        while len(text) > 100:
                            last_comma_index = text[0:100].rfind('，')
                            last_period_index = text[0:100].rfind('。')
                            if last_comma_index > last_period_index:
                                last_index = last_comma_index
                            else:
                                last_index = last_period_index
                            task = asyncio.ensure_future(self.downloadSpeech(
                                session, str(index) + '-' + str(index2), text[0:last_index]))
                            text = text[last_index + 1:len(text)]
                            tasks.append(task)
                            index2 += 1

                        task = asyncio.ensure_future(self.downloadSpeech(
                            session, str(index) + '-' + str(index2), text))
                        tasks.append(task)

                        index += 1

                    await asyncio.gather(*tasks)

    async def downloadSpeech(self, session, index, text):
        headers = {"Content-type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
                   "Authorization": "Bearer " + self.access_token}

        body = ElementTree.Element('speak', version='1.0')
        body.set('xml:lang', 'en-us')
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('xml:lang', 'en-us')
        voice.set('xml:gender', 'Female')
        voice.set(
            'name', 'Microsoft Server Speech Text to Speech Voice (zh-TW, Yating, Apollo)')
        voice.text = text

        # 建立資料夾
        os.makedirs('./sounds', exist_ok=True)

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            sound = await response.read()
            with open('./sounds/' + index + '.wav', 'wb') as f:
                if response.status != 200:
                    if response.status == 429:
                        print('失敗 : ' + index)
                        await asyncio.sleep(1.0)
                        await self.downloadSpeech(session, index, text)
                    else:
                        print('失敗 : ' + index + ' status = ' +
                              str(response.status) + ' text = ' + text)
                else:
                    f.write(sound)
                    print(index + '=' + text)


NewsClockCrawler()
