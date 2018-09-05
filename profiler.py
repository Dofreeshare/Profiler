import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *

import sqlite3
from sqlite3 import Error, IntegrityError

import re

import sys, getopt
import getpass

import urllib

help_banner = """python scrapTAJ.py -[option]

-h : for this banner
-a : Program will request you for Username and Password
-t : Text file having user name and password in it
     Please make sure its name is Credentials.txt
-l : Level of data collection
"""

login_ID = None
login_pass = None
login_page = None
age_from = "25"
age_to = "29"

def CreateNewDB():
    print ("Creating New DB\n")
    try:
        conn = sqlite3.connect("TAJ.db")
    except Error as e:
        print(e)
    else:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS candidate (
                    id text PRIMARY KEY,
                    f_name text, 
                    l_name text,
                    city text,
                    state text,
                    country text,
                    dob text,
                    height real,
                    wt real,
                    edu text,
                    edu_det text,
                    profession text,
                    income text,
                    bir_time int,
                    bir_place text,
                    ex_country text,
                    bir_state text,
                    bir_city text,
                    guna real,
                    additional_info text)''')
        return conn
#    finally:
#        conn.close()

def GetCredentialsFromFile():
    ID = None
    password = None
    page = None
    
    if (os.path.isfile('Credentials.txt') & os.path.exists('Credentials.txt')):
        # Open the existing DB connection 
        try:
            with open("Credentials.txt", "r") as fd:
                ID = fd.readline()
                password = fd.readline()
                page = fd.readline()
                
        except IOError:
            print("Error in opening Credentials.txt\n")
    else:
        print("Credentials.txt doen't exist\n")
    
    return ID, password, page

def NagivateToDashBoard():
    
    global login_ID
    global login_pass
    global login_page
    
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("browser.privatebrowsing.autostart", True)

    browser = webdriver.Firefox(firefox_profile=firefox_profile)
    browser.get(login_page)
    try:
        #Input the user name
        login_element = WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#txtUsername')))
        login_element.send_keys(login_ID)
        login_element.submit()
        
        #Input password
        login_element = WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#txtPassword')))
        login_element.send_keys(login_pass)
        login_element.submit()
        
#        pop_up_element = browser.find_element_by_xpath('//a[@class="popup-modal-dismiss"]')
        pop_up_element = WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.XPATH, '//a[@class="popup-modal-dismiss"]')))
        pop_up_element.click()
        
        #Wait for Dashboard to load
        dash_board_element = WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="MenuIconLinks_Div"]')))
        return browser
        
    except NoSuchElementException:
        print ("Unable to find out login forms\n")
        return None
    except TimeoutException:
        print ("Timeout happened\n")
        return None

def CollectAllQuickSearch(browser, conn):
    
    c = conn.cursor()
    try:
        dash_board_element = browser.find_element_by_xpath('//div[@onclick="CheckMyProfileStatus(1);"]')
        dash_board_element.click()
        
        #Quick search
        qck_srch_element = WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.XPATH , '//div[@id="divDatingQuickSearch_MainSearchBlock"]')))
        
        qck_srch_element = browser.find_element_by_xpath('//select[@id="selDatingQuickSearch_AgeFrom"]')
        select = Select(qck_srch_element)
        select.select_by_visible_text(age_from)
        
        qck_srch_element = browser.find_element_by_xpath('//select[@id="selDatingQuickSearch_AgeTo"]')
        select = Select(qck_srch_element)
        select.select_by_visible_text(age_to)
        
        qck_srch_element = browser.find_element_by_xpath('//select[@id="selDatingQuickSearch_Caste"]')
        select = Select(qck_srch_element)
        select.select_by_value("2")
        
        qck_srch_element = browser.find_element_by_xpath('//input[@class="DatingCSS_SearchButton"]')
        qck_srch_element.click()
        
        curr_candidate_index = 1
        while(True):
            #Wait for the results to load
            all_list = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH , '//div[@class="ResultList"]')))

            while(True):
            
                curr_candidate_xpath = '//div[@class="ResultList"]/div['+str(curr_candidate_index)+']'
                try:
                    result_box_elements = browser.find_element_by_xpath(curr_candidate_xpath)
                except NoSuchElementException:
                    break
                result_row = result_box_elements
                curr_candidate_index = curr_candidate_index + 1
                name_tag = result_row.find_element_by_xpath('.//a[@class="LinkBold"]').text
                
                name_extract = re.findall("\w+", name_tag)
                print (name_extract)
                id = name_extract[-1]
                if (len(name_extract) == 1):
                    l_name = None
                    f_name = None
                elif (len(name_extract) == 2):
                    l_name = name_extract[-2]
                    f_name = None
                elif (len(name_extract) == 3):
                    l_name = name_extract[-2]
                    f_name = name_extract[-3]
                    
                city_tag = result_row.find_element_by_xpath('.//div[@class="Text" and @style="padding-top: 5px;"]').text
                city_tag_extract = re.split('\n', city_tag)
                city_extract_new = re.split(',', city_tag_extract[-1])
#                city_extract_new = re.findall('\w+', city_tag_extract[-1])
                
                print (city_extract_new)
                
                country = city_extract_new[-1]
                if (len(city_extract_new) == 2):
                    state = city_extract_new[-2]
                    city = None
                elif(len(city_extract_new) == 3):
                    state = city_extract_new[-2]
                    city = city_extract_new[-3]
                
                try:
                    c.execute("insert into candidate (id ,f_name, l_name, city, state, country) values (?, ?, ?, ?, ?, ?)", (id ,f_name, l_name, city, state, country))
                except IntegrityError:
                    print ("Already there\n")
                    continue
                
            print ("Clicking the for more Updates\n")
            temp_elem = browser.find_element_by_xpath('//div[@id="divMoreUpdates"]')
            temp_elem.click()
            browser.implicitly_wait(5)
            
    except NoSuchElementException:
        print ("Unable to find out login forms\n")
    except TimeoutException:
        print ("Timeout happened\n")
        
    finally:
#    browser.close()
        conn.commit()
        c.close()

def CollectDetailedInformation(browser, conn):

    if (os.path.isfile('List.txt') & os.path.exists('List.txt')):
        # Open the existing DB connection 
        try:
            with open("List.txt", "r") as fd:
                list = fd.readlines()
        except IOError:
            print("Error in opening Credentials.txt\n")
    else:
        print("List.txt doen't exist\n")
    
    if not os.path.exists('snaps'):
        os.mkdir('snaps')
    
    c = conn.cursor()
    try:
        # Scraping the Search results
        main_window = browser.current_window_handle
        
        #Wait for Dashboard to load
        dash_board_element = WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.XPATH, '//div[@onclick="CheckMyProfileStatus(1);"]')))
        dash_board_element.click()
        
        #Quick search
        qck_srch_element = WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.XPATH , '//div[@id="divDatingQuickSearch_MainSearchBlock"]')))
        
        for ID in list:
            qck_srch_element = browser.find_element_by_xpath('//input[@id="txtDatingQuickSearch_SearchByKeyword"]')
            qck_srch_element.send_keys(ID)
            
            qck_srch_element = browser.find_element_by_xpath('//input[@class="DatingCSS_SearchButton"]')
            qck_srch_element.click()
            
            
            #Wait for the results to load
            all_list = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH , '//div[@class="ResultList"]')))
    
            candidate_link = browser.find_element_by_xpath('//div[@class="ResultList"]/div[1]//a[@class="LinkBold"]')
            candidate_link.click()
            
            #switch to new window
            browser.switch_to_window(browser.window_handles[1])
            
            candidate_page = WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.XPATH , '//div[@class="PageMidBG"]')))
            
            raw_string = candidate_page.find_element_by_xpath('//span[@id="spnProfileSerialNumber"]').text
            print raw_string.encode('utf-8')
            if (raw_string is not None):
            
                dob = None
                height = None
                wt = None
                edu = None
                edu_det  =None
                profession = None
                income = None
                bir_time = None
                bir_place = None
                ex_country = None
                bir_state = None
                bir_city  = None
                
                candidate_id = raw_string[4:]
                
                cand_img = candidate_page.find_element_by_xpath('//div[@id="divDatingProfileView_PhotoContainer"]/img').get_attribute("src")
                print cand_img
                if (cand_img):
                    file_name = "snaps\\" + candidate_id + '.jpeg'
                    urllib.urlretrieve(cand_img, file_name)
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[6]').text
                if (raw_string is not None):
                    dob = raw_string.replace(" ", "")
                    (dat, mon, yr) = dob.split("-")
                    dob = yr+"-"+mon+"-"+dat
                    print dob
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[19]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    height = float(re.findall("(\d+.?\d+)(?= cms)", raw_string)[0])
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[20]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    print raw_string
                    wt = float(re.findall("(\d+.?\d+ ?)(?=Kg)", raw_string)[0])
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[38]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    edu = raw_string
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[39]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    edu_det = raw_string
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[41]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    profession = raw_string
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[45]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    income = raw_string
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[63]').text
                if (raw_string):
                    hour = int(re.findall("\d+", raw_string)[0])
                    min = int(re.findall("\d+", raw_string)[1])
                    sec = 0
                    bir_time = "{:0>2}:{:0>2}:{:0>2}".format(hour,min,sec)
                    print bir_city
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[64]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    bir_place = raw_string
                    
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[87]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    ex_country = raw_string
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[88]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    bir_state = raw_string
                
                raw_string = candidate_page.find_element_by_xpath('(//br[@class="Clear"]/preceding::div[@class="DatingCSS_ProfileCol2"])[89]').text
                print raw_string.encode('utf-8')
                if (raw_string):
                    bir_city = raw_string
                    
                try:
                    c.execute("update candidate set dob = strftime('%d-%m-%Y',?), height = ? , wt = ?, edu = ?, edu_det = ?, profession = ?, income = ?, bir_time = time(?),bir_place = ?,ex_country = ?, bir_state = ?, bir_city = ? where id = ?", (dob, height, wt, edu, edu_det, profession, income, bir_time, bir_place, ex_country, bir_state, bir_city, candidate_id))
                except IntegrityError:
                    print ("Unable to update\n")
                
            else:
                print("Unabled to retrieve the ID proceeding to next candidate dropping this one\n")
            
            browser.close()
            browser.switch_to_window(main_window)
            browser.implicitly_wait(1)
            qck_srch_element = browser.find_element_by_xpath('//input[@id="txtDatingQuickSearch_SearchByKeyword"]')
            qck_srch_element.clear()
            
    except NoSuchElementException:
        print ("Unable to find out login forms\n")
    except TimeoutException:
        print ("Timeout happened\n")
    except IndexError:
        browser.close()
        browser.switch_to_window(main_window)
        pass
        
    finally:
#    browser.close()
        conn.commit()
        c.close()
        
def Update_Guna(conn):
    
    if (os.path.isfile('List.txt') & os.path.exists('List.txt')):
        # Open the existing DB connection 
        try:
            with open("List.txt", "r") as fd:
                list_1 = fd.readlines()
        except IOError:
            print("Error in opening Credentials.txt\n")
            return
    else:
        print("List.txt doen't exist\n")
        return
    
    if (len(list_1) == 0):
        print("No data in list.txt\n")
        return
    
    list_1 = map(lambda s: s.strip(), list_1)
    
    print list_1
    
    c = conn.cursor()
    
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("browser.privatebrowsing.autostart", True)

    browser = webdriver.Firefox(firefox_profile=firefox_profile)
#    browser.get('https://www.mpanchang.com/astrology/kundali-matching/')

    # Read the boys details
    try:
        c.execute("select candidate.f_name, candidate.dob, candidate.bir_time, candidate.bir_place from candidate where id = '1'")
    except IntegrityError:
        print ("Unable to read boys data from database\n")
    
    boy_data = c.fetchone()
    
    boy_f_name = "He"
    if (boy_data[0] != None):
        boy_f_name = boy_data[0]
    boy_date_list = boy_data[1].split('-')
    boy_time_list = boy_data[2].split(':')
    boy_bir_place = boy_data[3]
    
    # Desired values range is 01 to 12
    boy_month = boy_date_list[1]
    
    # Desired values range is 1 to 31
    boy_date = "{0:1}".format(int(boy_date_list[0]))
    
    # Desired values range is 2018 to 1918
    boy_year = boy_date_list[2]
    
    # Desired values range is 0 to 59
    boy_sec = "{0:1}".format(int(boy_time_list[2]))
    
    # Desired values range is 0 to 59
    boy_min = "{0:1}".format(int(boy_time_list[1]))
    
    if (int(boy_time_list[0]) > 12):
        boy_hour = str(int(boy_time_list[0]) - 12)
        # Desired values range is 0 to 12
        boy_hour = "{0:1}".format(int(boy_hour))
        boy_AM_PM = '02'
    else:
        boy_hour = "{0:1}".format(int(boy_time_list[0]))
        boy_AM_PM = '01'
    
    for ID in list_1:
        browser.get('https://www.drikpanchang.com/jyotisha/horoscope-match/horoscope-match.html')
        dash_board_element = WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.XPATH, '//div[@id="dpBoyData"]')))
        
        try:
            c.execute("select candidate.f_name, candidate.dob, candidate.bir_time, candidate.bir_place from candidate where id = ?", (ID,))
        except IntegrityError:
            print ("Unable to read girls database\n")
        
        candidate_data = c.fetchone()
        print candidate_data
        
        if ((candidate_data[1] == None) or (candidate_data[2] == None) or (candidate_data[3] == None)):
            print ("Unable to get %s candidate data properly\n") %(ID)
            continue
        #Male Details
        browser.find_element_by_xpath('//input[@id="kmb-name"]').send_keys(boy_f_name)
        
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-month"]'))
        input_fields.select_by_value(boy_month)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-day"]'))
        input_fields.select_by_value(boy_date)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-year"]'))
        input_fields.select_by_value(boy_year)
        
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-hr"]'))
        input_fields.select_by_value(boy_hour)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-min"]'))
        input_fields.select_by_value(boy_min)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-sec"]'))
        input_fields.select_by_value(boy_sec)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmb-ampm"]'))
        input_fields.select_by_value(boy_AM_PM)
        
        browser.find_element_by_xpath('//input[@id="kmb-city"]').send_keys(boy_bir_place)
       
        #female details
        f_name = "She"
        if (candidate_data[0] != None):
            f_name = candidate_data[0]
        date_list = candidate_data[1].split('-')
        time_list = candidate_data[2].split(':')
        bir_place = candidate_data[3]
        
        # Desired values range is 01 to 12
        month = date_list[1]
        
        # Desired values range is 1 to 31
        date = "{0:1}".format(int(date_list[0]))
        
        # Desired values range is 2018 to 1918
        year = date_list[2]
        
        # Desired values range is 0 to 59
        sec = "{0:1}".format(int(time_list[2]))
        
        # Desired values range is 0 to 59
        min = "{0:1}".format(int(time_list[1]))
        
        if (int(time_list[0]) > 12):
            hour = str(int(time_list[0]) - 12)
            # Desired values range is 0 to 12
            hour = "{0:1}".format(int(hour))
            AM_PM = '02'
        else:
            hour = "{0:1}".format(int(time_list[0]))
            AM_PM = '01'
        
        print ("Entering following detials for girl\n")
        print ("\nName: %s") %(f_name)
        
        print ("\nMonth: %s") %(month)
        print ("\nDate: %s") %(date)
        print ("\nYear: %s") %(year)
        
        print ("\nHour: %s") %(hour)
        print ("\nMin: %s") %(min)
        print ("\nSec: %s") %(sec)
        print ("\nZone: %s") %(AM_PM)
        
        browser.find_element_by_xpath('//input[@id="kmg-name"]').send_keys(f_name)
        
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-month"]'))
        input_fields.select_by_value(month)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-day"]'))
        input_fields.select_by_value(date)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-year"]'))
        input_fields.select_by_value(year)
        
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-hr"]'))
        input_fields.select_by_value(hour)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-min"]'))
        input_fields.select_by_value(min)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-sec"]'))
        input_fields.select_by_value(sec)
        input_fields = Select(browser.find_element_by_xpath('//select[@id="kmg-ampm"]'))
        input_fields.select_by_value(AM_PM)
        
        browser.find_element_by_xpath('//input[@id="kmg-city"]').send_keys(bir_place)
        
        raw_input("Press Enter to continue...")
        
#        browser.find_element_by_xpath('//input[@id="dpSubmitDiv"]').click()
        
        final_result = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, '//th[contains(text(),"Total Guna Milan =")]')))
        
        guna_temp = re.findall("[\d.]+(?= ?out)",final_result.text)[0]
        
        print guna_temp
        
        guna = float(guna_temp)
        
        print "\nCalculated guna are %f" %(guna)
        
        try:
            c.execute("update candidate set guna = ? where id = ?", (guna, ID))
        except IntegrityError:
            print ("Unable to update guna in database\n")
        
        conn.commit()
       
        
def main(argv):
    
    global login_ID
    global login_pass
    global login_page
    
    try:
        opts, remaining = getopt.getopt(argv, "hatl:")
    except getopt.GetoptError:
        print (help_banner)
    
    if (len(opts) == 0):
        print (help_banner)
        sys.exit()
    else:
        for o,a in opts:
            if o in ('-h'):
                print (help_banner)
            if o in ('-a'):
                login_ID = raw_input("Username:")
                login_pass = getpass.getpass("Password for " + login_ID + ":")
                login_page = raw_input("Enter Login page:")
            if o in ('-t'):
                (login_ID, login_pass, login_page) = GetCredentialsFromFile()
            if o in ('-l'):
                profiler_level = int(a)
                print (a)
    
#    sys.exit()
    
    conn = CreateNewDB()
    
    #Collect the First Stage of data
    if (profiler_level == 1):
        print ("Collecting only primary info\n")
        browser = NagivateToDashBoard()
        CollectAllQuickSearch(browser, conn)
    elif (profiler_level == 2):
        print ("Collecting Full info\n")
        browser = NagivateToDashBoard()
        CollectDetailedInformation(browser, conn)
    elif (profiler_level == 3):
        print("Collecting the Guna\n")
        Update_Guna(conn)


if __name__ == '__main__':
    main(sys.argv[1:])
