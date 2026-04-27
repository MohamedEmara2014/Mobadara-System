import streamlit as st
import pandas as pd
import requests
import json
import time
import io
from datetime import datetime

# --- 1. إعدادات الأمان والروابط ---
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

# تأكد من أن الرابط سليم ولا يحتوي على مسافات
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyvNeUALnqFg-vv8LkLhb1ND-OYl-2xdMCY95VFevp4130MSHMlP3781h1Q-pOy0nei/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

# --- 2. وظائف النظام ---
def send_telegram_msg(section_name, method="يدوي"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = (
            f"🏗️ **تحديث تقرير المبادرة**\n\n"
            f"📍 القسم: *{section_name}*\n"
            f"🛠️ الوسيلة: *{method}*\n"
            f"⏰ الوقت: *{now}*\n\n"
            f"✅ تم تحديث الموقف الحالي والحالات الإجرائية."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 3. واجهة التطبيق ---
st.set_page_config(page_title="نظام متابعة المبادرة | المطور", layout="wide")
st.title("📂 التقرير الأسبوعي لمتابعة المبادرة")

try:
    @st.cache_data(ttl=5) # تقليل الكاش لضمان سرعة التزامن مع التعديلات
    def load_data():
        # قراءة البيانات مع إجبار التحديث لتجنب خطأ 404 أو الكاش القديم
        return pd.read_csv(f"{SHEET_CSV_URL}&cache_bust={time.time()}", dtype=str).fillna("")

    df_raw = load_data()
    all_cols = df_raw.columns
    
    # استخراج الأقسام بذكاء: نأخذ فقط الأعمدة التي لا تبدأ بـ Unnamed وليست العمود الأول (أسماء المشاريع)
    sections = [col for col in all_cols if "Unnamed" not in col and col != all_cols[0]]
    
    selected_section = st.selectbox("حدد القسم المختص للتحديث الميداني:", sections)
    
    if selected_section:
        # تحديد موقع القسم في الشيت
        col_idx_main = list(all_cols).index(selected_section)
        
        # الفهارس البرمجية (الإنجاز = الأساس، المعوقات = +1، الحالة = +2)
        # العمود الرابع (Action = +3) سيتم تجاهله ولن يظهر هنا
        col_idx_done = col_idx_main + 1
        col_idx_issues = col_idx_main + 2
        col_idx_status = col_idx_main + 3

        # عرض تاريخ آخر تحديث من الصف الثاني
        try:
            last_val = df_raw.iloc[0, col_idx_main]
            if last_val and "تحديث" in str(last_val):
                st.info(f"🕒 {last_val}")
        except:
            pass

        # تجهيز البيانات للعرض
        project_names = df_raw.iloc[2:, 0].values.tolist()
        display_df = pd.DataFrame({
            "المشروع": project_names,
            "ما تم انجازه خلال الأسبوع": df_raw.iloc[2:, col_idx_done - 1].values.tolist(),
            "المعوقات والمشاكل": df_raw.iloc[2:, col_idx_issues - 1].values.tolist(),
            "حالة الاتحاد": df_raw.iloc[2:, col_idx_status - 1].values.tolist()
        })

        # محرر البيانات (Data Editor)
        edited_df = st.data_editor(
            display_df,
            column_config={
                "المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
                "ما تم انجازه خلال الأسبوع": st.column_config.TextColumn("✅ الموقف الحالي", width="medium"),
                "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات", width="medium"),
                "حالة الاتحاد": st.column_config.SelectboxColumn(
                    "📊 الحالة",
                    options=[
                        "🟢 مكتمل",
                        "🔵 قيد التنفيذ",
                        "🟠 بانتظار مستندات",
                        "🔴 متوقف / معلق"
                    ],
                    required=True,
                )
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

        st.divider()

        if st.button(f"🚀 اعتماد بيانات {selected_section}", type="primary", use_container_width=True):
            updates = []
            for i, row in edited_df.iterrows():
                target_row = i + 4 # الصفوف تبدأ من 4 في الشيت
                updates.append({"row": target_row, "col": col_idx_done, "val": str(row["ما تم انجازه خلال الأسبوع"]).strip()})
                updates.append({"row": target_row, "col": col_idx_issues, "val": str(row["المعوقات والمشاكل"]).strip()})
                updates.append({"row": target_row, "col": col_idx_status, "val": str(row["حالة الاتحاد"]).strip()})
            
            if updates:
                with st.spinner("جاري المزامنة مع قاعدة البيانات..."):
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps({"updates": updates}), timeout=60)
                        if "Success" in res.text:
                            send_telegram_msg(selected_section, "يدوي")
                            st.success("✅ تم الحفظ بنجاح. ملاحظات الإدارة (Action) يتم مراجعتها في الشيت المجمع.")
                            st.balloons()
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ خطأ استجابة: {res.text}")
                    except Exception as e:
                        st.error(f"🌐 خطأ اتصال: {e}")

except Exception as e:
    import traceback
    st.error("⚠️ خطأ في هيكلة البيانات - يرجى مراجعة عناوين الأعمدة في الشيت:")
    st.code(traceback.format_exc())
