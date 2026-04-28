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
            f"💰 **تحديث مالي - قسم الحسابات**\n\n" if "حسابات" in section_name else f"🏗️ **تحديث تقرير المبادرة**\n\n"
        )
        text += (
            f"📍 القسم: *{section_name}*\n"
            f"🛠️ الوسيلة: *{method}*\n"
            f"⏰ الوقت: *{now}*\n\n"
            f"✅ تم تحديث البيانات بنجاح."
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 3. واجهة التطبيق ---
st.set_page_config(page_title="نظام متابعة المبادرة | الحسابات والإدارة", layout="wide")
st.title("📂 التقرير الأسبوعي لمتابعة المبادرة")

try:
    @st.cache_data(ttl=5)
    def load_data():
        return pd.read_csv(f"{SHEET_CSV_URL}&cache_bust={time.time()}", dtype=str).fillna("")

    df_raw = load_data()
    all_cols = df_raw.columns
    
    # استخراج الأقسام (تجاهل الأعمدة الفارغة والعمود الأول)
    sections = [col for col in all_cols if "Unnamed" not in col and col != all_cols[0]]
    
    selected_section = st.selectbox("حدد القسم المختص للتحديث:", sections)
    
    if selected_section:
        col_idx_main = list(all_cols).index(selected_section)
        project_names = df_raw.iloc[2:, 0].values.tolist()

        # --- منطق مخصص لقسم الحسابات ---
        if "الحسابات" in selected_section:
            # ترتيب الأعمدة: 1.وارد العملاء، 2.صادر العملاء، 3.وارد التنفيذ، 4.صادر التنفيذ، 5.الرصيد (ونتجاهل 6.Action)
            col_indices = [col_idx_main + 1, col_idx_main + 2, col_idx_main + 3, col_idx_main + 4, col_idx_main + 5]
            
            display_df = pd.DataFrame({
                "المشروع": project_names,
                "وارد العملاء": df_raw.iloc[2:, col_indices[0]-1].values.tolist(),
                "صادر العملاء": df_raw.iloc[2:, col_indices[1]-1].values.tolist(),
                "وارد التنفيذ": df_raw.iloc[2:, col_indices[2]-1].values.tolist(),
                "صادر التنفيذ": df_raw.iloc[2:, col_indices[3]-1].values.tolist(),
                "الرصيد": df_raw.iloc[2:, col_indices[4]-1].values.tolist()
            })
            
            column_config = {
                "المشروع": st.column_config.TextColumn("🏗️ المشروع", disabled=True),
                "وارد العملاء": st.column_config.TextColumn("📥 وارد عملاء"),
                "صادر العملاء": st.column_config.TextColumn("📤 صادر عملاء"),
                "وارد التنفيذ": st.column_config.TextColumn("📥 وارد تنفيذ"),
                "صادر التنفيذ": st.column_config.TextColumn("📤 صادر تنفيذ"),
                "الرصيد": st.column_config.TextColumn("⚖️ الرصيد الحالي")
            }
        else:
            # النظام العادي لبقية الأقسام (إنجاز، معوقات، حالة)
            col_indices = [col_idx_main + 1, col_idx_main + 2, col_idx_main + 3]
            
            display_df = pd.DataFrame({
                "المشروع": project_names,
                "ما تم انجازه خلال الأسبوع": df_raw.iloc[2:, col_indices[0]-1].values.tolist(),
                "المعوقات والمشاكل": df_raw.iloc[2:, col_indices[1]-1].values.tolist(),
                "حالة الاتحاد": df_raw.iloc[2:, col_indices[2]-1].values.tolist()
            })
            
            column_config = {
                "المشروع": st.column_config.TextColumn("🏗️ المشروع", disabled=True),
                "ما تم انجازه خلال الأسبوع": st.column_config.TextColumn("✅ الموقف الحالي"),
                "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات"),
                "حالة الاتحاد": st.column_config.SelectboxColumn(
                    "📊 الحالة", 
                    options=["🟢 مكتمل", "🔵 قيد التنفيذ", "🟠 بانتظار مستندات", "🔴 متوقف / معلق"]
                )
            }

        # --- شريط الخيارات الجانبي ---
        with st.sidebar:
            st.header("📤 خيارات الإكسيل")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button(f"⬇️ تحميل نموذج {selected_section}", buffer.getvalue(), f"{selected_section}.xlsx")
            
            st.divider()
            update_method = "يدوي"
            uploaded_file = st.file_uploader("رفع ملف إكسيل", type=["xlsx"])
            if uploaded_file:
                excel_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                for col in display_df.columns[1:]: # تحديث كل الأعمدة عدا اسم المشروع
                    display_df[col] = excel_df[col].values[:len(display_df)]
                update_method = "ملف إكسيل"
                st.sidebar.success("✅ تم دمج البيانات")

        # --- محرر البيانات التفاعلي ---
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            height=500
        )

        st.divider()

        if st.button(f"🚀 حفظ بيانات {selected_section}", type="primary", use_container_width=True):
            updates = []
            for i, row in edited_df.iterrows():
                target_row = i + 4
                for idx, col_name in enumerate(display_df.columns[1:]):
                    updates.append({
                        "row": target_row, 
                        "col": col_indices[idx], 
                        "val": str(row[col_name]).strip()
                    })
            
            if updates:
                with st.spinner("جاري التحديث..."):
                    res = requests.post(SCRIPT_URL, data=json.dumps({"updates": updates}), timeout=60)
                    if "Success" in res.text:
                        send_telegram_msg(selected_section, update_method)
                        st.success("✅ تم الحفظ بنجاح.")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()

except Exception as e:
    st.error(f"⚠️ خطأ في النظام: {e}")
