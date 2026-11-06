"""NEXUS | Smart Inventory Control Agent
Run locally:  streamlit run app.py
"""
import math
import sqlite3
from datetime import datetime
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

# ------------------------------------------------------------------ config
st.set_page_config(
    page_title="NEXUS | Smart Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "inventory.db"
CUR = "₹"

ACCENT, OK, WARN, BAD, MUTED = "#38bdf8", "#34d399", "#fbbf24", "#f87171", "#8fa3c0"

SEED = [
    ("Keyboard", "Accessories", 45, 10, 1200),
    ("Laptop", "Electronics", 25, 5, 55000),
    ("Monitor", "Electronics", 5, 8, 12000),
    ("Mouse", "Accessories", 8, 10, 500),
    ("Printer", "Electronics", 3, 5, 15000),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#0a1020; --card:#0f1a30; --card2:#13223f; --line:#1f2f50;
  --text:#e6edf7; --muted:#8fa3c0; --accent:#38bdf8;
  --ok:#34d399; --warn:#fbbf24; --bad:#f87171;
}
html, body, .stApp, [class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:radial-gradient(1200px 600px at 15% -10%, #12306000 0%, #0a1020 60%), #0a1020;color:var(--text);}
.stApp{background-image:radial-gradient(900px 500px at 20% -5%, #11305f 0%, rgba(10,16,32,0) 70%);}
header[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:3rem;padding-bottom:3rem;max-width:1280px;}
section[data-testid="stSidebar"]{background:#0b1426;border-right:1px solid var(--line);}
section[data-testid="stSidebar"] .block-container{padding-top:2rem;}

/* brand */
.brand{display:flex;align-items:center;gap:12px;margin-bottom:2px;}
.brand-logo{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;
  font-size:20px;background:linear-gradient(135deg,#38bdf8,#6366f1);box-shadow:0 6px 18px rgba(56,189,248,.35);}
.brand-name{font-weight:800;font-size:1.25rem;letter-spacing:.04em;color:#fff;}
.brand-sub{font-size:.68rem;letter-spacing:.18em;color:var(--muted);margin:6px 0 0 50px;}
.side-label{font-size:.7rem;letter-spacing:.16em;color:var(--muted);font-weight:600;margin:1.2rem 0 .3rem;}
.side-divider{height:1px;background:var(--line);margin:1.2rem 0;}
.status-ok{background:rgba(52,211,153,.10);border:1px solid rgba(52,211,153,.35);color:#7ee9c0;
  padding:12px 14px;border-radius:12px;font-size:.85rem;font-weight:500;}
.side-foot{color:var(--muted);font-size:.75rem;margin-top:12px;}

/* sidebar nav radio -> menu look */
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:4px;}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  padding:9px 12px;border-radius:10px;border:1px solid transparent;width:100%;transition:all .15s;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(56,189,248,.08);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
  background:rgba(56,189,248,.14);border-color:rgba(56,189,248,.45);}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{display:none;}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{font-weight:500;font-size:.95rem;}

/* hero */
.hero{background:linear-gradient(135deg,#12315f 0%,#0f2347 55%,#0d1b36 100%);
  border:1px solid #234279;border-radius:20px;padding:26px 30px;margin-bottom:8px;
  box-shadow:0 10px 40px rgba(0,0,0,.35);}
.hero-eyebrow{font-size:.7rem;letter-spacing:.22em;color:var(--accent);font-weight:700;}
.hero-title{font-size:2rem;font-weight:800;color:#fff;margin:6px 0 6px;line-height:1.15;}
.hero-sub{color:#a9bddb;font-size:.95rem;}

.section{font-size:1.35rem;font-weight:700;color:#fff;margin:1.6rem 0 .8rem;}
.section small{font-size:.8rem;color:var(--muted);font-weight:500;margin-left:8px;}

/* KPI cards */
.kpi{background:linear-gradient(160deg,var(--card2),var(--card));border:1px solid var(--line);
  border-radius:16px;padding:18px 20px;height:100%;transition:transform .15s,border-color .15s;}
.kpi:hover{transform:translateY(-2px);border-color:#2c4577;}
.kpi-label{display:flex;gap:8px;align-items:center;font-size:.72rem;letter-spacing:.12em;
  color:var(--muted);font-weight:600;text-transform:uppercase;}
.kpi-value{font-size:2.1rem;font-weight:800;color:#fff;margin:10px 0 4px;}
.kpi-value.warn{color:var(--warn);} .kpi-value.bad{color:var(--bad);} .kpi-value.ok{color:var(--ok);}
.kpi-sub{font-size:.78rem;color:var(--ok);}

/* panels */
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:6px 10px;}

/* tables */
.tbl-wrap{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--card);}
.tbl{width:100%;border-collapse:collapse;font-size:.9rem;}
.tbl th{background:#0d1830;color:var(--muted);text-align:left;font-weight:600;font-size:.72rem;
  letter-spacing:.1em;text-transform:uppercase;padding:12px 16px;border-bottom:1px solid var(--line);}
.tbl td{padding:13px 16px;border-bottom:1px solid #16264a;color:var(--text);}
.tbl tr:last-child td{border-bottom:none;}
.tbl tbody tr:hover td{background:rgba(56,189,248,.05);}
.tbl td.num,.tbl th.num{text-align:right;}

/* pills */
.pill{display:inline-block;padding:3px 11px;border-radius:999px;font-size:.74rem;font-weight:600;border:1px solid;}
.pill.ok{color:var(--ok);background:rgba(52,211,153,.12);border-color:rgba(52,211,153,.35);}
.pill.warn{color:var(--warn);background:rgba(251,191,36,.12);border-color:rgba(251,191,36,.35);}
.pill.bad{color:var(--bad);background:rgba(248,113,113,.12);border-color:rgba(248,113,113,.35);}
.pill.info{color:var(--accent);background:rgba(56,189,248,.12);border-color:rgba(56,189,248,.35);}

/* insight cards */
.rec{background:linear-gradient(160deg,var(--card2),var(--card));border:1px solid var(--line);
  border-radius:14px;padding:14px 18px;margin-bottom:10px;}
.rec-title{font-weight:700;color:#fff;font-size:1.02rem;}
.rec-meta{color:var(--muted);font-size:.84rem;margin-top:4px;}
.rec-qty{color:var(--ok);font-weight:600;}

/* buttons / inputs */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button{
  background:linear-gradient(135deg,#2563eb,#38bdf8);color:#fff;border:none;border-radius:10px;
  font-weight:600;padding:.5rem 1.1rem;transition:filter .15s, transform .1s;}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover{
  filter:brightness(1.12);transform:translateY(-1px);color:#fff;}
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, .stNumberInput input, .stTextInput input{
  background:#0d1830 !important;border-color:var(--line) !important;border-radius:10px !important;}
[data-testid="stForm"]{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;}
[data-testid="stExpander"]{background:var(--card);border:1px solid var(--line);border-radius:14px;}
footer{visibility:hidden;}
</style>
"""

# ------------------------------------------------------------------ database
def run(sql, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall() if fetch else None
        conn.commit()
        return rows
    finally:
        conn.close()


def query_df(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def init_db():
    run("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL, stock INTEGER NOT NULL,
        min_stock INTEGER NOT NULL, price REAL NOT NULL)""")
    run("""CREATE TABLE IF NOT EXISTS movements(
        id INTEGER PRIMARY KEY AUTOINCREMENT, product TEXT NOT NULL,
        kind TEXT NOT NULL, qty INTEGER NOT NULL, note TEXT, ts TEXT NOT NULL)""")
    run("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, product TEXT NOT NULL,
        qty INTEGER NOT NULL, status TEXT NOT NULL, ts TEXT NOT NULL)""")
    if run("SELECT COUNT(*) FROM products", fetch=True)[0][0] == 0:
        conn = sqlite3.connect(DB_PATH)
        conn.executemany(
            "INSERT INTO products(name,category,stock,min_stock,price) VALUES(?,?,?,?,?)", SEED)
        conn.commit()
        conn.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def status_of(stock, min_stock):
    if stock <= 0:
        return "OUT"
    if stock < min_stock:
        return "LOW"
    return "HEALTHY"


def load_products():
    df = query_df("SELECT name, category, stock, min_stock, price FROM products ORDER BY name")
    df["status"] = [status_of(s, m) for s, m in zip(df["stock"], df["min_stock"])]
    df["value"] = df["stock"] * df["price"]
    return df


def log_movement(product, kind, qty, note=""):
    run("INSERT INTO movements(product,kind,qty,note,ts) VALUES(?,?,?,?,?)",
        (product, kind, qty, note, now()))


# ------------------------------------------------------------------ ui helpers
def flash(msg, kind="success"):
    st.session_state["flash"] = (kind, msg)


def show_flash():
    item = st.session_state.pop("flash", None)
    if item:
        getattr(st, item[0])(item[1])


def hero(eyebrow, title, sub):
    st.markdown(
        f'<div class="hero"><div class="hero-eyebrow">{eyebrow}</div>'
        f'<div class="hero-title">{title}</div><div class="hero-sub">{sub}</div></div>',
        unsafe_allow_html=True)


def section(title, small=""):
    extra = f"<small>{small}</small>" if small else ""
    st.markdown(f'<div class="section">{title}{extra}</div>', unsafe_allow_html=True)


def kpi(col, icon, label, value, sub, tone=""):
    col.markdown(
        f'<div class="kpi"><div class="kpi-label"><span>{icon}</span>{label}</div>'
        f'<div class="kpi-value {tone}">{value}</div><div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True)


def pill(status):
    cls, label = {
        "HEALTHY": ("ok", "Healthy"), "LOW": ("warn", "Low stock"), "OUT": ("bad", "Out of stock"),
    }[status]
    return f'<span class="pill {cls}">{label}</span>'


def html_table(rows, headers, num_cols=()):
    """rows: list of lists of ready-to-render HTML strings."""
    th = "".join(
        f'<th class="{"num" if h in num_cols else ""}">{escape(h)}</th>' for h in headers)
    body = ""
    for r in rows:
        tds = "".join(
            f'<td class="{"num" if h in num_cols else ""}">{v}</td>' for h, v in zip(headers, r))
        body += f"<tr>{tds}</tr>"
    st.markdown(
        f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead>'
        f'<tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


def product_table(df):
    headers = ["Product", "Category", "Stock", "Min stock", "Price", "Value", "Status"]
    rows = [[
        f"<b>{escape(r['name'])}</b>", escape(r["category"]), int(r["stock"]), int(r["min_stock"]),
        f"{CUR}{r['price']:,.0f}", f"{CUR}{r['value']:,.0f}", pill(r["status"]),
    ] for _, r in df.iterrows()]
    html_table(rows, headers, num_cols=("Stock", "Min stock", "Price", "Value"))


def style_chart(chart):
    return (chart.configure(background="#0f1a30")
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#1b2a48",
                            domainColor="#1b2a48", tickColor="#1b2a48", labelFontSize=12)
            .configure_view(strokeWidth=0)
            .configure_legend(labelColor=MUTED, titleColor=MUTED))


# ------------------------------------------------------------------ pages
def page_overview():
    df = load_products()
    hero("INVENTORY INTELLIGENCE PLATFORM", "Smart Inventory Control Agent",
         "Monitor stock, spot risks early, and make smarter replenishment decisions.")

    section("Your inventory at a glance")
    low = int((df["status"] == "LOW").sum())
    out = int((df["status"] == "OUT").sum())
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "📦", "Total products", len(df), "Items being tracked")
    kpi(c2, "📈", "Stock units", f"{int(df['stock'].sum()):,}", "Units currently available")
    kpi(c3, "⚠️", "Low / out alerts", low + out, f"{low} low • {out} out of stock",
        "bad" if out else ("warn" if low else "ok"))
    kpi(c4, "💰", "Inventory value", f"{CUR}{df['value'].sum():,.0f}", "Based on current stock × price")

    left, right = st.columns([3, 2])
    with left:
        section("Stock distribution", "dashes mark the reorder level")
        bars = alt.Chart(df).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=ACCENT).encode(
            x=alt.X("name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("stock:Q", title="Units"),
            tooltip=["name", "category", "stock", "min_stock"])
        ticks = alt.Chart(df).mark_tick(color=WARN, thickness=3, size=38).encode(
            x=alt.X("name:N", sort="-y"), y="min_stock:Q")
        st.altair_chart(style_chart(alt.layer(bars, ticks).properties(height=300)))
    with right:
        section("Stock health")
        health = pd.DataFrame({
            "Status": ["Healthy", "Low stock", "Out of stock"],
            "Products": [int((df["status"] == "HEALTHY").sum()), low, out]})
        chart = alt.Chart(health).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Status:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Products:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("Status:N", legend=None,
                            scale=alt.Scale(domain=["Healthy", "Low stock", "Out of stock"],
                                            range=[OK, WARN, BAD])),
            tooltip=["Status", "Products"]).properties(height=300)
        st.altair_chart(style_chart(chart))

    section("Needs attention")
    attn = df[df["status"] != "HEALTHY"]
    if attn.empty:
        st.success("All products are above their minimum stock level.")
    else:
        product_table(attn)


def page_inventory():
    hero("CATALOG", "Inventory", "Search, filter and maintain every product in one place.")
    df = load_products()
    section("All products")
    f1, f2, f3 = st.columns([2, 1, 1])
    search = f1.text_input("Search", placeholder="Search by product name…")
    cat = f2.selectbox("Category", ["All"] + sorted(df["category"].unique().tolist()))
    stat = f3.selectbox("Status", ["All", "Healthy", "Low", "Out"])

    view = df
    if search:
        view = view[view["name"].str.contains(search, case=False, na=False)]
    if cat != "All":
        view = view[view["category"] == cat]
    if stat != "All":
        view = view[view["status"] == {"Healthy": "HEALTHY", "Low": "LOW", "Out": "OUT"}[stat]]

    if view.empty:
        st.info("No products match these filters.")
    else:
        product_table(view)

    section("Edit or remove")
    if df.empty:
        return
    with st.expander("Update a product", expanded=False):
        name = st.selectbox("Product", df["name"], key="edit_name")
        row = df[df["name"] == name].iloc[0]
        a, b, c = st.columns(3)
        stock = a.number_input("Stock", min_value=0, value=int(row["stock"]), step=1, key=f"st_{name}")
        mn = b.number_input("Minimum stock", min_value=0, value=int(row["min_stock"]), step=1, key=f"mn_{name}")
        price = c.number_input("Price", min_value=0.0, value=float(row["price"]), step=100.0, key=f"pr_{name}")
        s1, s2 = st.columns(2)
        if s1.button("Save changes"):
            run("UPDATE products SET stock=?, min_stock=?, price=? WHERE name=?", (stock, mn, price, name))
            flash(f"Updated {name}.")
            st.rerun()
        if s2.button("Delete product"):
            run("DELETE FROM products WHERE name=?", (name,))
            flash(f"Deleted {name}.", "warning")
            st.rerun()


def page_add_product():
    hero("CATALOG", "Add Product", "Register a new item and set the level at which it should be reordered.")
    df = load_products()
    cats = sorted(df["category"].unique().tolist())
    with st.form("add_product", clear_on_submit=True):
        a, b = st.columns(2)
        name = a.text_input("Product name")
        cat_choice = b.selectbox("Category", cats + ["+ New category"])
        new_cat = b.text_input("New category name (only if you chose '+ New category')")
        c, d, e = st.columns(3)
        stock = c.number_input("Opening stock", min_value=0, step=1, value=0)
        mn = d.number_input("Minimum stock", min_value=0, step=1, value=5)
        price = e.number_input("Unit price", min_value=0.0, step=100.0, value=0.0)
        if st.form_submit_button("Add product"):
            category = new_cat.strip() if cat_choice == "+ New category" else cat_choice
            if not name.strip():
                st.error("Please enter a product name.")
            elif not category:
                st.error("Please enter a category.")
            elif name.strip().lower() in df["name"].str.lower().tolist():
                st.error("A product with this name already exists.")
            else:
                run("INSERT INTO products(name,category,stock,min_stock,price) VALUES(?,?,?,?,?)",
                    (name.strip(), category, stock, mn, price))
                if stock:
                    log_movement(name.strip(), "IN", int(stock), "Opening stock")
                flash(f"Added {name.strip()}.")
                st.rerun()


def page_stock_movement():
    hero("OPERATIONS", "Stock Movement", "Record stock coming in and going out. Every change is logged.")
    df = load_products()
    if df.empty:
        st.info("Add a product first.")
        return
    with st.form("movement", clear_on_submit=True):
        a, b, c = st.columns([2, 1, 1])
        product = a.selectbox("Product", df["name"])
        kind = b.radio("Type", ["Stock In", "Stock Out"], horizontal=True)
        qty = c.number_input("Quantity", min_value=1, step=1, value=1)
        note = st.text_input("Note (optional)", placeholder="e.g. Supplier delivery, customer order #123")
        if st.form_submit_button("Record movement"):
            current = int(df[df["name"] == product].iloc[0]["stock"])
            if kind == "Stock Out" and qty > current:
                st.error(f"Only {current} units of {product} in stock.")
            else:
                delta = int(qty) if kind == "Stock In" else -int(qty)
                run("UPDATE products SET stock = stock + ? WHERE name=?", (delta, product))
                log_movement(product, "IN" if delta > 0 else "OUT", int(qty), note)
                flash(f"{kind}: {int(qty)} × {product} recorded.")
                st.rerun()

    section("Recent movements")
    hist = query_df("SELECT ts, product, kind, qty, note FROM movements ORDER BY id DESC LIMIT 50")
    if hist.empty:
        st.info("No movements recorded yet.")
    else:
        rows = [[
            escape(r["ts"]), f"<b>{escape(r['product'])}</b>",
            f'<span class="pill {"ok" if r["kind"] == "IN" else "warn"}">'
            f'{"Stock in" if r["kind"] == "IN" else "Stock out"}</span>',
            int(r["qty"]), escape(r["note"] or "—"),
        ] for _, r in hist.iterrows()]
        html_table(rows, ["Time", "Product", "Type", "Qty", "Note"], num_cols=("Qty",))


def recommendations(df):
    """Rule-based reorder agent. Swap this function for an LLM/forecast call if you like."""
    usage = query_df(
        "SELECT product, SUM(qty) AS out_qty FROM movements "
        "WHERE kind='OUT' AND ts >= date('now','-30 day') GROUP BY product")
    velocity = {r["product"]: r["out_qty"] / 30 for _, r in usage.iterrows()}
    recs = []
    for _, r in df.iterrows():
        v = velocity.get(r["name"], 0)
        days_left = r["stock"] / v if v > 0 else None
        urgent = r["status"] != "HEALTHY" or (days_left is not None and days_left <= 7)
        if not urgent:
            continue
        qty = max(r["min_stock"] * 2 - r["stock"], 1)
        if v > 0:
            qty = max(qty, math.ceil(v * 14 - r["stock"]))
        priority = "Critical" if r["status"] == "OUT" else ("High" if r["status"] == "LOW" else "Medium")
        recs.append(dict(name=r["name"], stock=int(r["stock"]), min_stock=int(r["min_stock"]),
                         qty=int(qty), priority=priority, days_left=days_left,
                         cost=qty * r["price"]))
    order = {"Critical": 0, "High": 1, "Medium": 2}
    return sorted(recs, key=lambda x: order[x["priority"]])


def page_ai_insights():
    hero("AI AGENT", "AI Insights", "Reorder suggestions based on stock levels and your recent sales pace.")
    df = load_products()
    recs = recommendations(df)
    pending = set(query_df("SELECT product FROM orders WHERE status='Sent'")["product"])

    section("Reorder recommendations")
    if not recs:
        st.success("Nothing to reorder right now. Stock levels look healthy.")
    for r in recs:
        tone = {"Critical": "bad", "High": "warn", "Medium": "info"}[r["priority"]]
        days = f" • about {r['days_left']:.0f} days of cover" if r["days_left"] is not None else ""
        left, right = st.columns([5, 1])
        left.markdown(
            f'<div class="rec"><div class="rec-title">{escape(r["name"])} '
            f'<span class="pill {tone}">{r["priority"]}</span></div>'
            f'<div class="rec-meta">{r["stock"]} units left (minimum {r["min_stock"]}){days}</div>'
            f'<div class="rec-meta">Suggested order: <span class="rec-qty">{r["qty"]} units</span>'
            f' · est. cost {CUR}{r["cost"]:,.0f}</div></div>', unsafe_allow_html=True)
        if r["name"] in pending:
            right.markdown('<span class="pill info">Order sent</span>', unsafe_allow_html=True)
        elif right.button("Reorder", key=f"ro_{r['name']}"):
            run("INSERT INTO orders(product,qty,status,ts) VALUES(?,?,?,?)",
                (r["name"], r["qty"], "Sent", now()))
            flash(f"Purchase order placed: {r['qty']} × {r['name']}.")
            st.rerun()

    section("Order pipeline")
    orders = query_df("SELECT id, product, qty, status, ts FROM orders ORDER BY id DESC LIMIT 10")
    if orders.empty:
        st.info("No purchase orders yet. Use the Reorder buttons above.")
    for _, o in orders.iterrows():
        a, b = st.columns([5, 1])
        cls = "info" if o["status"] == "Sent" else "ok"
        a.markdown(
            f'<div class="rec"><div class="rec-title">PO #{int(o["id"])} · {escape(o["product"])} '
            f'<span class="pill {cls}">{o["status"]}</span></div>'
            f'<div class="rec-meta">{int(o["qty"])} units · placed {o["ts"]}</div></div>',
            unsafe_allow_html=True)
        if o["status"] == "Sent" and b.button("Mark received", key=f"rcv_{int(o['id'])}"):
            run("UPDATE orders SET status='Delivered' WHERE id=?", (int(o["id"]),))
            run("UPDATE products SET stock = stock + ? WHERE name=?", (int(o["qty"]), o["product"]))
            log_movement(o["product"], "IN", int(o["qty"]), f"Received PO #{int(o['id'])}")
            flash(f"PO #{int(o['id'])} received. Stock updated.")
            st.rerun()


def page_reports():
    hero("ANALYTICS", "Reports", "Value breakdown and data exports for your presentation.")
    df = load_products()
    section("Inventory value by category")
    by_cat = df.groupby("category", as_index=False)["value"].sum()
    chart = alt.Chart(by_cat).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=ACCENT).encode(
        x=alt.X("category:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("value:Q", title=f"Value ({CUR})"),
        tooltip=["category", alt.Tooltip("value:Q", format=",.0f")]).properties(height=300)
    st.altair_chart(style_chart(chart))

    section("Export data")
    a, b = st.columns(2)
    a.download_button("Download products (CSV)",
                      df.drop(columns=["status"]).to_csv(index=False), "products.csv", "text/csv")
    mv = query_df("SELECT ts, product, kind, qty, note FROM movements ORDER BY id DESC")
    b.download_button("Download movements (CSV)", mv.to_csv(index=False), "movements.csv", "text/csv")


# ------------------------------------------------------------------ main
PAGES = {
    "📊  Overview": page_overview,
    "📦  Inventory": page_inventory,
    "➕  Add Product": page_add_product,
    "🔄  Stock Movement": page_stock_movement,
    "🤖  AI Insights": page_ai_insights,
    "📑  Reports": page_reports,
}


def main():
    init_db()
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-logo">📦</div><div class="brand-name">NEXUS</div></div>'
            '<div class="brand-sub">SMART INVENTORY CONTROL</div>'
            '<div class="side-divider"></div><div class="side-label">WORKSPACE</div>',
            unsafe_allow_html=True)
        page = st.radio("Navigation", list(PAGES), label_visibility="collapsed")
        st.markdown(
            '<div class="side-divider"></div><div class="side-label">SYSTEM STATUS</div>'
            '<div class="status-ok">● Inventory database connected</div>'
            '<div class="side-foot">Academic project • Demo environment</div>',
            unsafe_allow_html=True)
    show_flash()
    PAGES[page]()


main()
