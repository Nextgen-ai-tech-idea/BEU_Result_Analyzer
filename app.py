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
.stApp { background-color: #f8fafc; }
h1 { color: #1e3a8a !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin-top: 0px !important; }
.stTextInput label p, .stFileUploader label p { font-size: 20px !important; font-weight: 800 !important; color: #1e3a8a !important; }
.stTextInput > div > div > input { border: 2px solid #1e3a8a !important; border-radius: 8px !important; }
.stFileUploader > div > div { border: 2px dashed #1e3a8a !important; border-radius: 8px !important; background-color: #ffffff !important; }
div.stButton > button:first-child { background-color: #2563eb !important; color: white !important; font-weight: 600 !important; border-radius: 8px !important; padding: 10px 24px !important; font-size: 18px !important; width: 100%; }
div.stDownloadButton > button { background: linear-gradient(135deg, #ff007f, #ff5e62) !important; color: white !important; font-weight: 800 !important; border-radius: 8px !important; padding: 12px 28px !important; font-size: 18px !important; }
.stFileUploader small { display: none !important; }
</style>
""", unsafe_allow_html=True)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        st.warning(f"System Chromedriver failed, trying WebdriverManager... Error: {e}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
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
        progress_bar = st.progress(0, text="🛡️ Opening Browser & Waiting for Cloudflare...")
        
        try:
            driver = get_driver()
            st.info("✅ Browser started successfully!")
            
            driver.get(url)
            time.sleep(5) # Thoda wait karte hain page load hone ka
            
            # 📸 DEBUG: Yahan browser ki screen print karke dikhayenge
            st.markdown("### 📸 Live Screenshot (What the server sees):")
            st.image(driver.get_screenshot_as_png(), use_container_width=True)
            
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//input")))
                progress_bar.progress(0, text=f"✅ Verification Passed! Starting... (0/{total_students})")
            except Exception as e:
                st.error("⚠️ Timeout waiting for input box! Cloudflare blocked us or page is empty.")
                st.write(f"**Error Details:** {e}")

            for index, row in df.iterrows():
                reg_no = str(row['Registration No.']).strip()
                if reg_no.endswith('.0'): reg_no = reg_no[:-2]

                if reg_no != 'nan' and reg_no != '':
                    try:
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        input_box = None
                        for inp in inputs:
                            if inp.get_attribute('type') in ['text', 'number'] or 'reg' in (inp.get_attribute('placeholder') or '').lower():
                                input_box = inp
                                break
                        if not input_box and inputs: input_box = inputs[0]

                        if input_box:
                            input_box.clear()
                            time.sleep(0.5)
                            input_box.send_keys(reg_no)
                            time.sleep(0.5)

                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            btn = None
                            for b in buttons:
                                if any(word in b.text.lower() for word in ['show', 'result', 'submit', 'search']):
                                    btn = b
                                    break
                            if not btn and buttons: btn = buttons[0]

                            if btn:
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(4) 

                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            data_found = False

                            for table in soup.find_all('table'):
                                table_text = table.get_text()
                                if 'SGPA' in table_text or 'CGPA' in table_text:
                                    rows = table.find_all('tr')
                                    for r in rows:
                                        cols = r.find_all(['td', 'th'])
                                        cols_text = [c.get_text(strip=True) for c in cols]
                                        if len(cols_text) > 1 and 'SGPA' in cols_text[0].upper():
                                            vals = cols_text[1:]
                                            if 'CGPA' in table_text:
                                                df.at[index, 'Cur. CGPA'] = vals[-1]
                                                sgpa_vals = vals[:-1]
                                            else:
                                                sgpa_vals = vals
                                            for i, val in enumerate(sgpa_vals):
                                                col_name = f'Semester {i+1} SGPA'
                                                if col_name in df.columns: df.at[index, col_name] = val
                                            data_found = True
                                            break
                                    if data_found: break

                    except Exception as e:
                        st.error(f"Error on Reg No {reg_no}: {e}") # Ab error dikhega

                progress_bar.progress((index + 1) / total_students, text=f"⏳ Extracting... ({index + 1}/{total_students})")

        except Exception as e:
            st.error(f"❌ CRITICAL ERROR: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()

        st.markdown("### 📊 Final Result Data")
        styled_df = df.style.format(precision=2).set_properties(**{'background-color': '#eef2ff', 'color': '#1e3a8a', 'border-color': 'white', 'text-align': 'center'})
        styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
        st.dataframe(styled_df, use_container_width=True)

        output = io.BytesIO()
        df.to_excel(output, index=False)
        st.download_button("📥 Download Filled Excel File", data=output.getvalue(), file_name="Final_Filled_" + uploaded_file.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")