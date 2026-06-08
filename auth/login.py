import streamlit as st
import time
from db import get_user
 
def login():
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
 
    if st.button("Login"):
        res = get_user(u)
 
        if res and res["password"] == p:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.display_name = res["display_name"] or u
 
            st.success(f"✅ Welcome {st.session_state.display_name}")
            st.balloons()
            time.sleep(1)
            st.rerun()
 
        else:
            st.error("Invalid Credentials")