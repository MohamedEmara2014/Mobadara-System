import streamlit as st
import pandas as pd
import requests
import json
import time

# --- إعدادات التليجرام المحدثة ---
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

def send_telegram_msg(section_name):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        text = f"🏗️ **تنبيه تحديث جديد**\n\nقام قسم: \n📍 *{section_name}*\n\nباعتماد وتصدير البيانات الآن عبر المنصة الرقمية. ✅"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": text, 
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload)
    except Exception as e:
        # لضمان عدم تعطل التطبيق في حال فشل إرسال الإشعار
        pass

# ----------------------------------------------------

st.set_page_config(page_title="التقرير اليومي للمبادرة", layout="wide")

# الروابط الأصلية الخاصة بك
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwE9XcpdsumPSoGJ0G_apcTbnRLj1zLPPVR8MVZRGANBwVGYtn0vavLJTabfY_Fda0/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # جلب البيانات من الشيت
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    # واجهة اختيار القسم (العبارة المطلوبة)
    selected_section = st.selectbox("حدد القسم الخاص بك واضغط اعتماد وتصدير البيانات أخر الصفحة", sections)
    
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    # عرض تاريخ آخر تحديث
    last_update_val = df_raw.iloc[0, col_idx_done - 1]
    if "تحديث:" in str(last_update_val):
        st.success(f"📅 {last_update_val}")

    # جلب البيانات الحالية (الإنجاز والمعوقات) من الصف الرابع
    project_names = df_raw.iloc[2:, 0].values.tolist()
    current_done_values = df_raw.iloc[2:, col_idx_done - 1].values.tolist()
    current_issues_values = df_raw.iloc[2:, col_idx_issues - 1].values.tolist()

    # بناء الجدول بالقيم المسترجعة
    input_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": current_done_values,
        "المعوقات والمشاكل": current_issues_values
    })

    # محرر البيانات
    edited_df = st.data_editor(
        input_df,
        key=f"editor_{selected_section}",
        column_config={
            "اسم المشروع": st.column_config.TextColumn("🏗️ اسم المشروع", disabled=True),
            "ما تم إنجازه": st.column_config.TextColumn("✅ ما تم إنجازه اليوم", width="large"),
            "المعوقات والمشاكل": st.column_config.TextColumn("⚠️ المعوقات والمشاكل", width="large")
        },
        hide_index=True,
        use_container_width=True,
        height=600 
    )

    st.divider()

    # زر الاعتماد والتصدير
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        for i in range(len(edited_df)):
            val_done = str(edited_df.iloc[i, 1]).strip()
            val_issues = str(edited_df.iloc[i, 2]).strip()
            
            # تحديد الصف المستهدف (يبدأ من الصف 4 في جوجل شيتس)
            target_row = i + 4
            
            updates_to_send.append({"row": target_row, "col": col_idx_done, "val": val_done})
            updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": val_issues})
        
        if updates_to_send:
            with st.spinner("جاري حفظ التحديثات وإرسال الإشعار لسيادتكم..."):
                params = {"updates": json.dumps(updates_to_send)}
                response = requests.get(SCRIPT_URL, params=params)
                
                if response.status_code == 200:
                    # إرسال إشعار التليجرام الفوري
                    send_telegram_msg(selected_section)
                    
                    st.success("✅ تم حفظ البيانات وإرسال إشعار فوري لتليجرام سيادتكم!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ فشل الاتصال بخادم جوجل.")
        else:
            st.warning("⚠️ لا توجد بيانات كافية للإرسال.")

except Exception as e:
    st.error(f"حدث خطأ في النظام: {e}")
