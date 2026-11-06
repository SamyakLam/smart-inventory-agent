import sqlite3
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import streamlit as st

DB_PATH = Path("inventory.db")

st.set_page_config(
    page_title="NEXUS | Smart Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#08111f; --panel:#101d30; --line:#20334d; --muted:#91a4bd; --blue:#55a8ff; }
.stApp { background: radial-gradient(circle at 75% 0%, #142b49 0%, #08111f 42%); color:#edf4ff; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif; letter-spacing:-.4px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1b2d,#091321); border-right:1px solid #20334d; }
[data-testid="stSidebar"] * { color:#eaf2ff; }
.block-container { padding-top:2rem; padding-bottom:3rem; max-width:1500px; }
.hero { padding:24px 26px; border:1px solid #294564; border-radius:20px;
        background:linear-gradient(115deg,rgba(25,61,101,.92),rgba(15,29,48,.92));
        box-shadow:0 14px 40px rgba(0,0,0,.18); margin-bottom:20px; }
.eyebrow { color:#83c3ff; text-transform:uppercase; letter-spacing:2px; font-size:11px; font-weight:700; }
.hero-title { font-family:'Space Grotesk'; font-size:32px; font-weight:700; margin:5px 0 4px; color:#f4f8ff; }
.hero-sub { color:#b4c6dc; font-size:14px; }
.kpi { background:linear-gradient(145deg,#142842,#0e1a2b); border:1px solid #284360;
       border-radius:16px; padding:18px 19px; min-height:118px; }
.kpi-label { color:#9db2cc; font-size:12px; font-weight:600; }
.kpi-value { color:#f3f8ff; font-family:'Space Grotesk'; font-size:27px; font-weight:700; margin-top:9px; }
.kpi-note { color:#72c5aa; font-size:11px; margin-top:3px; }
.section-card { background:rgba(16,29,48,.82); border:1px solid #203852; border-radius:16px; padding:18px; }
.small-muted { color:#91a4bd; font-size:12px; }
div[data-testid="stMetric"] { background:transparent; }
.stButton>button, .stDownloadButton>button { border-radius:10px; border:1px solid #3974aa; background:#1763a6; color:white; font-weight:600; }
.stButton>button:hover, .stDownloadButton>button:hover { background:#247dc9; border-color:#69b8ff; color:white; }
div[data-testid="stDataFrame"] { border:1px solid #243b56; border-radius:12px; overflow:hidden; }
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { border-radius:9px; }
hr { border-color:#20334d; }
</style>
""", unsafe_allow_html=True)

# ---------- Database ----------
def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL COLLATE NOCASE UNIQUE,
            category TEXT NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0,
            min_stock INTEGER NOT NULL DEFAULT 5,
            daily_usage REAL NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            change_qty INTEGER NOT NULL,
            reason TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            seed = [
                ("Laptop","Electronics",25,55000,10,0.5),
                ("Mouse","Accessories",8,500,10,1.2),
                ("Keyboard","Accessories",45,1200,15,1.0),
                ("Monitor","Electronics",5,12000,8,0.3),
                ("Headphones","Accessories",12,2500,10,0.6),
                ("Printer","Electronics",3,15000,5,0.2),
            ]
            now = datetime.now().isoformat(timespec="seconds")
            conn.executemany("""INSERT INTO products
                (product,category,stock,price,min_stock,daily_usage,updated_at)
                VALUES (?,?,?,?,?,?,?)""", [(*r, now) for r in seed])
        conn.commit()

def load_products():
    with connect() as conn:
        return pd.read_sql_query("""
            SELECT id, product AS Product, category AS Category, stock AS Stock,
                   price AS Price, min_stock AS 'Minimum Stock',
                   daily_usage AS 'Daily Usage'
            FROM products ORDER BY product
        """, conn)

def add_movement(product_id, change_qty, reason, note=""):
    with connect() as conn:
        conn.execute("""INSERT INTO movements
            (product_id,change_qty,reason,note,created_at) VALUES (?,?,?,?,?)""",
            (product_id, change_qty, reason, note, datetime.now().isoformat(timespec="seconds")))
        conn.execute("""UPDATE products SET stock=stock+?, updated_at=? WHERE id=?""",
            (change_qty, datetime.now().isoformat(timespec="seconds"), product_id))
        conn.commit()

init_db()
df = load_products()

# ---------- Helpers ----------
def money(value):
    return f"₹{value:,.0f}"

def kpi(label, value, note, icon):
    st.markdown(f"""
    <div class="kpi">
      <div class="kpi-label">{icon}&nbsp;&nbsp;{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-note">{note}</div>
    </div>""", unsafe_allow_html=True)

def stock_status(row):
    if row["Stock"] <= 0:
        return "Out of stock"
    if row["Stock"] <= row["Minimum Stock"]:
        return "Low stock"
    return "Healthy"

def get_suggestions(data):
    tips = []
    for _, r in data.iterrows():
        days = (r["Stock"] / r["Daily Usage"]) if r["Daily Usage"] > 0 else None
        if r["Stock"] <= 0:
            tips.append((r["Product"], "Urgent", "Out of stock — replenish before accepting new demand."))
        elif r["Stock"] <= r["Minimum Stock"]:
            target = max(int(r["Minimum Stock"] * 2), int(r["Daily Usage"] * 30))
            qty = max(target - int(r["Stock"]), 0)
            tips.append((r["Product"], "High", f"Below minimum level. Suggested replenishment: {qty} units."))
        elif days is not None and days <= 14:
            target = max(int(r["Minimum Stock"] * 2), int(r["Daily Usage"] * 30))
            qty = max(target - int(r["Stock"]), 0)
            tips.append((r["Product"], "Watch", f"Estimated stock cover: {days:.1f} days. Consider ordering {qty} units."))
    return tips

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 📦 NEXUS")
    st.caption("SMART INVENTORY CONTROL")
    st.markdown("---")
    page = st.radio("WORKSPACE", [
        "Overview", "Inventory", "Add Product", "Stock Movement",
        "AI Insights", "Reports"
    ], label_visibility="visible")
    st.markdown("---")
    st.markdown("**System status**")
    st.success("Inventory database connected")
    st.caption("Academic project • Demo environment")

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">Inventory intelligence platform</div>
  <div class="hero-title">Smart Inventory Control Agent</div>
  <div class="hero-sub">Monitor stock, spot risks early, and make smarter replenishment decisions.</div>
</div>
""", unsafe_allow_html=True)

# Refresh after page action
df = load_products()
total_products = len(df)
total_stock = int(df["Stock"].sum()) if not df.empty else 0
low_count = int(((df["Stock"] <= df["Minimum Stock"]) & (df["Stock"] > 0)).sum()) if not df.empty else 0
out_count = int((df["Stock"] <= 0).sum()) if not df.empty else 0
total_value = float((df["Stock"] * df["Price"]).sum()) if not df.empty else 0

# ---------- Overview ----------
if page == "Overview":
    st.subheader("Your inventory at a glance")
    cols = st.columns(4)
    with cols[0]: kpi("TOTAL PRODUCTS", f"{total_products}", "Items being tracked", "📦")
    with cols[1]: kpi("STOCK UNITS", f"{total_stock:,}", "Units currently available", "🧮")
    with cols[2]: kpi("LOW / OUT ALERTS", f"{low_count + out_count}", f"{low_count} low • {out_count} out of stock", "⚠️")
    with cols[3]: kpi("INVENTORY VALUE", money(total_value), "Based on current stock × price", "💰")

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("### Stock distribution")
        if not df.empty:
            chart_df = df[["Product", "Stock"]].set_index("Product")
            st.bar_chart(chart_df, use_container_width=True, height=300)
        else:
            st.info("Add products to see stock analytics.")
    with right:
        st.markdown("### Stock health")
        healthy = int(sum(stock_status(r) == "Healthy" for _, r in df.iterrows()))
        health_df = pd.DataFrame({"Status":["Healthy","Low stock","Out of stock"],
                                  "Products":[healthy,low_count,out_count]}).set_index("Status")
        st.bar_chart(health_df, use_container_width=True, height=300)

    st.markdown("### Needs attention")
    alerts = df[(df["Stock"] <= df["Minimum Stock"])]
    if alerts.empty:
        st.success("All products are above their minimum stock level.")
    else:
        view = alerts[["Product","Category","Stock","Minimum Stock","Price"]].copy()
        view["Status"] = view.apply(lambda r: "OUT" if r["Stock"] <= 0 else "LOW", axis=1)
        st.dataframe(view, hide_index=True, use_container_width=True)
    suggestions = get_suggestions(df)
    if suggestions:
        st.info("Smart suggestion: " + suggestions[0][0] + " — " + suggestions[0][2])
    else:
        st.success("No immediate replenishment actions are required.")

# ---------- Inventory ----------
elif page == "Inventory":
    st.subheader("Product inventory")
    c1, c2 = st.columns([2,1])
    search = c1.text_input("Search by product name", placeholder="e.g. Laptop")
    categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
    category = c2.selectbox("Category", categories)
    filtered = df.copy()
    if search:
        filtered = filtered[filtered["Product"].str.contains(search, case=False, na=False)]
    if category != "All":
        filtered = filtered[filtered["Category"] == category]
    st.caption(f"Showing {len(filtered)} of {len(df)} products")
    display = filtered.copy()
    display["Status"] = display.apply(stock_status, axis=1)
    st.dataframe(display[["Product","Category","Stock","Price","Minimum Stock","Daily Usage","Status"]],
                 hide_index=True, use_container_width=True)

    st.markdown("### Edit or remove a product")
    if not df.empty:
        selected = st.selectbox("Choose product", df["Product"].tolist())
        row = df[df["Product"] == selected].iloc[0]
        with st.form("edit_product_form"):
            a,b,c = st.columns(3)
            new_name = a.text_input("Product name", value=row["Product"])
            new_category = b.text_input("Category", value=row["Category"])
            new_price = c.number_input("Price (₹)", min_value=0.0, value=float(row["Price"]), step=100.0)
            d,e,f = st.columns(3)
            new_stock = d.number_input("Stock quantity", min_value=0, value=int(row["Stock"]), step=1)
            new_min = e.number_input("Minimum stock", min_value=0, value=int(row["Minimum Stock"]), step=1)
            new_usage = f.number_input("Average daily usage", min_value=0.0, value=float(row["Daily Usage"]), step=0.1)
            save = st.form_submit_button("Save changes")
        if save:
            try:
                with connect() as conn:
                    conn.execute("""UPDATE products SET product=?,category=?,stock=?,price=?,
                        min_stock=?,daily_usage=?,updated_at=? WHERE id=?""",
                        (new_name.strip(),new_category.strip(),int(new_stock),float(new_price),
                         int(new_min),float(new_usage),datetime.now().isoformat(timespec="seconds"),int(row["id"])))
                    conn.commit()
                st.success("Product updated.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("That product name is already in use.")
        if st.button("Delete selected product", type="secondary"):
            with connect() as conn:
                conn.execute("DELETE FROM movements WHERE product_id=?", (int(row["id"]),))
                conn.execute("DELETE FROM products WHERE id=?", (int(row["id"]),))
                conn.commit()
            st.success(f"{selected} deleted.")
            st.rerun()

# ---------- Add Product ----------
elif page == "Add Product":
    st.subheader("Register a new product")
    with st.form("add_product_form", clear_on_submit=True):
        a,b = st.columns(2)
        name = a.text_input("Product name *", placeholder="e.g. Wireless Speaker")
        category = b.selectbox("Category", ["Electronics","Accessories","Office Supplies","Other"])
        c,d,e = st.columns(3)
        stock = c.number_input("Opening stock", min_value=0, step=1)
        price = d.number_input("Unit price (₹)", min_value=0.0, step=100.0)
        minimum = e.number_input("Minimum stock level", min_value=0, value=5, step=1)
        usage = st.number_input("Estimated average daily usage (units)", min_value=0.0, value=1.0, step=0.1)
        submitted = st.form_submit_button("＋ Add product", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Please enter a product name.")
        else:
            try:
                with connect() as conn:
                    conn.execute("""INSERT INTO products
                        (product,category,stock,price,min_stock,daily_usage,updated_at)
                        VALUES (?,?,?,?,?,?,?)""",
                        (name.strip(),category,int(stock),float(price),int(minimum),float(usage),
                         datetime.now().isoformat(timespec="seconds")))
                    conn.commit()
                st.success(f"{name} added successfully.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("A product with that name already exists.")

# ---------- Stock Movement ----------
elif page == "Stock Movement":
    st.subheader("Record stock movement")
    st.write("Use this page whenever stock is received, sold, or corrected. Every movement is recorded in the activity log.")
    if not df.empty:
        with st.form("movement_form"):
            product = st.selectbox("Product", df["Product"].tolist())
            movement_type = st.radio("Movement type", ["Stock received","Stock issued / sold","Correction"], horizontal=True)
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
            note = st.text_input("Note (optional)", placeholder="e.g. Supplier delivery or customer order")
            submit_move = st.form_submit_button("Record movement")
        if submit_move:
            selected_row = df[df["Product"] == product].iloc[0]
            change = int(quantity) if movement_type == "Stock received" else -int(quantity)
            if movement_type == "Correction":
                new_value = int(quantity)
                change = new_value - int(selected_row["Stock"])
            if int(selected_row["Stock"]) + change < 0:
                st.error("This movement would make stock negative. Check the quantity.")
            else:
                add_movement(int(selected_row["id"]), change, movement_type, note)
                st.success("Stock movement recorded.")
                st.rerun()
    with connect() as conn:
        history = pd.read_sql_query("""
            SELECT p.product AS Product, m.change_qty AS 'Quantity Change',
                   m.reason AS Type, m.note AS Note, m.created_at AS 'Date & Time'
            FROM movements m JOIN products p ON p.id=m.product_id
            ORDER BY m.id DESC LIMIT 50
        """, conn)
    st.markdown("### Recent activity")
    if history.empty:
        st.caption("No stock movements recorded yet.")
    else:
        st.dataframe(history, hide_index=True, use_container_width=True)

# ---------- AI Insights ----------
elif page == "AI Insights":
    st.subheader("Inventory intelligence")
    st.caption("Decision-support suggestions generated from stock levels, minimum thresholds and estimated daily usage.")
    tips = get_suggestions(df)
    if not tips:
        st.success("Your current stock levels look healthy. No urgent actions detected.")
    else:
        for product, priority, message in tips:
            if priority in ("Urgent","High"):
                st.warning(f"**{priority} priority — {product}**  \n{message}")
            else:
                st.info(f"**{priority} priority — {product}**  \n{message}")
    st.markdown("### Stock cover forecast")
    forecast = df.copy()
    forecast["Estimated days remaining"] = forecast.apply(
        lambda r: round(r["Stock"] / r["Daily Usage"], 1) if r["Daily Usage"] > 0 else None, axis=1)
    forecast["Suggested order (30-day target)"] = forecast.apply(
        lambda r: max(int(max(r["Minimum Stock"]*2, r["Daily Usage"]*30) - r["Stock"]),0), axis=1)
    st.dataframe(forecast[["Product","Stock","Daily Usage","Estimated days remaining",
                           "Minimum Stock","Suggested order (30-day target)"]],
                 hide_index=True, use_container_width=True)
    st.caption("Forecasts are estimates based on the daily usage values entered for each product. They are not trained machine-learning predictions.")

# ---------- Reports ----------
elif page == "Reports":
    st.subheader("Reports & exports")
    report = df.copy()
    report["Stock Value"] = report["Stock"] * report["Price"]
    report["Status"] = report.apply(stock_status, axis=1)
    st.dataframe(report[["Product","Category","Stock","Price","Stock Value","Minimum Stock","Status"]],
                 hide_index=True, use_container_width=True)
    csv = report.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download inventory report (CSV)", data=csv,
                       file_name=f"inventory_report_{date.today().isoformat()}.csv",
                       mime="text/csv")
    st.metric("Total inventory value", money(float(report["Stock Value"].sum())))

st.markdown("---")
st.caption("NEXUS Smart Inventory Control Agent • Academic demonstration build")


