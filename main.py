import streamlit as st
import requests
import os
from google import genai

st.set_page_config(page_title="FPL AI Intelligence", page_icon="⚽")

st.title("⚽ FPL AI Strategy Dashboard")
st.write("Instant tactical analysis powered by Gemini Flash")

team_id = st.text_input("Enter your FPL Team ID:", placeholder="e.g. 1234567")

if st.button("Generate AI Breakdown", type="primary"):
    if not team_id:
        st.warning("Please enter a Team ID.")
    else:
        with st.spinner("Fetching squad data and running AI analysis..."):
            # 1. Fetch FPL Data
            try:
                bootstrap = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
                players = {p['id']: p['web_name'] for p in bootstrap['elements']}
                current_gw = next((e['id'] for e in bootstrap['events'] if e['is_current']), 1)
                
                picks_res = requests.get(f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{current_gw}/picks/").json()
                starting_xi = [players.get(p['element'], 'Unknown') for p in picks_res['picks'] if p['position'] <= 11]
                
                st.success(f"Loaded Gameweek {current_gw} Squad!")
                st.write("**Starting XI:** " + ", ".join(starting_xi))
                
            except Exception as fpl_err:
                st.error(f"FPL API Error: {fpl_err}")
                st.stop()

            # 2. Run Gemini AI Analysis
            try:
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
                    st.stop()

                client = genai.Client(api_key=api_key)
                prompt = f"Act as an elite FPL analyst. Here is my Gameweek {current_gw} starting XI: {', '.join(starting_xi)}. Give me 2 quick differential targets (<10% owned) and a 1-sentence team assessment."
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                st.markdown("---")
                st.markdown(response.text)

            except Exception as ai_err:
                st.error(f"Gemini API Error: {ai_err}")
