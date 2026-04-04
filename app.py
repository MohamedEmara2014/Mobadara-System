import streamlit as st
import pandas as pd
import requests
import json
import time

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط الخاصة بك
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwKryaebBnTZTOp1NIul4VS1SSaslq5TH_jDDEfCq77Ef1NZ21F0IDWYrt5NYJkgDwg/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات من جوجل شيتس
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    
    # استخراج أسماء الأقسام (بافتراض أن كل قسم له عمودين متتاليين في الشيت)
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2)]
    
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك ليظهر جدول الإدخال:", sections)
    
    # تحديد أرقام الأعمدة في الشيت (العمود المختار هو الإنجاز، والذى يليه هو المعوقات)
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # عرض تاريخ آخر تحديث من الشيت (موجود في الصف الثاني بالشيت)
    last_update_val = df_raw.iloc[0, col_idx_done - 1]
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")
    else:
        st.warning("⚠️ لم يتم تسجيل تحديثات لهذا القسم اليوم بعد.")

    st.markdown(f"### 📝 جدول إدخال بيانات: {selected_section}")
    st.info("قم بملء خانة الإنجاز وخانة المعوقات لكل مشروع في الجدول أدناه:")

    # تحضير أسماء المشاريع (تبدأ من الصف الرابع في الشيت)
    project_names = df_raw.iloc[1:, 0] 

    # --- بناء هيكل الجدول بـ 3 أعمدة متجاورة ---
    input_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": "",
        "المعوقات والمشاكل": ""
    })

    # عرض محرر البيانات (الجدول التفاعلي)
    edited_df = st.data_editor(
        input_df,
        key=f"editor_{selected_section}",
        column_config={
            "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
            "ما تم إنجازه": st.column_config.TextColumn("✅ ما تم إنجازه اليوم", width="large", placeholder="اكتب الموقف التنفيذي..."),
            "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات والمشاكل", width="large", placeholder="اكتب المعوقات إن وجدت...")
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

    st.divider()

    # زر الاعتماد والتصدير
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section} بالكامل", type="primary", use_container_width=True):
        updates_to_send = []
        
        # تجميع البيانات من العمودين المتجاورين في الجدول
        for i in range(len(edited_df)):
            val_done = edited_df.iloc[i, 1]
            val_issues = edited_df.iloc[i, 2]
            
            # i + 4 لأننا نبدأ الكتابة من الصف الرابع في الشيت
            updates_to_send.append({"row": i + 4, "col": col_idx_done, "val": str(val_done) if val_done else ""})
            updates_to_send.append({"row": i + 4, "col": col_idx_issues, "val": str(val_issues) if val_issues else ""})
        
        if updates_to_send:
            with st.spinner("جاري مزامنة البيانات مع سجل الإدارة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم اعتماد تقرير {selected_section} (الإنجاز والمعوقات) بنجاح!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال. يرجى التأكد من إعدادات الـ Web App في جوجل.")
        else:
            st.warning("⚠️ يرجى ملء بيانات الجدول أولاً.")

except Exception as e:
    st.error(f"تأكد من تنسيق الشيت (المشروع ثم عمودين لكل قسم). الخطأ: {e}")
