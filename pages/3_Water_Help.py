import streamlit as st
from datetime import datetime
import pandas as pd
import os
from PIL import Image
import matplotlib.pyplot as plt
from openai import OpenAI

# ✅ Initialize OpenAI with env variable
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.set_page_config(page_title="Report a Water Source", layout="wide")

# Optional: Global style matching main app
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f8fcfd;
    }
    .stButton > button {
        background-color: #00acc1;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚰 Report a Water Source")
st.markdown("""
Help your community by sharing information about local water sources. 
This tool is for awareness only — we do not verify the safety of any water.
""")

IMAGE_DIR = "uploaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

if "reports" not in st.session_state:
    st.session_state.reports = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def update_key():
    st.session_state.uploader_key += 1

def load_data():
    return pd.DataFrame(st.session_state.reports)

# Tabs
report_tab, gallery_tab, table_tab, trends_tab, ai_analysis_tab = st.tabs([
    "📋 Report", "🖼️ Gallery", "📊 Tabular View", "📈 Community Trends", "🤖AI Analysis"
])

with report_tab:
    st.header("Submit a Water Report or Upload a CSV")

    uploaded_file = st.file_uploader(
        "📤 Upload a CSV file to add reports",
        type=["csv"],
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            required_columns = ["timestamp", "address", "zipcode", "description", "concerns", "type", "used", "symptoms", "alert", "photo_path"]
            missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
            if missing_columns:
                st.error(f"Missing columns: {', '.join(missing_columns)}")
            else:
                uploaded_df["timestamp"] = pd.to_datetime(uploaded_df["timestamp"], errors="coerce")
                st.session_state.reports.extend(uploaded_df.to_dict(orient="records"))
                st.success("✅ CSV uploaded and merged successfully!")
                update_key()
        except Exception as e:
            st.error(f"Error processing uploaded CSV: {e}")

    with st.form("water_report_form"):
        st.subheader("🗺️ Location Details")
        address = st.text_input("Address or general location", placeholder="123 Riverside Blvd, City, State")
        zipcode = st.text_input("Zip Code", placeholder="Enter zip code")
        photo = st.file_uploader("📷 Upload a photo (optional)", type=["jpg", "jpeg", "png"])
        description = st.text_area("📝 Description", max_chars=300)
        concerns = st.multiselect("🚩 Observed issues:", ["Discoloration", "Foul smell", "Foam", "Bugs", "Industrial area", "Trash nearby"])
        source_type = st.selectbox("🧭 Source Type", ["Faucet", "River/Stream", "Pipe Leak", "Fountain", "Rainwater Pool", "Other"])
        used = st.radio("Did you use this water?", ["Yes", "No"])
        symptoms = st.text_input("Any symptoms after use? (optional)")
        alert_others = st.checkbox("Send community alert")
        submitted = st.form_submit_button("Submit Report")

        if submitted:
            photo_path = None
            if photo:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.name}"
                photo_path = os.path.join(IMAGE_DIR, filename)
                with open(photo_path, "wb") as f:
                    f.write(photo.getbuffer())

            report = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "address": address,
                "zipcode": zipcode,
                "description": description,
                "concerns": ", ".join(concerns),
                "type": source_type,
                "used": used,
                "symptoms": symptoms,
                "alert": alert_others,
                "photo_path": photo_path,
            }
            st.session_state.reports.append(report)
            st.success("✅ Your report has been submitted. Thank you!")

