import streamlit as st
import pandas as pd
from collections import defaultdict

# Bootstrap Django so we can use the ORM
from streamlit_django import setup_django
setup_django()

from campaigns.models import Campaign, EmailEvent


st.title("Campaign analysis")


@st.cache_data(show_spinner=False)
def get_campaigns():
    return list(Campaign.objects.all())


campaigns = get_campaigns()
if not campaigns:
    st.warning("No campaigns found in the database.")
else:
    campaign = st.selectbox("Select campaign", options=campaigns, format_func=lambda c: c.name)

    st.subheader(f"Overview — {campaign.name}")
    cols = st.columns(3)
    with cols[0]:
        st.metric("Sent", campaign.sent_count)
    with cols[1]:
        st.metric("Opens", campaign.open_count)
    with cols[2]:
        st.metric("Clicks", campaign.click_count)

    # Aggregate events by month
    events = EmailEvent.objects.filter(email__campaign=campaign)
    by_month = defaultdict(lambda: {'opened': 0, 'clicked': 0, 'sent': 0})
    for ev in events:
        month = ev.created_at.strftime('%Y-%m')
        if ev.event_type == 'opened':
            by_month[month]['opened'] += 1
        elif ev.event_type == 'clicked':
            by_month[month]['clicked'] += 1
        elif ev.event_type == 'sent':
            by_month[month]['sent'] += 1

    if by_month:
        df = pd.DataFrame.from_dict(by_month, orient='index').sort_index()
        df.index.name = 'Month'
        st.subheader('Monthly events')
        st.bar_chart(df)
    else:
        st.info('No email events found for this campaign yet.')

    # Footer and behavior insights (simple examples)
    st.subheader('Per-email breakdown')
    emails = campaign.emails.all()
    rows = []
    for e in emails:
        rows.append({'Subject': e.subject, 'Sent': campaign.sent_count, 'Opens': campaign.open_count, 'Clicks': campaign.click_count})
    if rows:
        df2 = pd.DataFrame(rows)
        st.table(df2)