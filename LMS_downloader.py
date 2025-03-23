import os
import sys
import time
import threading
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import re
import configparser
from tqdm import tqdm
import subprocess
import urllib
import codecs
from lxml import html

class LMSDownloader:
    def __init__(self):
        #생성자
        #변수 선언
        self.username = ""
        self.password = ""
        self.down_path = "./m3u8DL"
        self.auto_name= False
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
            config["config"]["auto_name"] = "False"
            config["config"]["down_path"] = "./m3u8DL"
            config["config"]["LMS_Login_url"] = "https://your_university.ac.kr/login.php"

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
        chk= config["config"]["auto_name"]
        if(chk=="True"):
            self.auto_name = True 
        else: 
            self.auto_name = False
        self.LMS_url=config["config"]["LMS_Login_url"]
        if not os.path.exists(self.down_path):  # create only once
            os.mkdir(self.down_path)

    def LMS_login(self):
        #LMS에 로그인 함
        self.LMSSession = requests.session()
        """
        LOGIN_INFO = {
            "username": self.username,
            "password": self.password,
        }
        LOGIN_INFO = urllib.parse.urlencode(LOGIN_INFO)
        self.RequestHeaders = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "referer": self.LMS_url,
            "host": urlparts.netloc,
            "origin": "https://"+urlparts.netloc,
            "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "dnt": "1",
            "content-type":"application/x-www-form-urlencoded",
            "content-length": str(len(LOGIN_INFO)),
            "upgrade-insecure-requests": "1"
        }
        
        login = self.LMSSession.post(
            self.LMS_url, 
            data=LOGIN_INFO, 
            headers=self.RequestHeaders
        )

        dashboard = self.LMSSession.get(self.LMS_url)
        """
        # 크롬 드라이버 설정
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service

        # 크롬 드라이버 불러오기
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument('headless') # 이거 쓰면 headless 됨
        chrome_options.add_argument('window-size=1920x1080')
        chrome_options.add_argument("disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(self.LMS_url)
        driver.implicitly_wait(time_to_wait=5)

        print("Logging in.. Please Wait..")

        # 입력창 찾기
        username_input = driver.find_element("name", "username")
        password_input = driver.find_element("name", "password")

        # 값 입력 시키기
        username_input.send_keys(self.username)
        time.sleep(1)
        password_input.send_keys(self.password)
        time.sleep(1)

        # 엔터 입력 (로그인)
        password_input.send_keys(Keys.ENTER)
        time.sleep(1)

        # 쿠키 복사
        print(driver.get_cookies)
        _cookies = driver.get_cookies()
        cookie_dict = {}
        for cookie in _cookies:
            cookie_dict[cookie['name']] = cookie['value']

        # 복사후 크롬 드라이버는 종료
        driver.quit()

        # 세션 만들기
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        }
        self.LMSSession.headers.update(headers)  # User-Agent 변경
        self.LMSSession.cookies.update(cookie_dict)  # 응답받은 cookies로 변경
        
        # 로그인 여부 확인 (로그아웃 같은게 없다면 실패와 같음)
        urlparts = urllib.parse.urlparse(self.LMS_url)
        dashboard = self.LMSSession.get("https://"+urlparts.netloc)
        if not ("로그아웃" in dashboard.text or "로그 아웃" in dashboard.text or "log out" in dashboard.text or "logout" in dashboard.text or "退出登录" in dashboard.text or "ログアウト" in dashboard.text):
            print("Login Failed!!")
            input("Press Enter to Continue...")
            exit()
        print("Login Successful")

    def get_html(self, url):
        html = self.LMSSession.get(url)
        return html.text


    # m3u8 정보 따오는 함수 
    # return : m3u8주소, 영상 제목
    def getM3U8Info(self, url):
        if url.find("view.php") != -1:
            url = url.replace("view.php", "viewer.php")

        rawHtml = self.get_html(url)
        tree = html.fromstring(rawHtml)

        result_URL = tree.xpath('/html/head/script[3]/text()')
        result_name = tree.xpath('//*[@id="vod_header"]/h1/text()')[0].strip()

        match = re.search(r"file: '(.+?)'", result_URL[0])

        if match:
            m3u8URL = match.group(1)
            return m3u8URL, result_name
        else :
            return("Unvalid URL!")

    # 페이지 저장하는 함수
    # m3u8 따오는 함수로 변경해야함
    def saveM3U8(self, url, name):
        # subprocess에 의한 ffmpeg 호출과정
        # auto_name이 true일 경우 자동이름
        if(self.auto_name == True):
            fileName = name

        # false일 경우 이름 따로 받음
        else:
            fileName = input("저장할 파일의 이름을 입력해주세요 (미입력시 임의로 저장됩니다) : ")
            if len(fileName) < 1 :
                fileName = name

        # 파일명에 특수문자가 들어가면 안되므로 제거
        fileName = re.sub(r'[\\/:*?"<>|]', '', fileName)
        
        # ffmpeg 호출
        code=subprocess.call([
        'ffmpeg',
        '-i', '%s' %url,
        '-codec','copy', '%s/%s.mp4' %(self.down_path, fileName),
        ])
        print('process = ' + str(code))
        
# 메인함수
def main():
    S=LMSDownloader()
    while True:
        urlin = input("다운로드 할 링크 입력 (exit 입력으로 종료) : ")

        if urlin == "exit":
            exit(0)

        m3u8Link, fileName = S.getM3U8Info(urlin)
        S.saveM3U8(m3u8Link, fileName)
    
if __name__ == "__main__":
	main()
