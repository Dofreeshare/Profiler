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

help_banner = """python scrapTAJ.py -[option]

-h : for this banner
-a : Program will request you for Username and Password
-t : Text file having user name and password in it
     Please make sure its name is Credentials.txt
"""

login_ID = None
login_pass = None
login_page = None
age_from = "25"
age_to = "27"

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
                    country text)''')
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
                print name_extract
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
                
                print city_extract_new
                
                country = city_extract_new[-1]
                if (len(city_extract_new) == 2):
                    state = city_extract_new[-2]
                    city = None
                elif(len(city_extract_new) == 3):
                    state = city_extract_new[-2]
                    city = city_extract_new[-3]
                
                try:
                    c.execute("insert into candidate values (?, ?, ?, ?, ?, ?)", (id ,f_name, l_name, city, state, country))
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

def main(argv):
    
    global login_ID
    global login_pass
    global login_page
    
    try:
        opts, remaining = getopt.getopt(argv, "hat")
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

    
#    sys.exit()
    
    conn = CreateNewDB()
    
    browser = NagivateToDashBoard()
    #Collect the First Stage of data
    CollectAllQuickSearch(browser, conn)
    
if __name__ == '__main__':
    main(sys.argv[1:])
