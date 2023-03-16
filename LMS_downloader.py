# -*- coding: utf-8 -*-
import os, sys
import time
import threading
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import configparser
from tqdm import tqdm
import subprocess
import codecs

global username
global password
global img_path

def config_generator():
    file = 'config.ini'
    if os.path.isfile(file) == True:
        print('Config Exists')
    else:
        # 설정파일 만들기
        config = configparser.ConfigParser(interpolation=None)
        # 설정파일 오브젝트 만들기
        config['account'] = {}
        config['account']['username'] = 'username'
        config['account']['password'] = 'password'
        config['config'] = {}
        config['config']['down_path'] = './m3u8DL'
        
        # 설정파일 저장
        with open('./config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)

def config_read():
    # 설정파일 읽기
    config = configparser.ConfigParser(interpolation=None)    
    config.read('config.ini', encoding='utf-8')
    version_read(config)

def version_read(config):
    #정보 전역변수에 저장
    global username
    global password
    global down_path
    username = config['account']['username']
    password = config['account']['password']
    down_path = config['config']['down_path']
    if not os.path.exists(down_path): # create only once
            os.mkdir(down_path)
    
def LMS_login():
    global RequestHeaders
    global LMSSession
    LMS_url = "https://your_university.ac.kr/login/index.php"
    LMSSession = requests.session()
    
    LOGIN_INFO = {
        'username': username,
        'password': password,
        'goto': '/',
    }
    RequestHeaders = {'user-agent': UserAgent().random,
        'referer': LMS_url
    }
    login = LMSSession.post(LMS_url, data=LOGIN_INFO, headers=RequestHeaders)
    if login.status_code != 200:
        print('Login Failed!!')
        input('Press Enter to Continue...')
        exit()
    login.raise_for_status()
    print('Login Successful')

def get_text(url):
    global LMSSession
    html = LMSSession.get(url).text
    return html

config_generator()
config_read()
LMS_login()


# url로 get 요청을 보내는 함수
def get_html(url):
    global LMSSession
    global RequestHeaders
    _html = ""
    suc = False
    while(suc == False):
        try:
            resp = LMSSession.get(url,headers=RequestHeaders)
        except requests.exceptions.RequestException as e:
            time.sleep(3)
            continue

        if resp.status_code == 200:
            suc = True
            _html = resp.text
            print(_html)
        else:
            suc = True
            _html = "<tbody><td>잘못된 주소 입니다.</td></tbody>"
    return _html


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#페이지 저장하는 함수
#m3u8 따오는 함수로 변경해야함
def saveM3U8(url, name):
    global LMSSession
    global down_path
    if url.find('view.php')!=-1:
        url=url.replace('view.php','viewer.php')
    html=get_text(url)  
    
    #제목 찾기
    soup = BeautifulSoup(html, 'html.parser')
    for title in soup.find_all('title'):
        #print(title.get_text())
        name=title.get_text()
    
    #m3u8 찾기
    m = re.search('https://.*?\.m3u8', html)
    if m is not None:
        if m.group(0).count("https")!=1:
            #묶여서 잡히기 때문에 글자 제거 후 한번 더 돌려줌
            tmp=m.group(0).lstrip('h')
            n = re.search('https://.*?\.m3u8', tmp)
            #print(n.group(0))
            m3u8_url=n.group(0)
        elif m.group(0).count("https")==1:
            #print(m.group(0))
            m3u8_url=m.group(0)
    else:
        print("None Error!")
        return
    # subprocess에 의한 ffmpeg 호출과정
    code=subprocess.call([
    'ffmpeg',
    '-i', '%s' %m3u8_url,
    '-codec','copy', '%s/%s.mp4' %(down_path,name),
    ])
    print('process = ' + str(code))
    
# 메인함
def main():
    while True:
        urlin=input("다운로드 할 링크 입력 (exit 입력으로 종료) : ")
        if urlin == "exit":
            exit(0)
        #name=input("파일 이름 입력 : ")
        name=""
        if name == "":
            name="tmp"
        saveM3U8(urlin,name)
    
if __name__ == "__main__":
	main()

