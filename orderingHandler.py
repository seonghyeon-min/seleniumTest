from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium import webdriver


import re, time, selenium, pyperclip, json, orderingLog
import streamlit as st
import pandas as pd

# ========== for dev =========== #

def set_inital_setting(*argv) :
    global URL
    global server
    orderingLog.SET_LOG()

    URL = argv[0]
    SDPURL = 'http://qt2-kic.smartdesk.lge.com/admin/master/ordering/ordering/retrieveAppOrderingList.lge?serverType=QA2'
    server = argv[1]

    orderingLog.log.info(f'{{"URL" : "{URL}", "ServerIndex":"{server}", "Platform Code" : "{argv[2]}"}}')
    st.info(f'{{"URL" : "{URL}", "ServerIndex":"{server}", "Platform Code" : "{argv[2]}"}}')
    get_driver()
    
    try :
        serverID, serverPW = argv[3], argv[4]
    except :
        orderingLog.log.info(f'exception happen at inital setting step.')
        return False
    
    retLogin = loginSession(serverID, serverPW)
    
    if retLogin :
        ## start to access Ordering SDP Site ##
        time.sleep(1.5)
        driver.get(SDPURL)
        if not loadOrderingJob(argv[2], argv[5]) :
            st.warning('🚨 Driver quit, unexpected condition has happened')
            driver.quit()
        
        return True
        
    else :
        orderingLog.log.info(f'{{"url" : "{SDPURL}", "retLogin" : "{retLogin}"}}')
        return False
        

def scale_zoomLevel(level) :
    zoomLevel = level
    
    driver.get('chrome://settings/')
    driver.execute_script(f'chrome.settingsPrivate.setDefaultZoom({zoomLevel});')
    orderingLog.log.info(f'{{"zoomLevel" : "{zoomLevel}"}}')

def is_alert_presented(delay=5) :
    try :
        alertPresented = WebDriverWait(driver, delay).until(EC.alert_is_present())
        print(alertPresented)
        
        if isinstance(alertPresented, selenium.webdriver.common.alert.Alert) :
            alert = driver.switch_to.alert
            alert_txt = alert.text
            alert.accept()
            return True, alert_txt
    
    except (NoAlertPresentException, TimeoutException):
        return True, 'No Alert'
    
    except Exception as err :
        orderingLog.log.info(f'{{"Exception"  : "{err}"}}')
        return False, err

def ClickEvent(contribute, path) :
    orderingLog.log.info(f'{{"contribute" : "{contribute}", "path" : "{path}"}}')
        
    try :
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((contribute, path)))
        element.click()

    except : # when Exception happen.
        driver.find_element(contribute, path).send_keys(Keys.ENTER)
        
def SendKeyEvent(contribute, path) : 
    orderingLog.log.info(f'{{"contribute" : "{contribute}", "path" : "{path}"}}')

    driver.find_element(contribute, path).send_keys(Keys.CONTROL, 'v')
    
def get_driver() :
    global driver
    st.info('get_driver session flow')
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                options=options)

    driver.maximize_window()
    driver.implicitly_wait(5)
    scale_zoomLevel(0.8)
    time.sleep(1.5)
    driver.get("http://naver.com")

    st.success('being successful to access page')
    st.code(driver.page_source)
    
    is_alert_presented() 
    return driver

def loginSession(id, pw) :
    ClickEvent(By.ID, 'USER')
    pyperclip.copy(id)
    SendKeyEvent(By.ID, 'USER')
    ClickEvent(By.ID, 'LDAPPASSWORD')
    pyperclip.copy(pw)
    SendKeyEvent(By.ID, 'LDAPPASSWORD')
    ClickEvent(By.ID, 'loginSsobtn')
    
    try :
        alertPresented = WebDriverWait(driver, 2).until(EC.alert_is_present())
        if isinstance(alertPresented, selenium.webdriver.common.alert.Alert) :
            driver.switch_to.alert.dismiss()

    except (NoAlertPresentException, TimeoutException):
        pass

    if is_loginSuccess() :
        orderingLog.log.info('get ready to order CP')
        return True
    else :
        return False

def is_loginSuccess() :
    chk_url = driver.current_url.split(';')[0]
    fail_endpoint = 'login_fail.jsp'
    
    if chk_url == URL + fail_endpoint :
        orderingLog.log.info('login Fail, please check the ID or Password')
        driver.quit()
        return False
    
    st.info('login Success')
    return True

