import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# 2. الروابط الأساسية
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzM8gX9uZz9CXTi1zsBH1qO3-4vAfnn8wRhv8wzqg7RXlv2roPYpOupEDOW3oCzVcI/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

# --- منطق إعادة ضبط الجدول (Reset Logic) ---
if 'count' not in st.session_state:
    st.session_state.count = 0

def reset_table():
    st.session_state.count += 1
    # مسح الذاكرة المؤقتة للجدول لضمان التفريغ الحقيقي
    if f"editor_{st.session_state.count-1}" in st.session_state:
        del st.session_state[f"editor_{st.session_state.count-1}"]

try:
    # جلب البيانات
    df = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    project_col = df.columns[0]
    sections = df.columns[1:]
    
    # تحديث العبارة التوجيهية بناءً على طلبك
    instruction_text = "🎯 حدد القسم الخاص بك ثم اضغط اعتماد وتصدير البيانات أسفل الصفحة:"
    selected_section = st.selectbox(instruction_text, sections)
    col_idx = list(df.columns).index(selected_section) + 1

    st.markdown(f"### 📊 جدول تحديثات: {selected_section}")

    # تحضير البيانات للعرض
    display_df = df[[project_col, selected_section]].copy()

    # استخدام مفتاح ديناميكي يتغير عند الضغط على زر المسح
    current_key = f"editor_{st.session_state.count}"
    
    edited_df = st.data_editor(
        display_df,
        key=current_key,
        column_config={
            project_col: st.column_config.TextColumn("اسم المشروع", disabled=True),
            selected_section: st.column_config.TextColumn(f"الموقف التنفيذي - {selected_section}", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

    # --- أزرار التحكم ---
    col_btn1, col_btn2 = st.columns([1, 3])
    
    with col_btn1:
        # زر المسح: يستدعي وظيفة reset_table لإعادة بناء الجدول ببيانات فارغة
        if st.button("🗑️ تفريغ كافة الخانات", use_container_width=True, on_click=reset_table):
            st.rerun()

    with col_btn2:
        if st.button(f"🚀 اعتماد وتصدير التقرير اليومي لـ {selected_section}", type="primary", use_container_width=True):
            updates_to_send = []
            
            # استخراج البيانات من الجدول المعدل
            for i in range(len(edited_df)):
                val = edited_df.iloc[i, 1]
                updates_to_send.append({
                    "row": i + 2,
                    "col": col_idx,
                    "val": str(val) if val else "" 
                })
            
            if updates_to_send:
                with st.spinner("جاري مسح القديم وتحديث البيانات الجديدة..."):
                    params = {"updates": json.dumps(updates_to_send)}
                    response = requests.get(SCRIPT_URL, params=params)
                    
                    if response.status_code == 200:
                        st.success("✅ تم تحديث التقرير بنجاح في ملف الإدارة!")
                        st.balloons()
                    else:
                        st.error("❌ فشل الاتصال بالسيرفر، تأكد من إعدادات الـ Deployment.")
            else:
                st.warning("⚠️ لا توجد بيانات لإرسالها.")

except Exception as e:
    st.error(f"خطأ تقني: {e}")
