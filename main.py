import streamlit as st
import requests
import os

st.set_page_config(page_title="FPL AI Intelligence", page_icon="⚽")

st.title("⚽ FPL AI Strategy Dashboard")
st.write("Instant tactical analysis powered by Gemini AI")

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
                if picks_res.get("detail") == "Not found.":
                    st.error("Invalid Team ID. Please check and try again.")
                    st.stop()
                    
                starting_xi = [players.get(p['element'], 'Unknown') for p in picks_res['picks'] if p['position'] <= 11]
                
                st.success(f"Loaded Gameweek {current_gw} Squad!")
                st.write("**Starting XI:** " + ", ".join(starting_xi))
                
            except Exception as fpl_err:
                st.error(f"FPL API Error: {fpl_err}")
                st.stop()

            # 2. Run Gemini AI Analysis (REST Fallback Engine)
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
                st.stop()

            prompt = f"Act as an elite FPL analyst. Here is my Gameweek {current_gw} starting XI: {', '.join(starting_xi)}. Give me 2 quick differential targets (<10% owned) and a 1-sentence team assessment."

            # List of model endpoints to cycle through automatically
            candidate_models = [
                "gemini-1.5-flash-latest",
                "gemini-2.0-flash",
                "gemini-1.5-pro-latest",
                "gemini-1.5-flash"
            ]

            ai_response = None
            errors_log = []

            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }

                try:
                    res = requests.post(url, json=payload, headers=headers, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        ai_response = data['candidates'][0]['content']['parts'][0]['text']
                        break  # Successfully generated analysis!
                    else:
                        errors_log.append(f"{model_name}: HTTP {res.status_code}")
                except Exception as req_err:
                    errors_log.append(f"{model_name}: {req_err}")

            if ai_response:
                st.markdown("---")
                st.markdown(ai_response)
            else:
                st.error(f"AI Service busy. Retried models: {', '.join(errors_log)}. Please click button again in a few seconds.")





