import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import json

# 1. UI Setup & Custom CSS (Bringing back the HTML look!)
st.set_page_config(page_title="SustAInability Oracle", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stMetric { background: #f9fafb; border: 1px solid #e5e7eb; padding: 15px; border-radius: 12px; }
    .report-card { background: #fff; border-radius: 16px; padding: 25px; border: 1px solid #e5e7eb; margin-top: 20px; }
    .conclusion-box { background: #f5f3ff; border-left: 5px solid #4f46e5; padding: 20px; border-radius: 8px; margin-bottom: 25px; color: #1e1b4b; }
    .red-flag-card { background: #fff1f2; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #fecaca; color: #991b1b; }
    .green-zone-card { background: #f0fdf4; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #bbf7d0; color: #166534; }
    .custom-header { font-weight: 800; font-size: 1.8em; letter-spacing: -1px; color: #111827; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar Navigation
with st.sidebar:
    st.title("🍃 Oracle Terminal")
    api_key = st.text_input("Gemini API Key", type="password")
    company_name = st.text_input("Company Entity", placeholder="e.g. ExxonMobil")
    jurisdiction = st.selectbox("Target Jurisdiction", ["California", "New York", "Texas"])
    st.divider()
    st.info("Ensure the Company Name matches the uploaded PDF for maximum accuracy.")

# 3. Main Interface
st.markdown(f'<div class="custom-header">Sust<span style="color:#22c55e">AI</span>nability Oracle <span style="font-size:0.8em">🍃</span></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Audit Target (PDF)", type="pdf")

if st.button("GENERATE INTERACTIVE ANALYSIS"):
    if not api_key or not uploaded_file or not company_name:
        st.warning("Initialization failed: Missing credentials or PDF target.")
    else:
        genai.configure(api_key=api_key)
        # Using the model that worked for you!
        model = genai.GenerativeModel('gemini-2.5-flash')

        with st.spinner("Oracle is auditing the data..."):
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

            try:
                response = model.generate_content(prompt)
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(res_text)

                # --- DASHBOARD RENDERING ---
                st.divider()
                st.subheader(f"Gap Analysis Report: {company_name}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric(f"{jurisdiction} Compliance", f"{data['state']['score']}%")
                col2.metric("GRI Standards", f"{data['gri']['score']}%")
                col3.metric("Net Zero Alignment", f"{data['nz']['score']}%")

                st.markdown(f"""
                    <div class="conclusion-box">
                        <strong>AI Auditor Conclusion:</strong><br>{data['state']['conclusion']}
                        <br><br><strong>Oracle Recommendation:</strong><br>{data['state']['recommend']}
                    </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div style="font-weight:800; color:#991b1b; margin-bottom:15px;">⊗ Red Flags</div>', unsafe_allow_html=True)
                    for red in data['state']['red']:
                        st.markdown(f'<div class="red-flag-card">{red}</div>', unsafe_allow_html=True)
                
                with c2:
                    st.markdown('<div style="font-weight:800; color:#166534; margin-bottom:15px;">⊙ Green Zone</div>', unsafe_allow_html=True)
                    for green in data['state']['green']:
                        st.markdown(f'<div class="green-zone-card">{green}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Analysis failed. The AI response was malformed. Error: {e}")

else:
    st.info("Waiting for Initialization. Upload a report and click 'Generate'.")
