import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import io

# ==========================================
# ✨ PAGE CONFIG (Text Hide karne aur Title set karne ke liye)
# ==========================================
# Yeh line sabse pehle honi chahiye
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

/* ✨ NAYA: Boxes par permanently border lagana ✨ */
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

/* ✨ CSS hack: 200MB limit text ko hide karne ke liye ✨ */
.css-11r2pvi {
    display: none !important;
}
.st-emotion-cache-9ycgxx {
    display: none !important;
}
/* ✨ NAYA: Download Button ko Colorful (Gradient) banana ✨ */
div.stDownloadButton > button {
    background: linear-gradient(135deg, #ff007f, #ff5e62) !important; /* Pink-Red Gradient */
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
/* ✨ 1. '200MB per file' ko kisi bhi haal me hatane ke liye ✨ */
.stFileUploader small {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}

/* ✨ 2. Upload ke baad aane wala '+' icon hatane ke liye ✨ */
.stFileUploader div[data-testid="stFileUploadDropzone"] > div > div:last-child {
    display: none !important;
}

.stFileUploader div[data-testid="stFileUploadDropzone"] svg[aria-hidden="true"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🎨 WEB APP UI (LOGO KE SATH)
# ==========================================

# Ek row banayenge jisme logo aur title ek sath aayen
col1, col2 = st.columns([1, 5]) # Logo chota (1), Title bada (5)

with col1:
    # Logo ko display karna (ensure file name 'logo.jpg' ho)
    try:
        st.image("logo.jpg", width=80) 
    except:
        st.write("🎓") # Agar logo load nahi hua toh topi dikhegi

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
        # ✨ Cloud Server (Streamlit Cloud) ke liye Headless Chrome Setup ✨
        chrome_options = Options()
        chrome_options.add_argument("--headless")              # Server par bina window ke chalanay ke liye
        chrome_options.add_argument("--no-sandbox")            # Linux server security bypass
        chrome_options.add_argument("--disable-dev-shm-usage")  # Memory limit error se bachne ke liye
        chrome_options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=chrome_options)
        
        total_students = len(df)
        
        # ✨ NAYA LOGIC: Progress Bar Jisme (1/5) format me text aayega
        progress_text = f"⏳ Processing started... (0/{total_students})"
        progress_bar = st.progress(0, text=progress_text)
        
        for index, row in df.iterrows():
            reg_no = str(row['Registration No.']).strip()
            
            if reg_no != 'nan' and reg_no != '':
                try:
                    while len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                        driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                    driver.get(url)
                    wait = WebDriverWait(driver, 15)
                    
                    input_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter Reg. No.']")))
                    time.sleep(8) 
                    
                    input_box = driver.find_element(By.XPATH, "//input[@placeholder='Enter Reg. No.']")
                    input_box.clear()
                    input_box.send_keys(reg_no)
                    time.sleep(1)
                    
                    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Show Result')]")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", submit_btn)
                    
                    time.sleep(6) 
                    
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                        time.sleep(3) 
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2) 
                    
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    data_found = False
                    
                    for table in soup.find_all('table'):
                        table_text = table.get_text()
                        if 'Cur. CGPA' in table_text and 'SGPA' in table_text:
                            rows = table.find_all('tr')
                            for r in rows:
                                cols = r.find_all(['td', 'th'])
                                cols_text = [c.get_text(strip=True) for c in cols]
                                
                                if len(cols_text) > 2 and 'SGPA' in cols_text[0].upper():
                                    vals = cols_text[1:] 
                                    
                                    if len(vals) > 0:
                                        try:
                                            df.at[index, 'Cur. CGPA'] = float(vals[-1])
                                        except:
                                            df.at[index, 'Cur. CGPA'] = vals[-1]
                                    
                                    sgpa_vals = vals[:-1]
                                    for i, val in enumerate(sgpa_vals):
                                        col_name = f'Semester {i+1} SGPA'
                                        if col_name in df.columns:
                                            try:
                                                df.at[index, col_name] = float(val)
                                            except:
                                                df.at[index, col_name] = val
                                            
                                    data_found = True
                                    break
                            if data_found:
                                break
                                
                except Exception as e:
                    pass # Screen saaf rakhne ke liye saare error messages hide kar diye gaye hain
                    
            # Har student ke baad text update hoga jaise (1/5), (2/5)
            progress_bar.progress((index + 1) / total_students, text=f"⏳ Extracting Data... ({index + 1}/{total_students})")
            
        driver.quit()
        
        # ✨ NAYA LOGIC: Attractive Colorful Table
        st.markdown("### 📊 Final Result Data")
        
        # Pandas DataFrame ko blue theme color aur 2 digit decimal format dena
        # .format(precision=2) sirf numbers ko 2 digit karega, '-' ko waisa hi chhod dega
        styled_df = df.style.format(precision=2).set_properties(**{
        'background-color': '#eef2ff',
        'color': '#1e3a8a',
        'border-color': 'white',
        'font-weight': '500',
        'text-align': 'center'  # ✨ NAYA: Data ko center karne ke liye
    })
    
    # ✨ NAYA: Table ki headings (Columns) ko center karne ke liye
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
        