def set_contribute(platform) :
    orderingLog.log.info(f'Set Contribute for ordering {{"platformCode" : "{platform}"}}')
    
    code = platform
    idx = -1
    length_Platform = len(driver.find_element(By.XPATH, '/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[1]/td/span/div/ul').find_elements(By.TAG_NAME, 'li'))
    
    ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[1]/td/span/div/button')

    for num in range(2, length_Platform+1) :
        candidate_platform = driver.find_element(By.XPATH, f'/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[1]/td/span/div/ul/li[{num}]/a/label').text
        modify_platform = candidate_platform.split('-')[1]
        
        if code == modify_platform :
            idx = num
            ret_cadidate_platform = candidate_platform 
            break

    if idx == -1 : # fail to find platform code
        orderingLog.log.info(f'ProductPlatform Code is not existed, Quit Driver')
        return False, idx
    
    time.sleep(1.5)
    
    ClickEvent(By.XPATH, f'/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[1]/td/span/div/ul/li[{idx}]/a/label')
    ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/div[1]/h3') # product-platform
    ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[3]/td[1]/select')
    # ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[3]/td[1]/select/option[1]') #request
    ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/fieldset/div/table/tbody/tr[3]/td[1]/select/option[2]') #draft 
    ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/div[2]/div[1]/select')
    ClickEvent(By.XPATH, '/html/body/div/div/form[2]/div/div[2]/div[1]/select/option[7]')
    
    time.sleep(1.5)
    
    return True, ret_cadidate_platform
    
def get_Pagination_group() :
    pagination_grp = ''.join(list(driver.find_element(By.XPATH, '/html/body/div/div/form[2]/div/nav/ul').text)).split('\n')
    orderingLog.log.info(f'allocatePage : {{"pagination_grp" : "{pagination_grp}"}}')
    
    return pagination_grp

def get_country_ordering_data(cntry, data) :
    flag = False
    needCols = ['Country Name', 'Order Type', 'App Name', 'App Id', 'Order Number']
    cntryOrdering = data[data['Country Name'] == cntry][needCols].reset_index(drop=True)
    
    if cntryOrdering.empty :
        orderingLog.log.info(f'{{"cntryOrdering" : "empty"}}')
        # st.info(f'{cntry} is not subject to do ordering')
        return flag, -1
    
    flag = True
    return flag, cntryOrdering

def set_orderingItems(data, country, ret) :
    try :
        home_items = data[data['Order Type'] == "HOME"]
        premium_items = data[data['Order Type'] == 'PREMIUM']
        
    except Exception as err :
        orderingLog.log.info(f'{{"Error" : "{err}"}}')
        return False
    
    ret[country]['HOME'] = {}
    ret[country]['HOME'] = dict((name, id) for name, id in zip(home_items['App Name'], home_items['App Id']))
    
    ret[country]['PREMIUM'] = {}
    ret[country]['PREMIUM'] = dict((name, id) for name, id in zip(premium_items['App Name'], premium_items['App Id']))

    orderingLog.log.info(f'{{"items" : "{ret}"}}')
    return True

def get_Instance(path) :
    try :
        _instance = driver.find_element(By.XPATH, path)
        orderingLog.log.info(f'{{"instance" : "{_instance}", "success" : {bool(_instance)}}}')
        return _instance
    
    except Exception as err :
        orderingLog.log.info(f'{{"Error" : {err}}}')
        return False

def get_ready_DragDrop_Event() : 
    global dropActions
    global home_candidate_Area
    global home_target_Area
    global premium_candidate_Area
    global premium_target_Area
    global home_candidate_len
    global premium_candidate_len
    
    dropActions = ActionChains(driver)
    home_candidate_Area = get_Instance('//*[@id="candidate1"]')
    home_target_Area = get_Instance('//*[@id="target1"]')
    
    premium_candidate_Area = get_Instance('//*[@id="candidate2"]')
    premium_target_Area = get_Instance('//*[@id="target2"]')
    
    if all([home_candidate_Area, home_target_Area, premium_candidate_Area, premium_target_Area]) :
        home_candidate_len = len(home_candidate_Area.find_elements(By.TAG_NAME, 'li'))
        premium_candidate_len = len(premium_candidate_Area.find_elements(By.TAG_NAME, 'li'))
        orderingLog.log.info(f'{{"home_candidate_len" : "{home_candidate_len}", "premium_candidate_len": "{premium_candidate_len}"}}')
        return True
    
    else :
        orderingLog.log.info(f'Please check the status of elements')
        return False
    
