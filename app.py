import streamlit as st
import pandas as pd
import requests
import json
import time
import io
from datetime import datetime

# --- 1. الإعدادات الأمنية والروابط ---
# ملاحظة: يفضل مستقبلاً وضع التوكن في Streamlit Secrets
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

# الروابط المحدثة
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyvNeUALnqFg-vv8LkLhb1ND-OYl-2xdMCY95VFevp4130MSHMlP3781h1Q-pOy0nei/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

# --- 2. وظائف النظام المساعدة ---

def send_telegram_msg(section_name, method="يدوي"):
    """إرسال إشعار تليجرام عند كل عملية اعتماد"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = (
            f"🏗️ **تنبيه تحديث جديد**\n\n"
            f"📍 القسم: *{section_name}*\n"
            f"🛠️ الوسيلة: *{method}*\n"
            f"⏰ الوقت: *{now}*\n\n"
            f"✅ تم تحديث قاعدة البيانات بنجاح."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass

# --- 3. واجهة التطبيق الرئيسية ---
st.set_page_config(page_title="نظام متابعة المبادرة", layout="wide")

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات الخام من جوجل
    @st.cache_data(ttl=30) # تحديث الكاش كل 30 ثانية
    def load_data():
        return pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    df_raw = load_data()
    
    # استخراج أسماء الأقسام (تفترض أن الأقسام تبدأ من العمود الثاني وتتكرر كل عمودين)
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    # اختيار القسم
    selected_section = st.selectbox("حدد القسم الخاص بك للمراجعة أو التعديل:", sections)
    
    if selected_section:
        # تحديد إحداثيات القسم
        col_idx_done = list(df_raw.columns).index(selected_section) + 1
        col_idx_issues = col_idx_done + 1 

        # --- إظهار تاريخ آخر تحديث من الصف الثاني ---
        try:
            # iloc[0] تقابل الصف الثاني في شيت جوجل (تحت اسم القسم مباشرة)
            last_update_info = df_raw.iloc[0, col_idx_done - 1]
            if last_update_info and "تحديث" in str(last_update_info):
                st.info(f"🕒 {last_update_info}")
        except:
            pass

        # تجهيز الجدول للعرض (البيانات تبدأ من الصف الرابع في الشيت، أي iloc[2:] في باندا)
        project_names = df_raw.iloc[2:, 0].values.tolist()
        current_done = df_raw.iloc[2:, col_idx_done - 1].values.tolist()
        current_issues = df_raw.iloc[2:, col_idx_issues - 1].values.tolist()

        display_df = pd.DataFrame({
            "اسم المشروع": project_names,
            "ما تم إنجازه": current_done,
            "المعوقات والمشاكل": current_issues
        })

        # --- 4. شريط الإجراءات الجانبي (تحميل/رفع إكسيل) ---
        with st.sidebar:
            st.header("📤 خيارات الإكسيل")
            # زر التحميل
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button("⬇️ تحميل التقرير الحالي", buffer.getvalue(), f"تقرير_{selected_section}.xlsx")
            
            st.divider()
            
            # زر الرفع
            update_method = "يدوي (أونلاين)"
            uploaded_file = st.file_uploader("رفع ملف إكسيل مكتمل", type=["xlsx"])
            if uploaded_file:
                try:
                    excel_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                    # التأكد من وجود أعمدة كافية لتجنب "خطأ 1"
                    if excel_df.shape[1] >= 3:
                        display_df["ما تم إنجازه"] = excel_df.iloc[:len(project_names), 1].values
                        display_df["المعوقات والمشاكل"] = excel_df.iloc[:len(project_names), 2].values
                        update_method = "ملف إكسيل"
                        st.sidebar.success("✅ تم تحديث البيانات من الملف")
                    else:
                        st.sidebar.error("❌ الملف المرفوع لا يحتوي على الأعمدة المطلوبة.")
                except Exception as e:
                    st.sidebar.error(f"⚠️ خطأ في قراءة الملف: {e}")

        # --- 5. محرر البيانات التفاعلي ---
        edited_df = st.data_editor(
            display_df,
            column_config={
                "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
                "ما تم إنجازه": st.column_config.TextColumn("✅ ما تم إنجازه اليوم", width="large"),
                "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات والمشاكل", width="large")
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

        st.divider()

        # --- 6. عملية الاعتماد والحفظ (POST) ---
        if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
            updates_to_send = []
            for i, row in edited_df.iterrows():
                target_row = i + 4 # الحفاظ على هيكل (اسم القسم، التاريخ، العناوين)
                updates_to_send.append({"row": target_row, "col": col_idx_done, "val": str(row[1])})
                updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": str(row[2])})
            
            if updates_to_send:
                with st.spinner("جاري حفظ البيانات وتسجيل الوقت..."):
                    payload = json.dumps({"updates": updates_to_send})
                    try:
                        # إرسال البيانات باستخدام POST لضمان استقرار النصوص الطويلة
                        response = requests.post(SCRIPT_URL, data=payload, timeout=60)
                        
                        if response.status_code == 200 and "Success" in response.text:
                            send_telegram_msg(selected_section, update_method)
                            st.success("✅ تم الحفظ وتحديث الوقت بنجاح!")
                            st.balloons()
                            st.cache_data.clear() # مسح الكاش لرؤية البيانات الجديدة
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ فشل الاتصال بخادم جوجل: {response.status_code}")
                            st.text(response.text)
                    except Exception as req_e:
                        st.error(f"🌐 خطأ في الاتصال بالشبكة: {req_e}")
            else:
                st.warning("⚠️ لا توجد بيانات جديدة لإرسالها.")

except Exception as e:
    import traceback
    st.error("⚠️ حدث خطأ في معالجة البيانات:")
    st.code(traceback.format_exc()) # يظهر لك مكان الخطأ بالضبط بدلاً من مجرد رقم
