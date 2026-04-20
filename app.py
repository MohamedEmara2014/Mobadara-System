import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. إعدادات التليجرام ---
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

def send_telegram_msg(section_name, method="يدوي"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        text = (
            f"🏗️ **تنبيه تحديث جديد**\n\n"
            f"قام قسم: \n📍 *{section_name}*\n\n"
            f"باعتماد البيانات عبر (تحديث {method}) الآن. ✅"
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 2. إعدادات الواجهة ---
st.set_page_config(page_title="التقرير اليومي لمتابعة المبادرة", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwE9XcpdsumPSoGJ0G_apcTbnRLj1zLPPVR8MVZRGANBwVGYtn0vavLJTabfY_Fda0/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # 3. جلب البيانات الخام
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    # 4. اختيار القسم
    selected_section = st.selectbox("حدد القسم الخاص بك واضغط اعتماد وتصدير البيانات أخر الصفحة", sections)
    
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # جلب البيانات الحالية من الشيت
    project_names = df_raw.iloc[2:, 0].values.tolist()
    current_done_values = df_raw.iloc[2:, col_idx_done - 1].values.tolist()
    current_issues_values = df_raw.iloc[2:, col_idx_issues - 1].values.tolist()

    # الحالة الافتراضية للبيانات
    default_data = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": current_done_values,
        "المعوقات والمشاكل": current_issues_values
    })

    # --- ميزة رفع ملف إكسيل ---
    st.sidebar.header("📤 خيارات الرفع")
    uploaded_file = st.sidebar.file_uploader("ارفع ملف إكسيل لتحديث الجدول تلقائياً", type=["xlsx"])
    
    upload_method = "يدوي"
    if uploaded_file is not None:
        try:
            excel_data = pd.read_excel(uploaded_file, dtype=str).fillna("")
            # التأكد من مطابقة عدد المشاريع أو الأسماء (تبسيطاً سنأخذ أول عمودين بعد اسم المشروع)
            if len(excel_data) >= len(project_names):
                default_data["ما تم إنجازه"] = excel_data.iloc[:len(project_names), 1].values
                default_data["المعوقات والمشاكل"] = excel_data.iloc[:len(project_names), 2].values
                st.sidebar.success("✅ تم استيراد البيانات من الملف بنجاح!")
                upload_method = "ملف إكسيل"
            else:
                st.sidebar.error("❌ عدد الصفوف في الملف أقل من المطلوب.")
        except Exception as ex:
            st.sidebar.error(f"خطأ في قراءة الملف: {ex}")

    # 5. عرض محرر البيانات (سيظهر البيانات المرفوعة أو القديمة)
    edited_df = st.data_editor(
        default_data,
        key=f"editor_{selected_section}",
        column_config={
            "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
            "ما تم إنجازه": st.column_config.TextColumn("✅ ما تم إنجازه اليوم", width="large"),
            "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات والمشاكل", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=600 
    )

    st.divider()

    # 6. زر الاعتماد
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        for i in range(len(edited_df)):
            val_done = str(edited_df.iloc[i, 1]).strip()
            val_issues = str(edited_df.iloc[i, 2]).strip()
            target_row = i + 4
            updates_to_send.append({"row": target_row, "col": col_idx_done, "val": val_done})
            updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": val_issues})
        
        if updates_to_send:
            with st.spinner("جاري المزامنة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    send_telegram_msg(selected_section, upload_method)
                    st.success("✅ تم حفظ البيانات بنجاح!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال بخادم جوجل.")

except Exception as e:
    st.error(f"خطأ في النظام: {e}")