def get_cp_current_home(cntry, ret, pflag=False) :
    dRet = dict()
    dRet[cntry] = dict()
    preOrdered_homeApp = []
    home_target_len = len(home_target_Area.find_elements(By.TAG_NAME, 'li'))
    
    # TargerHome 영역에 전시된 앱들 pre-checking
    for idx in range(1, home_target_len+1) :
        text = driver.find_element(By.XPATH, f'//*[@id="target1"]/li[{idx}]/span[2]').text
        name, id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[0]
        preOrdered_homeApp.append([name, id])
        
    dRet[cntry] = {
        'ordered' : preOrdered_homeApp,
        'returnValue' : False 
    }
    
    if pflag :
        dRet[cntry]['returnValue'] = is_validation(preOrdered_homeApp, cntry, 'HOME', ret)
        
    orderingLog.log.info(f'{{"preOrdered_homeApp" : "{preOrdered_homeApp}", "returnValue":"{dRet[cntry]["returnValue"]}"}}')

    return dRet 

def get_cp_current_premium(cntry, ret, pflag=False) :
    dRet = dict()
    dRet[cntry] = dict()
    preOrdered_PremiumApp = []
    premium_target_len = len(premium_target_Area.find_elements(By.TAG_NAME, 'li'))
    
    if premium_target_len < 1:
        dRet[cntry] = {
            'ordered' : [],
            'returnValue' : False #ordering needed
        }
        return dRet
    
    for idx in range(1, premium_target_len+1) :
        text = driver.find_element(By.XPATH, f'//*[@id="target2"]/li[{idx}]/span[2]').text
        name, id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[-1]
        preOrdered_PremiumApp.append([name, id]) # string, string
    
    dRet[cntry] = {
        'ordered' : preOrdered_PremiumApp,
        'returnValue' : False
    }
    
    if pflag :
        dRet[cntry]['returnValue'] = is_validation(preOrdered_PremiumApp, cntry, 'PREMIUM', ret)
    
    return dRet

    
def is_validation(applist, cntry, area, base) :
    original = [[cp, id] for cp, id in base[cntry][area].items()]
    target = applist
    
    orderingLog.log.info(f'compare original with target data, {{"original" : "{original}", "target" : "{target}"}}')
    
    if original == target :
        orderingLog.log.info(f'{{"result" : "True"}}')
        return True
    else :
        orderingLog.log.info(f'{{"result" : "False"}}')
        return False
    
def clean_target_area(area) :
    if area == 'target1' :
        target_len = len(home_target_Area.find_elements(By.TAG_NAME, 'li'))
        drop_area = home_candidate_Area
        
    else :
        target_len = len(premium_target_Area.find_elements(By.TAG_NAME, 'li'))
        drop_area = premium_candidate_Area
    
    if target_len < 1 :
        orderingLog.log.info(f'there is no need to clean, "{area}" area')
        return
    
    orderingLog.log.info(f'Clean "{area}" area "{{"length" : "{target_len}"}}"')

    for _ in range(target_len, 0, -1) :
        dragItem = driver.find_element(By.XPATH,  f'//*[@id="{area}"]/li[1]')
        dropActions.move_to_element(dragItem).click_and_hold().move_to_element(drop_area).release().perform()
        is_alert_presented(3)
        
