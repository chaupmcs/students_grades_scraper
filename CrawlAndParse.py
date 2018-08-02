# coding: utf-8
import requests
from bs4 import BeautifulSoup  # To get everything
import re
import pandas as pd
import json
import os
import sys
import yaml
from PIL import Image
from PIL import ImageFilter
from pytesseract import pytesseract

class CrawlAndParse:

    ERRORS = {'ERROR_SAI_CAPTCHA': 'Khong the bypass captcha. Ban vui long kiem tra captcha roi chay lai. Chuong trinh ket thuc.',
            'ERROR_CHUA_CO_DIEM': 'Chua co diem. Chuong trinh ket thuc.',
            'ERROR_KET_QUA_RONG':'Ket qua rong. Kiem tra lai hoc_ky. Chuong trinh ket thuc.'}

    MAXIMUM_TEST_CAPTCHA = 100

    url = "http://www.aao.hcmut.edu.vn/image/data/Tra_cuu/xem_bd"
    link_captcha = 'http://aao.hcmut.edu.vn/image/data/Tra_cuu/phpcaptcha/captcha.php'

    key = ['MSSV', 'HoVaTen', 'MaMH', 'TenMH', 'Nhom', 'SoTC', 'DiemThanhPhan', 'DiemThi', 'DiemTK']
    key_sort = ['STT', 'MSSV', 'HoVaTen', 'Nhom', 'DiemThanhPhan', 'DiemThi', 'DiemTK']

    mon_hoc_dict = {'Mang Xa Hoi': '505027', 'An Ninh Mang': '506005', 'Thuc Tap TN': '501302',
                    'Xu Ly Song Song': '501047',
                    'Phan Tich TKGT': '503003', 'Data mining': '503008'}

    hoc_ky_dict = {'Mang Xa Hoi': 'd.hk_nh=20162', 'An Ninh Mang': 'd.hk_nh=20162', 'Thuc Tap TN': 'd.hk_nh=20162',
                    'Xu Ly Song Song': 'd.hk_nh=20162',
                    'Phan Tich TKGT': 'd.hk_nh=20152', 'Data mining': 'd.hk_nh=20161'}

    ten_hoc_ky_dict = {'d.hk_nh=20172' : 'Học kì 2 (2017 - 2018)', 'd.hk_nh=20171' : 'Học kì 1 (2017 - 2018)',
                        'd.hk_nh=20162' : 'Học kì 2 (2016 - 2017)', 'd.hk_nh=20161' : 'Học kì 1 (2016 - 2017)',
                       'd.hk_nh=20152': 'Học kì 2 (2015 - 2016)', 'd.hk_nh=20151': 'Học kì 1 (2015 - 2016)',
                       'd.hk_nh=20142': 'Học kì 2 (2014- 2015)', 'd.hk_nh=20141': 'Học kì 1 (2014 - 2015)'}

    class_title_list = {'all': 'MT13', 'cs': 'MT13KHTN', 'cs_ce': 'MT13KSTN'}

    def __init__(self, subject_crawl = None, folder_names_ids = None):

        # Read parameters file:
        with open("parameters.yaml", 'r') as ymlfile:
            parameters = yaml.load(ymlfile)

        if subject_crawl == None:
            self.mon_hoc = parameters['mon_hoc']
        else:
            self.mon_hoc = subject_crawl
        if folder_names_ids == None:
            list_to_crawl = parameters['list_to_crawl']
        else:
            list_to_crawl = folder_names_ids


        self.ma_mon_hoc = CrawlAndParse.mon_hoc_dict[self.mon_hoc]


        path_list_to_crawl = self.get_sub_folder_of_working_folder(list_to_crawl)
        self.class_title = CrawlAndParse.class_title_list[list_to_crawl]


        # Read config file
        with open("config.yaml", 'r') as ymlfile:
            config = yaml.load(ymlfile)

        self.hoc_ky = CrawlAndParse.hoc_ky_dict[self.mon_hoc]
        self.ten_hoc_ky = CrawlAndParse.ten_hoc_ky_dict[self.hoc_ky]
        self.captcha_code = config['captcha_code']
        self.cookie = config['cookie']
        self.folder_store = os.path.join(config['folder_store'],  self.class_title, self.mon_hoc)


        with open(os.path.join(path_list_to_crawl, 'IDs.txt'), "r") as f:
            self.IDs = f.read().splitlines()

        with open(os.path.join(path_list_to_crawl, "Names.txt"), "r") as f:
            self.Names = f.read().splitlines()

        for i in range(len(self.Names)):
            self.Names[i] = self.Names[i].strip("\"")
            self.Names[i] = " ".join(self.Names[i].split())

    def run(self):

        print("\t################################################################")
        print("\t#                      ==== CATBUILTS ====                     #")
        print("\t#  ###############     ###################     #############   #")
        print("\t#  #   Ver 2.1   #     ## Crawl + Parse ##     # Jun 14 17 #   #")
        print("\t#  ###############     ###################     #############   #")
        print("\t################################################################")


        # let go
        print('starting...')
        result = self.getSubjectGrade_All()

        #if the previous captcha (session) is not working anymore:
        i_capt=0
        while result == CrawlAndParse.ERRORS['ERROR_SAI_CAPTCHA'] and i_capt < CrawlAndParse.MAXIMUM_TEST_CAPTCHA :
            self.captcha_code = self.readCaptcha()
            i_capt = i_capt + 1
            print('trying bypass captcha... ' + str(i_capt))
            result = self.getSubjectGrade_All()

        # update captcha (if the previous captcha changed):
        if i_capt > 0 and i_capt < CrawlAndParse.MAXIMUM_TEST_CAPTCHA:
            with open("config.yaml", 'r') as ymlfile:
                config = yaml.load(ymlfile)
                config['captcha_code'] = self.captcha_code
            with open("config.yaml", 'w') as ymlfile:
                yaml.dump(config, ymlfile)

        # if any errors:
        if result in CrawlAndParse.ERRORS.values():
            print(result)
            return None#exit
        else:
            print('\n' + str(self.mon_hoc) + ': crawl xong !\nLoading the result and save to files...\n')

        # load the result into a dataframe, rearrange and write to files:
        result = self.loadResultAndSaveFiles(result)
        print('down xong. Xuat file tai: ' + self.folder_store + '\n')
        return result

    def loadResultAndSaveFiles(self, result):
        # create json file
        result_json = json.dumps(result, ensure_ascii=False)

        # create a dataframe
        result_pd = pd.read_json(result_json)

        # sort
        result_pd = result_pd.sort_values('DiemTK', ascending=False)

        # add index col
        result_pd['STT'] = range(1, len(result_pd.index) + 1)

        if not os.path.exists(self.folder_store):
            os.makedirs(self.folder_store)

        # write json result to csv file
        result_pd.to_csv(os.path.join(self.folder_store, 'result.csv'), sep=',', columns=CrawlAndParse.key_sort,
                         encoding='utf-8', index=False)

        # write the dataframe to latex
        self.writeToLatex(result_pd)

        # read the csv into pandas
        read_pd = pd.read_csv(os.path.join(self.folder_store, 'result.csv'), index_col=False, header=0, squeeze=True)

        return read_pd


    def get_sub_folder_of_working_folder(self, list_to_crawl):
        full_path = os.path.realpath(__file__)
        working_folder = os.path.dirname(full_path)  # This file directory only
        return os.path.join(working_folder, 'IDs_Names',list_to_crawl)

    def checkCaptcha(self, td_all):
        grade = td_all[0]
        td_grade = grade.find_all('span')
        i = 0
        for t in td_grade:
            if (t.text == 'Nhập sai!'):
                #print('Nhập sai captcha !!!')
                return False

        return True


    def writeToLatex(self, result_pd):
        with open('latex_origin.tex', 'r') as file_read:
            latex = file_read.read()
                
        grade  = result_pd.to_latex(columns=CrawlAndParse.key_sort, encoding='utf-8', index=False)
        new_title = 'title{Diem Mon ' + self.mon_hoc + '}'
        class_title = 'author{Lớp ' +  self.class_title + ' - ' + self.ten_hoc_ky + '}'
        # Replace the target string
        latex_file = latex.replace('title{GRADE}', new_title)
        latex_file = latex_file.replace('author{catbuilts}', class_title)
        latex_file = latex_file.replace('%replace_here', grade)
        latex_file = latex_file.replace('begin{tabular}', 'begin{longtable}')
        latex_file = latex_file.replace('end{tabular}', 'end{longtable}')
        
        
        #result_pd.to_latex(self.folder_name + '/result_latex.txt', columns=CrawlAndParse.key_sort,
        # encoding='utf-8', index=False)

        # Write the file out again
        with open(os.path.join(self.folder_store,'result_latex.tex'), 'w') as file:
            file.write(latex_file)


    def getSubjectGrade(self, index_id, td_grade):
        dict_obj = {}  # to store the result
        for i in range(len(td_grade)):
            if (self.ma_mon_hoc == td_grade[i].text):
                dict_obj['MSSV'] = self.IDs[index_id]
                dict_obj['HoVaTen'] = self.Names[index_id]
                dict_obj['Nhom'] = td_grade[i + 2].text
                dict_obj['DiemThanhPhan'] = td_grade[i + 4].text
                dict_obj['DiemThi'] = td_grade[i + 5].text
                dict_obj['DiemTK'] = td_grade[i + 6].text
                if dict_obj['DiemTK'] == 'CH':
                    return CrawlAndParse.ERRORS['ERROR_CHUA_CO_DIEM']
                break
        return dict_obj


    def getSubjectGrade_All(self):
        store_list = []
        len_ids = len(self.IDs)
        last_percent_reported = None
        first_time = True
        for i in range(len_ids):

            response = requests.post(CrawlAndParse.url, cookies=self.cookie, files={'HOC_KY': (None, self.hoc_ky),
                                                                                    'mssv': (None, self.IDs[i]),
                                                                 'captcha_code': (None, self.captcha_code),
                                                                 'Submit': (None, '»Xem')})
            soup = BeautifulSoup(''.join(response.text), "lxml")

            td_all = soup.find_all('td')
            #check if captcha is valid
            if (first_time == True):
                first_time = False
                if self.checkCaptcha(td_all)==False:
                    return CrawlAndParse.ERRORS['ERROR_SAI_CAPTCHA']

            td = td_all[5]
            td_grade = td.find_all('td')
            result = self.getSubjectGrade(i, td_grade)
            if result == CrawlAndParse.ERRORS['ERROR_CHUA_CO_DIEM']: # hasnt had grades yet
                return result
            elif (len(result) > 0):
                store_list.append(result)


            #percent:
            percent = int(i * 100 / len_ids)
            if last_percent_reported != percent:
                if percent % 5 == 0:
                    sys.stdout.write("%s%%" % percent)
                    sys.stdout.flush()
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                last_percent_reported = percent
        if store_list==[]:
            return CrawlAndParse.ERRORS['ERROR_KET_QUA_RONG']

        return store_list

    def readCaptcha(self):
        r = requests.get(CrawlAndParse.link_captcha, cookies=self.cookie, stream=True)
        r.raw.decode_content = True  # handle spurious Content-Encoding
        ima_ = Image.open(r.raw).convert('L')

        # convert to gray scale
        #ima_ = Image.open('captcha.png').convert('L')

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

        #ima_.show()


if __name__ == "__main__":
    crawl = CrawlAndParse()
    crawl.run()
    print('Chuong trinh ket thuc\n')
