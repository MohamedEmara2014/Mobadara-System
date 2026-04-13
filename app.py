import streamlit as st
import pandas as pd
import requests
import json
import time

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الرابط الجديد الذي قمت بتزويدي به
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwE9XcpdsumPSoGJ0G_apcTbnRLj1zLPPVR8MVZRGANBwVGYtn0vavLJTabfY_Fda0/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات من جوجل شيتس
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    
    # استخراج أسماء الأقسام (كل قسم يغطي عمودين)
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:", sections)
    
    # تحديد أرقام الأعمدة (الإنجاز والمعوقات)
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # عرض تاريخ آخر تحديث من الشيت
    last_update_val = df_raw.iloc[0, col_idx_done - 1]
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")
    else:
        st.warning("⚠️ لم يتم تسجيل تحديثات لهذا القسم اليوم بعد.")

    st.markdown(f"### 📝 جدول إدخال بيانات: {selected_section}")

    # قراءة أسماء المشاريع (تلقائياً مهما كان عددها)
    project_names = df_raw.iloc[2:, 0].tolist() 

    # بناء هيكل الجدول
    input_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": "",
        "المعوقات والمشاكل": ""
    })

    # عرض محرر البيانات بـ 3 أعمدة متجاورة
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
        height=600 # ارتفاع مناسب لـ 38 مشروعاً
    )

    st.divider()

    # زر الاعتماد والتصدير
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        for i in range(len(edited_df)):
            val_done = edited_df.iloc[i, 1]
            val_issues = edited_df.iloc[i, 2]
            
            # إرسال البيانات للصفوف ابتداءً من الصف 4
            target_row = i + 4
            
            updates_to_send.append({"row": target_row, "col": col_idx_done, "val": str(val_done) if val_done else ""})
            updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": str(val_issues) if val_issues else ""})
        
        if updates_to_send:
            with st.spinner("جاري المزامنة مع الرابط الجديد..."):
                params = {"updates": json.dumps(updates_to_send)}
                # استخدام الرابط الجديد
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    st.success(f"✅ تم الاعتماد بنجاح لـ {len(project_names)} مشروعاً!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال بالرابط الجديد. تأكد من إعدادات النشر (Anyone).")
        else:
            st.warning("⚠️ يرجى ملء الجدول أولاً.")

except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
