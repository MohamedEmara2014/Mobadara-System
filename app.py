import streamlit as st
import pandas as pd
import requests
import json
import time
import io

# --- 1. إعدادات الأمان والتواصل (تليجرام) ---
TELEGRAM_TOKEN = "8574934082:AAFaRPpZT8a86wGLKb8C_ZqLR3jZ1xx7Gt0"
TELEGRAM_CHAT_ID = "303528498" 

def send_telegram_msg(section_name, method="يدوي"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        text = (
            f"🏗️ **تنبيه تحديث جديد**\n\n"
            f"قام قسم: \n📍 *{section_name}*\n\n"
            f"باعتماد وتصدير البيانات الآن عبر (تحديث {method}). ✅"
        )
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# --- 2. إعدادات واجهة التطبيق ---
st.set_page_config(page_title="التقرير اليومي لمتابعة المبادرة", layout="wide")

# الرابط الجديد الذي زودتني به
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyvNeUALnqFg-vv8LkLhb1ND-OYl-2xdMCY95VFevp4130MSHMlP3781h1Q-pOy0nei/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YDgqz1oi8Yi56DFFp03LlMWhmJxo1MeuSN_2hGSB2EM/export?format=csv"

st.title("📂 التقرير اليومي لمتابعة المبادرة")

try:
    # 3. جلب البيانات من جوجل شيتس
    df_raw = pd.read_csv(SHEET_CSV_URL, dtype=str).fillna("")
    all_cols = df_raw.columns
    sections = [all_cols[i] for i in range(1, len(all_cols), 2) if "Unnamed" not in all_cols[i]]
    
    # 4. اختيار القسم
    selected_section = st.selectbox("حدد القسم الخاص بك واضغط اعتماد وتصدير البيانات أخر الصفحة", sections)
    
    col_idx_done = list(df_raw.columns).index(selected_section) + 1
    col_idx_issues = col_idx_done + 1 

    project_names = df_raw.iloc[2:, 0].values.tolist()
    current_done_values = df_raw.iloc[2:, col_idx_done - 1].values.tolist()
    current_issues_values = df_raw.iloc[2:, col_idx_issues - 1].values.tolist()

    display_df = pd.DataFrame({
        "اسم المشروع": project_names,
        "ما تم إنجازه": current_done_values,
        "المعوقات والمشاكل": current_issues_values
    })

    # --- 5. ركن الملفات (تحميل ورفع) في الشريط الجانبي ---
    st.sidebar.header("📂 إدارة ملفات الإكسيل")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        display_df.to_excel(writer, index=False, sheet_name='التقرير')
    
    st.sidebar.download_button(
        label="⬇️ تحميل نموذج الإكسيل الفارغ",
        data=buffer.getvalue(),
        file_name=f"نموذج_تقرير_{selected_section}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.sidebar.divider()

    uploaded_file = st.sidebar.file_uploader("📤 ارفع الملف المكتمل هنا", type=["xlsx"])
    
    update_method = "يدوي"
    if uploaded_file is not None:
        try:
            excel_data = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
            if len(excel_data) >= len(project_names):
                display_df["ما تم إنجازه"] = excel_data.iloc[:len(project_names), 1].values
                display_df["المعوقات والمشاكل"] = excel_data.iloc[:len(project_names), 2].values
                st.sidebar.success("✅ تم تحديث الجدول من الملف!")
                update_method = "ملف إكسيل"
            else:
                st.sidebar.error("❌ عدد الصفوف في الملف غير مطابق.")
        except Exception as ex:
            st.sidebar.error(f"⚠️ خطأ في القراءة: {ex}")

    # 6. عرض محرر البيانات
    edited_df = st.data_editor(
        display_df,
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

    # 7. زر الاعتماد والإرسال (باستخدام POST لتجنب خطأ 400)
    if st.button(f"🚀 اعتماد وتصدير بيانات {selected_section}", type="primary", use_container_width=True):
        updates_to_send = []
        for i in range(len(edited_df)):
            val_done = str(edited_df.iloc[i, 1]).strip()
            val_issues = str(edited_df.iloc[i, 2]).strip()
            target_row = i + 4
            updates_to_send.append({"row": target_row, "col": col_idx_done, "val": val_done})
            updates_to_send.append({"row": target_row, "col": col_idx_issues, "val": val_issues})
        
        if updates_to_send:
            with st.spinner("جاري المزامنة عبر POST وإرسال الإشعار..."):
                # تحويل البيانات إلى JSON لإرسالها في جسم الطلب
                payload = json.dumps({"updates": updates_to_send})
                
                # استخدام POST بدلاً من GET لتجنب حدود طول الرابط
                response = requests.post(SCRIPT_URL, data=payload, timeout=60)
                
                if response.status_code == 200 and "Success" in response.text:
                    send_telegram_msg(selected_section, update_method)
                    st.success("✅ تم حفظ البيانات بنجاح!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ فشل الاتصال: {response.status_code}")
                    st.code(response.text) # سيظهر لك تفاصيل رد الخادم
        else:
            st.warning("⚠️ لا توجد بيانات لإرسالها.")

except Exception as e:
    st.error(f"⚠️ خطأ في النظام: {e}")
