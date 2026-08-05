"""
Reviews Reporting Dashboard (Streamlit) — "Midnight Command" theme
--------------------------------------------------
Dark navy sidebar + terminal-style monospace KPI tiles on a light main
canvas. Interactive, cross-filterable rebuild of the Power BI "Reviews
Reporting Dashboard". Click a donut slice or a garage bar in Top 10 /
Bottom 10 to cross-filter the rest of the page. Top 10 / Bottom 10 rankings
themselves always stay fixed to the sidebar filters (Manager & Month) only.

RUN LOCALLY
    pip install -r requirements.txt
    streamlit run app.py
"""

import os
import re
import base64
import html as _html_lib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from groq import Groq

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
MASTER_FILE = os.path.join(DATA_DIR, "master_data.csv")
LOGO_PATH = os.path.join(APP_DIR, "assets", "metropolis_icon.png")
RM_MASTER_PATH = os.path.join(APP_DIR, "assets", "master_sheet_for_rm.xlsx")

RAW_COLUMNS = [
    "Title", "Rental ID", "Starts Local Timezone Date", "Ends Local Timezone Date",
    "Review Created Date", "Star Rating", "Redacted Comments", "Category List",
]

# ---- "Midnight Command" palette ----
MIDNIGHT = "#14123A"       # sidebar + KPI tile background
MIDNIGHT_LIGHT = "#1F1B4D" # slightly lighter navy for nested boxes/pills
INDIGO_950 = "#1E1B4B"
INDIGO_800 = "#3730A3"
INDIGO_700 = "#4338CA"
INDIGO_600 = "#4F46E5"
INDIGO_500 = "#6366F1"
INDIGO_400 = "#818CF8"
INDIGO_300 = "#A5B4FC"
INDIGO_200 = "#C7D2FE"
INDIGO_100 = "#E0E7FF"
INDIGO_50 = "#EEF2FF"
SLATE_700 = "#334155"
MUTED_GRAY = "#9CA3AF"
CORAL = "#F87171"
MINT = "#34D399"
PAGE_BG = "#F3F4F6"
TEXT_DARK = "#111827"

STAR_COLOR_MAP = {5: MIDNIGHT, 4: INDIGO_700, 3: INDIGO_500, 2: INDIGO_300, 1: INDIGO_200}
BODY_FONT = "'Inter Tight', 'Segoe UI', system-ui, sans-serif"

