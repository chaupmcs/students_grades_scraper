import CrawlAndParse as code
import yaml
import requests
from bs4 import BeautifulSoup  # To get everything
import re
from PIL import Image
from PIL import ImageFilter
from pytesseract import pytesseract
import webbrowser
import time
import threading
import eventlet #set timeout for the request
#eventlet.monkey_patch()  #the program will auto finish after request timeout


url = "http://www.aao.hcmut.edu.vn/image/data/Tra_cuu/xem_bd"
link_captcha = 'http://aao.hcmut.edu.vn/image/data/Tra_cuu/phpcaptcha/captcha.php'
ERROR_SAI_CAPTCHA = -1
BYPASS_CAPTCHA = 1
CHUA_CO_DIEM = 2
CO_DIEM_ROI = 3
REQUEST_TIMEOUT = 4

num_of_request_timeout = 0
mon_hoc_list = ['An Ninh Mang', 'Thuc Tap TN', 'Xu Ly Song Song']
mon_hoc_dict = {'An Ninh Mang': '506005', 'Thuc Tap TN': '501302',
                'Xu Ly Song Song': '501047'}
hoc_ky = 'd.hk_nh=20162'
id = '51300904'
time_out_max = 20
time_loop = 300 #second


def checkCaptcha(td_all):
    grade = td_all[0]
    td_grade = grade.find_all('span')
    i = 0
    for t in td_grade:
        if (t.text == 'Nhập sai!'):# 'Nhập sai captcha !!!'
            return False

    return True


def readCaptcha(cookie):
    r = requests.get(link_captcha, cookies=cookie, stream=True)
    r.raw.decode_content = True  # handle spurious Content-Encoding
    ima_ = Image.open(r.raw).convert('L')

    px = ima_.load()

    # filter:
    for y in range(ima_.size[1]):
        for x in range(ima_.size[0]):
            if px[x, y] < 30 or px[x, y] > 230:
                px[x, y] = 255  # white
            else:
                px[x, y] = 0  # black

    ima_ = ima_.filter(ImageFilter.MaxFilter)
    return pytesseract.image_to_string(ima_)


def post_request(cookie, hoc_ky, id, captcha_code):
    try:
        with eventlet.Timeout(time_out_max):
            response = requests.post(url, cookies=cookie, files={'HOC_KY': (None, hoc_ky),
                                                                            'mssv': (None, id),
                                                                            'captcha_code': (None, captcha_code),
                                                                            'Submit': (None, '»Xem')})
    except:
        return REQUEST_TIMEOUT

    soup = BeautifulSoup(''.join(response.text), "lxml")

    td_all = soup.find_all('td')
    return td_all


def getSubjectGrade(mon_hoc, td_grade):
    dict_obj = {}  # to store the result
    for i in range(len(td_grade)):
        if (mon_hoc_dict[mon_hoc] == td_grade[i].text):
            dict_obj['DiemTK'] = td_grade[i + 6].text
            if dict_obj['DiemTK'] == 'CH':
                return CHUA_CO_DIEM
            else:
                return CO_DIEM_ROI

def down_grade(mon_hoc):
    crawl = code.CrawlAndParse(mon_hoc, 'cs_ce')
    crawl.run()

def run_check():
    #read_parameters
    with open("config.yaml", 'r') as ymlfile:
        config = yaml.load(ymlfile)

    captcha_code = config['captcha_code']
    cookie = config['cookie']

    first_time = True
    check = ERROR_SAI_CAPTCHA
    so_mon_co_diem = 0

    captcha_changed = False
    is_timeout = False

    while(check == ERROR_SAI_CAPTCHA):
        td_all = post_request(cookie, hoc_ky, id, captcha_code)

        if (td_all == REQUEST_TIMEOUT):
            global num_of_request_timeout
            num_of_request_timeout = num_of_request_timeout + 1
            print('REQUEST_TIMEOUT_' + str(num_of_request_timeout) + ': ' + time.ctime())
            is_timeout = True
            break

        # check if captcha is valid or not
        if checkCaptcha(td_all) == False:
            captcha_code = readCaptcha(cookie)
            captcha_changed = True
            check = ERROR_SAI_CAPTCHA
        else:
            check = BYPASS_CAPTCHA 

            td = td_all[5]
            td_grade = td.find_all('td')
            for mon_hoc in mon_hoc_list:
                result = getSubjectGrade(mon_hoc, td_grade)
                if result == CO_DIEM_ROI:
                    so_mon_co_diem = so_mon_co_diem + 1
                    print('da co diem mon ' + mon_hoc +'. downloading...\n')
                    down_grade();

                    #exclude the mon_hoc out of the list:
                    mon_hoc_list.remove(mon_hoc)
                    del mon_hoc_dict[mon_hoc]


    if  (captcha_changed == True): # updated captcha
        with open("config.yaml", 'r') as ymlfile:
            config = yaml.load(ymlfile)
            config['captcha_code'] = captcha_code
        with open("config.yaml", 'w') as ymlfile:
            yaml.dump(config, ymlfile)
            print('updated captcha !\n')

    thong_bao_da_co_diem = 'da co '+ str(so_mon_co_diem) + '/' + str(len(mon_hoc_list)) + ' mon co diem.\n============'

    if so_mon_co_diem == 0:
        if is_timeout == False:
            print('chua co mon nao trong ' + str(len(mon_hoc_list)) + ' mon co diem. '+ time.ctime())
        threading.Timer(time_loop, run_check).start()
    else:
        webbrowser.open(url, new=2)
        print(time.ctime())
        print(thong_bao_da_co_diem)
        return

if __name__ == '__main__':
    print('ver 2.1 Jun 15 2017 - starting...\n')
    run_check()

