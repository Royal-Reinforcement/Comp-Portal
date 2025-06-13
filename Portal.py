import streamlit as st
import pandas as pd

st.set_page_config(page_title='Comp Listings Portal', page_icon='🏠', layout="centered", initial_sidebar_state="auto", menu_items=None)

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

    st.title('Comp Listings Portal')
    st.success('Welcome to the **Comp Listings Portal**!', icon='👋')
    st.info('Use the side navigation to **view reports** and **manage settings** pertaining to comp listings.')

    with st.expander('See past updates'):
        for item in st.secrets['done']:
            item

    st.subheader('Coming soon')
    for item in st.secrets['soon']:
        item