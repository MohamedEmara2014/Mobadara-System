import streamlit as st
import pandas as pd
import requests
import json
import time
import io
from datetime import datetime

# --- 1. الإعدادات الأمنية والروابط ---
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

# الروابط المحدثة (تأكد من نشر السكريبت في جوجل كـ Anyone)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyvNeUALnqFg-vv8LkLhb1ND-OYl-2xdMCY95VFevp4130MSHMlP3781h1Q-pOy0nei/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

# --- 2. وظائف النظام ---

def send_telegram_msg(section_name, method="يدوي"):
    """إرسال إشعار تليجرام عند الاعتماد"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = (
            f"🏗️ **تنبيه تحديث جديد**\n\n"
            f"📍 القسم: *{section_name}*\n"
            f"🛠️ الوسيلة: *{method}*\n"
            f"⏰ الوقت: *{now}*\n\n"
            f"✅ تم تحديث قاعدة البيانات بنجاح."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 3. واجهة التطبيق الرئيسية ---
st.set_page_config(page_title="نظام متابعة المبادرة", layout="wide")

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات مع كاش لمدة 30 ثانية
    @st.cache_data(ttl=30)
    def load_data():
        return pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    df_raw = load_data()
    
    # استخراج أسماء الأقسام من الصف الأول
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    selected_section = st.selectbox("حدد القسم الخاص بك للمراجعة أو التعديل:", sections)
    
    if selected_section:
        # تحديد إحداثيات القسم
        col_idx_done = list(df_raw.columns).index(selected_section) + 1
        col_idx_issues = col_idx_done + 1 

        # --- عرض تاريخ آخر تحديث من الصف الثاني في الشيت ---
        try:
            last_update_info = df_raw.iloc[0, col_idx_done - 1]
            if last_update_info and "تحديث" in str(last_update_info):
                st.info(f"🕒 {last_update_info}")
        except:
            pass

        # تجهيز البيانات (المشاريع تبدأ من الصف الرابع في الشيت = iloc[2:] في باندا)
        project_names = df_raw.iloc[2:, 0].values.tolist()
        current_done = df_raw.iloc[2:, col_idx_done - 1].values.tolist()
        current_issues = df_raw.iloc[2:, col_idx_issues - 1].values.tolist()

        display_df = pd.DataFrame({
            "اسم المشروع": project_names,
            "ما تم إنجازه": current_done,
            "المعوقات والمشاكل": current_issues
        })

        # --- 4. الشريط الجانبي لإدارة الملفات ---
        with st.sidebar:
            st.header("📤 خيارات الإكسيل")
            # زر تحميل النموذج
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button("⬇️ تحميل التقرير الحالي", buffer.getvalue(), f"تقرير_{selected_section}.xlsx")
            
            st.divider()
            
            # رفع ملف معدل
            update_method = "يدوي (أونلاين)"
            uploaded_file = st.file_uploader("رفع ملف إكسيل مكتمل", type=["xlsx"])
            if uploaded_file:
                try:
                    excel_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                    if excel_df.shape[1] >= 3:
                        display_df["ما تم إنجازه"] = excel_df.iloc[:len(project_names), 1].values
                        display_df["المعوقات والمشاكل"] = excel_df.iloc[:len(project_names), 2].values
                        update_method = "ملف إكسيل"
                        st.sidebar.success("✅ تم تحديث البيانات من الملف")
                    else:
                        st.sidebar.error("❌ الملف المرفوع لا يحتوي على الأعمدة الكافية.")
                except Exception as e:
                    st.sidebar.error(f"⚠️ خطأ في القراءة: {e}")

        # --- 5. محرر البيانات التفاعلي ---
        edited_df = st.data_editor(
            display_df,
            column_config={
                "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع
