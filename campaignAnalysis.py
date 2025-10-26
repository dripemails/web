import streamlit as st 
import pandas as pd 

st.title("Here's the latest on campaign: (campaign name)")
numViewsData={
    'Date': ['January 2025', 'February 2025', 'March 2025'],
    'Views': [200, 300, 500]
}
df1=pd.DataFrame(numViewsData)
behaviorsData={
    'Behavior': ['Clicking on ad', 'Ignoring ad'],
    'Number of people': [200, 400]
}
footerData={
    'Link': ['Privacy policy link', 'Main site link'],
    'Number of people': [200, 400]
}
df2=pd.DataFrame(behaviorsData)
numViews, behaviors=st.columns(2)
df3=pd.DataFrame(footerData)
with numViews:
    st.subheader("Number of views")
    st.bar_chart(df1.set_index('Date'))
with behaviors:
    st.subheader("Behavior analytics")
    st.bar_chart(df2.set_index('Behavior'))
st.subheader("Email footer analytics")
st.bar_chart(df3.set_index('Link'))