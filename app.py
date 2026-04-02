import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. وظائف قاعدة البيانات (Database Logic) ---
def init_db():
    conn = sqlite3.connect('mobadara_data.db')
    c = conn.cursor()
    # إنشاء جدول الأرشيف إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS archive 
                 (report_date TEXT, department TEXT, project_name TEXT, achievement TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(date, dept, project, task):
    conn = sqlite3.connect('mobadara_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO archive VALUES (?, ?, ?, ?)", (date, dept, project, task))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('mobadara_data.db')
    df = pd.read_sql_query("SELECT * FROM archive", conn)
    conn.close()
    return df

# --- 2. إعداد واجهة البرنامج ---
st.set_page_config(page_title="نظام متابعة المبادرة - SQLite", layout="wide")
init_db() # تشغيل قاعدة البيانات عند بدء التطبيق

st.title("🏗️ نظام المتابعة الرقمي (نسخة قاعدة البيانات المحلية)")

projects_list = [f"مشروع رقم {i}" for i in range(1, 27)]
tabs = st.tabs(["📝 إدخال البيانات", "📊 لوحة تحكم المدير"])

# --- التبويب الأول: إدخال البيانات (للموبايل) ---
with tabs[0]:
    st.header("تسجيل الموقف اليومي")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            dept = st.selectbox("القسم", ["قسم التنفيذ", "قسم التصميم", "المكتب الفني"])
            project = st.selectbox("المشروع", projects_list)
        with col2:
            report_date = st.date_input("التاريخ", datetime.now())
            achievement = st.text_area("ما تم إنجازه")
        
        if st.form_submit_button("حفظ البيانات"):
            if achievement.strip() == "":
                st.warning("الرجاء كتابة الإنجاز")
            else:
                save_to_db(str(report_date), dept, project, achievement)
                st.success(f"✅ تم حفظ بيانات {project} في قاعدة البيانات المحلية")

# --- التبويب الثاني: لوحة تحكم المدير ---
with tabs[1]:
    st.header("استعراض الأرشيف العام")
    df = load_data()
    
    if not df.empty:
        # خيارات التصفية (Filtering)
        filter_date = st.date_input("فلترة بالتاريخ", datetime.now())
        filtered_df = df[df['report_date'] == str(filter_date)]
        
        if filtered_df.empty:
            st.info("لا توجد بيانات لهذا التاريخ.")
        else:
            st.dataframe(filtered_df, use_container_width=True)
            
            # تصدير البيانات لملف Excel (CSV)
            csv = filtered_df.to_csv(index=False).encode('utf_8_sig')
            st.download_button("📥 تحميل التقرير الحالي (Excel)", csv, f"Report_{filter_date}.csv", "text/csv")
    else:
        st.info("قاعدة البيانات فارغة حالياً. ابدأ بإدخال البيانات أولاً.")