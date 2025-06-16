import firebase_admin.firestore
import streamlit as st
import pandas as pd
import numpy as np

import firebase_admin
import smartsheet

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter, And


st.set_page_config(page_title='Reports', page_icon='📄', layout="wide", initial_sidebar_state="auto", menu_items=None)


def smartsheet_to_dataframe(sheet_id):
    smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
    sheet             = smartsheet_client.Sheets.get_sheet(sheet_id)
    columns           = [col.title for col in sheet.columns]
    rows              = []
    for row in sheet.rows: rows.append([cell.value for cell in row.cells])
    return pd.DataFrame(rows, columns=columns)


def get_daterange(column):
    today = pd.to_datetime('today')
    dates = column.date_input('Date Range', value=(today, today), max_value=today)

    if isinstance(dates, tuple) and len(dates) == 2:

        start_date, end_date = dates
        
        if (end_date - start_date).days > 9:
            st.error("Please select a date range of 10 days or less.")

            return None
        else:
            date_range = pd.date_range(start=start_date, end=end_date)
            date_range = date_range.strftime('%Y-%m-%d').to_list()

            return date_range
    
    else:
        st.warning("Please select a valid date range.")

        return None


def get_date(column):
    today = pd.to_datetime('today')
    date  = column.date_input('Date', value=today, max_value=today)

    return date





if 'valid_session' not in st.session_state: st.session_state['valid_session'] = False

display = st.empty()

