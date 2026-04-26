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
            f"✅ تم تحديث البيانات والحالات بنجاح."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 3. واجهة التطبيق ---
st.set_page_config(page_title="نظام متابعة المبادرة | الشئون القانونية وأقساط الجهاز", layout="wide")
st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    @st.cache_data(ttl=10)
    def load_data():
        return pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    df_raw = load_data()
    all_cols = df_raw.columns
    
    # استخراج الأقسام: نقفز 3 أعمدة (Column 1, 4, 7, 10...)
    sections = [all_cols[i] for i in range(1, len(all_cols), 3) if "Unnamed" not in all_cols[i]]
    
    selected_section = st.selectbox("حدد القسم الخاص بك للمراجعة أو التعديل:", sections)
    
    if selected_section:
        # تحديد الفهارس للأعمدة الثلاثة لكل قسم
        col_idx_done = list(df_raw.columns).index(selected_section) + 1
        col_idx_issues = col_idx_done + 1
        col_idx_status = col_idx_done + 2

        # عرض تاريخ آخر تحديث من الصف الثاني (المدمج برمجياً فوق الـ 3 أعمدة)
        try:
            last_val = df_raw.iloc[0, col_idx_done - 1]
            if last_val and "تحديث" in str(last_val):
                st.info(f"🕒 {last_val}")
        except:
            pass

        # تجهيز البيانات للعرض
        project_names = df_raw.iloc[2:, 0].values.tolist()
        display_df = pd.DataFrame({
            "اسم المشروع": project_names,
            "ما تم إنجازه": df_raw.iloc[2:, col_idx_done - 1].values.tolist(),
            "المعوقات والمشاكل": df_raw.iloc[2:, col_idx_issues - 1].values.tolist(),
            "حالة الاتحاد": df_raw.iloc[2:, col_idx_status - 1].values.tolist()
        })

        # الشريط الجانبي
        with st.sidebar:
            st.header("📤 خيارات الإكسيل")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button(f"⬇️ تحميل نموذج {selected_section}", buffer.getvalue(), f"{selected_section}.xlsx")
            st.divider()
            update_method = "يدوي (أونلاين)"
            uploaded_file = st.file_uploader("رفع ملف إكسيل مكتمل", type=["xlsx"])
            
            if uploaded_file:
                excel_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                if excel_df.shape[1] >= 4:
                    display_df["ما تم إنجازه"] = excel_df.iloc[:len(project_names), 1].values
                    display_df["المعوقات والمشاكل"] = excel_df.iloc[:len(project_names), 2].values
                    display_df["حالة الاتحاد"] = excel_df.iloc[:len(project_names), 3].values
                    update_method = "ملف إكسيل"
                    st.sidebar.success("✅ تم دمج الملف بنجاح")

        # محرر البيانات مع خاصية القائمة المنسدلة الملونة (إيموجي)
        edited_df = st.data_editor(
            display_df,
            column_config={
                "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
                "ما تم إنجازه": st.column_config.TextColumn("✅ ما تم إنجازه خلال الأسبوع", width="medium"),
                "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات والمشاكل", width="medium"),
                "حالة الاتحاد": st.column_config.SelectboxColumn(
                    "📊 حالة الاتحاد",
                    options=[
                        "🟢 تم",
                        "🟡 جاري",
                        "🔴 متعثر"
                    ],
                    required=True,
                )
            },
            hide_index=True,
            use_container_width=True,
            height=550
        )

        st.divider()

        # زر الاعتماد النهائي
        if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
            updates = []
            for i, row in edited_df.iterrows():
                target_row = i + 4
                updates.append({"row": target_row, "col": col_idx_done, "val": str(row["ما تم إنجازه"]).strip()})
                updates.append({"row": target_row, "col": col_idx_issues, "val": str(row["المعوقات والمشاكل"]).strip()})
                updates.append({"row": target_row, "col": col_idx_status, "val": str(row["حالة الاتحاد"]).strip()})
            
            if updates:
                with st.spinner(f"جاري مزامنة بيانات {selected_section}..."):
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps({"updates": updates}), timeout=60)
                        if "Success" in res.text:
                            send_telegram_msg(selected_section, update_method)
                            st.success(f"✅ تم حفظ بيانات {selected_section} وتحديث التاريخ بنجاح!")
                            st.balloons()
                            st.cache_data.clear()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ خطأ من الخادم: {res.text}")
                    except Exception as e:
                        st.error(f"🌐 خطأ في الاتصال: {e}")
            else:
                st.warning("⚠️ لا توجد بيانات جديدة لإرسالها.")

except Exception as e:
    import traceback
    st.error("⚠️ حدث خطأ في النظام:")
    st.code(traceback.format_exc())
