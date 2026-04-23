import streamlit as st
import pandas as pd
import requests
import json
import time
import io
from datetime import datetime

# --- 1. إعدادات التليجرام (يفضل وضعها في Secrets للأمان) ---
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

def send_telegram_msg(section_name, method="يدوي"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        curr_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = (
            f"🏗️ **تنبيه تحديث جديد**\n\n"
            f"📍 القسم: *{section_name}*\n"
            f"🛠️ الوسيلة: *{method}*\n"
            f"⏰ الوقت: *{curr_time}*\n\n"
            f"✅ تم الاعتماد وحفظ البيانات بنجاح."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 2. إعدادات واجهة التطبيق ---
st.set_page_config(page_title="التقرير اليومي لمتابعة المبادرة", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyvNeUALnqFg-vv8LkLhb1ND-OYl-2xdMCY95VFevp4130MSHMlP3781h1Q-pOy0nei/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # 3. جلب البيانات (استخدام كاش بسيط لتحسين الأداء)
    @st.cache_data(ttl=60)
    def load_data():
        return pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    df_raw = load_data()
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    # 4. اختيار القسم
    selected_section = st.selectbox("حدد القسم الخاص بك:", sections)
    
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # --- عرض التاريخ من الصف الثاني ---
    # ملاحظة: iloc[0] في باندا تعني الصف رقم 2 في الإكسيل (بعد العناوين)
    last_update_val = df_raw.iloc[0, col_idx_done - 1] 
    if last_update_val and "تحديث" in str(last_update_val):
        st.info(f"🕒 {last_update_val}")
    else:
        st.warning("⚠️ لا يوجد تاريخ تحديث مسجل لهذا القسم حالياً.")

    # 5. تجهيز الجدول
    project_names = df_raw.iloc[2:, 0].values.tolist()
    display_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": df_raw.iloc[2:, col_idx_done - 1].values.tolist(),
        "المعوقات والمشاكل": df_raw.iloc[2:, col_idx_issues - 1].values.tolist()
    })

    # --- 6. الجانب الجانبي (تحميل ورفع الملفات) ---
    with st.sidebar:
        st.header("📤 خيارات الإكسيل")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            display_df.to_excel(writer, index=False)
        st.download_button("⬇️ تحميل النموذج الحالي", buffer.getvalue(), f"نموذج_{selected_section}.xlsx")
        
        st.divider()
        uploaded_file = st.file_uploader("📤 رفع ملف بعد التعديل", type=["xlsx"])
        
    update_method = "يدوي (أونلاين)"
    if uploaded_file:
        excel_data = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
        if len(excel_data) >= len(project_names):
            display_df["ما تم إنجازه"] = excel_data.iloc[:len(project_names), 1].values
            display_df["المعوقات والمشاكل"] = excel_data.iloc[:len(project_names), 2].values
            update_method = "ملف إكسيل"
            st.sidebar.success("✅ تم استيراد الملف للجدول")

    # 7. عرض محرر البيانات
    edited_df = st.data_editor(
        display_df,
        column_config={"اسم المشروع": st.column_config.TextColumn(disabled=True)},
        use_container_width=True, hide_index=True, height=550
    )

    # 8. زر الاعتماد والإرسال (POST)
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        for i, row in edited_df.iterrows():
            target_row = i + 4 # الحفاظ على مسافة العناوين والتاريخ
            updates_to_send.append({"row": target_row, "col": col_idx_done, "val": str(row[1])})
            updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": str(row[2])})
        
        if updates_to_send:
            with st.spinner("جاري الحفظ وتسجيل الوقت..."):
                payload = json.dumps({"updates": updates_to_send})
                response = requests.post(SCRIPT_URL, data=payload, timeout=60)
                
                if response.status_code == 200 and "Success" in response.text:
                    send_telegram_msg(selected_section, update_method)
                    st.success("✅ تم الحفظ وتحديث التاريخ بنجاح!")
                    st.balloons()
                    st.cache_data.clear() # لمسح الكاش ورؤية التاريخ الجديد
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ فشل الاتصال: {response.status_code}")
        else:
            st.warning("⚠️ لا توجد بيانات لإرسالها.")

except Exception as e:
    st.error(f"⚠️ حدث خطأ في النظام: {e}")