if not st.session_state['valid_session']:

    with display.container():

        st.caption('ROYAL DESTINATIONS')
        st.header('Comp Listings Portal')
        st.info('Please login to view this page.')

        with st.form('login'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')

            if st.form_submit_button('LOGIN', use_container_width=True, type='primary'):
                if [username, password] in st.secrets['users']:
                    st.session_state['valid_session'] = True
                else:
                    st.warning('Please enter a valid username and password.')

if st.session_state['valid_session']:

    display.empty()

    with st.sidebar:
        st.caption('ROYAL DESTINATIONS')

    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

    if not firebase_admin._apps:
        auth = firebase_admin.credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(auth)

    db         = firestore.client()
    collection = db.collection(st.secrets['database']['collection'])

    
    l, r = st.columns(2)

    reports = [
        'Detail',
        '❗️ Comp Review',
        '🏘️ Comp Summary',
        '🏠 Unit Summary',
        '💲 Comp Booking Summary',
        '🕵️ Unit Comp Query',
        ]

    report = l.selectbox(label='Report', options=reports)
    

    match report:
        case 'Detail':
            st.info('This is the raw data that is populated with the comp listings script.')
            date_range = get_daterange(column=r)

        case '❗️ Comp Review':
            st.info('This is a list of comps that have returned zeros or undefined on specific comp weeks.')
            date_range = get_daterange(column=r)
        
        case '🏘️ Comp Summary':
            st.info('This is the per-comp, aggregate average of each non-zero-or-undefined value.')
            date_range = get_daterange(column=r)
    
        case '🏠 Unit Summary':
            st.info('This is the per-unit, aggregate average of each non-zero-or-undefined comps.')
            date_range = get_daterange(column=r)
        
        case '💲 Comp Booking Summary':
            st.info('This is the comparison of a date to the date prior, highlightling proposed bookings and associated rates.')
            date = get_date(column=r)
        
        case '🕵️ Unit Comp Query':
            st.info("This is the status of a unit\'s comps for a specific week.")

            cdf          = smartsheet_to_dataframe(st.secrets['smartsheet']['sheets']['comps'])
            ddf          = smartsheet_to_dataframe(st.secrets['smartsheet']['sheets']['dates'])
            ddf['Start'] = pd.to_datetime(ddf['Start']).dt.date.astype(str)
            ddf['End']   = pd.to_datetime(ddf['End']).dt.date.astype(str)
            ddf['Week']  = ddf['Start'] + ' - ' + ddf['End']
            cdf          = cdf.sort_values(by='Unit_Code').reset_index(drop=True)
            cdf          = cdf['Unit_Code'].drop_duplicates().to_list()
            ddf          = ddf.sort_values(by='Start').reset_index(drop=True)
            ddf          = ddf['Week'].to_list()
            unit         = l.selectbox(label='Unit', options=cdf)
            week         = r.selectbox(label='Week', options=ddf)

        case _:
            st.info('Coming soon!')





    if st.button('Pull Report', use_container_width=True, type='primary'):

        match report:
            case 'Detail':
                if date_range is not None:
                    query      = collection.where(filter=FieldFilter('Date','in',date_range)).stream()
                    result     = [item.to_dict() for item in query]
                    df         = pd.DataFrame(result)
                    df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
                    df['Date'] = pd.to_datetime(df['Date']).dt.date
                    st.dataframe(data=df, hide_index=True, use_container_width=True)


            case '❗️ Comp Review':
                if date_range is not None:
                    query        = collection.where(filter=FieldFilter('Date','in',date_range)).stream()
                    result       = [item.to_dict() for item in query]
                    df           = pd.DataFrame(result)
                    df['Date']   = pd.to_datetime(df['Date']).dt.normalize()
                    df['Date']   = pd.to_datetime(df['Date']).dt.date
                    df           = df.groupby(['Date','Season','Unit','Comp'])[['Total_Rate','Service_Fee','Cost_to_Guest']].agg(np.average)
                    df           = df[df.Cost_to_Guest == 0].reset_index()
                    df           = df[['Season','Unit','Comp']]
                    df           = df.drop_duplicates()
                    df           = df.groupby(['Unit','Comp'])['Season'].agg(list).reset_index()
                    df['Misses'] = df['Season'].str.len()
                    df           = df.sort_values(by='Misses', ascending=False)
                    st.dataframe(data=df, hide_index=True, use_container_width=True)


            case '🏘️ Comp Summary':
                if date_range is not None:
                    query      = collection.where(filter=FieldFilter('Date','in',date_range)).stream()
                    result     = [item.to_dict() for item in query]
                    df         = pd.DataFrame(result)
                    df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
                    df['Date'] = pd.to_datetime(df['Date']).dt.date
                    df         = df[df.Cost_to_Guest != 0]
                    df         = df.groupby(['Date','Season','Unit','Comp'])[['Total_Rate','Service_Fee','Cost_to_Guest']].agg(
                        Total_Rate = ('Total_Rate', np.average),
                        Service_Fee = ('Service_Fee', np.average),
                        Cost_to_Guest = ('Cost_to_Guest', np.average),
                        Count = ('Total_Rate','size')
                    )
                    st.dataframe(data=df, use_container_width=True)


            case '🏠 Unit Summary':
                if date_range is not None:
                    query      = collection.where(filter=FieldFilter('Date','in',date_range)).stream()
                    result     = [item.to_dict() for item in query]
                    df         = pd.DataFrame(result)
                    df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
                    df['Date'] = pd.to_datetime(df['Date']).dt.date
                    df         = df[df.Cost_to_Guest != 0]
                    df         = df.groupby(['Date','Season','Unit','Comp'])[['Total_Rate','Service_Fee','Cost_to_Guest']].agg(
                        Total_Rate = ('Total_Rate', np.average),
                        Service_Fee = ('Service_Fee', np.average),
                        Cost_to_Guest = ('Cost_to_Guest', np.average),
                        Count = ('Total_Rate','size')
                    )
                    df        = df.groupby(['Date','Season','Unit'])[['Total_Rate','Service_Fee','Cost_to_Guest']].agg(
                        Total_Rate = ('Total_Rate', np.average),
                        Service_Fee = ('Service_Fee', np.average),
                        Cost_to_Guest = ('Cost_to_Guest', np.average),
                        Count = ('Total_Rate','size')
                    )
                    st.dataframe(data=df, use_container_width=True)
            

            case '💲 Comp Booking Summary':
                prior_date   = date - pd.Timedelta(days=1)
                date_str     = date.strftime('%Y-%m-%d')
                prior_str    = prior_date.strftime('%Y-%m-%d')
                dates        = [date_str, prior_str]

                query        = collection.where(filter=FieldFilter('Date','in',dates)).stream()
                result       = [item.to_dict() for item in query]
                df           = pd.DataFrame(result)

                sdf          = df[df['Date'] == date_str]
                pdf          = df[df['Date'] == prior_str]

                sdf          = sdf[sdf.Cost_to_Guest == 0]
                pdf          = pdf[pdf.Cost_to_Guest != 0]

                df           = pd.merge(sdf, pdf, on=['Unit','Comp','Dates'], how='left', suffixes=('_s','_p'))
                df           = df[df.Cost_to_Guest_p.notnull()]
                df           = df[['Unit','Comp','Dates','Cost_to_Guest_p']]
                df['Nights'] = df['Dates'].str.split(' - ').apply(lambda x: (pd.to_datetime(x[1]) - pd.to_datetime(x[0])).days)
                df           = df.sort_values(by=['Unit','Comp','Dates']).reset_index(drop=True)
                df           = df.rename(columns={'Cost_to_Guest_p': 'Cost_to_Guest'})
                df           = df[['Unit','Comp','Dates','Nights','Cost_to_Guest']]
                df.Comp      = 'https://www.vrbo.com/' + df.Comp.astype(str)
                st.dataframe(data=df, use_container_width=True, hide_index=True)
            

            case '🕵️ Unit Comp Query':
                query            = collection.where(filter=And([FieldFilter('Unit','==',unit),FieldFilter('Dates','==',week)])).stream()
                result           = [item.to_dict() for item in query]
                df               = pd.DataFrame(result)

                df.Date          = pd.to_datetime(df.Date).dt.normalize().dt.date
                df               = df.sort_values(by='Date').reset_index(drop=True)
                most_recent_date = df.tail(1).Date.values[0]
                ddf              = df[df.Date == most_recent_date]
                comps            = ddf.Comp.unique().tolist()
                results          = []

                for comp in comps:
                    cdf = df[df.Comp == comp]
                    cdf = cdf[cdf.Cost_to_Guest != 0]
                    la  = cdf.tail(1)
                    
                    if la.shape[0] == 0:
                        results.append([most_recent_date.strftime('%m/%d/%Y'), comp, 'Unavailable', 'Always been unavailable', 'No cost data'])
                    else:
                        is_most_recent = la.Date.values[0] == most_recent_date
                        
                        if is_most_recent:
                            results.append([most_recent_date.strftime('%m/%d/%Y'), comp, 'Available', la.Date.values[0].strftime('%m/%d/%Y'), la.Cost_to_Guest.values[0]])
                        else:
                            results.append([most_recent_date.strftime('%m/%d/%Y'), comp, 'Unavailable', la.Date.values[0].strftime('%m/%d/%Y'), la.Cost_to_Guest.values[0]])
                
                results = pd.DataFrame(results, columns=['As_of_Date','Comp','Availability_Status','Last_Available_Date','Cost_to_Guest'])
                st.dataframe(data=results, use_container_width=True, hide_index=True)


            case _:
                '**Coming soon!**'