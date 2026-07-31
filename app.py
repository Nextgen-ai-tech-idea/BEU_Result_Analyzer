import streamlit as st
import pandas as pd
import time
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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

h1 {
    color: #1e3a8a !important; 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-top: 0px !important;
}

.stTextInput label p, .stFileUploader label p {
    font-size: 20px !important;
    font-weight: 800 !important;
    color: #1e3a8a !important;
}

.stTextInput > div > div > input {
    border: 2px solid #1e3a8a !important;
    border-radius: 8px !important;
}

.stFileUploader > div > div {
    border: 2px dashed #1e3a8a !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
}

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

.stFileUploader small {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Helper function to initialize Driver (Local + Cloud Supported)
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    try:
        # Streamlit Cloud Environment
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        # Local Environment
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    return driver

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
        progress_bar = st.progress(0, text=f"⏳ Starting Browser... (0/{total_students})")
        
        driver = get_driver()

        try:
            for index, row in df.iterrows():
                reg_no = str(row['Registration No.']).strip()
                if reg_no.endswith('.0'):
                    reg_no = reg_no[:-2]

                if reg_no != 'nan' and reg_no != '':
                    try:
                        driver.get(url)
                        time.sleep(2)  # Page loading time

                        # Find Input Field & Fill Reg No
                        input_box = None
                        try:
                            input_box = driver.find_element(By.XPATH, "//input[@type='text' or @type='number' or contains(@placeholder, 'Reg') or contains(@id, 'reg') or contains(@name, 'reg')]")
                        except:
                            inputs = driver.find_elements(By.TAG_NAME, "input")
                            if inputs:
                                input_box = inputs[0]

                        if input_box:
                            input_box.clear()
                            input_box.send_keys(reg_no)
                            time.sleep(0.5)

                            # Click Show Result / Submit Button
                            btn = None
                            try:
                                btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Show') or contains(text(), 'Result') or contains(text(), 'Submit') or contains(text(), 'Search')]")
                            except:
                                buttons = driver.find_elements(By.TAG_NAME, "button")
                                if buttons:
                                    btn = buttons[0]

                            if btn:
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(3)  # Wait for Result to render

                            # Parse HTML with BeautifulSoup
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            data_found = False

                            for table in soup.find_all('table'):
                                table_text = table.get_text()
                                if 'SGPA' in table_text or 'CGPA' in table_text:
                                    rows = table.find_all('tr')
                                    for r in rows:
                                        cols = r.find_all(['td', 'th'])
                                        cols_text = [c.get_text(strip=True) for c in cols]

                                        if len(cols_text) > 1:
                                            # SGPA Parsing
                                            if 'SGPA' in cols_text[0].upper():
                                                vals = cols_text[1:]
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
                        pass

                progress_bar.progress((index + 1) / total_students, text=f"⏳ Extracting Data... ({index + 1}/{total_students})")

        finally:
            driver.quit()

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