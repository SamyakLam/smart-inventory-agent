

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Smart Inventory Control Agent",
    page_icon="📦",
    layout="wide"
)

if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame({
        "Product": ["Laptop", "Mouse", "Keyboard", "Monitor", "Headphones", "Printer"],
        "Category": ["Electronics", "Accessories", "Accessories", "Electronics", "Accessories", "Electronics"],
        "Stock": [25, 8, 45, 5, 12, 3],
        "Price": [55000, 500, 1200, 12000, 2500, 15000],
        "Minimum Stock": [10, 10, 15, 8, 10, 5]
    })

df = st.session_state.inventory

st.title("📦 Smart Inventory Control Agent")
st.caption("AI-powered inventory monitoring and stock management")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Section",
    ["Dashboard", "Inventory", "Add Product"]
)

total_products = len(df)
total_stock = int(df["Stock"].sum())
low_stock = int((df["Stock"] <= df["Minimum Stock"]).sum())
inventory_value = int((df["Stock"] * df["Price"]).sum())

if page == "Dashboard":

    st.subheader("📊 Inventory Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Products", total_products)
    c2.metric("Total Stock Units", total_stock)
    c3.metric("Low Stock Alerts", low_stock)
    c4.metric("Inventory Value", f"₹{inventory_value:,}")

    left, right = st.columns(2)

    with left:
        st.subheader("Stock by Product")
        st.bar_chart(df.set_index("Product")["Stock"])

    with right:
        st.subheader("Low Stock Alerts")
        alerts = df[df["Stock"] <= df["Minimum Stock"]]

        if not alerts.empty:
            st.dataframe(alerts, use_container_width=True)
        else:
            st.success("All products have sufficient stock!")

    st.info(
        "Smart Suggestion: Review low-stock products "
        "and plan replenishment."
    )

elif page == "Inventory":

    st.subheader("Complete Inventory")

    search = st.text_input("Search product")

    filtered = df[
        df["Product"].str.contains(search, case=False)
    ]

    st.dataframe(filtered, use_container_width=True)

    for _, item in df.iterrows():
        if item["Stock"] <= item["Minimum Stock"]:
            st.warning(f"{item['Product']}: Low stock!")
        else:
            st.success(f"{item['Product']}: Stock available")

elif page == "Add Product":

    st.subheader("Add New Product")

    with st.form("product_form"):

        name = st.text_input("Product Name")

        category = st.selectbox(
            "Category",
            ["Electronics", "Accessories", "Other"]
        )

        stock = st.number_input("Stock Quantity", min_value=0)
        price = st.number_input("Price (₹)", min_value=0)
        minimum = st.number_input(
            "Minimum Stock Level", min_value=0, value=5
        )

        submitted = st.form_submit_button("Add Product")

        if submitted:
            if not name.strip():
                st.error("Enter a product name.")
            elif name in df["Product"].values:
                st.error("Product already exists.")
            else:
                new_product = pd.DataFrame([{
                    "Product": name,
                    "Category": category,
                    "Stock": int(stock),
                    "Price": int(price),
                    "Minimum Stock": int(minimum)
                }])

                st.session_state.inventory = pd.concat(
                    [df, new_product],
                    ignore_index=True
                )

                st.success("Product added successfully!")
                st.rerun()

st.divider()
st.caption("Smart Inventory Control Agent | Academic Project")