def auto_dragdrop(area, country, ret, platform) :
    enableMappingItems = checkPlatformisin(area, country, ret, platform)
    candidate_len, candidate_id, location = get_setup_instance(area)
    
    if area == 'target1' :
        if len(enableMappingItems) > 5 :
            enableMappingItems = reorganize_mapping_Items(enableMappingItems)
            
    for cp, cpID in enableMappingItems.items() :
        dropFlag = False
        orderingLog.log.info(f'start to find "{{"cp" : "{cp}", "cpID" : "{cpID}"}}"')

        for idx in range(1, candidate_len+1) :
            try :
                text = driver.find_element(By.XPATH, f'//*[@id="{candidate_id}"]/li[{idx}]/span[2]').text
                
            except Exception as err :
                orderingLog.log.info(f'while founding app, error happen {{"error" : "{err}"}}')
                return False
        
            name, Id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[-1]
            print(f'idx : {idx}, name : {name}, id: {Id}')
            if (cpID == Id) :
                dropFlag = True
                
                orderingLog.log.info(f'{{"cp" : "{name}", "cpID" : "{Id}", "isfound" : "True", "ord_candi" : "{idx}"}}')
                st.success(f'dropped "{{"cp" : "{name}", "cpID" : "{Id}"}}"')
                
                dragItem = driver.find_element(By.XPATH, f'//*[@id="{candidate_id}"]/li[{idx}]/span[2]')
                dropActions.move_to_element(dragItem).click_and_hold().move_to_element(location).release().perform()
                
                bRet, alertMessage = is_alert_presented(1)
            
                if 'not available' not in alertMessage :
                    orderingLog.log.info(f'{{"content" : {{"{name}" : "{Id}", "droppable" : "True", "alertText" : "None"}}}}')
                else : # found app not droppped
                    orderingLog.log.info(f'{{"content" : {{"{name}" : "{Id}", "droppable" : "False", "alertText" : "{alertMessage}"}}}}')
                break
    
        if not dropFlag  :
            orderingLog.log.info(f'fail to find "{{"cp" : "{cp}", "cpID" : "{cpID}"}}"')
            st.error(f'dropped error "{{"cp" : "{name}", "cpID" : "{Id}"}}"')
            return False
        
    return True

def reorganize_mapping_Items(Items) :
    reorganize_mapping_items = dict()
    
    for cp, cpID in dict(list(Items.items())[:4]).items() :
        reorganize_mapping_items[cp] = cpID

    for cp, cpID in dict(list(Items.items())[:3:-1]).items() :
        reorganize_mapping_items[cp] = cpID
        
    orderingLog.log.info(f'reorganization completed {{"reorganize_mapping_items" : "{reorganize_mapping_items}"}}')
    
    return reorganize_mapping_items

def checkPlatformisin(area, country, ret, platform) :
    # rgb(255, 0, 0) 인 경우 issue 가 있는 app으로 간주 
    unableDropItems = []

    if area == 'target1' :
        location = 'HOME'
        candidateLength = len(home_candidate_Area.find_elements(By.TAG_NAME, 'li'))
        path = 'candidate1'
        mapping_items = ret[country][location]    
    
    else :
        location = 'PREMIUM'
        candidateLength = len(premium_candidate_Area.find_elements(By.TAG_NAME, 'li'))
        path = 'candidate2'
        mapping_items = dict([[cp, cpID] for cp , cpID in ret[country][location].items()
                                if (cp, cpID) not in ret[country]['HOME'].items()])
        
    orderingLog.log.info(f'checkEnablePlatformList Start {{"mapping_items" : "{mapping_items}"}}')
    orderingLog.log.info(f'{{"location" : "{location}", "candidatelength" : "{candidateLength}", "path" : "{path}"}}')
    
    for idx in range(1, candidateLength+1) :
        text = driver.find_element(By.XPATH, f'//*[@id="{path}"]/li[{idx}]/span[2]').text
        plfmlist = driver.find_element(By.XPATH, f'//*[@id="{path}"]/li[{idx}]').get_attribute('plfmlist').split(',')
        try :
            styleCont = driver.find_element(By.XPATH, f'//*[@id="{path}"]/li[{idx}]').get_attribute('style').split('; ')

        except :
            styleCont = ''
        
        
        name, id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[-1]

        if id in list(mapping_items.values()) :
            orderingLog.log.info(f'{{"name" : "{name}({id})","platform_isin" : {bool(platform in set(plfmlist))}, "styleCont" : "{styleCont}"}}')
            
            if(platform not in plfmlist) or ('color: rgb(255, 0, 0)' in styleCont):
                orderingLog.log.info(f'{{"del" : "{id}"}}')
                unableDropItems.append(id)
            else :
                orderingLog.log.info('checkPlatformList Skip')
                continue
            
    enableMappingItems = dict([[cp, cpID] for cp, cpID in mapping_items.items() if cpID not in unableDropItems])

    orderingLog.log.info(f'{{"enableMappingItems" : "{enableMappingItems}"}}')
    
    return enableMappingItems
                
