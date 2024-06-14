from multiprocessing import pool
import requests
import re
import subprocess  # 后续会用到，控制终端的库
import os
from tqdm import tqdm  # 为了好看，加上进度条
from time import sleep
from multiprocessing.dummy import Pool  # 多线程的

#  
cookie = '_uab_collina=166183974175643687934375; Hm_lvt_92a5d4e0ba2140a5aa6001c88a65ef97=1661839705; looyu_id=2074544c1b3b028ddcf9b13e9771992a_20004236%3A1; Hm_lvt_5253ded03765ddd71ca75302ab1e548d=1661839705; _sensors_dapeng_anonymous_uuid=%22ccf1b1fe-934f-45e2-a84a-7cc0fda13830%22; _pk_ses.3.fd4d=1; _uab_collina=166184014501702175629925; _99_mon=%5B0%2C0%2C0%5D; _sensors_dapeng_login_id=%22k09rdwx4ap%22; Hm_lpvt_92a5d4e0ba2140a5aa6001c88a65ef97=1661844614; redirect_url=https://www.dapengjiaoyu.cn/dp-course/secure/course/playback?courseId=ijmiw8ve&stageId=e5acb4e292b741049ddcc7965f6da466&v=ef4825bc7eca11d196b87c5b185ebee8_e&cid=3c87c197009e4252ae7d1758ce9ad34b&faid=ccf1b1fe-934f-45e2-a84a-7cc0fda13830&said=ccf1b1fe-934f-45e2-a84a-7cc0fda13830&fuid=k09rdwx4ap&suid=&d=0&suu=a5add414-dff4-44d7-aef4-831ba944e9d7&suc=1; dptoken=3c1d2a05-cf0e-4762-9d02-65b5eda19a20; userinfo={%22userId%22:%22k09rdwx4ap%22%2C%22nickname%22:%22%E6%97%B6%E7%8E%96026%22%2C%22avatar%22:%22https://image.dapengjiaoyu.com/images/avatars/5avatar.jpg%22%2C%22dpAccount%22:%22dp79241393%22%2C%22mobile%22:%2215887442156%22%2C%22loginName%22:%22%E6%97%B6%E7%8E%96026%22%2C%22studentSatusId%22:null}; userCloseWxBinding=true; Hm_lpvt_5253ded03765ddd71ca75302ab1e548d=1661847559; looyu_20004236=v%3A2074544c1b3b028ddcf9b13e9771992a%2Cref%3A%2Cr%3A%2Cmon%3A//m6815.talk99.cn/monitor%2Cp0%3Ahttps%253A//www.dapengjiaoyu.cn/details/course%253Ftype%253DVIP%2526courseId%253Dijmiw8ve%2526faid%253D0853c508-9328-47e6-b65a-7b155523e509%2526said%253D0853c508-9328-47e6-b65a-7b155523e509%2526fuid%253Dkewhtyxxuk%2526suid%253D%2526d%253D0%2526suu%253D51898ffd-988e-4455-8d8e-4158660db282%2526suc%253D1%2526state%253DLIVING; _pk_id.3.fd4d=fb479c1886f88dca.1661839705.1.1661849149.1661839705.'
className =  "电商设计行业实战模块"
pageUrl = "https://www.dapengjiaoyu.cn/dp-course/api/courses/stages/jypgsforxz/chapters?courseId=ijmiym07&size=16&page="
START = 20

# 处理cookies的方式
cookies = {}
cookie = cookie.encode('utf-8').decode('latin1')  # 如果cookies有中文，这样处理编码就不会报错了
for k_v in cookie.split(';'):
    k, v = k_v.split('=', 1)
    cookies[k.strip()] = v.replace('"', '')
headers = {
    # 防盗链建议加上
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55',
    'Host': 'www.dapengjiaoyu.cn',
    'Referer': 'https://www.dapengjiaoyu.cn/dp-course/secure/course/playback?courseId=ijmiw8ve&stageId=e5acb4e292b741049ddcc7965f6da466&v=ef4825bc7ea791e031d703f31387c33b_e&cid=b0db646527dd482385a16825d7eff21b&faid=ccf1b1fe-934f-45e2-a84a-7cc0fda13830&said=ccf1b1fe-934f-45e2-a84a-7cc0fda13830&fuid=k09rdwx4ap&suid=&d=0&suu=a5add414-dff4-44d7-aef4-831ba944e9d7&suc=1'
}


