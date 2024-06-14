from multiprocessing import Pool, Event, Queue
import requests
import re
import subprocess  # 后续会用到，控制终端的库
import os
from tqdm import tqdm  # 为了好看，加上进度条
from time import sleep
import time
from multiprocessing.dummy import Pool  # 多线程的
from requests.exceptions import RequestException


#  
cookie =  ''
className =  "陀螺女孩 HD"
pageUrl = "http://v6.tlkqc.com/wjv6/202406/14/tbJrFT1LUy78/video/1000k_0X720_64k_25/hls/index.m3u8"
START = 20

# 处理cookies的方式
cookies = {}
cookie = cookie.encode('utf-8').decode('latin1')  # 如果cookies有中文，这样处理编码就不会报错了
# for k_v in cookie.split(';'):
#     k, v = k_v.split('=', 1)
#     cookies[k.strip()] = v.replace('"', '')
headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7,so;q=0.6',
    'Connection': 'keep-alive',
    'Origin': 'https://www.cupfox.cc',
    'Referer': 'https://www.cupfox.cc/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

def fetch_content_with_retry(ts_url, headers, max_retries=3):
    retry_count = 0
    while retry_count <= max_retries:
        try:
            # 尝试获取内容
            ts = requests.get(url=ts_url, headers=headers).content
            # 如果请求成功，则直接返回内容
            return ts
        except RequestException as e:
            print(f"请求出错: {e}, 尝试重新请求 ({retry_count + 1}/{max_retries})")
            retry_count += 1
            # 可以根据需要增加重试间隔，避免频繁重试
            # time.sleep(1)  # 例如，等待1秒后重试
        
    # 如果尝试了max_retries次仍然失败，则抛出异常
    raise Exception(f"请求{ts_url}失败，已达到最大重试次数{max_retries}")

def fetch_content(ts_url,tempName,index):
    if not os.path.exists("{}/{}".format(tempName,index)):
            try:
                ts_content = fetch_content_with_retry(ts_url, headers)
                # 在这里处理成功的响应
            except Exception as e:
                # 在这里处理最终失败的情况
                print(f"最终请求失败: {e}")
            else:  
                # 这是保存的函数，下边解释
                write(tempName, ts_content, index)


def download(filePath):
    videoName = className  # 保存的视频名
    print("download->", videoName)
    with open(file=filePath, mode='r') as f:
       m3u8_data = f.read()
    # 提取m3u8里边的ts文件的url
    ts_urls = re.findall('(http.*?\.ts)', m3u8_data)
    tempName = os.getcwd() + "/temp1/"+ videoName
    # 下载每一个ts文件
    for index, ts_url in tqdm(enumerate(ts_urls), total=len(ts_urls)):
        # 给下载的ts命名
        # index = re.findall('([^/]+)\.ts$', ts_url)[0]
        index = "{}.ts".format(index+100000)
        fetch_content(ts_url, tempName, index)
        # 将m3u8里边的ts url替换掉，成ts文件名，为了方便合并
        m3u8_data = m3u8_data.replace(ts_url, index)
    if 'URI' in m3u8_data:  # 判断是否有密钥，有就提取url下载key
        key_url = re.findall('URI="(.*?key)', m3u8_data)[0]
        key = requests.get(url=key_url, headers=headers).content
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
    download("./index.m3u8")