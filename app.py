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
        
        for index, row in df.iterrows():
            reg_no = str(row['Registration No.']).strip()

            if reg_no != 'nan' and reg_no != '':
                try:
                    session = requests.Session()
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }

                    # Pehle POST request try karein
                    response = session.post(url, data={'regNo': reg_no}, headers=headers, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Agar POST se table na mile, toh GET request try karein
                    if not soup.find_all('table'):
                        # URL ke aage query parameter jod kar GET karna
                        separator = '&' if '?' in url else '?'
                        full_url = f"{url}{separator}regNo={reg_no}"
                        response = session.get(full_url, headers=headers, timeout=15)
                        soup = BeautifulSoup(response.content, 'html.parser')

                    data_found = False

                    for table in soup.find_all('table'):
                        table_text = table.get_text()
                        # Keywords matching
                        if 'SGPA' in table_text or 'CGPA' in table_text:
                            rows = table.find_all('tr')
                            for r in rows:
                                cols = r.find_all(['td', 'th'])
                                cols_text = [c.get_text(strip=True) for c in cols]

                                if len(cols_text) > 1:
                                    # CGPA Check
                                    if 'CGPA' in cols_text[0].upper() or 'CUR. CGPA' in cols_text[0].upper():
                                        df.at[index, 'Cur. CGPA'] = cols_text[-1]
                                        data_found = True

                                    # SGPA Check
                                    if 'SGPA' in cols_text[0].upper():
                                        vals = cols_text[1:]
                                        # CGPA agar last value ho
                                        if 'CGPA' in table_text:
                                            df.at[index, 'Cur. CGPA'] = vals[-1]
                                            sgpa_vals = vals[:-1]
                                        else:
                                            sgpa_vals = vals

                                        for i, val in enumerate(sgpa_vals):
                                            col_name = f'Semester {i+1} SGPA'
                                            if col_name in df.columns:
                                                df.at[index, col_name] = val
                                        
                                        data_found = True
                                        break
                            if data_found:
                                break

                except Exception as e:
                    st.warning(f"Registration No {reg_no} ke liye data extract nahi ho paya: {e}")

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