def download(dom, x):
    videoName = dom['title']  # 保存的视频名
    print("download->", videoName)
    videoName = videoName.replace(' ', '').replace(
        "/", "-")  # 将空格替换掉，如果有空格，ffmpeg会报错
    m3u8_url = dom['videoContent']['mp4'].replace(
        '.mp4', '.m3u8').replace("mpv.videocc.net", 'hls.videocc.net')
    if not m3u8_url.endswith(".m3u8"):
        m3u8_url = "https://hls.videocc.net/ef4825bc7e/e/{}_1.m3u8".format(dom['videoContent']['vid'].replace("_e", ""))
    m3u8_data = requests.get(m3u8_url).text
    # 提取m3u8里边的ts文件的url
    ts_urls = re.findall('(http.*?\.ts)', m3u8_data)
    tempName = os.getcwd() + "/temp_" + str(x)
    # 下载每一个ts文件
    for ts_url in tqdm(ts_urls):
        # 给下载的ts命名
        index = re.findall('_(\d+\.ts)', ts_url)[0]
        if not os.path.exists("{}/{}".format(tempName,index)):
            ts = requests.get(url=ts_url).content
            # 这是保存的函数，下边解释
            write(tempName, ts, index)
        # 将m3u8里边的ts url替换掉，成ts文件名，为了方便合并
        m3u8_data = m3u8_data.replace(ts_url, index)
    if 'URI' in m3u8_data:  # 判断是否有密钥，有就提取url下载key
        key_url = re.findall('URI="(.*?key)', m3u8_data)[0]
        key = requests.get(url=key_url).content
        # tempName是文件夹的名称
        with open(tempName + '/' + 'key.m3u8', 'wb') as f3:
            f3.write(key)
        # 将kye的url替换成本地的key密钥，方便合并
        m3u8_data = m3u8_data.replace(key_url, 'key.m3u8')
    # 保存函数
    write(tempName, m3u8_data)
    # 利用ffmpeg合并视频的函数，下边有解释
    merge(videoName, tempName, x)
    # 删除除mp4文件以为的文件的函数，下边解释
    # remove()
    sleep(2)
    print(f'合成完毕:{videoName}')


# 保存文件的函数
def write(name, data, index=''):
    # 创建文件夹
    if not os.path.exists(name):
        os.mkdir(name)
     # 因为保存的格式不一样，需要判断一下
    if type(data) == str:
        # 这是m3u8文件
        with open(name + '/' + 'index.m3u8', 'w') as f1:
            f1.write(data)
    else:
        # 这是ts文件，index是上边的序号
        with open(name + '/' + index, 'wb') as f2:
            f2.write(data)


# 这是利用ffmpeg的函数
def merge(title, tempName, x):
    savePath = '{}/{}'.format(os.getcwd(),className)
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    # 还记得上边那个计数的x嘛，在这里用，因为如果名称一样的话，ffmpeg会报错
    c = 'ffmpeg -allowed_extensions ALL -i {}/index.m3u8 -c copy {}/{}{}.mp4'.format(
        tempName, savePath, x, title)
    # 在终端中输入ffmpeg的命令，合并视频
    subprocess.Popen(c, shell=True)


# 删除多余文件的函数
def remove():
    con = True
    while con:
        li = os.listdir()
        for i in li:
            # 我曾想检测到mp4合成以后再删除文件，就不用sleep()了，但是ffmpeg不是一次性合并完成，所以只能用sleep()了，如果大佬有好的方法，可以指点小弟一下
            if 'mp4' in i:
                for j in li:
                    if 'mp4' not in j:
                        os.remove(j)
                con = False
                break

if __name__ == '__main__':
    x = 0
    pool = Pool(10)
    # page = 1
    # while True:
    url = '{}{}'.format(pageUrl,str(page))
    menu = requests.get(url=url, headers=headers, cookies=cookies).json()
    if not menu:
        pass
        # break
    for tmp in menu:
        x += 1  # 计数
        if x > START:
            pool.apply_async(download, args=(tmp, x,))
    # page += 1
    pool.close()
    pool.join()