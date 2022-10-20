import os
import sys
import time
import re
import socket
import json

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')


# 执行打卡
def send(sessionid, ur):
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': sessionid,
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL Build/RQ3A.210705.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36 AliApp(DingTalk/5.1.5) com.alibaba.android.rimet/13534898 Channel/212200 language/zh-CN UT4Aplus/0.2.25 colorScheme/light'
    }
    url = "https://skl.hdu.edu.cn/api/punch"
    data = {
        "currentLocation": "浙江省杭州市钱塘区",
        "city": "杭州市",
        "districtAdcode": "330114",
        "province": "浙江省",
        "district": "钱塘区",
        "healthCode": 0,
        "healthReport": 0,
        "currentLiving": 0,
        "last14days": 0
    }

    for retryCnt in range(3):
        try:
            res = requests.post(url, json=data, headers=headers, timeout=30)
            if res.status_code == 200:
                message(ur, "成功")
                return "打卡成功"
            elif retryCnt == 3:
                print("提交表单失败")
                message(ur, "失败")
                wechatNotice(os.environ["SCKEY"], "打卡失败")
        except Exception as e:
            if retryCnt < 2:
                print(e.__class__.__name__ + "打卡失败，正在重试")
                time.sleep(3)
            else:
                print("打卡失败")
                message(ur, "失败")
                wechatNotice(os.environ["SCKEY"], "打卡失败")


# 获取本地 SESSIONID
def punch(browser, wait, un, pd, ur):


    try:
        browser.get("https://cas.hdu.edu.cn/cas/login")
        wait.until(EC.presence_of_element_located((By.ID, "un")))
        wait.until(EC.presence_of_element_located((By.ID, "pd")))
        wait.until(EC.presence_of_element_located((By.ID, "index_login_btn")))
        browser.find_element(By.ID, 'un').clear()
        browser.find_element(By.ID, 'un').send_keys(un)  # 传送帐号
        browser.find_element(By.ID, 'pd').clear()
        browser.find_element(By.ID, 'pd').send_keys(pd)  # 输入密码
        browser.find_element(By.ID, 'index_login_btn').click()
    except Exception as e:
        print(e.__class__.__name__ + "无法访问数字杭电")
        message(ur, "失败，无法访问数字杭电")
        wechatNotice(os.environ["SCKEY"], "无法访问数字杭电")
        sys.exit(1)

    try:
        wait.until(EC.presence_of_element_located((By.ID, "errormsg")))
        print("帐号登录失败")
        message(ur, "失败，帐号登录失败")
        wechatNotice(os.environ["SCKEY"], un + "帐号登录失败")
    except TimeoutException as e:
        browser.get("https://skl.hduhelp.com/passcard.html#/passcard")
        for retryCnt in range(10):
            time.sleep(1)
            browser.save_screenshot("C:/Users/10663/Desktop/test.png")
            sessionId = browser.execute_script("return window.localStorage.getItem('sessionId')")
            if sessionId is not None and sessionId != '':
                break
        print(send(sessionId, ur))
    finally:
        browser.quit()

def getCookies():
    rep = requests.get(url="https://raw.githubusercontent.com/handsomeXZ/branch-filestorage-action/actions/filedb/cookie")
    return rep.text

if __name__ == '__main__':
    # https://login.dingtalk.com/oauth2/challenge.htm?client_id=dinghd3ewha7rzdjn3my&response_type=code&scope=openid&prompt=consent&state=lUQ2nF4gs5qfkAxILLf&redirect_uri=https%3A%2F%2Fskl.hdu.edu.cn%2Fapi%2Flogin%2Fdingtalk%2Fauth%3Findex%3D
    driver = webdriver.Chrome(service=Service('chromedriver'), options=chrome_options)
    wait = WebDriverWait(driver, 3, 0.5)
    # print(driver.get_cookies())
    driver.get("https://login.dingtalk.com/oauth2/challenge.htm?client_id=dinghd3ewha7rzdjn3my&response_type=code&scope=openid&prompt=consent&state=lUQ2nF4gs5qfkAxILLf&redirect_uri=https%3A%2F%2Fskl.hdu.edu.cn%2Fapi%2Flogin%2Fdingtalk%2Fauth%3Findex%3D")
    time.sleep(1)
    cookies = eval(getCookies())
    print(cookies)
    for cookie in cookies:
        driver.add_cookie(cookie)
    print(driver.get_cookies())
    driver.set_window_size(720, 1280)
    driver.get("https://login.dingtalk.com/oauth2/challenge.htm?client_id=dinghd3ewha7rzdjn3my&response_type=code&scope=openid&prompt=consent&state=lUQ2nF4gs5qfkAxILLf&redirect_uri=https%3A%2F%2Fskl.hdu.edu.cn%2Fapi%2Flogin%2Fdingtalk%2Fauth%3Findex%3D")
    time.sleep(1)
    driver.save_screenshot("/home/runner/work/branch-filestorage-action/branch-filestorage-action/scan.png")

    #Server()

# file = open("/home/runner/work/branch-filestorage-action/branch-filestorage-action/cookie", 'w')
# file.write("test")
# file.close()

