import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط المحدثة
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzM8gX9uZz9CXTi1zsBH1qO3-4vAfnn8wRhv8wzqg7RXlv2roPYpOupEDOW3oCzVcI/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات الخام لمعرفة أسماء المشاريع والأقسام
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    project_col = df_raw.columns[0]
    sections = df_raw.columns[1:]
    
    # التوجيه للمستخدم
    instruction = "🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:"
    selected_section = st.selectbox(instruction, sections)
    col_idx = list(df_raw.columns).index(selected_section) + 1

    st.markdown(f"### 📊 جدول تحديثات: {selected_section}")

    # --- التصفير الأوتوماتيكي ---
    # ننشئ جدولاً فارغاً تماماً في كل مرة يتم فيها اختيار القسم
    empty_display_df = pd.DataFrame({
        project_col: df_raw[project_col],
        selected_section: "" 
    })

    # عرض الجدول الفارغ (نستخدم selected_section كـ Key لضمان التصفير عند التبديل)
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
        
        # تجميع البيانات: نرسل row = i + 3 لأن:
        # الصف 1 هو العناوين
        # الصف 2 هو تاريخ التحديث (الذي سيملؤه السكريبت)
        # الصف 3 هو أول مشروع
        for i in range(len(edited_df)):
            val = edited_df.iloc[i, 1]
            updates_to_send.append({
                "row": i + 3, 
                "col": col_idx,
                "val": str(val) if val else "" 
            })
        
        if updates_to_send:
            with st.spinner("جاري مسح الموقف القديم وتسجيل التاريخ والبيانات الجديدة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم تحديث قسم {selected_section} وتسجيل وقت التحديث بنجاح!")
                    st.balloons()
                else:
                    st.error("❌ فشل الاتصال. تأكد من أن الرابط مفعل للجميع (Anyone).")
        else:
            st.warning("⚠️ لا توجد بيانات جديدة لإرسالها.")

except Exception as e:
    st.error(f"خطأ تقني: {e}")
