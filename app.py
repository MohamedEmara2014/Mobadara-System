import streamlit as st
import pandas as pd
import requests
import json
import time

st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwKryaebBnTZTOp1NIul4VS1SSaslq5TH_jDDEfCq77Ef1NZ21F0IDWYrt5NYJkgDwg/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات - مع مراعاة أن الصف الأول هو أسماء الأقسام
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    
    # قائمة الأقسام (نأخذ الأسماء من الصف الأول في الشيت - Headers)
    # ملاحظة: بما أن الأقسام مدمجة، سنأخذ الأعمدة الفردية (1, 3, 5...)
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2)]
    
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك:", sections)
    
    # تحديد مكان الأعمدة في الشيت
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 # العمود الذي يليه مباشرة هو المعوقات

    # عرض تاريخ آخر تحديث (موجود في الصف الأول من الداتا، أي الصف 2 في الشيت)
    last_update_val = df_raw.iloc[0, col_idx_done - 1]
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")

    st.markdown(f"### 📊 تحديثات قسم: {selected_section}")

    # أسماء المشاريع تبدأ من الصف الثالث في الداتا (أي الصف 4 في الشيت)
    project_names = df_raw.iloc[1:, 0] 

    # إنشاء جدول الإدخال بخانتين
    input_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": "",
        "المعوقات والمشاكل": ""
    })

    edited_df = st.data_editor(
        input_df,
        key=f"editor_{selected_section}",
        column_config={
            "اسم المشروع": st.column_config.TextColumn("اسم المشروع", disabled=True),
            "ما تم إنجازه": st.column_config.TextColumn("التنفيذ الفعلي", width="medium"),
            "المعوقات والمشاكل": st.column_config.TextColumn("المعوقات", width="medium")
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        for i in range(len(edited_df)):
            val_done = edited_df.iloc[i, 1]
            val_issues = edited_df.iloc[i, 2]
            
            # إرسال للعمود الأول (إنجاز) وللعمود الثاني (معوقات)
            # الصف يبدأ من i + 4 لأن عندنا (1: عناوين، 2: تاريخ، 3: مسميات الأعمدة)
            updates_to_send.append({"row": i + 4, "col": col_idx_done, "val": str(val_done) if val_done else ""})
            updates_to_send.append({"row": i + 4, "col": col_idx_issues, "val": str(val_issues) if val_issues else ""})
        
        if updates_to_send:
            with st.spinner("جاري الإرسال للمنظومة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                if response.status_code == 200:
                    st.success("✅ تم الاعتماد بنجاح!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
except Exception as e:
    st.error(f"تأكد من تنسيق الشيت (عمودين لكل قسم). الخطأ: {e}")