with gallery_tab:
    st.header("🖼️ Community Gallery of Reports")
    df = pd.DataFrame(st.session_state.reports)
    if not df.empty:
        df['zipcode'] = df['zipcode'].astype(str)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        selected_zip = st.selectbox("Filter by ZIP Code (optional):", ["All"] + sorted(df['zipcode'].dropna().unique()))
        if selected_zip != "All":
            df = df[df['zipcode'] == selected_zip]

        sort_option = st.radio("Sort by:", ["Newest First", "Oldest First"], horizontal=True)
        df = df.sort_values(by='timestamp', ascending=(sort_option == "Oldest First"))

        view_option = st.radio("Choose view:", ["Grid View", "Detailed View"], horizontal=True)
        reports = df.to_dict(orient='records')

        if view_option == "Grid View":
            rows = [reports[i:i + 3] for i in range(0, len(reports), 3)]
            for row in rows:
                cols = st.columns(len(row))
                for col, report in zip(cols, row):
                    with col:
                        st.markdown(f"**📍 {report['address']}**")
                        st.markdown(f"🕒 {report['timestamp']}")
                        if report.get("photo_path") and os.path.exists(report["photo_path"]):
                            st.image(report["photo_path"], use_container_width=True)
                        st.markdown(f"**Type:** {report['type']} | **Used:** {report['used']}")
                        if report['symptoms']:
                            st.markdown(f"*Symptoms:* {report['symptoms']}")
        else:
            for report in reports:
                with st.expander(f"📍 {report['address']} ({report['timestamp']})"):
                    st.write(f"**Source Type:** {report['type']} | **Used:** {report['used']}")
                    if report['concerns']:
                        st.write(f"**Concerns:** {report['concerns']}")
                    if report['symptoms']:
                        st.write(f"**Symptoms after use:** {report['symptoms']}")
                    st.write(f"**Description:** {report['description']}")
                    if report.get("photo_path") and os.path.exists(report["photo_path"]):
                        st.image(report["photo_path"], caption="Reported Photo", use_container_width=True)
    else:
        st.info("No reports to display yet.")

with table_tab:
    df = pd.DataFrame(st.session_state.reports).drop(columns=["photo_path"], errors="ignore")
    st.subheader("📊 Tabular View of Reports")
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Download Reports CSV", df.to_csv(index=False).encode("utf-8"), "water_reports.csv")

with trends_tab:
    st.header("📈 Community Trends by Zip Code")
    data = load_data()
    if not data.empty:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['week'] = data['timestamp'].dt.to_period("W").astype(str)
        trend_data = data.groupby(['zipcode', 'week']).size().reset_index(name='report_count')
        selected_zip = st.selectbox("Select a Zip Code to View Trends", trend_data['zipcode'].unique())
        selected_data = trend_data[trend_data['zipcode'] == selected_zip]

        st.subheader(f"📍 Reports Over Time for Zip Code: {selected_zip}")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(selected_data['week'], selected_data['report_count'], marker='o')
        ax.set_xticks(selected_data['week'][::4])
        ax.set_xticklabels(selected_data['week'][::4], rotation=45)
        ax.set_title(f"Water Source Reports - {selected_zip}")
        ax.set_xlabel("Week")
        ax.set_ylabel("Reports")
        st.pyplot(fig)

        st.subheader("Top Zip Codes by Total Reports")
        top_zips = trend_data.groupby('zipcode')['report_count'].sum().sort_values(ascending=False).head(5)
        st.bar_chart(top_zips)
    else:
        st.info("Submit some reports to see trends.")

with ai_analysis_tab:
    st.header("🤖 AI Analysis of Reports")
    data = load_data()
    if not data.empty:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['week'] = data['timestamp'].dt.to_period("W").astype(str)
        trend_data = data.groupby(['zipcode', 'week']).size().reset_index(name='report_count')
        selected_zip = st.selectbox("Select a Zip Code to Analyze", trend_data['zipcode'].unique())
        if st.button("🔍 Analyze"):
            weekly_summary = trend_data[trend_data['zipcode'] == selected_zip].tail(12).to_dict(orient='records')
            system_prompt = f"""
            You are analyzing water quality reports for ZIP code {selected_zip}.
            Summarize the major issues, repeated trends, and any areas of concern.
            """
            user_prompt = f"Report data: {weekly_summary}"
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.5
                )
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"AI analysis failed: {e}")
    else:
        st.info("No data yet to analyze.")
