import streamlit as st
import pandas as pd
import requests
import json
import time

st.set_page_config(page_title="تحديث المبادرة", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwKryaebBnTZTOp1NIul4VS1SSaslq5TH_jDDEfCq77Ef1NZ21F0IDWYrt5NYJkgDwg/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    all_cols = df_raw.columns
    # نأخذ الأقسام (كل قسم يمثل عمودين في الشيت)
    sections = [all_cols[i] for i in range(1, len(all_cols), 2)]
    
    selected_section = st.selectbox("🎯 اختر القسم:", sections)
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1

    # عرض التاريخ
    last_update = df_raw.iloc[0, col_idx_done - 1]
    st.success(f"📅 {last_update}" if "تحديث:" in str(last_update) else "⚠️ لا يوجد تحديث اليوم")

    st.write("---")
    st.subheader(f"📝 إدخال بيانات: {selected_section}")

    # قائمة المشاريع (من الصف 4 في الشيت)
    project_names = df_raw.iloc[1:, 0].tolist()
    
    # مخزن للبيانات المدخلة
    user_inputs = []

    # إنشاء الخانات متجاورة لكل مشروع
    for i, name in enumerate(project_names):
        st.markdown(f"**🏗️ {name}**")
        col1, col2 = st.columns(2) # تقسيم السطر لعمودين متساويين
        
        with col1:
            done = st.text_input("ما تم إنجازه", key=f"done_{i}", placeholder="أدخل الموقف التنفيذي...")
        with col2:
            issues = st.text_input("المعوقات والمشاكل", key=f"issue_{i}", placeholder="أدخل المعوقات إن وجدت...")
        
        user_inputs.append({"done": done, "issues": issues})
        st.write("") # فاصل بسيط بين المشاريع

    st.divider()

    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        for i, entry in enumerate(user_inputs):
            # i + 4 لأننا تجاوزنا الصفوف الثلاثة الأولى في الشيت
            updates_to_send.append({"row": i + 4, "col": col_idx_done, "val": entry["done"]})
            updates_to_send.append({"row": i + 4, "col": col_idx_issues, "val": entry["issues"]})
        
        if any(d["val"] for d in updates_to_send): # التأكد أن هناك بيانات كتبت
            with st.spinner("جاري الإرسال..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                if response.status_code == 200:
                    st.success("✅ تم التحديث بنجاح!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
        else:
            st.warning("⚠️ يرجى كتابة بيانات قبل الاعتماد.")

except Exception as e:
    st.error(f"خطأ: {e}")