def get_setup_instance(area) :
    if area == 'target1' :
        candidate_len = len(home_candidate_Area.find_elements(By.TAG_NAME, 'li'))
        location = home_target_Area
        candidate_id = 'candidate1'
    
    else :
        candidate_len = len(premium_candidate_Area.find_elements(By.TAG_NAME, 'li'))
        location = premium_target_Area
        candidate_id = 'candidate2'
        
    return (candidate_len, candidate_id, location)

def is_Well_Ordered(area, original, country) :
    dropped_Items = dict()
    
    if area == 'target1' :
        target_len = len(home_target_Area.find_elements(By.TAG_NAME, 'li'))
    else :
        target_len = len(premium_target_Area.find_elements(By.TAG_NAME, 'li'))
        
    for idx in range(1, target_len+1) :
        text = driver.find_element(By.XPATH, f'//*[@id="{area}"]/li[{idx}]/span[2]').text
        name, id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[0]
        dropped_Items[name] = id
    
    orderingLog.log.info(f'{{ "original" : "{original}", "droppedItems" :"{dropped_Items}"}}')
    st.info(f'{country}, "droppend_Items" : {dropped_Items}')
    
    # --- start to verify ---#
    if len(dropped_Items) == 0 : return False
    if dropped_Items.values() == original.values() : return True
    else : # 계약상이유로 빠질수도있음, 해당앱은 무시하고 다음 앱오더링 진행하여 해당앱이 순서에서 제외된 경우
        droppedItemsOrd = dict([[items[1], ord] for ord, items in enumerate(dropped_Items.items(), 1)])
        orderingLog.log.info(f'{{"droppedItemsOrd" : "{droppedItemsOrd}"}}')
        
        step = 0
        
        for ord, items in enumerate(original.items(), 1) :
            order, cp, cpID = ord, items[0], items[1]
            
            if cpID in dropped_Items.values() :
                if order == droppedItemsOrd[cpID] : continue
                elif order == droppedItemsOrd[cpID] + step : continue
                else :
                    orderingLog.log.info(f'{{"country" : "{country}", "Vaildation" : "False"}}')
                    return False
                
            else :
                step += 1
    return True

def confirm_ordering_event() : 
    orderingLog.log.info("orderingConfirmation start")
    
    orderingStatus = driver.find_element(By.XPATH, '//*[@id="orderingForm"]/div[2]/div[2]/table/tbody/tr[2]/td[2]').text

    orderingLog.log.info(f'"{{"orderingStatus" : "{orderingStatus}"}}"')
    
    if orderingStatus == 'Draft' :
        ClickEvent(By.XPATH, '//*[@id="orderingForm"]/div[2]/div[8]/div[2]/button[1]')
    
    elif orderingStatus == 'Request' :
        ClickEvent(By.XPATH, '//*[@id="orderingForm"]/div[2]/div[8]/div[2]/button[3]')
        
    bRet, alertMsg = is_alert_presented(5)
    
    if alertMsg == 'No Alert' :
        ClickEvent(By.XPATH, '//*[@id="popup-todayChangeList"]/div/div/div[3]/button')

    while True :
        bRet, alertMsg = is_alert_presented(10)
        if alertMsg == 'Exposed App only can be ordered.' :
            st.warning(f'{alertMsg}, you gotta check app status')
            return False
        if alertMsg == 'No Alert' :
            orderingLog.log.info(f'{{"confirmFlag" : "{bRet}"}}')
            break
    
    return bRet

