import streamlit as st
import pandas as pd
import requests
import json
import time  # تم إضافة المكتبة لضبط توقيت ظهور البالونات

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط الخاصة بك
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzGx48qSN8zXAgoCBqfg6U3pgnTkS70-4v75iG-nVWNOtckDsLZtRXxeBK0tAlWS6Ip/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات اللحظية (بدون كاش لضمان الدقة)
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    sections = df_raw.columns[1:]
    
    # اختيار القسم
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:", sections)
    col_idx = list(df_raw.columns).index(selected_section) + 1

    # --- عرض تاريخ آخر تحديث (للقراءة فقط) ---
    # جلب القيمة من الصف الأول في الـ DataFrame (المقابل للصف 2 في الشيت)
    last_update_val = df_raw.iloc[0, col_idx - 1]
    
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")
    else:
        st.warning("⚠️ لم يتم تسجيل تحديثات لهذا القسم اليوم بعد.")

    st.markdown(f"### 📊 جدول تحديثات: {selected_section}")

    # تحضير الجدول (استبعاد صف التاريخ من قائمة المشاريع المعروضة)
    # أسماء المشاريع تبدأ من السطر الثاني في الـ DataFrame (السطر 3 في الشيت)
    project_names = df_raw.iloc[1:, 0]

    empty_display_df = pd.DataFrame({
        df_raw.columns[0]: project_names,
        selected_section: "" 
    })

    # محرر البيانات التفاعلي
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

    st.divider()

    # زر الاعتماد والتصدير
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        
        # تجميع البيانات للإرسال (row: i + 3 لتبدأ من صف المشاريع الفعلي)
        for i in range(len(edited_df)):
            val = edited_df.iloc[i, 1]
            updates_to_send.append({
                "row": i + 3, 
                "col": col_idx,
                "val": str(val) if val else "" 
            })
        
        if updates_to_send:
            with st.spinner("جاري المزامنة مع سجل الإدارة..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    # إظهار رسالة النجاح والبالونات
                    st.success("✅ تم التحديث بنجاح! جاري تحديث بيانات الصفحة...")
                    st.balloons()
                    
                    # الانتظار لمدة ثانيتين لضمان رؤية التأثيرات البصرية
                    time.sleep(2)
                    
                    # إعادة تحميل الصفحة لعرض التاريخ الجديد في الأعلى
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال بالسيرفر. يرجى التحقق من صلاحيات الـ Web App.")
        else:
            st.warning("⚠️ يرجى إدخال البيانات في الجدول أولاً.")

except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
