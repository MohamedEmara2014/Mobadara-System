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
    # جلب البيانات - header=0 يعني أن الصف الأول (الأقسام) هو العنوان
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    
    # استخراج أسماء الأقسام (الأعمدة B, D, F, H, J)
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك:", sections)
    
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # التاريخ موجود في الصف رقم 2 في الشيت (أي الصف index 0 في البيانات المقروءة)
    last_update_val = df_raw.iloc[0, col_idx_done - 1]
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")

    # أسماء المشاريع تبدأ من الصف 4 في الشيت 
    # في pandas، بما أننا قرأنا الهيدر، فإن الصف 4 في الشيت يقابل index رقم 2 في البيانات
    project_names = df_raw.iloc[2:, 0] 

    input_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": "",
        "المعوقات والمشاكل": ""
    })

    edited_df = st.data_editor(
        input_df,
        key=f"editor_{selected_section}",
        column_config={
            "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
            "ما تم إنجازه": st.column_config.TextColumn("✅ ما تم إنجازه اليوم", width="large"),
            "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات والمشاكل", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        for i in range(len(edited_df)):
            val_done = edited_df.iloc[i, 1]
            val_issues = edited_df.iloc[i, 2]
            
            # التعديل الجوهري هنا:
            # i هو ترتيب المشروع في الجدول (0, 1, 2...)
            # المشروع الأول (i=0) يجب أن يذهب للصف 4 في الشيت
            # إذن المعادلة هي i + 4
            target_row = i + 4
            
            updates_to_send.append({"row": target_row, "col": col_idx_done, "val": str(val_done) if val_done else ""})
            updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": str(val_issues) if val_issues else ""})
        
        if updates_to_send:
            with st.spinner("جاري المزامنة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                if response.status_code == 200:
                    st.success("✅ تم الاعتماد بنجاح!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
except Exception as e:
    st.error(f"حدث خطأ: {e}")
