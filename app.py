import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzGx48qSN8zXAgoCBqfg6U3pgnTkS70-4v75iG-nVWNOtckDsLZtRXxeBK0tAlWS6Ip/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    sections = df_raw.columns[1:]
    
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك:", sections)
    col_idx = list(df_raw.columns).index(selected_section) + 1

    # --- عرض تاريخ آخر تحديث (غير قابل للتعديل) ---
    # نقرأ القيمة الموجودة حالياً في الصف الثاني من الشيت (التي سجلها السكريبت)
    last_update_val = df_raw.iloc[0, col_idx - 1] # إحضار أول صف بيانات (الذي يمثل التاريخ في الشيت)
    
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")
    else:
        st.warning("⚠️ لم يتم تسجيل تحديثات لهذا القسم اليوم بعد.")

    st.markdown(f"### 📊 جدول تحديثات: {selected_section}")

    # تحضير الجدول (إظهار أسماء المشاريع وخانات فارغة للملء)
    # ملاحظة: استبعدنا أول صف (صف التاريخ) من قائمة المشاريع المعروضة
    project_names = df_raw.iloc[1:, 0] # تبدأ الأسماء من الصف الثاني في الـ DataFrame

    empty_display_df = pd.DataFrame({
        df_raw.columns[0]: project_names,
        selected_section: "" 
    })

    edited_df = st.data_editor(
        empty_display_df,
        key=f"editor_{selected_section}",
        column_config={
            df_raw.columns[0]: st.column_config.TextColumn("اسم المشروع", disabled=True),
            selected_section: st.column_config.TextColumn(f"الموقف التنفيذي الجديد", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        # i + 3 لأننا نبدأ من صف المشاريع بعد العنوان والتاريخ
        for i in range(len(edited_df)):
            val = edited_df.iloc[i, 1]
            updates_to_send.append({
                "row": i + 3, 
                "col": col_idx,
                "val": str(val) if val else "" 
            })
        
        if updates_to_send:
            with st.spinner("جاري المزامنة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                if response.status_code == 200:
                    st.success("✅ تم التحديث بنجاح!")
                    st.balloons()
                    st.rerun() # لإعادة تحميل الصفحة وعرض التاريخ الجديد
except Exception as e:
    st.error(f"خطأ: {e}")
