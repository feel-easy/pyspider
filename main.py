import os
import re
import subprocess
import requests
from tqdm import tqdm
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException

# 处理cookies的方式
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
            ts = requests.get(url=ts_url, headers=headers).content
            return ts
        except RequestException as e:
            print(f"请求出错: {e}, 尝试重新请求 ({retry_count + 1}/{max_retries})")
            retry_count += 1
    raise Exception(f"请求{ts_url}失败，已达到最大重试次数{max_retries}")

def fetch_content(ts_url, tempName, index):
    if not os.path.exists(f"{tempName}/{index}"):
        try:
            ts_content = fetch_content_with_retry(ts_url, headers)
        except Exception as e:
            print(f"最终请求失败: {e}")
        else:
            write(tempName, ts_content, index)

def download(filePath, videoName, host=""):
    print("download->", videoName)
    with open(file=filePath, mode='r') as f:
        m3u8_data = f.read()
    ts_urls = re.findall('(.*?\.ts)', m3u8_data)
    tempName = os.getcwd() + "/temp1/" + videoName
    if host:
        ts_urls = [f'{host}{url}' for url in ts_urls ]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for index, ts_url in enumerate(ts_urls):
            ts_index = f"{index + 100000}.ts"
            futures.append(executor.submit(fetch_content, ts_url, tempName, ts_index))
        for future in tqdm(as_completed(futures), total=len(futures)):
            future.result()

    for index, ts_url in enumerate(ts_urls):
        ts_index = f"{index + 100000}.ts"
        if host:
            ts_url = ts_url.replace(host, '')
        m3u8_data = m3u8_data.replace(ts_url, ts_index)

    if 'URI' in m3u8_data:
        key_url = re.findall('URI="(.*?key)', m3u8_data)[0]
        key = requests.get(url=key_url, headers=headers).content
        with open(f"{tempName}/key.m3u8", 'wb') as f3:
            f3.write(key)
        m3u8_data = m3u8_data.replace(key_url, 'key.m3u8')

    write(tempName, m3u8_data)
    merge(tempName, videoName)
    sleep(2)
    print(f'合成完毕: {videoName}')

def write(name, data, index=''):
    if not os.path.exists(name):
        os.mkdir(name)
    if type(data) == str:
        with open(f"{name}/index.m3u8", 'w') as f1:
            f1.write(data)
    else:
        with open(f"{name}/{index}", 'wb') as f2:
            f2.write(data)

def merge(tempName, title):
    savePath = f'{os.getcwd()}/{title}'
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    command = f'ffmpeg -allowed_extensions ALL -i "{tempName}/index.m3u8" -c copy {savePath}/{title}.mp4'
    subprocess.Popen(command, shell=True)

if __name__ == '__main__':
    pageUrl = "https://yzzy.play-cdn8.com/20220722/9500_f9e1dfc5/1000k/hls/index.m3u8"
    host = "https://yzzy.play-cdn8.com/20220722/9500_f9e1dfc5/1000k/hls/"
    
    fileName = "./index.m3u8"
    resp = requests.get(url=pageUrl, headers=headers)
    with open(file=fileName, mode='w') as f:
        f.write(resp.text)
    download(fileName,"林中小屋",host)
