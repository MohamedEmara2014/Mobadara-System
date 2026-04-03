import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط الأساسية
# تأكد أن رابط الـ Apps Script هو النسخة التي تقوم بمسح العمود (ClearContent)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzM8gX9uZz9CXTi1zsBH1qO3-4vAfnn8wRhv8wzqg7RXlv2roPYpOupEDOW3oCzVcI/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب أسماء المشاريع والأقسام فقط من الشيت الأصلي
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    project_col = df_raw.columns[0]
    sections = df_raw.columns[1:]
    
    # التوجيه الجديد كما طلبت
    instruction = "🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:"
    selected_section = st.selectbox(instruction, sections)
    col_idx = list(df_raw.columns).index(selected_section) + 1

    st.markdown(f"### 📊 جدول تحديثات: {selected_section}")

    # --- التصفير الأوتوماتيكي ---
    # ننشئ جدول جديد يحتوي على أسماء المشاريع ولكن بخانات فارغة تماماً للقسم المختار
    empty_display_df = pd.DataFrame({
        project_col: df_raw[project_col],
        selected_section: "" # جعل جميع الخانات خالية أوتوماتيكياً
    })

    # عرض الجدول الفارغ للملء
    # ملاحظة: استخدمنا selected_section كـ Key لضمان إعادة ضبط الجدول عند تغيير القسم
    edited_df = st.data_editor(
        empty_display_df,
        key=f"editor_{selected_section}", 
        column_config={
            project_col: st.column_config.TextColumn("اسم المشروع", disabled=True),
            selected_section: st.column_config.TextColumn(f"الموقف التنفيذي الجديد - {selected_section}", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

    st.divider()
    
    # زر الاعتماد والتصدير
    if st.button(f"🚀 اعتماد وتصدير التقرير اليومي لـ {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        # تجميع البيانات المدخلة (حتى لو كانت فارغة ستقوم بمسح القديم في الشيت)
        for i in range(len(edited_df)):
            val = edited_df.iloc[i, 1]
            updates_to_send.append({
                "row": i + 2,
                "col": col_idx,
                "val": str(val) if val else "" 
            })
        
        if updates_to_send:
            with st.spinner("جاري مسح الموقف القديم واعتماد التقرير الجديد..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم تحديث قسم {selected_section} بنجاح في ملف الإدارة!")
                    st.balloons()
                else:
                    st.error("❌ فشل في الاتصال. يرجى التأكد من أن رابط الـ Web App مفعل لـ Anyone.")
        else:
            st.warning("⚠️ الجدول فارغ تماماً.")

except Exception as e:
    st.error(f"خطأ تقني: {e}")
