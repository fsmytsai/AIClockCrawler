import asyncio
import aiohttp
import time
import os
from xml.etree import ElementTree


class DownloadMySound:
    all_texts = [{'complete': '第一則新聞', 'alias': 'news1'},
                 {'complete': '第二則新聞', 'alias': 'news2'},
                 {'complete': '第三則新聞', 'alias': 'news3'},
                 {'complete': '第四則新聞', 'alias': 'news4'},
                 {'complete': '第五則新聞', 'alias': 'news5'},
                 {'complete': '第六則新聞', 'alias': 'news6'},
                 {'complete': '第七則新聞', 'alias': 'news7'},
                 {'complete': '第八則新聞', 'alias': 'news8'},
                 {'complete': '第九則新聞', 'alias': 'news9'},
                 {'complete': '第十則新聞', 'alias': 'news10'},
                 {'complete': '第十一則新聞', 'alias': 'news11'},
                 {'complete': '第十二則新聞', 'alias': 'news12'},
                 {'complete': '祝您有美好的一天，再見', 'alias': 'bye'},
                 {'complete': '嗨，我將為您播報天氣及新聞', 'alias': 'hello'},
                 {'complete': '此音檔已遺失', 'alias': 'lost'},
                 {'complete': '本次播報的不是即時資料，原因可能是網路不穩', 'alias': 'olddata'}]

    all_speekers = [{'complete': 'Yating, Apollo', 'alias': 'f1'},
                    {'complete': 'HanHanRUS', 'alias': 'f2'},
                    {'complete': 'Zhiwei, Apollo', 'alias': 'm1'}]
    absolute_path = './'
    api_key = 'c251429f2b504b0b853a8c43644e169d'

    def __init__(self):
        tStart = time.time()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.crawl())
        loop.close()

        tEnd = time.time()
        print('It cost %f sec' % (tEnd - tStart))

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key}
            async with session.post('https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers) as response:
                self.access_token = await response.text()
                tasks = []
                for speaker in self.all_speekers:
                    for text in self.all_texts:
                        tasks.append(self.downloadSpeech(
                            session, speaker, text))

                await asyncio.gather(*tasks)

    async def downloadSpeech(self, session, speaker, text):
        print('start download %s_%s' % (speaker['alias'], text['alias']))
        headers = {"Content-type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
                   "Authorization": "Bearer " + self.access_token}

        body = ElementTree.Element('speak', version='1.0')
        body.set('xml:lang', 'en-us')
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('xml:lang', 'en-us')
        voice.set('xml:gender', 'Female')
        voice.set(
            'name', 'Microsoft Server Speech Text to Speech Voice (zh-TW, %s)' % (speaker['complete']))
        voice.text = text['complete']

        uri = self.absolute_path + 'sounds/'

        # 建立資料夾
        os.makedirs(uri, exist_ok=True)

        async with session.post('https://speech.platform.bing.com/synthesize', data=ElementTree.tostring(body), headers=headers) as response:
            sound = await response.read()
            with open('%s%s_%s.wav' % (uri, speaker['alias'], text['alias']), 'wb') as f:
                if response.status != 200:
                    print('error %d %s_%s' %
                          (response.status, speaker['alias'], text['alias']))
                    await asyncio.sleep(1.0)
                    await self.downloadSpeech(session, speaker, text)
                else:
                    f.write(sound)
                    print('新音檔 %d %s_%s' %
                          (len(sound), speaker['alias'], text['alias']))


DownloadMySound()
