import streamlit as st
import requests as req
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
import yaml

import warnings
warnings.filterwarnings("ignore")


with open('auth_config.yml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'sidebar')

#print(authentication_status)

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    
    #st.title('Some content')
    #with st.sidebar:
    #    logout_but = st.button("logout")
    st.markdown("""
    <style>
    body {
    background-color: black;
    }
    .header img {
    float: left;
    width: 150px;
    height: 150px;
    padding: 10px;
    }
    .header h1 {
    position: relative;
    text-align: center;
    color: orange;
    padding-top: 2em;
    </style>
    <div class="header">
    <h1 class="big-font">Mission Input Form</h1>
    </div>""", unsafe_allow_html=True)
    
    #st.write(f'Welcome *{name}*')

    def read_minerva(qr):
        #dat = {'query':qr, 'cluster-name':'minervaa'}
        creds = ('balaji', 'YXRsYXNfZTc1YzFhNjZhZTQwNmRiN2QyZjQ1MWIyMTZiMTA2NjQuMWFiMTUyODctMWZhMy00YWE5LTk3MzUtNzhhZTJlYmE4NjNi')
        init_req = req.post('https://tcp.enough-kingfish.dataos.app:7432/v1/statement?',
                        auth = creds,
                        headers={'cluster-name':'minervaa'},
                        data = qr)
        res = init_req.json()

        while (res['stats']['queued']) or ('data' not in res.keys()):
            #print(res)
            res = req.get(res['nextUri'], auth = creds).json()
        return res

    def minerva_to_pandas(res, count_qr = ""):
        if count_qr != "":
            count_res = read_minerva(count_qr)
            #print(res)
            total_count = count_res['data'][0][0]
        out_df = pd.DataFrame()
        cols = [c['name'] for c in res['columns']]
        while 'data' in res.keys():
            out_df = out_df.append(pd.DataFrame(res['data'], columns = cols))
            res = req.get(res['nextUri']).json()
            if count_qr != "":
                print("{0} out of {1} read".format(len(out_df), total_count), flush=True)
        return out_df

    fleet_qr = "SELECT DISTINCT model, icao24 FROM icebase.mitreusaf.usaf_fleet WHERE milage <> '0.0'"
    depot_qr = "SELECT depotid, depotname  FROM icebase.mitreusaf.usaf_depot"
    aoc_qr = "SELECT  idaoc, name FROM icebase.mitreusaf.usaf_aoc"

    fleet_init_res = read_minerva(fleet_qr)
    fleet_res = minerva_to_pandas(fleet_init_res).drop_duplicates(subset = ['model'])

    depot_init_res = read_minerva(depot_qr)
    depot_res = minerva_to_pandas(depot_init_res)

    aoc_init_res = read_minerva(aoc_qr)
    aoc_res = minerva_to_pandas(aoc_init_res)


    list_fleet_res = list(fleet_res['model'])
    list_aoc_res = list(aoc_res['name'])




    with st.form(key='mission_form'):
        

        title = st.text_input('Mission Name', '')

        total_kms = st.number_input('Total Distance (miles)')*1.6
    
        fleet = st.multiselect('Select your planned fleet', list_fleet_res)
        
        print(fleet)

        start_date = st.date_input(
            "Mission start date",
            datetime.now().date())

        end_date = st.date_input(
            "Mission end date",
            datetime.now().date()) 

        status = st.selectbox(
            'Mission Status',
            ('Active', 'Inactive', 'NA'))

        aoc = st.selectbox(
            'Select the Air Operations Center you would like to associate this mission with',list_aoc_res)
        print(aoc)

        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            #st.write(fleet)
            try:
                mis_res = req.get('https://enough-kingfish.dataos.app/usafmitredb/api/v1/missiondata').json()
                mis_df = pd.DataFrame(mis_res)
                mid_new = "USAF"+str(int(mis_df.tail(1).missionid.values[0].replace('USAF', ''))+1)
            except:
                mid_new = 'USAF10001'

            output_data = {
                "missionid": mid_new,
                "missionname": title,
                "fleet": fleet,
                "total_distance": total_kms,
                "startdate": start_date.strftime("%Y-%m-%d"),
                "enddate": end_date.strftime("%Y-%m-%d"),
                "status_mission": status,
                "depots": {},
                "aoc": aoc,
                "createdat": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "updatedat": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            #st.write(output_data)
            creds = ('balaji', 'dG9rZW5fbGVnYWxseV9hbWF6aW5nbHlfYWR2YW5jZWRfc2hpbmVyLmYyMDgyZDljLWUwOTktNDU3Ny1hOTIyLWMzNThkYWI0ZjAzMw==')
            res = req.post("https://enough-kingfish.dataos.app/usafmitredb/api/v1/missiondata",
                        json = output_data )#, auth = creds)
            #print(res.text)
            #st.balloons()
            if (res.status_code == 200) or (res.status_code == 201):
                st.success("Mission created successfully!")
            else:
                st.error(str(res.text), icon="🚨")

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')

