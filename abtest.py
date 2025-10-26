import streamlit as st 

st.title("Email version comparison")

orig, new=st.columns(2)

with orig:
    st.subheader("Original email")
    st.write("Original email goes here")
with new:
    st.subheader("Revised email")
    draft=st.text_area("Edit email below:", height=250, placeholder="Type here...")