def make_dropped_data(cntry, original) :
    dropped_items = dict()
    dropped_items['HOME'] = []
    dropped_items['PREMIUM'] = []    
    
    # home #
    home_target_len = len(home_target_Area.find_elements(By.TAG_NAME, 'li'))
    for idx in range(1, home_target_len+1) :
        text = driver.find_element(By.XPATH, f'//*[@id="target1"]/li[{idx}]/span[2]').text
        name, id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[-1]
        
        if (name, id) in original[cntry]['HOME'].items() :
            dropped_items['HOME'].append(
                                            {
                                            'ord' : idx, 
                                            'app_name' : name, 
                                            'app_id' : id, 
                                            'isDropped' : True
                                            }
                                        )
        else :
            dropped_items['HOME'].append(
                                            {
                                            'ord' : idx, 
                                            'app_name' : name, 
                                            'app_id' : id, 
                                            'isDropped' : False
                                            }
                                        )
        
    # premium #
    premium_target_len = len(premium_target_Area.find_elements(By.TAG_NAME, 'li'))
    
    for idx in range(1, premium_target_len+1) :
        text = driver.find_element(By.XPATH, f'//*[@id="target2"]/li[{idx}]/span[2]').text
        name, id = re.sub(r' \([^)]*\)', '', text), re.compile('\(([^)]+)').findall(text)[-1]
        
        if (name, id) in original[cntry]['PREMIUM'].items() :
            dropped_items['PREMIUM'].append(
                                            {
                                            'ord' : idx, 
                                            'app_name' : name, 
                                            'app_id' : id, 
                                            'isDropped' : True
                                            }
                                        )
        else :
            dropped_items['PREMIUM'].append(
                                            {
                                            'ord' : idx, 
                                            'app_name' : name, 
                                            'app_id' : id, 
                                            'isDropped' : False
                                            }
                                        )
    
    orderingLog.log.info(f'{{"dropped_items" : "{dropped_items}"}}')

    return dropped_items        

