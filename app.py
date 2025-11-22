import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

A = 686.4385618977473
B = 28.85390081777927

# --------------------
# Helper Function
# --------------------
def calculate_behavior_score(pd_value):
    return A - B * np.log(pd_value / (1 - pd_value))

# --------------------
# Streamlit UI Design
# --------------------
st.set_page_config(
    page_title="Behavior Scorecard Dashboard",
    layout="wide",
    page_icon="📊"
)

# Header
st.markdown("""
    <h1 style='text-align:center; color:#2C3E50;'>
        📊 Behavior Scorecard Dashboard
    </h1>
    <h4 style='text-align:center; color:#7F8C8D;'>
        Machine Learning Based Credit Risk Insights
    </h4>
""", unsafe_allow_html=True)

# File Upload Section
uploaded_file = st.file_uploader("📁 Upload your PD File (CSV with column: PD)", type=['csv'])

# ------------------------------------------------------------------------
#  CUSTOMER RISK INPUT FORM (SIDEBAR)
# ------------------------------------------------------------------------
st.sidebar.header("🧮 Customer Risk Predictor")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if "PD" not in df.columns:
        st.error("CSV must contain a 'PD' column!")
        st.stop()

    # These are all other available features
    feature_cols = [c for c in df.columns if c != "PD"]

    st.sidebar.subheader("Enter Customer Details")

    # dynamic form based on uploaded data
    user_inputs = {}
    for col in feature_cols:
        if df[col].dtype in ['float64', 'int64']:
            user_inputs[col] = st.sidebar.number_input(
                f"{col}", 
                float(df[col].min()), 
                float(df[col].max()),
                float(df[col].mean())
            )
        else:
            user_inputs[col] = st.sidebar.selectbox(
                f"{col}",
                options=df[col].unique()
            )

    if st.sidebar.button("Predict Risk"):
        # Dummy PD prediction logic (replace with ML model later)
        # Using simple heuristic: avg PD adjusted by numeric inputs
        pd_pred = df["PD"].mean()

        for num in [c for c in feature_cols if df[c].dtype != "object"]:
            pd_pred += (user_inputs[num] - df[num].mean()) * 0.0001

        pd_pred = max(min(pd_pred, 0.99), 0.01)

        behavior_score = calculate_behavior_score(pd_pred)

        if behavior_score < 580:
            risk = "High Risk"
        elif behavior_score < 700:
            risk = "Medium Risk"
        else:
            risk = "Low Risk"

        st.sidebar.success(f"""
        ### ✅ Prediction Result
        **Predicted PD:** {pd_pred:.3f}  
        **Behavior Score:** {behavior_score:.2f}  
        **Risk Category:** **{risk}**
        """)

# ------------------------------------------------------------------------
#  MAIN DASHBOARD SECTION
# ------------------------------------------------------------------------
if uploaded_file is not None:

    # Behavior Score Calculation
    df["Behavior_Score"] = df["PD"].apply(calculate_behavior_score)

    # Risk Labels
    def risk_category(score):
        if score < 580:
            return "High Risk"
        elif score < 700:
            return "Medium Risk"
        else:
            return "Low Risk"

    df["Risk_Category"] = df["Behavior_Score"].apply(risk_category)

    # KPIs
    avg_pd = df["PD"].mean()
    avg_score = df["Behavior_Score"].mean()
    high_risk = sum(df["Risk_Category"] == "High Risk")

    col1, col2, col3 = st.columns(3)
    col1.metric("📉 Average PD", f"{avg_pd:.3f}")
    col2.metric("⭐ Average Behavior Score", f"{avg_score:.2f}")
    col3.metric("⚠️ High Risk Customers", high_risk)

    st.markdown("### 🔹 PD Distribution")
    fig_pd = px.histogram(df, x="PD", nbins=10, color_discrete_sequence=["#FF8C00"])
    st.plotly_chart(fig_pd, use_container_width=True)

    st.markdown("### 🔹 Behavior Score Distribution (300–900)")
    fig_score = px.histogram(df, x="Behavior_Score", nbins=10, color_discrete_sequence=["#16A085"])
    st.plotly_chart(fig_score, use_container_width=True)

    st.markdown("### 🔹 PD vs Behavior Score")
    fig_scatter = px.scatter(
        df,
        x="PD",
        y="Behavior_Score",
        color="Risk_Category",
        color_discrete_map={
            "Low Risk": "#27AE60",
            "Medium Risk": "#F1C40F",
            "High Risk": "#E74C3C"
        }
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### 🔹 Download Scored Dataset")
    st.download_button(
        label="Download Results (CSV)",
        data=df.to_csv(index=False),
        file_name="behavior_scorecard_output.csv",
        mime="text/csv"
    )

else:
    st.info("Upload a CSV file to generate the scorecard dashboard.")

# Footer
st.markdown("""
<hr>
<p style='text-align:center; color:gray;'>
Developed by <b>Vaishnavi Desai— ML Credit Risk Project</b>
</p>
""", unsafe_allow_html=True)
