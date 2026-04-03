import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة (العرض الواسع لتسهيل القراءة والملء)
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط الخاصة بمشروعك (يرجى التأكد من أن رابط الـ Web App هو الأحدث ومفعل للجميع)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzGx48qSN8zXAgoCBqfg6U3pgnTkS70-4v75iG-nVWNOtckDsLZtRXxeBK0tAlWS6Ip/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

# عنوان التطبيق والتعليمات الجديدة
st.title("📂 التقرير اليومي لمتابعة المبادرة")
instruction_text = "🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:"

try:
    # جلب البيانات من جوجل شيتس (أسماء المشاريع والأقسام)
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    project_col = df_raw.columns[0]
    sections = df_raw.columns[1:]
    
    # اختيار القسم من القائمة المنسدلة
    selected_section = st.selectbox(instruction_text, sections)
    col_idx = list(df_raw.columns).index(selected_section) + 1

    st.markdown(f"### 📊 جدول تحديثات قسم: {selected_section}")

    # --- التصفير التلقائي (نموذج إدخال نظيف) ---
    # ننشئ جدولاً فارغاً تماماً في كل مرة يتم فيها اختيار قسم جديد
    empty_display_df = pd.DataFrame({
        project_col: df_raw[project_col],
        selected_section: "" 
    })

    # محرر البيانات التفاعلي
    # تم استخدام مفتاح (key) ديناميكي لضمان تصفير الخانات عند تبديل الأقسام
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
    
    # زر الاعتماد والتصدير النهائي للمدير العام
    if st.button(f"🚀 اعتماد وتصدير التقرير اليومي لـ {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        # --- ضبط إحداثيات الصفوف (علاج مشكلة الترحيل) ---
        # i + 2 تعني:
        # إذا كان i = 0 (أول مشروع)، سيتم الكتابة في الصف رقم 2 في جوجل شيتس
        for i in range(len(edited_df)):
            val = edited_df.iloc[i, 1]
            updates_to_send.append({
                "row": i + 2, 
                "col": col_idx,
                "val": str(val) if val else "" 
            })
        
        if updates_to_send:
            with st.spinner(f"جاري مسح الموقف القديم واعتماد تحديثات {selected_section}..."):
                # إرسال البيانات المجمعة (Batch Update) إلى Apps Script
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم تحديث بيانات قسم {selected_section} بنجاح في ملف الإدارة!")
                    st.balloons()
                else:
                    st.error("❌ فشل الاتصال بالسيرفر. يرجى التأكد من صلاحيات رابط الـ Web App.")
        else:
            st.warning("⚠️ الجدول فارغ، يرجى إدخال البيانات قبل الإرسال.")

except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
