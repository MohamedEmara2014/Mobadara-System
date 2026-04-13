import streamlit as st
import pandas as pd
import requests
import json
import time

st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# الرابط الجديد الخاص بك
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwE9XcpdsumPSoGJ0G_apcTbnRLj1zLPPVR8MVZRGANBwVGYtn0vavLJTabfY_Fda0/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    # العبارة كما طلبتها تماماً دون تغيير
    selected_section = st.selectbox("حدد القسم الخاص بك واضغط اعتماد وتصدير البيانات أخر الصفحة", sections)
    
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # عرض تاريخ التحديث
    last_update_val = df_raw.iloc[0, col_idx_done - 1]
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")

    # قراءة أسماء المشاريع (تبدأ من الصف الرابع في الشيت)
    project_names = df_raw.iloc[2:, 0].values.tolist()

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
        height=600 
    )

    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        for i in range(len(edited_df)):
            val_done = str(edited_df.iloc[i, 1]).strip()
            val_issues = str(edited_df.iloc[i, 2]).strip()
            
            # نرسل فقط الصفوف التي تحتوي على بيانات (هذا يمنع الكتابة العشوائية فوق العناوين)
            if val_done or val_issues:
                target_row = i + 4 # المشروع الأول i=0 يذهب للصف 4
                
                updates_to_send.append({"row": target_row, "col": col_idx_done, "val": val_done})
                updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": val_issues})
        
        if updates_to_send:
            with st.spinner("جاري المزامنة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                if response.status_code == 200:
                    st.success("✅ تم التحديث بنجاح!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
        else:
            st.warning("⚠️ يرجى كتابة أي بيانات في الجدول أولاً قبل الضغط على اعتماد.")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
