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
# Helper function to initialize Driver (Anti-Bot Bypass ke sath)
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 🛡️ NAYA: Cloudflare Anti-Bot Bypass Options
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    # Selenium ko detect hone se bachana
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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
        progress_bar = st.progress(0, text="🛡️ Opening Browser & Bypassing Cloudflare... (Please Wait)")
        
        driver = get_driver()

        try:
            # 🚨 URL ko sirf EK BAAR load karna hai loop se pehle
            driver.get(url)
            
            # Wait until Cloudflare verification passes and input box is visible (Max 20 seconds)
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input"))
                )
                progress_bar.progress(0, text=f"✅ Verification Passed! Starting extraction... (0/{total_students})")
            except:
                st.error("⚠️ Cloud Verification time-out ho gaya. Ho sakta hai server IP block ho. Kripya URL check karein.")

            for index, row in df.iterrows():
                reg_no = str(row['Registration No.']).strip()
                if reg_no.endswith('.0'):
                    reg_no = reg_no[:-2]

                if reg_no != 'nan' and reg_no != '':
                    try:
                        # Find Input Field dynamically
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        input_box = None
                        for inp in inputs:
                            if inp.get_attribute('type') in ['text', 'number'] or 'reg' in (inp.get_attribute('placeholder') or '').lower():
                                input_box = inp
                                break
                                
                        if not input_box and inputs:
                            input_box = inputs[0]

                        if input_box:
                            input_box.clear()
                            time.sleep(0.5)
                            input_box.send_keys(reg_no)
                            time.sleep(0.5)

                            # Find & Click Submit Button
                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            btn = None
                            for b in buttons:
                                if any(word in b.text.lower() for word in ['show', 'result', 'submit', 'search']):
                                    btn = b
                                    break
                            
                            if not btn and buttons:
                                btn = buttons[0]

                            if btn:
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(4)  # Wait for React to fetch and render the new table

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
                        pass # Ignore row error and continue

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