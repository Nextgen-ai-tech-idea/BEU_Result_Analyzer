import streamlit as st
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import io

# ==========================================
# ✨ PAGE CONFIG
# ==========================================
st.set_page_config(page_title="BEU Result Analyzer", page_icon="🎓")

# ==========================================
# ✨ CUSTOM CSS 
# ==========================================
st.markdown("""
<style>
.stApp {
    background-color: #f8fafc;
}

/* Header style */
h1 {
    color: #1e3a8a !important; 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-top: 0px !important;
}

/* Labels */
.stTextInput label p, .stFileUploader label p {
    font-size: 20px !important;
    font-weight: 800 !important;
    color: #1e3a8a !important;
}

/* Boxes par border */
.stTextInput > div > div > input {
    border: 2px solid #1e3a8a !important;
    border-radius: 8px !important;
}

.stFileUploader > div > div {
    border: 2px dashed #1e3a8a !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
}

/* Button CSS */
div.stButton > button:first-child {
    background-color: #2563eb !important; 
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 10px 24px !important;
    font-size: 18px !important;
    width: 100%; 
    transition: 0.3s;
    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
}

div.stButton > button:first-child:hover {
    background-color: #1d4ed8 !important; 
}

/* Download Button CSS */
div.stDownloadButton > button {
    background: linear-gradient(135deg, #ff007f, #ff5e62) !important;
    color: white !important;
    font-weight: 800 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 12px 28px !important;
    font-size: 18px !important;
    transition: 0.3s;
    box-shadow: 0 4px 10px rgba(255, 94, 98, 0.4);
}

div.stDownloadButton > button:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 6px 15px rgba(255, 94, 98, 0.6);
}

.stFileUploader small {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🎨 WEB APP UI
# ==========================================

col1, col2 = st.columns([1, 5])

with col1:
    try:
        st.image("logo.jpg", width=80) 
    except:
        st.write("🎓")

with col2:
    st.markdown("<h1>BEU Result Analyzer</h1>", unsafe_allow_html=True)

st.write("") 

url = st.text_input("Result Page URL")
uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

if st.button("Start") and uploaded_file and url:
    df = pd.read_excel(uploaded_file)
    
    for col in df.columns:
        if 'CGPA' in col or 'SGPA' in col:
            df[col] = df[col].astype(object)
            
    if "Registration No." not in df.columns:
        st.error("Excel file me 'Registration No.' column nahi mila!")
    else:
        total_students = len(df)
        
        progress_text = f"⏳ Processing started... (0/{total_students})"
        progress_bar = st.progress(0, text=progress_text)
        
        # URL se parameters parse/extract karne ka logic
        for index, row in df.iterrows():
            reg_no = str(row['Registration No.']).strip()

            if reg_no != 'nan' and reg_no != '':
                try:
                    # BEU Result Search Backend API Call
                    api_url = "https://beu-bih.ac.in/api/result-search" 
                    
                    payload = {
                        "regNo": reg_no,
                        "semester": 7,
                        "exam_id": "250107"
                    }
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Content-Type': 'application/json'
                    }

                    response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # API JSON Response Structure Parsing
                        if 'data' in data or 'result' in data:
                            res_data = data.get('data', data.get('result', {}))
                            
                            # CGPA Set karna
                            if 'cgpa' in res_data:
                                df.at[index, 'Cur. CGPA'] = res_data['cgpa']
                            elif 'cur_cgpa' in res_data:
                                df.at[index, 'Cur. CGPA'] = res_data['cur_cgpa']
                                
                            # SGPA Semesters Set karna
                            if 'sgpa_list' in res_data and isinstance(res_data['sgpa_list'], list):
                                for i, sgpa_val in enumerate(res_data['sgpa_list']):
                                    col_name = f'Semester {i+1} SGPA'
                                    if col_name in df.columns:
                                        df.at[index, col_name] = sgpa_val

                except Exception as e:
                    # Error dekhne ke liye temporary warning log
                    st.warning(f"Reg No {reg_no} Error: {e}")

            # Progress Bar Update
            progress_bar.progress((index + 1) / total_students, text=f"⏳ Extracting Data... ({index + 1}/{total_students})")

        # ✨ NAYA LOGIC: Attractive Colorful Table
        st.markdown("### 📊 Final Result Data")

        styled_df = df.style.format(precision=2).set_properties(**{
            'background-color': '#eef2ff',
            'color': '#1e3a8a',
            'border-color': 'white',
            'font-weight': '500',
            'text-align': 'center'
        })

        styled_df = styled_df.set_table_styles([
            dict(selector='th', props=[('text-align', 'center')])
        ])

        st.dataframe(styled_df, use_container_width=True)

        # Download button
        output_name = "Final_Filled_" + uploaded_file.name
        output = io.BytesIO()
        df.to_excel(output, index=False)
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Filled Excel File",
            data=processed_data,
            file_name=output_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )