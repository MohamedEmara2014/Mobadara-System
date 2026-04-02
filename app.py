import streamlit as st
import pandas as pd
import requests

# 1. إعدادات واجهة الموبايل والكمبيوتر
st.set_page_config(page_title="منظومة المبادرة المركزية", layout="wide")

# 2. الروابط الخاصة بك (تم وضع رابط الـ Exec الجديد)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwyEp27smOcrwmKKehIAn6LGlOGooOPjKFvuHjjlQkthv91QxMAfMoixD4QzHJ_L8P9/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("🏗️ مصفوفة المتابعة المركزية - 26 مشروعاً")
st.markdown("---")

try:
    # سحب البيانات الحالية لعرضها
    # نستخدم dtype=str لمنع أخطاء الأرقام والنصوص العربية
    df = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    # --- نافذة تحديث البيانات ---
    with st.container(border=True):
        st.subheader("📝 تحديث موقف تنفيذي جديد")
        with st.form("main_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                project = st.selectbox("اسم المشروع:", df.iloc[:, 0].unique())
            with col2:
                section = st.selectbox("القسم/المرحلة:", df.columns[1:])
            
            new_status = st.text_input("الموقف الحالي (اكتب التحديث هنا):")
            
            submitted = st.form_submit_button("إرسال التحديث للمدير العام ✅")

            if submitted:
                if new_status:
                    # حساب موقع الخلية بدقة مهنية
                    # +2 لأن جوجل شيتس يبدأ العد من 1 وهناك سطر عناوين
                    row_index = list(df.iloc[:, 0]).index(project) + 2
                    col_index = list(df.columns).index(section) + 1
                    
                    # إرسال البيانات عبر "الجسر" البرمجي (Apps Script)
                    payload = {
                        "row": row_index,
                        "col": col_index,
                        "val": new_status
                    }
                    
                    with st.spinner("جاري المزامنة مع ملف المدير..."):
                        res = requests.get(SCRIPT_URL, params=payload)
                    
                    if res.status_code == 200:
                        st.success(f"تم التحديث بنجاح: {project} ⮕ {section}")
                        st.balloons()
                    else:
                        st.error("فشل التحديث. تأكد أن رابط الـ Web App مفعل لـ Anyone.")
                else:
                    st.warning("يرجى كتابة نص التحديث أولاً.")

    # --- عرض الجدول الشامل للمدير ---
    st.markdown("### 📊 المصفوفة الختامية للمشاريع")
    
    # ميزة البحث السريع بالاسم
    search = st.text_input("🔍 بحث سريع عن مشروع:")
    if search:
        display_df = df[df.iloc[:, 0].str.contains(search, na=False)]
    else:
        display_df = df

    st.dataframe(display_df, use_container_width=True, height=500)

except Exception as e:
    st.error(f"خطأ في تحميل البيانات: {e}")
