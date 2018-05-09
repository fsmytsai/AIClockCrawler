def getChinesePlace(parent, child):
    arr = [
        {
            'parent':['Taipei','臺北市'],
            'child':[['Taipei','臺北市'],['Zhongzheng', '中正區'],['Datong', '大同區'],['Zhongshan', '中山區'],
                    ['Songshan', '松山區'],['Da’an','大安區'],['Wanhua','萬華區'],['Xinyi','信義區'],
                    ['Shilin','士林區'],['Beitou','北投區'],['Neihu','內湖區'],['Nangang','南港區'],
                    ['Wenshan','文山區']]
        },
        {
            'parent':['Keelung','基隆市'],
            'child':[['Keelung','基隆市'],['Ren’ai','仁愛區'],['Xinyi','信義區'],['Zhongzheng', '中正區'],
                    ['Zhongshan', '中山區'],['Anle','安樂區'],['Nuannuan','暖暖區'],['Qidu','七堵區']]
        },
        {
            'parent':['New Taipei','新北市'],
            'child':[['New Taipei','新北市'],['Wanli','萬里區'],['Jinshan','金山區'],['Banqiao','板橋區'],
                    ['Xizhi','汐止區'],['Shenkeng','深坑區'],['Shiding','石碇區'],['Ruifang','瑞芳區'],
                    ['Pingxi','平溪區'],['Shuangxi','雙溪區'],['Gongliao','貢寮區'],['Xindian','新店區'],
                    ['Pinglin','坪林區'],['Wulai','烏來區'],['Yonghe','永和區'],['Zhonghe','中和區'],
                    ['Tucheng','土城區'],['Sanxia','三峽區'],['Shulin','樹林區'],['Yingge','鶯歌區'],
                    ['Sanchong','三重區'],['Xinzhuang','新莊區'],['Taishan','泰山區'],['Linkou','林口區'],
                    ['Luzhou','蘆洲區'],['Wugu','五股區'],['Bali','八里區'],['Tamsui','淡水區'],
                    ['Sanzhi','三芝區'],['Shimen','石門區']]
        },
        {
            'parent':['Lienchiang','連江縣'],
            'child':[['Lienchiang','連江縣'],['Nangan','南竿鄉'],['Beigan','北竿鄉'],['Juguang','莒光鄉'],
                    ['Dongyin','東引鄉']]
        },
        {
            'parent':['Yilan County','宜蘭縣'],
            'child':[['Yilan County','宜蘭縣'],['Yilan City','宜蘭市'],['Toucheng','頭城鎮'],
                    ['Jiaoxi','礁溪鄉'],['Zhuangwei','壯圍鄉'],['Yuanshan','員山鄉'],['Luodong','羅東鎮'],
                    ['Sanxing','三星鄉'],['Datong','大同鄉'],['Wujie','五結鄉'],['Dongshan','冬山鄉'],
                    ['Su’ao','蘇澳鎮'],['Nan’ao','南澳鄉']]
        },
        {
            'parent':['Hsinchu City','新竹市'],
            'child':[['Hsinchu City','新竹市'],['East','東區'],['North','北區'],['Xiangshan','香山區']]
        },
        {
            'parent':['Hsinchu County','新竹縣'],
            'child':[['Hsinchu County','新竹縣'],['Zhubei','竹北市'],['Hukou','湖口鄉'],['Xinfeng','新豐鄉'],
                    ['Xinpu','新埔鎮'],['Guanxi','關西鎮'],['Qionglin','芎林鄉'],['Baoshan','寶山鄉'],
                    ['Zhudong','竹東鎮'],['Wufeng','五峰鄉'],['Hengshan','橫山鄉'],['Jianshi','尖石鄉'],
                    ['Beipu','北埔鄉'],['Emei','峨眉鄉']]
        },
        {
            'parent':['Taoyuan City','桃園市'],
            'child':[['Taoyuan City','桃園市'],['Zhongli','中壢區'],['Pingzhen','平鎮區'],['Longtan','龍潭區'],
                    ['Yangmei','楊梅區'],['Xinwu','新屋區'],['Guanyin','觀音區'],['Taoyuan Dist','桃園區'],
                    ['Guishan','龜山區'],['Bade','八德區'],['Daxi','大溪區'],['Fuxing','復興區'],
                    ['Dayuan','大園區'],['Luzhu','蘆竹區']]
        },
        {
            'parent':['Miaoli County','苗栗縣'],
            'child':[['Miaoli County','苗栗縣'],['Zhunan','竹南鎮'],['Toufen','頭份市'],['Sanwan','三灣鄉'],
                    ['Nanzhuang','南庄鄉'],['Shitan','獅潭鄉'],['Houlong','後龍鎮'],['Tongxiao','通霄鎮'],
                    ['Yuanli','苑裡鎮'],['Miaoli City','苗栗市'],['Zaoqiao','造橋鄉'],['Touwu','頭屋鄉'],
                    ['Gongguan','公館鄉'],['Dahu','大湖鄉'],['Tai’an','泰安鄉'],['Tongluo','銅鑼鄉'],
                    ['Sanyi','三義鄉'],['Xihu','西湖鄉'],['Zhuolan','卓蘭鎮']]
        },
        {
            'parent':['Taichung','臺中市'],
            'child':[['Taichung','臺中市'],['Central','中區'],['East','東區'],['South','南區'],
                    ['West','西區'],['North','北區'],['Beitun','北屯區'],['Xitun','西屯區'],
                    ['Nantun','南屯區'],['Taiping','太平區'],['Dali','大里區'],['Wufeng','霧峰區'],
                    ['Wuri','烏日區'],['Fengyuan','豐原區'],['Houli','后里區'],['Shigang','石岡區'],
                    ['Dongshi','東勢區'],['Heping','和平區'],['Xinshe','新社區'],['Tanzi','潭子區'],
                    ['Daya','大雅區'],['Shengang','神岡區'],['Dadu','大肚區'],['Shalu','沙鹿區'],
                    ['Longjing','龍井區'],['Wuqi','梧棲區'],['Qingshui','清水區'],['Dajia','大甲區'],
                    ['Waipu','外埔區'],['Da’an','大安區']]
        },
        {
            'parent':['Changhua County','彰化縣'],
            'child':[['Changhua County','彰化縣'],['Changhua City','彰化市'],['Fenyuan','芬園鄉'],['SoutHuatanh','花壇鄉'],
                    ['Xiushui','秀水鄉'],['Lukang','鹿港鎮'],['Fuxing','福興鄉'],['Xianxi','線西鄉'],
                    ['Hemei','和美鎮'],['Shengang','伸港鄉'],['Yuanlin','員林市'],['Shetou','社頭鄉'],
                    ['Yongjing','永靖鄉'],['Puxin','埔心鄉'],['Xihu','溪湖鎮'],['Dacun','大村鄉'],
                    ['Puyan','埔鹽鄉'],['Tianzhong','田中鎮'],['Beidou','北斗鎮'],['Tianwei','田尾鄉'],
                    ['Pitou','埤頭鄉'],['Xizhou','溪州鄉'],['Zhutang','竹塘鄉'],['Erlin','二林鎮'],
                    ['Dacheng','大城鄉'],['Fangyuan','芳苑鄉'],['Ershui','二水鄉']]
        },
        {
            'parent':['Nantou County','南投縣'],
            'child':[['Nantou County','南投縣'],['Nantou City','南投市'],['Zhongliao','中寮鄉'],['Caotun','草屯鎮'],
                    ['Guoxing','國姓鄉'],['Puli','埔里鎮'],['Ren’ai','仁愛鄉'],['Mingjian','名間鄉'],
                    ['Jiji','集集鎮'],['Shuili','水里鄉'],['Yuchi','魚池鄉'],['Xinyi','信義鄉'],
                    ['Zhushan','竹山鎮'],['Lugu','鹿谷鄉']]
        },
        {
            'parent':['Chiayi City','嘉義市'],
            'child':[['Chiayi City','嘉義市'],['East','東區'],['West','西區']]
        },
        {
            'parent':['Chiayi County','嘉義縣'],
            'child':[['Chiayi County','嘉義縣'],['Fanlu','番路鄉'],['Meishan','梅山鄉'],['Zhuqi','竹崎鄉'],
                    ['Alishan','阿里山鄉'],['Zhongpu','中埔鄉'],['Dapu','大埔鄉'],['Shuishang','水上鄉'],
                    ['Lucao','鹿草鄉'],['Taibao','太保市'],['Puzi','朴子市'],['Dongshi','東石鄉'],
                    ['Liujiao','六腳鄉'],['Xingang','新港鄉'],['Minxiong','民雄鄉'],['Dalin','大林鎮'],
                    ['Xikou','溪口鄉'],['Yizhu','義竹鄉'],['Budai','布袋鎮']]
        },
        {
            'parent':['Yunlin County','雲林縣'],
            'child':[['Yunlin County','雲林縣'],['Dounan','斗南鎮'],['Dapi','大埤鄉'],['Huwei','虎尾鎮'],
                    ['Tuku','土庫鎮'],['Baozhong','褒忠鄉'],['Dongshi','東勢鄉'],['Taixi','臺西鄉'],
                    ['Lunbei','崙背鄉'],['Mailiao','麥寮鄉'],['Douliu','斗六市'],['Linnei','林內鄉'],
                    ['Gukeng','古坑鄉'],['Citong','莿桐鄉'],['Xiluo','西螺鎮'],['Erlun','二崙鄉'],
                    ['Beigang','北港鎮'],['Shuilin','水林鄉'],['Kouhu','口湖鄉'],['Sihu','四湖鄉'],
                    ['Yuanchang','元長鄉']]
        },
        {
            'parent':['Tainan','臺南市'],
            'child':[['Tainan','臺南市'],['West Central','中西區'],['East','東區'],['South','南區'],
                    ['North','北區'],['Anping','安平區'],['Annan','安南區'],['Yongkang','永康區'],
                    ['Guiren','歸仁區'],['Xinhua','新化區'],['Zuozhen','左鎮區'],['Yujing','玉井區'],
                    ['Nanxi','楠西區'],['Nanhua','南化區'],['Rende','仁德區'],['Guanmiao','關廟區'],
                    ['Longqi','龍崎區'],['Guantian','官田區'],['Madou','麻豆區'],['Jiali','佳里區'],
                    ['Xigang','西港區'],['Qigu','七股區'],['Jiangjun','將軍區'],['Xuejia','學甲區'],
                    ['Beimen','北門區'],['Xinying','新營區'],['Houbi','後壁區'],['Baihe','白河區'],
                    ['Dongshan','東山區'],['Liujia','六甲區'],['Xiaying','下營區'],['Liuying','柳營區'],
                    ['Yanshui','鹽水區'],['Shanhua','善化區'],['Danei','大內區'],['Shanshang','山上區'],
                    ['Xinshi','新市區'],['Anding','安定區']]
        },
        {
            'parent':['Kaohsiung','高雄市'],
            'child':[['Kaohsiung','高雄市'],['Xinxing','新興區'],['Qianjin','前金區'],['Lingya','苓雅區'],
                    ['Yancheng','鹽埕區'],['Gushan','鼓山區'],['Qijin','旗津區'],['Qianzhen','前鎮區'],
                    ['Sanmin','三民區'],['Nanzi','楠梓區'],['Xiaogang','小港區'],['Zuoying','左營區'],
                    ['Renwu','仁武區'],['Dashe','大社區'],['Dongsha','東沙群島'],['Nansha','南沙群島'],
                    ['Gangshan','岡山區'],['Luzhu','路竹區'],['Alian','阿蓮區'],['Tianliao','田寮區'],
                    ['Yanchao','燕巢區'],['Qiaotou','橋頭區'],['Ziguan','梓官區'],['Mituo','彌陀區'],
                    ['Yong’an','永安區'],['Hunei','湖內區'],['Fengshan','鳳山區'],['Daliao','大寮區'],
                    ['Linyuan','林園區'],['Niaosong','鳥松區'],['Dashu','大樹區'],['Qishan','旗山區'],
                    ['Meinong','美濃區'],['Liugui','六龜區'],['Neimen','內門區'],['Shanlin','杉林區'],
                    ['Jiaxian','甲仙區'],['Taoyuan','桃源區'],['Namaxia','那瑪夏區'],['Maolin','茂林區'],
                    ['Qieding','茄萣區']]
        },
        {
            'parent':['Penghu','澎湖縣'],
            'child':[['Penghu','澎湖縣'],['Magong','馬公市'],['Xiyu','西嶼鄉'],['Wang’an','望安鄉'],
                    ['Qimei','七美鄉'],['Baisha','白沙鄉'],['Huxi','湖西鄉']]
        },
        {
            'parent':['Kinmen','金門縣'],
            'child':[['Kinmen','金門縣'],['Jinsha','金沙鎮'],['Jinhu','金湖鎮'],['Jinning','金寧鄉'],
                    ['Jincheng','金城鎮'],['Lieyu','烈嶼鄉'],['Wuqiu','烏坵鄉']]
        },
        {
            'parent':['Pingtung County','屏東縣'],
            'child':[['Pingtung County','屏東縣'],['Pingtung City','屏東市'],['Sandimen','三地門鄉'],['Wutai','霧臺鄉'],
                    ['Majia','瑪家鄉'],['Jiuru','九如鄉'],['Ligang','里港鄉'],['Gaoshu','高樹鄉'],
                    ['Yanpu','鹽埔鄉'],['Changzhi','長治鄉'],['Linluo','麟洛鄉'],['Zhutian','竹田鄉'],
                    ['Neipu','內埔鄉'],['Wandan','萬丹鄉'],['Chaozhou','潮州鎮'],['Taiwu','泰武鄉'],
                    ['Laiyi','來義鄉'],['Wanluan','萬巒鄉'],['Kanding','崁頂鄉'],['Xinpi','新埤鄉'],
                    ['Nanzhou','南州鄉'],['Linbian','林邊鄉'],['Donggang','東港鎮'],['Liuqiu','琉球鄉'],
                    ['Jiadong','佳冬鄉'],['Xinyuan','新園鄉'],['Fangliao','枋寮鄉'],['Fangshan','枋山鄉'],
                    ['Chunri','春日鄉'],['Shizi','獅子鄉'],['Checheng','車城鄉'],['Mudan','牡丹鄉'],
                    ['Hengchun','恆春鎮'],['Manzhou','滿州鄉']]
        },
        {
            'parent':['Taitung County','臺東縣'],
            'child':[['Taitung County','臺東縣'],['Taitung City','臺東市'],['Ludao','綠島鄉'],['Lanyu','蘭嶼鄉'],
                    ['Yanping','延平鄉'],['Beinan','卑南鄉'],['Luye','鹿野鄉'],['Guanshan','關山鎮'],
                    ['Haiduan','海端鄉'],['Chishang','池上鄉'],['Donghe','東河鄉'],['Chenggong','成功鎮'],
                    ['Changbin','長濱鄉'],['Taimali','太麻里鄉'],['Jinfeng','金峰鄉'],['Dawu','大武鄉'],
                    ['Daren','達仁鄉']]
        },
        {
            'parent':['Hualien County','花蓮縣'],
            'child':[['Hualien County','花蓮縣'],['Hualien City','花蓮市'],['Xincheng','新城鄉'],['Xiulin','秀林鄉'],
                    ['Ji’an','吉安鄉'],['Shoufeng','壽豐鄉'],['Fenglin','鳳林鎮'],['Guangfu','光復鄉'],
                    ['Fengbin','豐濱鄉'],['Ruisui','瑞穗鄉'],['Wanrong','萬榮鄉'],['Yuli','玉里鎮'],
                    ['Zhuoxi','卓溪鄉'],['Fuli','富里鄉']]
        }
    ]

    for data in arr:
        if data['parent'][0] in parent:
            for ch in data['child']:
                if ch[0] in child:
                    return data['parent'][1], ch[1]

    return '', ''


# a, b = getChinesePlace(' Nantou County','Lugu Township')
# print(a)
# print(b)