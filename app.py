import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import json

# 1. UI Setup & Custom CSS
st.set_page_config(page_title="SustAInability Oracle", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stMetric { background: #f9fafb; border: 1px solid #e5e7eb; padding: 15px; border-radius: 12px; }
    .stMetric label { color: #4b5563 !important; font-weight: 700 !important; }
    .stMetric div[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 800 !important; }
    .conclusion-box { background: #f5f3ff; border-left: 5px solid #4f46e5; padding: 20px; border-radius: 8px; margin-bottom: 25px; color: #1e1b4b; }
    .red-flag-card { background: #fff1f2; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #fecaca; color: #991b1b; }
    .green-zone-card { background: #f0fdf4; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #bbf7d0; color: #166534; }
    .custom-header { font-weight: 800; font-size: 1.8em; letter-spacing: -1px; color: #111827; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar Configuration
with st.sidebar:
    st.title("🍃 Oracle Terminal")
    api_key = st.text_input("Gemini API Key", type="password")
    company_name = st.text_input("Company Entity", placeholder="e.g. ExxonMobil")
    jurisdiction = st.selectbox("Target Jurisdiction", ["California", "New York", "Texas"])
    st.divider()
    st.info("The AI will audit the PDF based on the Framework selected in the dashboard.")

# 3. Main Interface
st.markdown(f'<div class="custom-header">Sust<span style="color:#22c55e">AI</span>nability Oracle <span style="font-size:0.8em">🍃</span></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Audit Target (PDF)", type="pdf")

if st.button("GENERATE INTERACTIVE ANALYSIS"):
    if not api_key or not uploaded_file or not company_name:
        st.warning("Initialization failed: Please provide an API Key, Company Name, and PDF.")
    else:
        genai.configure(api_key=api_key)
        # Using the model we confirmed works for you!
        model = genai.GenerativeModel('gemini-2.5-flash') 

        with st.spinner("Oracle is auditing the data..."):
            try:
                # Extract Text
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                context = "".join([page.get_text() for page in doc])[:60000]

                # The Prompt
                prompt = f"""
                You are a Senior ESG Auditor. Analyze the provided text for {company_name}.
                Return ONLY a JSON object with this exact structure:
                {{
                  "state": {{"score": 0-100, "conclusion": "str", "recommend": "str", "red": [], "green": []}},
                  "gri": {{"score": 0-100, "conclusion": "str", "recommend": "str", "red": [], "green": []}},
                  "nz": {{"score": 0-100, "conclusion": "str", "recommend": "str", "red": [], "green": []}}
                }}
                TEXT: {context}
                """

                response = model.generate_content(prompt)
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                # Save data to session state so it stays visible during clicks
                st.session_state['audit_results'] = json.loads(res_text)
                st.session_state['run_complete'] = True

            except Exception as e:
                st.error(f"Analysis failed. Error: {e}")

# 4. Display Results (This part handles the 'Clickable' logic)
if st.session_state.get('run_complete'):
    data = st.session_state['audit_results']
    
    st.divider()
    st.markdown(f"### Gap Analysis Report: {company_name}")
    
    # 3 Metrics Boxes at the top (Filled)
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{jurisdiction} Compliance", f"{data['state']['score']}%")
    m2.metric("GRI Standards", f"{data['gri']['score']}%")
    m3.metric("Net Zero Alignment", f"{data['nz']['score']}%")

    st.markdown("---")
    
    # CLICKABLE SELECTOR
    framework = st.pills(
        "Select Detailed View:",
        options=["State Framework", "GRI Standards", "Net Zero Pathway"],
        default="State Framework"
    )

    if framework == "State Framework":
        res = data['state']
        title = f"{jurisdiction} Regulatory Audit"
    elif framework == "GRI Standards":
        res = data['gri']
        title = "GRI Standards Analysis"
    else:
        res = data['nz']
        title = "Net Zero Pathway Audit"

    st.markdown(f"#### {title}")
    
    st.markdown(f"""
        <div class="conclusion-box">
            <strong>Conclusion:</strong><br>{res['conclusion']}
            <br><br><strong>Oracle Recommendation:</strong><br>{res['recommend']}
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="font-weight:800; color:#991b1b; margin-bottom:10px;">⊗ Red Flags</div>', unsafe_allow_html=True)
        for red in res['red']:
            st.markdown(f'<div class="red-flag-card">{red}</div>', unsafe_allow_html=True)
    
    with c2:
        st.markdown('<div style="font-weight:800; color:#166534; margin-bottom:10px;">⊙ Green Zone</div>', unsafe_allow_html=True)
        for green in res['green']:
            st.markdown(f'<div class="green-zone-card">{green}</div>', unsafe_allow_html=True)

else:
    st.info("Waiting for Initialization. Upload a report and click 'Generate Analysis'.")
