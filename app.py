

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# 1. PAGE SETUP
st.set_page_config(page_title="Interactive Price Chart", page_icon="📈", layout="wide")

# 2. TITLE & DESCRIPTION
st.title("📊 Interactive Price Analysis Tool")
st.markdown("""
Upload your CSV, toggle the **Moving Averages (SMA)** in the sidebar, and export your custom analysis.
""")

# 3. PDF GENERATION FUNCTION
def create_pdf(df, price_col, fig):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Interactive Price Analysis Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 725, f"Data Column: {price_col}")
    latest_val = df[price_col].iloc[-1]
    p.drawString(100, 710, f"Latest Value: {float(latest_val):,.2f}")

    # Capture the figure with all selected SMA lines
    try:
        img_bytes = fig.to_image(format="png", width=600, height=350)
        img_reader = ImageReader(io.BytesIO(img_bytes))
        p.drawImage(img_reader, 50, 330, width=500, height=300)
    except Exception as e:
        p.drawString(100, 450, f"(Chart image error: {e})")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 300, "Recent Data Summary:")
    p.setFont("Helvetica", 10)
    y_position = 280
    for i in range(1, 6):
        if i <= len(df):
            row = df.iloc[-i]
            date_str = row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
            text = f"Date: {date_str} | Price: {float(row[price_col]):,.2f}"
            p.drawString(120, y_position, text)
            y_position -= 18
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# 4. FILE UPLOADER
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        date_col = next((c for c in df.columns if 'Date' in c or 'Time' in c), None)
        price_col = next((c for c in df.columns if any(k in c for k in ['Price', 'Close', 'Val', 'Amt'])), None)

        if date_col and price_col:
            # Data Cleaning
            df[price_col] = df[price_col].astype(str).str.replace(',', '', regex=False).astype(float)
            df[date_col] = pd.to_datetime(df[date_col], format='mixed')
            df = df.sort_values(by=date_col)

            # --- SIDEBAR INTERACTION ---
            st.sidebar.header("Chart Settings")
            show_sma10 = st.sidebar.checkbox("10-day SMA", value=False)
            show_sma20 = st.sidebar.checkbox("20-day SMA", value=False)
            show_sma30 = st.sidebar.checkbox("30-day SMA", value=False)

            # --- PLOTTING WITH PLOTLY GRAPH OBJECTS ---
            fig = go.Figure()

            # Main Price Line
            fig.add_trace(go.Scatter(
                x=df[date_col], y=df[price_col],
                mode='lines', name=f'Original Price ({price_col})',
                line=dict(color='#00d1ff', width=2)
            ))

            # Add SMAs if selected
            if show_sma10:
                df['SMA10'] = df[price_col].rolling(window=10).mean()
                fig.add_trace(go.Scatter(x=df[date_col], y=df['SMA10'], name='10-day SMA', line=dict(color='green', width=1.5, dash='dot')))
            
            if show_sma20:
                df['SMA20'] = df[price_col].rolling(window=20).mean()
                fig.add_trace(go.Scatter(x=df[date_col], y=df['SMA20'], name='20-day SMA', line=dict(color='yellow', width=1.5, dash='dot')))
            
            if show_sma30:
                df['SMA30'] = df[price_col].rolling(window=30).mean()
                fig.add_trace(go.Scatter(x=df[date_col], y=df['SMA30'], name='30-day SMA', line=dict(color='red', width=1.5, dash='dot')))

            fig.update_layout(
                title=f"Trend Analysis: {price_col}",
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Price",
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- EXPORT SECTION ---
            st.write("---")
            st.subheader("Generate Report")
            if st.button("Prepare PDF for Download"):
                with st.spinner("Processing your custom report..."):
                    pdf_data = create_pdf(df, price_col, fig)
                    st.download_button(
                        label="💾 Download PDF Report",
                        data=pdf_data,
                        file_name="Price_Analysis_SMA.pdf",
                        mime="application/pdf"
                    )
        else:
            st.error("Missing Date or Price columns.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👆 Please upload a CSV file to begin.")
