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
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LkMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

# --- 2. وظائف النظام ---
def send_telegram_msg(section_name, method="يدوي"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = (
            f"🏗️ **تحديث تقرير المبادرة الإجرائي**\n\n"
            f"📍 القسم: *{section_name}*\n"
            f"🛠️ الوسيلة: *{method}*\n"
            f"⏰ الوقت: *{now}*\n\n"
            f"✅ تم تحديث بيانات المشاريع بنجاح."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 3. واجهة التطبيق ---
st.set_page_config(page_title="نظام متابعة المبادرة | Dashboard", layout="wide")
st.title("📂 التقرير الأسبوعي لمتابعة المبادرة")

try:
    @st.cache_data(ttl=10)
    def load_data():
        return pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")

    df_raw = load_data()
    all_cols = df_raw.columns
    
    # القفز كل 4 أعمدة (الإنجاز، المعوقات، الحالة، والأكشن المخفي للإدارة)
    sections = [all_cols[i] for i in range(1, len(all_cols), 4) if "Unnamed" not in all_cols[i]]
    
    selected_section = st.selectbox("حدد القسم المختص للتحديث:", sections)
    
    if selected_section:
        col_idx_done = list(df_raw.columns).index(selected_section) + 1
        col_idx_issues = col_idx_done + 1
        col_idx_status = col_idx_done + 2

        try:
            last_val = df_raw.iloc[0, col_idx_done - 1]
            if last_val and "تحديث" in str(last_val):
                st.info(f"🕒 {last_val}")
        except:
            pass

        project_names = df_raw.iloc[2:, 0].values.tolist()
        display_df = pd.DataFrame({
            "اسم المشروع": project_names,
            "إنجاز الأسبوع": df_raw.iloc[2:, col_idx_done - 1].values.tolist(),
            "المعوقات": df_raw.iloc[2:, col_idx_issues - 1].values.tolist(),
            "الحالة الإجرائية": df_raw.iloc[2:, col_idx_status - 1].values.tolist()
        })

        with st.sidebar:
            st.header("📤 خيارات النظام")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button(f"⬇️ تحميل نموذج {selected_section}", buffer.getvalue(), f"{selected_section}.xlsx")
            st.divider()
            update_method = "يدوي (أونلاين)"
            uploaded_file = st.file_uploader("رفع تقرير إكسيل (أسبوعي)", type=["xlsx"])
            
            if uploaded_file:
                excel_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                if excel_df.shape[1] >= 4:
                    display_df["إنجاز الأسبوع"] = excel_df.iloc[:len(project_names), 1].values
                    display_df["المعوقات"] = excel_df.iloc[:len(project_names), 2].values
                    display_df["الحالة الإجرائية"] = excel_df.iloc[:len(project_names), 3].values
                    update_method = "ملف إكسيل"
                    st.sidebar.success("✅ تم استيراد الملف")

        # محرر البيانات مع المسميات الجديدة المعتمدة
        edited_df = st.data_editor(
            display_df,
            column_config={
                "اسم المشروع": st.column_config.TextColumn("🏗️ المشروع", disabled=True),
                "إنجاز الأسبوع": st.column_config.TextColumn("✅ الموقف الحالي", width="medium"),
                "المعوقات": st.column_config.TextColumn("⚠️ المعوقات (إن وجدت)", width="medium"),
                "الحالة الإجرائية": st.column_config.SelectboxColumn(
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
            height=550
        )

        st.divider()

        if st.button(f"🚀 اعتماد بيانات {selected_section}", type="primary", use_container_width=True):
            updates = []
            for i, row in edited_df.iterrows():
                target_row = i + 4
                updates.append({"row": target_row, "col": col_idx_done, "val": str(row["إنجاز الأسبوع"]).strip()})
                updates.append({"row": target_row, "col": col_idx_issues, "val": str(row["المعوقات"]).strip()})
                updates.append({"row": target_row, "col": col_idx_status, "val": str(row["الحالة الإجرائية"]).strip()})
            
            if updates:
                with st.spinner(f"جاري مزامنة بيانات {selected_section}..."):
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps({"updates": updates}), timeout=60)
                        if "Success" in res.text:
                            send_telegram_msg(selected_section, update_method)
                            st.success("✅ تم الحفظ. يمكنك الآن مراجعة عمود Action في الشيت المجمع.")
                            st.balloons()
                            st.cache_data.clear()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ خطأ: {res.text}")
                    except Exception as e:
                        st.error(f"🌐 خطأ اتصال: {e}")
            else:
                st.warning("⚠️ لا توجد بيانات للتحديث.")

except Exception as e:
    import traceback
    st.error("⚠️ خطأ في تشغيل النظام:")
    st.code(traceback.format_exc())