def loadOrderingJob(platformCode, std_data) :
    st.info('access SDP stie ----> start ordering job')
    
    dropped_data = dict()
    cntry_cp_ordering = dict()
    platformCode = platformCode
    baseOrderingdata = std_data
    TargetCntryLst = list(baseOrderingdata['Country Name'].unique())
    
    orderingLog.log.info(f'{{"TargetCountry" : "{TargetCntryLst}"}}')
    
    if len(TargetCntryLst) == 0 :
        return False
    
    bset_Contribute, ret_platform = set_contribute(platformCode)
    
    orderingLog.log.info(f'{{"returnValue" : "{bset_Contribute}", "platformCode" : "{ret_platform}"}}')
    
    if not bset_Contribute :
        orderingLog.log.info('Fail to get Full String Platform Code')
        return False
            
    pagination_grp = get_Pagination_group()

    if '' in pagination_grp :
        orderingLog.log.info('Fail to delicate pagination_group')
        return False
    
    startPageIdx = int(pagination_grp[pagination_grp.index('1')])
    
    if 'Next' in pagination_grp :
        endpageIdx = int(pagination_grp[pagination_grp.index('10')])
    else :
        endpageIdx = int(pagination_grp[-1])
        
    orderingLog.log.info(f'{{"startPageIndex: : {startPageIdx}, "endPageIdx" : {endpageIdx}}}')
    
    for page in range(startPageIdx, endpageIdx+1) :
        try :
            pgXpath = f'/html/body/div/div/form[2]/div/nav/ul/li[{page}]/a'
        except :
            pgXpath = f'/html/body/div/div/form[2]/div/nav/ul/li/a'
            
        ClickEvent(By.XPATH, pgXpath)
        
        trLength = len(driver.find_element(By.XPATH, '/html/body/div/div/form[2]/div/div[3]/table/tbody').find_elements(By.TAG_NAME, 'tr'))
        
        for num in range(trLength, 0, -1) :
            time.sleep(1.5)
            country = driver.find_element(By.XPATH,
                        f'/html/body/div/div/form[2]/div/div[3]/table/tbody/tr[{num}]/td[2]').text
            
            # leave result dict.
            cntry_cp_ordering[country] = dict()
            orderingLog.log.info(f'{{"country" : "{country}"}}')
            
            bRet_get_ordering, country_ordering_df = get_country_ordering_data(country, baseOrderingdata)
            
            if not bRet_get_ordering :
                orderingLog.log.info(f'search next country, "{country}" data is empty')
                continue
            
            # # for leave streamlit log
            # partial_data_country = country_ordering_df[['App Name', 'App Id']].values.tolist()
            # st.info(f'{country} : {partial_data_country}')
            # # modal 로 만드는것도 괜찮
            
            bRet_set_orderingItems = set_orderingItems(country_ordering_df, country, cntry_cp_ordering)
            
            if not bRet_set_orderingItems :
                continue
            
            st.info(f'{country} : {cntry_cp_ordering[country]}')
            dropped_data[country] = []
            curr_window = driver.current_url
            refresh_flag = False
            
            ClickEvent(By.XPATH, f'/html/body/div/div/form[2]/div/div[3]/table/tbody/tr[{num}]/td[4]/a')
            
            curr_time = time.time()
            while driver.current_url == curr_window :
                if time.time() - curr_time > 30 :
                    orderingLog.log.info("Fail to load Page, Time out")
                    driver.refresh()
                    refresh_flag = True
                    break
                
            if refresh_flag : continue
            
            bRet_get_DragDrop_Event = get_ready_DragDrop_Event()
            if not bRet_get_DragDrop_Event :
                driver.back()
                continue
            
            # --- home --- #
            Ret_get_current_cp_home = get_cp_current_home(country,cntry_cp_ordering, True)
            
            if not Ret_get_current_cp_home[country]['returnValue'] : # False
                orderingLog.log.info('start Drag & Drop Event {"area" : "HOME"}')
                
                clean_target_area('target1')
                bRet_auto_dragdrop = auto_dragdrop('target1', country, cntry_cp_ordering, platformCode)
                
                if not bRet_auto_dragdrop : # drop fail
                    driver.back() # 다른 국가 먼저 우선? 아니면 try ?
                    continue
                
                # drop 잘됬는지 확인용
                bRet_is_Well_ordered = is_Well_Ordered('target1', cntry_cp_ordering[country]['HOME'], country)
                
                if not bRet_is_Well_ordered :
                    st.warning(f'[HOME] {country}_ordering_result : False')
                    driver.back() # ordering 실패
                    continue
                
                st.success(f'{country}_ordering_result : True')
            
            # if well ordered
            if Ret_get_current_cp_home[country]['returnValue'] or bRet_is_Well_ordered :
                bRet_comparision = bool(cntry_cp_ordering[country]['HOME'] == cntry_cp_ordering[country]['PREMIUM'])
                if bRet_comparision :
                    orderingLog.log.info(f'{{"bRet_comparision" : "{bRet_comparision}", "messages" : "no need to order at PREMIUM"}}')
                    
                    returnValue = make_dropped_data(country, cntry_cp_ordering)
                    dropped_data[country].append(returnValue)
                    st.info(f'{dropped_data[country]}', icon='ℹ️')
            
                    # press confirm button
                    if not confirm_ordering_event() :
                        driver.back()
                        continue
                    
                    time.sleep(2)
                    continue
                
            # --- PREMIUM --- #
            Ret_get_current_cp_premium = get_cp_current_premium(country, cntry_cp_ordering, True)
            if not Ret_get_current_cp_premium[country]['returnValue'] :
                orderingLog.log.info('start Drag & Drop Event {{"area" : "PREMIUM"}}')
                
                clean_target_area('target2')
                bRet_auto_dragdrop = auto_dragdrop('target2', country, cntry_cp_ordering, platformCode)
                
                if not bRet_auto_dragdrop :
                    driver.back()
                    continue
                
                bRet_is_Well_ordered = is_Well_Ordered('target2', cntry_cp_ordering[country]['PREMIUM'], country)
                
                if not bRet_is_Well_ordered :
                    st.warning(f'[PREMIUM] {country}_ordering_result : False')
                    driver.back() # ordering 실패
                    continue
                
            
            returnValue = make_dropped_data(country, cntry_cp_ordering)
            dropped_data[country].append(returnValue)
            st.info(f'{dropped_data[country]}', icon='ℹ️')
            
            
            # ordering Done #
            ClickEvent(By.XPATH, '//*[@id="orderingForm"]/div[2]/div[8]/div[2]/button[1]')
            
            try :
                ClickEvent(By.XPATH, '//*[@id="popup-todayChangeList"]/div/div/div[3]/button') # todayChangePopup confirm

            except :
                is_alert_presented(2)
                
            else :
                while True :
                    bRet, alertMsg = is_alert_presented(2)
                    if alertMsg == 'No Alert' :
                        orderingLog.log.info(f'{{"confirmFlag" : "{bRet}", "alertMsg" : "{alertMsg}"}}')
                        break
            
            if bRet :
                time.sleep(1.5)
            else :
                driver.back()
    
    orderingLog.log.info(f'{{"dropped_data" : "{dropped_data}"}}')
    st.json(dropped_data)
    driver.quit()
    
    return True