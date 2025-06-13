import streamlit as st
import pandas as pd
import smartsheet


def smartsheet_to_dataframe(sheet_id):
    smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
    sheet             = smartsheet_client.Sheets.get_sheet(sheet_id)
    columns           = [col.title for col in sheet.columns]
    rows              = []
    for row in sheet.rows: rows.append([cell.value for cell in row.cells])
    return pd.DataFrame(rows, columns=columns)


def display_setting_widget(setting, filter_by_column, status_icon):
    st.subheader(f'{status_icon} {setting.title()}')

    df = smartsheet_to_dataframe(st.secrets['smartsheet']['sheets'][setting])
    df = df.sort_values(by=filter_by_column).reset_index(drop=True)
    st.dataframe(data=df, use_container_width=True, key=f'{setting}_data_editor')
    st.link_button(label=f"ADJUST **{setting.upper()}** IN SMARTSHEETS", url=st.secrets['smartsheet']['urls'][setting], type='primary', use_container_width=True)


st.set_page_config(page_title='Manage', page_icon='⚙️', layout="wide", initial_sidebar_state="auto", menu_items=None)

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

    with st.sidebar: st.caption('ROYAL DESTINATIONS')

    st.info('Manage the settings for comp listings and dates.')

    display_setting_widget(setting='comps', filter_by_column='Unit_Code', status_icon='🏘️')
    display_setting_widget(setting='dates', filter_by_column='Start',     status_icon='🗓️')
