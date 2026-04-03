import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة (العرض العريض لتناسب الـ 26 مشروعاً)
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط الخاصة بك (تم تحديث الرابط الجديد هنا)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzGx48qSN8zXAgoCBqfg6U3pgnTkS70-4v75iG-nVWNOtckDsLZtRXxeBK0tAlWS6Ip/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات الأساسية (أسماء المشاريع والأقسام)
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    project_col = df_raw.columns[0]
    sections = df_raw.columns[1:]
    
    # التوجيه المحدث لرؤساء الأقسام
    instruction = "🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:"
    selected_section = st.selectbox(instruction, sections)
    col_idx = list(df_raw.columns).index(selected_section) + 1

    st.markdown(f"### 📊 جدول تحديثات قسم: {selected_section}")

    # --- التصفير التلقائي للجدول ---
    # ننشئ جدولاً فارغاً تماماً في كل مرة يتم فيها فتح الصفحة أو تغيير القسم
    empty_display_df = pd.DataFrame({
        project_col: df_raw[project_col],
        selected_section: "" 
    })

    # عرض محرر البيانات (Data Editor)
    # نستخدم selected_section كـ Key لضمان تصفير الخانات عند التبديل بين الأقسام
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
    
    # زر الاعتماد والتصدير النهائي
    if st.button(f"🚀 اعتماد وتصدير التقرير اليومي لـ {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        # تجميع البيانات: نرسل row = i + 3 لضمان التسكين في الصف الثالث وما بعده
        # الصف 1: العناوين | الصف 2: التاريخ التلقائي | الصف 3: أول مشروع
        for i in range(len(edited_df)):
            val = edited_df.iloc[i, 1]
            updates_to_send.append({
                "row": i + 3, 
                "col": col_idx,
                "val": str(val) if val else "" 
            })
        
        if updates_to_send:
            with st.spinner("جاري مسح الموقف القديم وتسجيل التاريخ والبيانات الجديدة..."):
                # إرسال التحديثات للجسر البرمجي
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم تحديث قسم {selected_section} وتسجيل وقت التحديث في الشيت المجمع!")
                    st.balloons()
                else:
                    st.error("❌ فشل في الاتصال. يرجى التأكد من أن الرابط الجديد مفعل لـ (Anyone).")
        else:
            st.warning("⚠️ الجدول فارغ، يرجى كتابة التحديثات قبل الإرسال.")

except Exception as e:
    st.error(f"حدث خطأ فني: {e}")
