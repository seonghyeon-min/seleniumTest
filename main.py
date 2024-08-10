import pandas as pd
import streamlit as st
import csv
import orderingHandler

from io import StringIO
from streamlit_quill import st_quill

def set_page_config() :
    st.set_page_config(
        page_title="CP Ordering",
        layout='wide',
        initial_sidebar_state="expanded"
    )
    
def get_cpid_to_replace() : 
    replace_to = {
        '95384' : '357640', # tv_youtube : smnt_youtube for dev
        # '70318' : '1243766' # tv_netflix : smnt_netflix for dev
    }
    
    return replace_to

def main() :
    set_page_config()
    st.title("CP Ordering")
    st.info('This Application is for automation of cp ordering job, The platform object is over webOS23 ver.')
    
    # before starting ordering jobs, set configure
    col1, col2, col3, col4 = st.columns(4)
    
    with col1 :
        selectServer = st.selectbox('Server', ['', 'QA2', 'Production'])
        if selectServer == 'QA2' :
            URL = 'https://testsso.lge.com/' 
        else :
            URL = 'https://sso.lge.com/eplogin.jsp' # prod_login
            
    with col2 :
        selectPlatformCode = st.selectbox('Platform Code', ['', 'V24G', 'V24U', 'V24V'])
        
    with col3 : 
        serverID = st.text_input("input SDP Server ID",
                    value="",
                    placeholder='input id')
    with col4 :
        if selectServer == 'QA2' :
            serverPW = st.text_input("input SDP Server PW",
                    type="password",
                    value= "",
                    placeholder='input password')
        else :
            serverPW = st.text_input("input SDP Server PW",
                            "",
                            disabled=True,
                            placeholder='please log in by OTP')
            
    if selectServer and serverID and serverPW :
        serverPW_masking = '*'*len(serverPW)
        st.write(f'Server : {URL}, PlatformCode : {selectPlatformCode}, ID : {serverID}, Password : {serverPW_masking}')
        with st.expander("Input ordering app csv") :
            content = st_quill()
            
        try :
            orderingJoblst = content.split('\n')
            columns = orderingJoblst[0].split(',')
            data_row = []
            
            for row in orderingJoblst[1:] :
                if row :
                    reader = csv.reader(StringIO(row))
                    data_row.append(next(reader))
                    
            df = pd.DataFrame(data_row, columns=columns)
            scale_replace = get_cpid_to_replace()
            Ordering_df = df.replace(to_replace=scale_replace)

            st.dataframe(Ordering_df, use_container_width=True)
            
            if not Ordering_df.empty :
                isbuttonClicked = st.button("Ordering start")
                if isbuttonClicked :
                    if not orderingHandler.set_inital_setting(URL, selectServer, selectPlatformCode, serverID, serverPW, Ordering_df) : # orderings start
                        st.warning("🚨 check your condition (Server, ID, PW) --> try again")
                    else :
                        st.success('Ordering has been Finished, please check the result file')

        except Exception as err :
            st.warning('please input the csv text or take care the Error message.')
            st.exception(f'{err}')
    
    else :
        st.warning("🚨 check your condition (Server, ID, PW)")

    
    
    
                    
if __name__ == '__main__' :
    main()