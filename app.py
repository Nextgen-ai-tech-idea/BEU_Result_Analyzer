import streamlit as st
import pandas as pd
import time
import io
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# ==========================================
# ✨ PAGE CONFIG & CSS
# ==========================================
st.set_page_config(page_title="BEU Result Analyzer", page_icon="🎓")
st.markdown("""
<style>
.stApp { background-color: #f8fafc; }
h1 { color: #1e3a8a !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin-top: 0px !important; }
.stTextInput label p, .stFileUploader label p { font-size: 20px !important; font-weight: 800 !important; color: #1e3a8a !important; }
.stTextInput > div > div > input { border: 2px solid #1e3a8a !important; border-radius: 8px !important; }
.stFileUploader > div > div { border: 2px dashed #1e3a8a !important; border-radius: 8px !important; background-color: #ffffff !important; }
div.stButton > button:first-child { background-color: #2563eb !important; color: white !important; font-weight: 600 !important; border-radius: 8px !important; border: none !important; padding: 10px 24px !important; font-size: 18px !important; width: 100%; transition: 0.3s; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3); }
div.stDownloadButton > button { background: linear-gradient(135deg, #ff007f, #ff5e62) !important; color: white !important; font-weight: 800 !important; border-radius: 8px !important; border: none !important; padding: 12px 28px !important; font-size: 18px !important; transition: 0.3s; box-shadow: 0 4px 10px rgba(255, 94, 98, 0.4); }
.stFileUploader small { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 🕵️ UNDETECTED CHROMEDRIVER
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--window-position=-2000,0")
    
    driver = uc.Chrome(options=options, version_main=150)
    return driver

# Helper function: Excel numbers float conversion
def safe_float(val):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return val

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
        progress_bar = st.progress(0, text="🛡️ Undetected Browser Starting...")
        
        driver = get_driver()
        try:
            for index, row in df.iterrows():
                reg_no = str(row['Registration No.']).strip()
                if reg_no.endswith('.0'): reg_no = reg_no[:-2]

                if reg_no != 'nan' and reg_no != '':
                    try:
                        # 🔴 SAFETY CHECK: Agar hum Result Search Page par nahi hain, toh button click karke ya Direct URL se wapas aayein
                        current_url = driver.current_url
                        
                        # Pehle Page Par Result Page Wala ← Back Click Karne Ki Koshish
                        back_clicked = False
                        try:
                            page_buttons = driver.find_elements(By.TAG_NAME, "button")
                            for pb in page_buttons:
                                if "back" in pb.text.lower():
                                    driver.execute_script("arguments[0].click();", pb)
                                    back_clicked = True
                                    break
                        except:
                            pass

                        # Agar back button nahi mila ya galat URL par chale gaye, toh Target URL Reload karke Safety Lock lagao
                        if not back_clicked or "google" in driver.current_url.lower() or url.split('?')[0] not in driver.current_url:
                            driver.get(url)

                        # 1️⃣ Cloudflare verification buffer wait
                        time.sleep(6) 

                        # 2️⃣ Search for Registration Input Box
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        input_box = None
                        for inp in inputs:
                            if inp.get_attribute('type') in ['text', 'number'] or 'reg' in (inp.get_attribute('placeholder') or '').lower():
                                input_box = inp
                                break
                        if not input_box and inputs: input_box = inputs[0]

                        # 3️⃣ Search for Show Result Button
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        btn = None
                        for b in buttons:
                            if any(word in b.text.lower() for word in ['show', 'result', 'submit', 'search']):
                                btn = b
                                break
                        if not btn and buttons: btn = buttons[0]

                        if input_box and btn:
                            input_box.clear()
                            time.sleep(0.4)
                            input_box.send_keys(reg_no)
                            time.sleep(0.4)

                            # Click Show Result
                            driver.execute_script("arguments[0].click();", btn)
                            
                            # 4️⃣ Result Render Wait (Max 3 attempts = 6s)
                            table_loaded = False
                            for attempt in range(3):
                                time.sleep(2)
                                soup = BeautifulSoup(driver.page_source, 'html.parser')
                                if 'SGPA' in soup.get_text() or 'CGPA' in soup.get_text():
                                    table_loaded = True
                                    break

                            # 5️⃣ Extract Data
                            if table_loaded:
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
                                                    df.at[index, 'Cur. CGPA'] = safe_float(vals[-1])
                                                    sgpa_vals = vals[:-1]
                                                else:
                                                    sgpa_vals = vals
                                                for i, val in enumerate(sgpa_vals):
                                                    col_name = f'Semester {i+1} SGPA'
                                                    if col_name in df.columns: 
                                                        df.at[index, col_name] = safe_float(val)
                                                data_found = True
                                                break
                                        if data_found: break

                    except Exception as e:
                        driver.get(url)

                progress_bar.progress((index + 1) / total_students, text=f"⏳ Extracting Data... ({index + 1}/{total_students})")

        finally:
            driver.quit()

        st.markdown("### 📊 Final Result Data")
        styled_df = df.style.format(precision=2).set_properties(**{'background-color': '#eef2ff', 'color': '#1e3a8a', 'border-color': 'white', 'text-align': 'center'})
        styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
        st.dataframe(styled_df, use_container_width=True)

        output = io.BytesIO()
        df.to_excel(output, index=False)
        st.download_button("📥 Download Filled Excel File", data=output.getvalue(), file_name="Final_Filled_" + uploaded_file.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")