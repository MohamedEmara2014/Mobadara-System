import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة للعرض العريض (مناسب للجداول)
st.set_page_config(page_title="مصفوفة المبادرة - تحديث الأقسام", layout="wide")

# 2. الروابط المحدثة
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzM8gX9uZz9CXTi1zsBH1qO3-4vAfnn8wRhv8wzqg7RXlv2roPYpOupEDOW3oCzVcI/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")
st.info("اختر قسمك، عدل البيانات في الجدول، ثم اضغط 'اعتماد التحديثات' لإرسال الكل دفعة واحدة.")

try:
    # جلب البيانات الحالية
    df = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    # --- الخطوة 1: اختيار القسم ---
    # نفترض أن العمود الأول هو أسماء المشاريع والبقية هي الأقسام
    project_col = df.columns[0]
    sections = df.columns[1:]
    
    selected_section = st.selectbox("🎯 اختر القسم الخاص بك:", sections)
    col_idx = list(df.columns).index(selected_section) + 1

    # --- الخطوة 2: محرر البيانات التفاعلي ---
    st.subheader(f"📊 جدول تحديثات قسم: {selected_section}")
    
    # تجهيز جدول فرعي للعرض والتعديل فقط
    # يحتوي على اسم المشروع والعمود الخاص بالقسم المختار فقط
    display_df = df[[project_col, selected_section]].copy()
    
    edited_df = st.data_editor(
        display_df,
        column_config={
            project_col: st.column_config.TextColumn("اسم المشروع", disabled=True),
            selected_section: st.column_config.TextColumn(f"الموقف الحالي لـ {selected_section}", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

    # --- الخطوة 3: زر الإرسال الجماعي ---
    st.divider()
    if st.button(f"🚀 اعتماد وإرسال كافة تحديثات {selected_section}", type="primary"):
        updates_to_send = []
        
        # مقارنة الجدول المعدل بالقديم لاستخراج التغييرات فقط
        for i in range(len(df)):
            new_val = edited_df.iloc[i, 1]
            old_val = df.iloc[i, col_idx - 1]
            
            if str(new_val).strip() != str(old_val).strip():
                updates_to_send.append({
                    "row": i + 2, # +2 لتعويض سطر العناوين وبدء العد من 1 في جوجل
                    "col": col_idx,
                    "val": str(new_val)
                })
        
        if updates_to_send:
            with st.spinner(f"جاري مزامنة {len(updates_to_send)} تحديثاً مع ملف المدير العام..."):
                # إرسال التحديثات كـ JSON لتوافق الكود الجديد في Apps Script
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم تحديث {len(updates_to_send)} خلية بنجاح في ملف المدير العام!")
                    st.balloons()
                else:
                    st.error("❌ حدث خطأ في السيرفر. تأكد من إعدادات الـ Deployment.")
        else:
            st.warning("⚠️ لم تقم بإجراء أي تغييرات في الجدول لإرسالها.")

except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
