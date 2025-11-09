import streamlit as st
from typing import List

# Bootstrap Django so we can use the ORM
from streamlit_django import setup_django
setup_django()

from campaigns.models import Campaign, Email
import streamlit.components.v1 as components


st.title("Email version comparison")


@st.cache_data(show_spinner=False)
def get_campaigns() -> List[Campaign]:
    return list(Campaign.objects.all())


campaigns = get_campaigns()
if not campaigns:
    st.warning("No campaigns found in the database.")
else:
    campaign = st.selectbox("Select campaign", options=campaigns, format_func=lambda c: c.name)

    emails = list(campaign.emails.all())
    if not emails:
        st.info("This campaign has no emails configured.")
    else:
        email = st.selectbox("Select email", options=emails, format_func=lambda e: f"{e.order} - {e.subject}")

        orig, new = st.columns(2)

        with orig:
            st.subheader("Original email")
            # Render HTML body if present, otherwise show text body
            if email.body_html:
                st.components.v1.html(email.body_html, height=300)
            else:
                st.write(email.body_text)

        with new:
            st.subheader("Revised email")
            draft = st.text_area("Edit email below:", value=email.body_html or email.body_text or "", height=300)
            if st.button("Save draft"):
                # Persist edited draft back to the Email record
                email.body_html = draft
                email.save()
                st.success("Draft saved to database.")