import os
import sys
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

class LMSDownloader:
    def __init__(self):
        #생성자
        #변수 선언
        self.username = ""
        self.password = ""
        self.down_path = "./m3u8DL"
        self.RequestHeaders = {}
        self.LMSSession = None
        self.LMS_url = ""
        #선언시 기본으로 시작하는 것들
        self.config_generator()
        self.config_read()
        self.LMS_login()
    
    def config_generator(self):
        #설정 ini 생성
        file = "config.ini"
        if os.path.isfile(file) == True:
            print("Config Exists")
        else:
            # 설정파일 만들기
            config = configparser.ConfigParser(interpolation=None)
            # 설정파일 오브젝트 만들기
            config["account"] = {}
            config["account"]["username"] = "username"
            config["account"]["password"] = "password"
            config["config"] = {}
            config["config"]["down_path"] = "./m3u8DL"
            config["config"]["LMS_Login_url"] = "https://your_university.ac.kr/login/index.php"

            # 설정파일 저장
            with open("./config.ini", "w", encoding="utf-8") as configfile:
                config.write(configfile)
    
    def config_read(self):
        # 설정파일 읽기
        config = configparser.ConfigParser(interpolation=None)
        config.read("config.ini", encoding="utf-8")
        self.version_read(config)

    def version_read(self, config):
        # 정보를 변수들에 저장
        self.username = config["account"]["username"]
        self.password = config["account"]["password"]
        self.down_path = config["config"]["down_path"]
        self.LMS_url=config["config"]["LMS_Login_url"]
        if not os.path.exists(self.down_path):  # create only once
            os.mkdir(self.down_path)

    def LMS_login(self):
        #LMS에 로그인 함
        self.LMSSession = requests.session()

        LOGIN_INFO = {
            "username": self.username,
            "password": self.password,
            "goto": "/",
        }
        self.RequestHeaders = {
            "user-agent": UserAgent().random,
            "referer": self.LMS_url,
        }
        login = self.LMSSession.post(
            self.LMS_url, data=LOGIN_INFO, headers=self.RequestHeaders
        )
        if login.status_code != 200:
            print("Login Failed!!")
            input("Press Enter to Continue...")
            exit()
        login.raise_for_status()
        print("Login Successful")

    def get_text(self, url):
        html = self.LMSSession.get(url).text
        return html

    # 페이지 저장하는 함수
    # m3u8 따오는 함수로 변경해야함
    def saveM3U8(self, url):
        if url.find("view.php") != -1:
            url = url.replace("view.php", "viewer.php")
        html = self.get_text(url)

        # 제목 찾기
        soup = BeautifulSoup(html, "html.parser")
        for title in soup.find_all("title"):
            # print(title.get_text())
            name = title.get_text()

        # m3u8 찾기
        m = re.search("https://.*?\.m3u8", html)
        if m is not None:
            if m.group(0).count("https") != 1:
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
        '-codec','copy', '%s/%s.mp4' %(self.down_path,name),
        ])
        print('process = ' + str(code))
        
# 메인함
def main():
    S=LMSDownloader()
    while True:
        urlin=input("다운로드 할 링크 입력 (exit 입력으로 종료) : ")
        if urlin == "exit":
            exit(0)
        S.saveM3U8(urlin)
    
if __name__ == "__main__":
	main()