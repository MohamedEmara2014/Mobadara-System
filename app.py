import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzM8gX9uZz9CXTi1zsBH1qO3-4vAfnn8wRhv8wzqg7RXlv2roPYpOupEDOW3oCzVcI/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

# --- وظيفة تفريغ الخانات ---
if 'table_key' not in st.session_state:
    st.session_state.table_key = 0

def clear_table():
    st.session_state.table_key += 1 # تغيير المفتاح يجبر التيبول على إعادة التحميل فارغاً

try:
    # جلب البيانات
    df = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    project_col = df.columns[0]
    sections = df.columns[1:]
    
    selected_section = st.selectbox("🎯 حدد القسم الخاص بك:", sections)
    col_idx = list(df.columns).index(selected_section) + 1

    st.markdown(f"### 📊 جدول تحديثات: {selected_section}")

    # تحضير نسخة فارغة من العمود إذا طلب المستخدم المسح
    display_df = df[[project_col, selected_section]].copy()

    # استخدام مفتاح (key) ديناميكي للتحكم في إعادة ضبط الجدول
    edited_df = st.data_editor(
        display_df,
        key=f"editor_{st.session_state.table_key}", 
        column_config={
            project_col: st.column_config.TextColumn("اسم المشروع", disabled=True),
            selected_section: st.column_config.TextColumn(f"الموقف التنفيذي - {selected_section}", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

    # --- أزرار التحكم ---
    col_btn1, col_btn2 = st.columns([1, 4]) # تقسيم المساحة بين الزرين
    
    with col_btn1:
        # زر المسح (باللون الأحمر للتحذير)
        if st.button("🗑️ تفريغ كافة الخانات", use_container_width=True, on_click=clear_table):
            st.rerun()

    with col_btn2:
        # زر الاعتماد (باللون الأخضر)
        if st.button(f"🚀 اعتماد وتصدير التقرير اليومي لـ {selected_section}", type="primary", use_container_width=True):
            updates_to_send = []
            
            for i in range(len(edited_df)):
                val = edited_df.iloc[i, 1]
                updates_to_send.append({
                    "row": i + 2,
                    "col": col_idx,
                    "val": str(val) if val else "" 
                })
            
            if updates_to_send:
                with st.spinner("جاري تهيئة القسم وتحديث البيانات..."):
                    params = {"updates": json.dumps(updates_to_send)}
                    response = requests.get(SCRIPT_URL, params=params)
                    
                    if response.status_code == 200:
                        st.success("✅ تم مسح القديم وتحديث التقرير اليومي بنجاح!")
                        st.balloons()
                    else:
                        st.error("❌ فشل الاتصال. تأكد من رابط الـ Web App.")
            else:
                st.warning("⚠️ الجدول فارغ، لا يوجد بيانات لإرسالها.")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