st.set_page_config(page_title="Reviews Reporting Dashboard", page_icon="🅿️", layout="wide")

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&display=swap');
    *:not([data-testid="stIconMaterial"]):not([data-testid="stIconMaterial"] *) {{ font-family: {BODY_FONT} !important; }}
    [data-testid="stIconMaterial"] {{ font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', sans-serif !important; }}
    html, body, [class*="css"] {{ font-family: {BODY_FONT}; }}
    div.block-container {{ padding-top: 3rem !important; }}
    [data-testid="stAppViewContainer"] {{ background-color: {PAGE_BG}; }}

    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] div,
    button[data-baseweb="tab"] span {{ font-family: {BODY_FONT}; font-size: 27px !important; font-weight: 700 !important; color: #374151 !important; }}
    button[data-baseweb="tab"] {{ padding: 12px 20px !important; height: auto !important; border-radius: 8px 8px 0 0 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ background-color: #E5E7EB !important; }}
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] div,
    button[data-baseweb="tab"][aria-selected="true"] span {{ color: #111827 !important; font-weight: 800 !important; }}
    [data-baseweb="tab-list"] {{ gap: 12px !important; }}
    [data-baseweb="tab-highlight"] {{ background-color: transparent !important; }}
    div[data-baseweb="tab-panel"] {{ padding-top: 16px; }}

    /* KPI tiles: dark navy "terminal" tiles with monospace numbers */
    .kpi-card {{
        background-color: {MIDNIGHT}; border: none; border-radius: 10px;
        padding: 16px 20px; box-shadow: 0 3px 10px rgba(20,18,58,0.35); margin-bottom: 6px;
    }}
    .kpi-label {{ font-size: 15px; color: {MUTED_GRAY}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }}
    .kpi-value {{ font-family: {BODY_FONT}; font-size: 28px; font-weight: 800; color: #F8FAFC; }}
    .kpi-value.decline {{ color: {CORAL}; }}
    .kpi-value.positive {{ color: {MINT}; }}

    /* Sidebar: dark navy "Midnight Command" panel */
    section[data-testid="stSidebar"] {{ background-color: {MIDNIGHT} !important; }}
    section[data-testid="stSidebar"] * {{ color: #E5E7EB !important; }}
    section[data-testid="stSidebar"] label p {{ font-size: 13px !important; font-weight: 600 !important; }}
    section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] textarea {{
        background-color: {MIDNIGHT_LIGHT} !important; border: 1px solid #33306B !important; color: #E5E7EB !important;
    }}
    /* Multiselect / selectbox (BaseWeb) dark styling */
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: {MIDNIGHT_LIGHT} !important; border: 1px solid #33306B !important; color: #E5E7EB !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] input {{ color: #E5E7EB !important; }}
    section[data-testid="stSidebar"] [data-baseweb="tag"] {{ background-color: {INDIGO_600} !important; }}
    div[data-baseweb="popover"] ul {{ background-color: {MIDNIGHT_LIGHT} !important; }}
    div[data-baseweb="popover"] li {{ color: #E5E7EB !important; }}
    div[data-baseweb="popover"] li:hover {{ background-color: {INDIGO_600} !important; }}
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] svg {{ fill: #E5E7EB !important; }}
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] {{
        border: 1px solid rgba(255,255,255,0.55) !important;
        border-radius: 6px !important;
        background: transparent !important;
        padding: 7px 12px !important;
        margin-top: 2px !important;
        margin-bottom: 2px !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] label {{
        gap: 8px !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {MIDNIGHT_LIGHT}; border-radius: 10px; border: 1px solid #33306B !important;
        margin-left: -0.9rem !important;
    }}
    section[data-testid="stSidebar"] > div:first-child {{ padding-left: 0.6rem !important; padding-right: 0.6rem !important; }}
    .filter-title {{ font-size: 16px; font-weight: 800; color: #F1F5F9; margin-bottom: 4px; }}
    .filter-badge {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 19px; height: 19px; border-radius: 50%;
        background: {INDIGO_600}; margin-right: 6px; vertical-align: middle;
    }}
    .sidebar-heading {{ font-size: 20px; letter-spacing: 0.10em; color: #F1F5F9; font-weight: 800; margin: 4px 0 14px 0.7rem !important; padding-left: 0 !important; }}

    h1 {{ font-size: 34px !important; }}
    .section-title {{
        font-size: 20px; font-weight: 800; color: {TEXT_DARK};
        border-left: 4px solid {MIDNIGHT}; padding-left: 10px;
        margin-top: 14px; margin-bottom: 10px;
    }}
    .chart-subtitle {{ font-size: 16px; font-weight: 700; color: {TEXT_DARK}; margin-bottom: 4px; }}
    .kpi-spacer {{ height: 20px; }}

    div[data-testid="stPlotlyChart"] {{
        background: #ffffff; border-radius: 10px; padding: 8px;
        border: 1px solid #E5E7EB; box-shadow: 0 1px 4px rgba(17,24,39,0.08);
    }}

    .mom-table-wrap {{ max-height: 620px; overflow-y: auto; border: 1px solid #E5E7EB; border-radius: 8px; background: white; }}
    .mom-table table {{ font-size: 15px; border-collapse: collapse; width: 100%; color: {TEXT_DARK}; }}
    .mom-table thead th {{
        background: #F9FAFB; color: {TEXT_DARK}; font-size: 17px; font-weight: 800;
        padding: 10px 12px; text-align: left; position: sticky; top: 0; border-bottom: 2px solid #E5E7EB;
    }}
    .mom-table td {{ padding: 8px 12px; border-bottom: 1px solid #f1f1f6; }}
    .mom-table tr:nth-child(even) td {{ background: #fafaff; }}
    .mom-table tr.total-row td {{ font-weight: 800; background: {INDIGO_100} !important; border-top: 2px solid {INDIGO_300}; }}

    .comments-table-wrap {{ max-height: 420px; overflow-y: auto; border: 1px solid #E5E7EB; border-radius: 8px; background: white; }}
    .comments-table {{ border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 14px; color: {TEXT_DARK}; }}
    .comments-table thead th {{
        position: sticky; top: 0; background: #F9FAFB; padding: 8px 14px; text-align: left;
        border-bottom: 2px solid #E5E7EB; font-weight: 800; font-size: 14px;
    }}
    .comments-table td {{
        padding: 8px 14px; border-bottom: 1px solid #f1f1f6; vertical-align: top;
        white-space: normal; word-wrap: break-word; overflow-wrap: break-word;
    }}
    .comments-table tr:nth-child(even) td {{ background: #fafaff; }}

    .brand-wrap {{ display: flex; align-items: center; gap: 14px; margin-bottom: 4px; }}
    .brand-mark-img-wrap {{
        background: white; border-radius: 12px; padding: 8px 10px;
        box-shadow: 0 1px 4px rgba(17,24,39,0.15); display: flex; align-items: center;
    }}
    .brand-title {{ font-size: 34px; font-weight: 800; color: {TEXT_DARK}; }}

    /* EXPLICIT INLINE SORT CONTAINER STYLING */
    .inline-sort-box div[data-testid="stSelectbox"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .inline-sort-box div[data-baseweb="select"] > div {{
        min-height: 38px !important;
        height: 38px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
        border-radius: 8px !important;
        display: flex !important;
        align-items: center !important;
    }}
    .inline-sort-box div[data-baseweb="select"] span {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #111827 !important;
        line-height: normal !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

CHART_FONT = dict(family=BODY_FONT, size=13, color=TEXT_DARK)
HOVER_STYLE = dict(bgcolor="white", font_size=15, font_family=BODY_FONT, font_color=TEXT_DARK, bordercolor=INDIGO_300)


def short_label(name: str, maxlen: int = 24) -> str:
    name = str(name)
    return name if len(name) <= maxlen else name[: maxlen - 1].rstrip() + "…"


def extract_points(raw):
    if not raw:
        return []
    sel = raw.get("selection") if isinstance(raw, dict) else getattr(raw, "selection", None)
    if sel is None:
        return []
    return sel.get("points", []) if isinstance(sel, dict) else getattr(sel, "points", [])


def point_val(point, key):
    return point.get(key) if isinstance(point, dict) else getattr(point, key, None)


@st.cache_data(show_spinner=False)
def get_logo_b64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="10" height="10">{}</svg>'
)
ICON_LOT = ICON_SVG.format('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>')
ICON_MONTH = ICON_SVG.format('<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>')
ICON_COMMENTS = ICON_SVG.format('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>')
ICON_RM = ICON_SVG.format('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>')
ICON_OPS = ICON_SVG.format('<path d="M17 21v-2a4 4 0 0 0-3-3.87"></path><path d="M7 23v-2a4 4 0 0 1 3-3.87"></path><circle cx="9" cy="7" r="4"></circle>')


def _lerp_hex(c1, c2, t):
    c1 = c1.lstrip("#"); c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = round(r1 + (r2 - r1) * t); g = round(g1 + (g2 - g1) * t); b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def value_shade(v, vmin, vmax, light=INDIGO_200, dark=MIDNIGHT):
    if vmax == vmin:
        return dark
    t = (v - vmin) / (vmax - vmin)
    return _lerp_hex(light, dark, t)


def build_sparkline_svg(values, width=220, height=44, color=MIDNIGHT):
    if len(values) < 2:
        return ""
    vmin, vmax = min(values), max(values)
    span = (vmax - vmin) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = 4 + i * (width - 8) / (n - 1)
        y = height - 4 - (v - vmin) / span * (height - 8)
        pts.append(f"{x:.1f},{y:.1f}")
    last_x, last_y = pts[-1].split(",")
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="4" fill="{color}"/>'
        f"</svg>"
    )


# --------------------------------------------------------------------------
# DATA PERSISTENCE
# --------------------------------------------------------------------------
def load_master_data() -> pd.DataFrame:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(MASTER_FILE):
        return pd.read_csv(MASTER_FILE)
    return pd.DataFrame(columns=RAW_COLUMNS)


def save_master_data(df: pd.DataFrame) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(MASTER_FILE, index=False)


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    for col in RAW_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    return df[RAW_COLUMNS]


def merge_new_files(uploaded_files) -> int:
    master = load_master_data()
    before = len(master)
    new_frames = []
    for f in uploaded_files:
        try:
            raw = pd.read_csv(f)
            new_frames.append(standardize(raw))
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")
    combined = pd.concat([master] + new_frames, ignore_index=True) if new_frames else master
    combined = combined.drop_duplicates(subset=["Rental ID", "Review Created Date"], keep="last")
    save_master_data(combined)
    return len(combined) - before


# --------------------------------------------------------------------------
# TRANSFORMATION
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def prep_data(df: pd.DataFrame, cache_key: str) -> pd.DataFrame:
    df = df.copy()
    df["Review Created Date"] = pd.to_datetime(df["Review Created Date"], errors="coerce")
    df["Star Rating"] = pd.to_numeric(df["Star Rating"], errors="coerce")
    df = df.dropna(subset=["Review Created Date", "Star Rating", "Title"])
    df["Month"] = df["Review Created Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Label"] = df["Month"].dt.strftime("%b %Y")
    df["Redacted Comments"] = df["Redacted Comments"].fillna("").astype(str).str.strip()
    
    # Strip raw HTML tags and normalize newlines to prevent broken table formatting
    df["Redacted Comments"] = df["Redacted Comments"].apply(
        lambda x: re.sub(r"[\r\n]+", " ", re.sub(r"<[^>]*>", "", _html_lib.unescape(x))).strip()
    )
    df["Has Comment"] = np.where(df["Redacted Comments"] != "", "Has Comment", "No Comment")
    return df


def monthly_lot_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Title", "Month"])
        .agg(avg_rating=("Star Rating", "mean"), reviews=("Star Rating", "size"))
        .reset_index()
    )


def build_comparison_table(df: pd.DataFrame, prior_month: pd.Timestamp, current_month: pd.Timestamp):
    monthly = monthly_lot_summary(df)
    total_reviews = df.groupby("Title")["Star Rating"].size().rename("Total Reviews")
    cur = monthly[monthly["Month"] == current_month].set_index("Title")["avg_rating"].rename("Current Month Avg")
    prior = monthly[monthly["Month"] == prior_month].set_index("Title")["avg_rating"].rename("Prior Month Avg")
    table = pd.concat([total_reviews, prior, cur], axis=1).reset_index().rename(columns={"Title": "Lot Name"})
    table["Rolling MoM Improvement %"] = np.where(
        table["Prior Month Avg"].notna() & (table["Prior Month Avg"] != 0),
        (table["Current Month Avg"] - table["Prior Month Avg"]) / table["Prior Month Avg"] * 100,
        np.nan,
    )
    table = table.sort_values("Total Reviews", ascending=False)
    return table


def fmt_num(v):
    return "—" if pd.isna(v) else f"{v:.2f}"


def fmt_pct_html(v):
    if pd.isna(v):
        return "—"
    color = "#16A34A" if v >= 0 else CORAL
    arrow = "▲" if v >= 0 else "▼"
    return f'<span style="color:{color}; font-weight:800;">{arrow} {v:.2f}%</span>'


# --------------------------------------------------------------------------
# REGIONAL / OPERATIONS MANAGER MASTER SHEET
# --------------------------------------------------------------------------
def _normalize_name(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("–", "-").replace("—", "-")
    return s


@st.cache_data(show_spinner=False)
def load_rm_master(path: str, mtime: float) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["_norm", "SP Code", "Regional Manager", "Operations Manager"])
    raw = pd.read_excel(path, sheet_name="Master Mapping")
    raw = raw.rename(columns={
        "SpotHero Garage Name": "Lot Name",
        "SP#": "SP Code",
    })
    raw["Regional Manager"] = raw["Regional Manager"].fillna("Unassigned").astype(str).str.strip()
    raw["Operations Manager"] = raw["Operations Manager"].fillna("Unassigned").astype(str).str.strip()
    raw["SP Code"] = raw["SP Code"].astype(str).str.strip()
    raw["_norm"] = raw["Lot Name"].map(_normalize_name)
    return raw[["_norm", "SP Code", "Regional Manager", "Operations Manager"]].drop_duplicates(subset=["_norm"])


def attach_manager_info(df: pd.DataFrame) -> pd.DataFrame:
    mtime = os.path.getmtime(RM_MASTER_PATH) if os.path.exists(RM_MASTER_PATH) else 0
    rm_master = load_rm_master(RM_MASTER_PATH, mtime)
    if rm_master.empty:
        df["SP Code"] = "—"
        df["Regional Manager"] = "Unmapped"
        df["Operations Manager"] = "Unmapped"
        return df
    df = df.copy()
    df["_norm"] = df["Title"].map(_normalize_name)
    df = df.merge(rm_master, on="_norm", how="left")
    df["SP Code"] = df["SP Code"].fillna("—")
    df["Regional Manager"] = df["Regional Manager"].fillna("Unmapped")
    df["Operations Manager"] = df["Operations Manager"].fillna("Unmapped")
    return df.drop(columns=["_norm"])


def searchable_filter(label: str, options: list, key_prefix: str, icon: str):
    with st.sidebar.container(border=True):
        st.markdown(f'<div class="filter-title"><span class="filter-badge">{icon}</span>{label}</div>', unsafe_allow_html=True)
        all_checked = st.checkbox(f"Select all {label.lower()}", value=True, key=f"{key_prefix}_all")
        picked = st.multiselect(
            f"Type to search {label.lower()}",
            options=options,
            default=[],
            key=f"{key_prefix}_multiselect",
            placeholder=f"Type to search & pick specific {label.lower()}...",
            label_visibility="collapsed",
        )
    if picked:
        return picked
    if all_checked:
        return options
    return []


# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
logo_b64 = get_logo_b64()
logo_html = f'<div class="brand-mark-img-wrap"><img src="data:image/png;base64,{logo_b64}" style="height:50px;"/></div>' if logo_b64 else ""
st.markdown(f'<div class="brand-wrap">{logo_html}<div class="brand-title">Reviews Reporting Dashboard</div></div>', unsafe_allow_html=True)
st.caption(
    "Drop each new biweekly reviews report below. It's merged permanently into "
    "`data/master_data.csv` — previous months stay loaded every time you reopen this app."
)

uploaded_files = st.file_uploader("Drag & drop biweekly report(s) here (.csv)", type=["csv"], accept_multiple_files=True)
if uploaded_files:
    added = merge_new_files(uploaded_files)
    st.success(f"Processed {len(uploaded_files)} file(s). Added {added} new review record(s).")
    st.cache_data.clear()

master_raw = load_master_data()
if master_raw.empty:
    st.info("No data yet. Drop a CSV report above to get started.")
    st.stop()

cache_key = f"{len(master_raw)}_{master_raw['Rental ID'].sum() if 'Rental ID' in master_raw else 0}"
data = prep_data(master_raw, cache_key)

if not os.path.exists(RM_MASTER_PATH):
    st.warning(
        "⚠️ Regional/Operations Manager master sheet not found at `assets/master_sheet_for_rm.xlsx`. "
        "Every garage will show as Unmapped until that file is placed there — copy it from the zip into "
        "the `assets` folder next to `app.py`."
    )
data = attach_manager_info(data)

with st.expander("📁 View / manage stored dataset"):
    c1, c2, c3 = st.columns(3)
    c1.metric("Total records stored", len(data))
    c2.metric("Months of data", data["Month"].nunique())
    c3.metric("Distinct garages", data["Title"].nunique())
    unmapped_count = data[data["Regional Manager"] == "Unmapped"]["Title"].nunique()
    if unmapped_count:
        st.caption(f"⚠️ {unmapped_count} garage(s) couldn't be matched to the Regional/Operations Manager master sheet by name.")
    st.download_button(
        "⬇️ Download master dataset (CSV)",
        data=master_raw.to_csv(index=False).encode("utf-8"),
        file_name="master_data_backup.csv",
        mime="text/csv",
    )
    if st.button("🗑️ Reset all stored data", type="secondary"):
        save_master_data(pd.DataFrame(columns=RAW_COLUMNS))
        st.cache_data.clear()
        st.rerun()

# --------------------------------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------------------------------
st.sidebar.markdown('<div class="sidebar-heading">FILTERS</div>', unsafe_allow_html=True)

all_lots = sorted(data["Title"].unique())
lot_filter = searchable_filter("Lot Name", all_lots, "lot", ICON_LOT)

month_order = sorted(data["Month"].unique())
month_labels = [pd.Timestamp(m).strftime("%b %Y") for m in month_order]
month_label_to_ts = dict(zip(month_labels, month_order))
month_filter_labels = searchable_filter("Month", month_labels, "month", ICON_MONTH)

with st.sidebar.container(border=True):
    st.markdown(f'<div class="filter-title"><span class="filter-badge">{ICON_COMMENTS}</span>Comments</div>', unsafe_allow_html=True)
    comments_all = st.checkbox("Select all (Has + No Comment)", value=True, key="comments_all")
    comments_filter = ["Has Comment", "No Comment"] if comments_all else st.multiselect(
        "Filter by comment presence", options=["Has Comment", "No Comment"], default=[], label_visibility="collapsed"
    )
    keyword = st.text_input("Search comment text (optional)", "")

all_rms = sorted(data["Regional Manager"].unique())
rm_filter = searchable_filter("Regional Manager", all_rms, "rm", ICON_RM)

all_ops = sorted(data["Operations Manager"].unique())
ops_filter = searchable_filter("Operations Manager", all_ops, "ops", ICON_OPS)

selected_month_ts = [month_label_to_ts[m] for m in month_filter_labels]
if not selected_month_ts:
    selected_month_ts = month_order

if len(selected_month_ts) == 1:
    current_month = selected_month_ts[0]
    prior_month = current_month - pd.offsets.MonthBegin(1)
    analysis_months = [prior_month, current_month]
else:
    prior_month = min(selected_month_ts)
    current_month = max(selected_month_ts)
    analysis_months = selected_month_ts

base_filtered = data[
    data["Title"].isin(lot_filter)
    & data["Month"].isin(analysis_months)
    & data["Has Comment"].isin(comments_filter)
    & data["Regional Manager"].isin(rm_filter)
    & data["Operations Manager"].isin(ops_filter)
].copy()

movers_filtered = data[
    data["Month"].isin(analysis_months)
    & data["Has Comment"].isin(comments_filter)
    & data["Regional Manager"].isin(rm_filter)
    & data["Operations Manager"].isin(ops_filter)
].copy()

if keyword:
    base_filtered = base_filtered[base_filtered["Redacted Comments"].str.contains(keyword, case=False, na=False)]
    movers_filtered = movers_filtered[movers_filtered["Redacted Comments"].str.contains(keyword, case=False, na=False)]

if base_filtered.empty:
    st.warning("No records match the current sidebar filters.")
    st.stop()

# --------------------------------------------------------------------------
# REGIONAL / OPERATIONS MANAGER LOOKUP — shown when 1-10 specific garages are picked
# --------------------------------------------------------------------------
if 1 <= len(lot_filter) <= 10 and len(lot_filter) < len(all_lots):
    lookup_df = (
        base_filtered[["Title", "SP Code", "Regional Manager", "Operations Manager"]]
        .drop_duplicates(subset=["Title"])
        .rename(columns={"Title": "Lot Name"})
    )
    with st.expander(f"Garage Manager Lookup — {len(lookup_df)} garage(s)", expanded=True):
        st.dataframe(lookup_df, hide_index=True, use_container_width=True)

# --------------------------------------------------------------------------
# CROSS-FILTERING: read any active chart click selections
# --------------------------------------------------------------------------
donut_pts = extract_points(st.session_state.get("donut_chart"))
top10_pts = extract_points(st.session_state.get("top10_chart"))
bottom10_pts = extract_points(st.session_state.get("bottom10_chart"))

sel_rating = None
if donut_pts:
    lbl = point_val(donut_pts[0], "label")
    if lbl:
        try:
            sel_rating = int(str(lbl).replace("★", "").strip())
        except ValueError:
            sel_rating = None

sel_lot = None
for pts in (top10_pts, bottom10_pts):
    if pts:
        cd = point_val(pts[0], "customdata")
        if cd:
            sel_lot = cd[0]

if sel_rating is not None or sel_lot:
    bits = []
    if sel_rating is not None:
        bits.append(f"⭐ {sel_rating} stars")
    if sel_lot:
        bits.append(f"🏢 {sel_lot}")
    b1, b2 = st.columns([6, 1])
    b1.info("Cross-filtered by click: " + "  ·  ".join(bits))
    if b2.button("✕ Clear"):
        for k in ("donut_chart", "top10_chart", "bottom10_chart"):
            st.session_state.pop(k, None)
        st.rerun()

filtered = base_filtered.copy()
if sel_rating is not None:
    filtered = filtered[filtered["Star Rating"] == sel_rating]
if sel_lot:
    filtered = filtered[filtered["Title"] == sel_lot]

base_comparison = build_comparison_table(movers_filtered, prior_month, current_month)
base_movers = base_comparison.dropna(subset=["Rolling MoM Improvement %"])

tab_overview, tab_detail = st.tabs(["Dashboard Overview", "All Garages — MoM Detail"])

# ==========================================================================
# TAB 1: OVERVIEW
# ==========================================================================
with tab_overview:
    if filtered.empty:
        st.warning("No records match the current click selection. Use ✕ Clear above to reset.")
    else:
        comparison = build_comparison_table(filtered, prior_month, current_month)
        comparable = comparison.dropna(subset=["Prior Month Avg", "Current Month Avg"])

        total_garages = filtered[filtered["Month"] == current_month]["Title"].nunique()
        total_declines = (comparable["Rolling MoM Improvement %"] < 0).sum()
        total_improvements = (comparable["Rolling MoM Improvement %"] > 0).sum()
        avg_rating_overall = filtered["Star Rating"].mean()
        prior_avg_overall = filtered[filtered["Month"] == prior_month]["Star Rating"].mean()

        k1, k2, k3, k4 = st.columns(4)
        kpis = [
            (k1, f"Total Garages · {pd.Timestamp(current_month).strftime('%b %Y')}", f"{total_garages}", ""),
            (k2, "Total Declines (MoM)", f"▼ {total_declines}", "decline"),
            (k3, "Total Improvements (MoM)", f"▲ {total_improvements}", "positive"),
            (k4, "Avg Rating", f"{avg_rating_overall:.2f}", ""),
        ]
        for col, label, value, cls in kpis:
            with col:
                st.markdown(
                    f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value {cls}">{value}</div></div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="kpi-spacer"></div>', unsafe_allow_html=True)
        r2c1, r2c2, r2c3 = st.columns([1.15, 1, 0.85])

        with r2c1:
            st.markdown('<div class="section-title">Star Rating Distribution</div>', unsafe_allow_html=True)
            star_counts = filtered["Star Rating"].astype(int).value_counts().sort_index(ascending=False)
            labels = [f"{s}★" for s in star_counts.index]
            colors = [STAR_COLOR_MAP.get(int(s), INDIGO_400) for s in star_counts.index]
            pulls = [0.08 if sel_rating == int(s) else 0 for s in star_counts.index]
            fig_donut = go.Figure(data=[go.Pie(
                labels=labels, values=star_counts.values, hole=0.55, pull=pulls,
                domain=dict(x=[0.12, 0.88], y=[0.05, 1]),
                marker=dict(colors=colors, line=dict(color="white", width=2)),
                textinfo="percent", textposition="outside",
                textfont=dict(size=11, color=TEXT_DARK, family=CHART_FONT["family"]),
                hovertemplate="<b>%{label}</b><br>Reviews: %{value}<br>Share: %{percent}<extra></extra>",
            )])
            fig_donut.update_layout(
                margin=dict(t=28, b=10, l=10, r=10), height=250, showlegend=True,
                legend=dict(font=dict(size=13, color=TEXT_DARK), orientation="h", x=0.5, y=-0.12, xanchor="center"),
                hoverlabel=HOVER_STYLE, font=CHART_FONT,
                paper_bgcolor="white", plot_bgcolor="white",
            )
            st.plotly_chart(fig_donut, use_container_width=True, on_select="rerun", selection_mode="points", key="donut_chart")
            st.caption("Click a slice to filter the whole dashboard to that star rating. Click again to clear.")

        with r2c2:
            st.markdown('<div class="section-title">Ratings Month Over Month</div>', unsafe_allow_html=True)
            mom_trend = filtered.groupby("Month")["Star Rating"].agg(["mean", "size"]).reset_index()
            mom_trend.columns = ["Month", "Avg Rating", "Reviews"]
            mom_trend["Month Label"] = mom_trend["Month"].dt.strftime("%b %Y")
            mom_trend = mom_trend.sort_values("Month")
            n_bars = max(len(mom_trend), 1)
            vmin, vmax = mom_trend["Avg Rating"].min(), mom_trend["Avg Rating"].max()
            bar_colors = [value_shade(v, vmin, vmax) for v in mom_trend["Avg Rating"]]
            fig_mom = go.Figure(go.Bar(
                x=mom_trend["Avg Rating"], y=mom_trend["Month Label"], orientation="h",
                marker_color=bar_colors, text=mom_trend["Avg Rating"].round(2),
                textposition="outside", textfont=dict(size=15, color=SLATE_700), customdata=mom_trend["Reviews"],
                hovertemplate="<b>%{y}</b><br>Avg Rating: %{x:.2f}<br>Reviews: %{customdata}<extra></extra>",
            ))
            fig_mom.update_traces(width=min(0.45, 3.2 / n_bars))
            fig_mom.update_layout(
                xaxis_range=[0, 6.2], margin=dict(t=10, b=10, l=10, r=40),
                height=250, bargap=0.5,
                yaxis_title="", xaxis_title="Avg Rating", plot_bgcolor="white", paper_bgcolor="white",
                hoverlabel=HOVER_STYLE, font=CHART_FONT,
            )
            fig_mom.update_xaxes(tickfont=dict(size=13, color=SLATE_700), title_font=dict(size=13, color=SLATE_700))
            fig_mom.update_yaxes(tickfont=dict(size=14, color=SLATE_700))
            st.plotly_chart(fig_mom, use_container_width=True)

        with r2c3:
            st.markdown('<div class="section-title">Avg Rating</div>', unsafe_allow_html=True)
            delta_ref = round(float(prior_avg_overall), 2) if pd.notna(prior_avg_overall) else round(float(avg_rating_overall), 2)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=round(float(avg_rating_overall), 2),
                number={"font": {"size": 34, "color": MIDNIGHT, "family": BODY_FONT}, "valueformat": ".2f"},
                delta={"reference": delta_ref, "increasing": {"color": "#16A34A"}, "decreasing": {"color": CORAL}, "font": {"size": 15, "family": BODY_FONT}},
                gauge={
                    "axis": {"range": [0, 5], "tickfont": {"size": 12, "color": SLATE_700, "family": BODY_FONT}, "tickcolor": INDIGO_300},
                    "bar": {"color": MIDNIGHT, "thickness": 0.32},
                    "bgcolor": "white", "borderwidth": 1, "bordercolor": INDIGO_200,
                    "steps": [
                        {"range": [0, 2], "color": INDIGO_50},
                        {"range": [2, 3.5], "color": INDIGO_100},
                        {"range": [3.5, 5], "color": INDIGO_200},
                    ],
                    "threshold": {"line": {"color": MIDNIGHT, "width": 3}, "thickness": 0.85, "value": round(float(avg_rating_overall), 2)},
                },
            ))
            fig_gauge.update_layout(margin=dict(t=30, b=10, l=20, r=20), height=250, font=dict(family=BODY_FONT, size=13, color=TEXT_DARK), hoverlabel=HOVER_STYLE, paper_bgcolor="white")
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption(f"vs. prior month ({pd.Timestamp(prior_month).strftime('%b %Y')}): {delta_ref:.2f}")

        st.markdown('<div class="kpi-spacer"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title" style="margin-bottom: 4px;">Customer Comments</div>', unsafe_allow_html=True)
        
        ctrl_left, ctrl_right = st.columns([1.5, 4.5]) 
        
        with ctrl_left:
            st.markdown('<div class="inline-sort-box">', unsafe_allow_html=True)
            sort_option = st.selectbox(
                "Sort comments by",
                options=["Month (Newest)", "Month (Oldest)", "Rating (High to Low)", "Rating (Low to High)"],
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
        comments_raw = filtered[filtered["Redacted Comments"] != ""][
            ["Title", "Month", "Month Label", "Star Rating", "Redacted Comments"]
        ]
        
        if sort_option == "Month (Newest)":
            comments_raw = comments_raw.sort_values("Month", ascending=False)
        elif sort_option == "Month (Oldest)":
            comments_raw = comments_raw.sort_values("Month", ascending=True)
        elif sort_option == "Rating (High to Low)":
            comments_raw = comments_raw.sort_values(["Star Rating", "Month"], ascending=[False, False])
        elif sort_option == "Rating (Low to High)":
            comments_raw = comments_raw.sort_values(["Star Rating", "Month"], ascending=[True, False])
            
        comments_df = comments_raw[["Title", "Month Label", "Star Rating", "Redacted Comments"]].rename(
            columns={"Title": "Lot Name", "Month Label": "Month", "Redacted Comments": "Comment"}
        )
        
        comment_count = len(comments_df)

        with ctrl_right:
            st.markdown(
                f'<div style="text-align: right; margin-top: 0px; margin-bottom: 0px;">'
                f'<span style="background-color: {MIDNIGHT}; color: #F8FAFC; padding: 6px 14px; '
                f'border-radius: 20px; font-weight: 700; font-size: 13px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">'
                f'💬 {comment_count:,} Comments</span></div>',
                unsafe_allow_html=True
            )

        # 1. RENDER COMMENTS TABLE
        comment_rows = []
        for _, r in comments_df.iterrows():
            clean_comment = _html_lib.escape(str(r['Comment']))
            comment_rows.append(
                f"<tr><td>{_html_lib.escape(str(r['Lot Name']))}</td>"
                f"<td>{_html_lib.escape(str(r['Month']))}</td>"
                f"<td>{int(r['Star Rating'])}</td>"
                f"<td>{clean_comment}</td></tr>"
            )
        comments_html = f"""
        <div class="comments-table-wrap" style="margin-top: 4px;">
        <table class="comments-table">
          <colgroup>
            <col style="width:20%"><col style="width:10%"><col style="width:10%"><col style="width:60%">
          </colgroup>
          <thead><tr><th>Lot Name</th><th>Month</th><th>Star Rating</th><th>Comment</th></tr></thead>
          <tbody>{''.join(comment_rows)}</tbody>
        </table>
        </div>
        """
        st.markdown(comments_html, unsafe_allow_html=True)

        # 2. POSITION GROQ AI BUTTON AT THE BOTTOM RIGHT OF THE TABLE
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        btn_col_left, btn_col_right = st.columns([3, 1.5])
        with btn_col_right:
            analyze_clicked = st.button("✨ Analyze Selected Comments with AI", use_container_width=True)

        if analyze_clicked:
            comments_list = comments_df["Comment"].dropna().tolist()
            
            if not comments_list:
                st.warning("No comments available to analyze.")
            else:
                with st.spinner("Analyzing comments with Groq..."):
                    text_to_analyze = "\n- ".join(comments_list[:100])
                    
                    prompt = f"""
                    You are an expert operations analyst for a parking garage company. 
                    Based ONLY on the following customer review comments, provide:
                    1. Top 3 common operational issues or complaints.
                    2. Top positive highlights or themes.
                    3. Actionable recommendations for the Operations Manager.
                    
                    Comments:
                    - {text_to_analyze}
                    """
                    
                    try:
                        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                        
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.1-8b-instant",
                        )
                        
                        st.info("### 🤖 AI Comment Analysis\n" + chat_completion.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Failed to connect to the AI. Make sure you set GROQ_API_KEY in `.streamlit/secrets.toml`. Error: {e}")

    st.markdown('<div class="kpi-spacer"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-title">Garage Movers: '
        f'{pd.Timestamp(prior_month).strftime("%b %Y")} → {pd.Timestamp(current_month).strftime("%b %Y")}</div>',
        unsafe_allow_html=True,
    )
    st.caption("Fixed to sidebar Manager & Month filters. Click a bar to cross-filter everything above by that garage.")
    r3c1, r3c2 = st.columns(2)

    def movers_chart(df_subset, color, key):
        df_subset = df_subset.copy()
        df_subset["short"] = df_subset["Lot Name"].apply(short_label)
        n = max(len(df_subset), 1)
        vmin = df_subset["Rolling MoM Improvement %"].min()
        vmax = df_subset["Rolling MoM Improvement %"].max()
        pad = max(abs(vmin), abs(vmax), 5) * 0.4
        fig = go.Figure(go.Bar(
            x=df_subset["Rolling MoM Improvement %"], y=df_subset["short"], orientation="h",
            marker_color=color, text=df_subset["Rolling MoM Improvement %"].round(1).astype(str) + "%",
            textposition="outside", textfont=dict(size=15, color=SLATE_700),
            customdata=np.stack([
                df_subset["Lot Name"], df_subset["Prior Month Avg"].round(2),
                df_subset["Current Month Avg"].round(2), df_subset["Total Reviews"],
            ], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>MoM Change: %{x:.1f}%<br>"
                "Prior Avg: %{customdata[1]}<br>Current Avg: %{customdata[2]}<br>"
                "Total Reviews: %{customdata[3]}<extra></extra>"
            ),
        ))
        fig.update_traces(width=min(0.7, 6 / n))
        fig.update_layout(
            xaxis_range=[vmin - pad, vmax + pad],
            margin=dict(t=10, b=10, l=10, r=40), height=min(380, max(260, 32 * n + 70)),
            yaxis_title="", bargap=0.3, plot_bgcolor="white", paper_bgcolor="white",
            hoverlabel=HOVER_STYLE, font=CHART_FONT,
        )
        fig.update_xaxes(tickfont=dict(size=13, color=SLATE_700))
        fig.update_yaxes(tickfont=dict(size=14, color=SLATE_700))
        st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points", key=key)

    with r3c1:
        st.markdown('<div class="chart-subtitle">Top 10 Garages by MoM Improvement</div>', unsafe_allow_html=True)
        top10 = base_movers.sort_values("Rolling MoM Improvement %", ascending=False).head(10)
        if top10.empty:
            st.caption("Not enough consecutive-month data to compute improvements.")
        else:
            movers_chart(top10.sort_values("Rolling MoM Improvement %"), MINT, "top10_chart")

    with r3c2:
        st.markdown('<div class="chart-subtitle">Bottom 10 Garages by MoM Decline</div>', unsafe_allow_html=True)
        bottom10 = base_movers.sort_values("Rolling MoM Improvement %", ascending=True).head(10)
        if bottom10.empty:
            st.caption("Not enough consecutive-month data to compute declines.")
        else:
            movers_chart(bottom10.sort_values("Rolling MoM Improvement %", ascending=False), CORAL, "bottom10_chart")

# ==========================================================================
# TAB 2: ALL GARAGES — MoM DETAIL
# ==========================================================================
with tab_detail:
    st.markdown('<div class="section-title">All Garages — Month-over-Month Detail</div>', unsafe_allow_html=True)
    if filtered.empty:
        st.warning("No records match the current click selection. Use ✕ Clear above to reset.")
    else:
        comparison = build_comparison_table(filtered, prior_month, current_month)
        st.caption(
            f"Comparing **{pd.Timestamp(prior_month).strftime('%b %Y')}** (prior) vs "
            f"**{pd.Timestamp(current_month).strftime('%b %Y')}** (current), based on sidebar + click filters."
        )

        search_lot = st.text_input("Search garage name", "", key="detail_search")
        detail_table = comparison.copy()
        if search_lot:
            detail_table = detail_table[detail_table["Lot Name"].str.contains(search_lot, case=False, na=False)]

        html_rows = []
        for _, row in detail_table.iterrows():
            html_rows.append(
                f"<tr><td>{row['Lot Name']}</td>"
                f"<td>{int(row['Total Reviews'])}</td>"
                f"<td>{fmt_num(row['Prior Month Avg'])}</td>"
                f"<td>{fmt_num(row['Current Month Avg'])}</td>"
                f"<td>{fmt_pct_html(row['Rolling MoM Improvement %'])}</td></tr>"
            )

        total_reviews_sum = detail_table["Total Reviews"].sum()
        prior_overall = filtered[filtered["Month"] == prior_month]["Star Rating"].mean()
        current_overall = filtered[filtered["Month"] == current_month]["Star Rating"].mean()
        overall_pct = (
            (current_overall - prior_overall) / prior_overall * 100
            if pd.notna(prior_overall) and prior_overall != 0 else np.nan
        )
        html_rows.append(
            f"<tr class='total-row'><td>Total / Overall</td>"
            f"<td>{int(total_reviews_sum)}</td>"
            f"<td>{fmt_num(prior_overall)}</td>"
            f"<td>{fmt_num(current_overall)}</td>"
            f"<td>{fmt_pct_html(overall_pct)}</td></tr>"
        )

        table_html = f"""
        <div class="mom-table-wrap mom-table">
        <table>
          <thead><tr>
            <th>Lot Name</th><th>Total Reviews</th><th>Prior Month Avg</th>
            <th>Current Month Avg</th><th>Rolling MoM Improvement %</th>
          </tr></thead>
          <tbody>{''.join(html_rows)}</tbody>
        </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)
