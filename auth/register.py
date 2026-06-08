import streamlit as st
from db import get_user, create_user

def register():
    new_u = st.text_input("Create Username")
    new_p = st.text_input("Create Password", type="password")
 
    if st.button("Register"):
        if get_user(new_u):
            st.error("User exists!")
        else:
            create_user(new_u, new_p, new_u)
            st.success("Registered!")