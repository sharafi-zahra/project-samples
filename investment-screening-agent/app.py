"""
Investment Screening — Streamlit UI
Portfolio Manager interface: select a company, run screening, read results.
"""

import re

import streamlit as st
from screening_agent import (
    RunMonitor,
    ScreeningOutput,
    load_deps,
    screen,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Investment Screener",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.verdict-wrap { display: flex; align-items: center; gap: 16px; margin: 4px 0 24px 0; }
.verdict-pill { font-size: 15px; font-weight: 800; letter-spacing: 0.05em; padding: 8px 22px; border-radius: 24px; white-space: nowrap; }
.verdict-high   { background: #d1fae5; color: #065f46; }
.verdict-worth  { background: #dbeafe; color: #1e3a8a; }
.verdict-low    { background: #fef3c7; color: #92400e; }
.verdict-deprio { background: #fee2e2; color: #991b1b; }
.growth-signal  { font-size: 15px; line-height: 1.65; color: #1a2233; flex: 1; }

.section-label { font-size: 11px; font-weight: 700; letter-spacing: 0.10em; text-transform: uppercase; color: #8494aa; margin: 20px 0 10px 0; }

.item-positive { display: flex; align-items: flex-start; gap: 10px; padding: 9px 14px; border-left: 3px solid #1a9e5c; background: #f4fbf7; border-radius: 0 6px 6px 0; margin-bottom: 7px; font-size: 13.5px; line-height: 1.5; color: #1a2233; }
.item-positive::before { content: "↑"; color: #1a9e5c; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
.item-negative { display: flex; align-items: flex-start; gap: 10px; padding: 9px 14px; border-left: 3px solid #c0392b; background: #fdf4f4; border-radius: 0 6px 6px 0; margin-bottom: 7px; font-size: 13.5px; line-height: 1.5; color: #1a2233; }
.item-negative::before { content: "↓"; color: #c0392b; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
.item-risk { display: flex; align-items: flex-start; gap: 10px; padding: 9px 14px; border-left: 3px solid #d4890a; background: #fdf8f0; border-radius: 0 6px 6px 0; margin-bottom: 7px; font-size: 13.5px; line-height: 1.5; color: #1a2233; }
.item-risk::before { content: "⚑"; color: #d4890a; font-weight: 700; flex-shrink: 0; margin-top: 1px; }

.financials-box { background: #f8f9fb; border: 1px solid #dce3ed; border-radius: 8px; padding: 14px 18px; font-size: 13.5px; line-height: 1.7; color: #1a2233; }

.col-header-pos { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #1a9e5c; margin-bottom: 8px; }
.col-header-neg { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #c0392b; margin-bottom: 8px; }

.badge-row { display: flex; flex-wrap: wrap; gap: 7px; margin: 6px 0 18px 0; }
.badge { background: #eef3fb; color: #1e4d8c; border: 1px solid #c5d5ee; border-radius: 20px; padding: 3px 13px; font-size: 12px; font-weight: 600; }

.compliance-pass { background: #eef7f1; border-left: 4px solid #1a9e5c; border-radius: 0 6px 6px 0; padding: 9px 15px; font-size: 12.5px; color: #156b3a; font-weight: 600; margin-bottom: 16px; }
.compliance-fail { background: #fdf0f0; border-left: 4px solid #c0392b; border-radius: 0 6px 6px 0; padding: 9px 15px; font-size: 12.5px; color: #a01a1a; font-weight: 600; margin-bottom: 8px; }

.tool-chain { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin: 6px 0 10px 0; }
.chip-ok  { background: #eef7f1; color: #156b3a; border: 1px solid #a0ddb6; border-radius: 14px; padding: 2px 11px; font-size: 11.5px; font-weight: 600; font-family: monospace; }
.chip-bad { background: #fdf0f0; color: #a01a1a; border: 1px dashed #e08080; border-radius: 14px; padding: 2px 11px; font-size: 11.5px; font-weight: 600; font-family: monospace; text-decoration: line-through; }
.chip-arr { color: #9ba6b8; font-weight: 700; }
.chip-par { color: #6b7280; font-weight: 700; font-size: 13px; padding: 0 3px; }

.mon-row { display: flex; justify-content: space-between; font-size: 12.5px; padding: 4px 0; border-bottom: 1px solid #eaecf0; }
.mon-lbl { color: #6b7280; }
.mon-val { font-weight: 600; color: #1a2233; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*',     r'\1', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__',     r'\1', text, flags=re.DOTALL)
    return text.strip()


def _cards(items: list[str], style: str) -> None:
    html = "".join(f'<div class="item-{style}">{_clean(item)}</div>' for item in items)
    st.markdown(html, unsafe_allow_html=True)


_VERDICT_CSS = {
    "High Priority":        "verdict-high",
    "Worth Further Review": "verdict-worth",
    "Low Priority":         "verdict-low",
    "Deprioritize":         "verdict-deprio",
}


_TOOL_LABELS = {"get_news": "News", "get_fundamentals": "Fundamentals"}


def _tool_chain_html(mon: RunMonitor) -> str:
    # Group called tools by the LLM turn they were issued in.
    # Same llm_turn = parallel dispatch; different turns = sequential.
    by_turn: dict[int, list[str]] = {}
    for tc in mon.tool_call_sequence:
        by_turn.setdefault(tc.get("llm_turn", 1), []).append(tc["tool"])

    turn_htmls = []
    for turn_num in sorted(by_turn):
        tools = by_turn[turn_num]
        chips = [
            f'<span class="chip-ok">✓ {_TOOL_LABELS.get(t, t)}</span>'
            for t in tools
        ]
        # Multiple tools in the same turn were called in parallel
        sep = '<span class="chip-par">  ‖  </span>'
        turn_htmls.append(sep.join(chips))

    # Uncalled tools shown as struck-through at the end
    called_names = {tc["tool"] for tc in mon.tool_call_sequence}
    for tool, label in _TOOL_LABELS.items():
        if tool not in called_names:
            turn_htmls.append(f'<span class="chip-bad">✗ {label}</span>')

    inner = '<span class="chip-arr">→</span>'.join(turn_htmls)
    return f'<div class="tool-chain">{inner}</div>'


# ---------------------------------------------------------------------------
# Data (cached across reruns)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_deps():
    return load_deps()

deps = get_deps()

def _label(row) -> str:
    return f"{row['Name']}  —  {row['BB_Ticker'].split()[0]}  |  {row['Country']}"

company_labels  = deps.companies.apply(_label, axis=1).tolist()
label_to_ticker = {_label(r): r["BB_Ticker"].split()[0] for _, r in deps.companies.iterrows()}
label_to_row    = {_label(r): r                          for _, r in deps.companies.iterrows()}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Investment Screener")
    st.caption("Growth Equity · Early-Stage Screening")
    st.divider()

    selected_label = st.selectbox("Company", company_labels)
    run_clicked    = st.button("Run Screening", type="primary", use_container_width=True)

    st.divider()
    st.markdown("**Monitor**")

    mon: RunMonitor | None = st.session_state.get("monitor")
    if mon is None:
        st.caption("No run yet.")
    else:
        badge_col = "#1a9e5c" if mon.tool_compliance == "Full Input" else "#c0392b"
        st.markdown(
            f'<span style="background:{badge_col};color:#fff;padding:2px 9px;'
            f'border-radius:10px;font-size:11.5px;font-weight:700;">{mon.tool_compliance}</span>',
            unsafe_allow_html=True,
        )
        news_v = "✓" if mon.news_called else "✗"
        fund_v = "✓" if mon.fundamentals_called else "✗"
        st.markdown(f"""
<div class="mon-row"><span class="mon-lbl">News</span><span class="mon-val">{news_v}</span></div>
<div class="mon-row"><span class="mon-lbl">Fundamentals</span><span class="mon-val">{fund_v}</span></div>
<div class="mon-row"><span class="mon-lbl">LLM requests</span><span class="mon-val">{mon.llm_requests}</span></div>
<div class="mon-row"><span class="mon-lbl">Tokens in</span><span class="mon-val">{mon.input_tokens:,}</span></div>
<div class="mon-row"><span class="mon-lbl">Tokens out</span><span class="mon-val">{mon.output_tokens:,}</span></div>
""", unsafe_allow_html=True)
        if mon.tool_call_sequence:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Call order**")
            st.markdown(_tool_chain_html(mon), unsafe_allow_html=True)

    st.divider()
    st.markdown("**Quality**")

    q: dict | None = st.session_state.get("quality")
    if q is None:
        st.caption("No run yet.")
    else:
        checks = [
            (q["schema_complete"],          "Schema"),
            (q.get("fundamentals_available", True), "Fundamentals data"),
            (q["company_in_news"],          "Company name in news"),
            (q["news_positives_filled"],    "News positives"),
            (q["news_negatives_filled"],    "News negatives"),
            (q["risks_filled"],             "Risks"),
        ]
        for ok, label in checks:
            icon = "✅" if ok is True else ("⚠️" if ok is False else "–")
            st.markdown(
                f'<div class="mon-row"><span class="mon-lbl">{label}</span>'
                f'<span class="mon-val">{icon}</span></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run_clicked:
    ticker = label_to_ticker[selected_label]
    with st.spinner(f"Screening {ticker}…"):
        output, mon, quality = screen(ticker, deps)
        company_row          = label_to_row[selected_label]

    st.session_state.output      = output
    st.session_state.monitor     = mon
    st.session_state.quality     = quality
    st.session_state.company_row = company_row
    st.rerun()


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------
output: ScreeningOutput | None = st.session_state.get("output")

if output is None:
    st.markdown("## Investment Screening Agent")
    st.info("Select a company from the sidebar and click **Run Screening**.", icon="ℹ️")
    st.stop()

mon = st.session_state["monitor"]
row = st.session_state["company_row"]

# Company header
st.markdown(f"## {row['Name']}")
st.markdown(
    f'<div class="badge-row">'
    f'<span class="badge">{row["BB_Ticker"].split()[0]}</span>'
    f'<span class="badge">{row["Country"]}</span>'
    f'<span class="badge">{row["Sector"]}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Show a warning in the main panel only when a tool was skipped
missing = [t for t in _TOOL_LABELS if t not in {tc["tool"] for tc in mon.tool_call_sequence}]
if missing:
    missing_labels = [_TOOL_LABELS[t] for t in missing]
    st.warning(
        f"Tool(s) not called: {', '.join(missing_labels)}. Analysis may be incomplete.",
        icon="⚠️",
    )

# Missing fundamentals warning
q = st.session_state.get("quality", {})
if not q.get("fundamentals_available", True):
    st.warning(
        "No financial data available for this company in the dataset. "
        "Financial highlights are based on news only — treat them with caution.",
        icon="⚠️",
    )

# Verdict + growth signal
st.markdown(
    f'<div class="verdict-wrap">'
    f'<span class="verdict-pill {_VERDICT_CSS.get(output.verdict, "verdict-low")}">{output.verdict.upper()}</span>'
    f'<span class="growth-signal">{_clean(output.growth_signal)}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# News
st.markdown('<div class="section-label">Recent News</div>', unsafe_allow_html=True)
col_pos, col_neg = st.columns(2)
with col_pos:
    st.markdown('<div class="col-header-pos">Positives</div>', unsafe_allow_html=True)
    _cards(output.news_positives, "positive")
with col_neg:
    st.markdown('<div class="col-header-neg">Negatives</div>', unsafe_allow_html=True)
    _cards(output.news_negatives, "negative")

# Financials
st.markdown('<div class="section-label">Financial Highlights</div>', unsafe_allow_html=True)
st.markdown(f'<div class="financials-box">{_clean(output.financial_highlights)}</div>', unsafe_allow_html=True)

# Risks
st.markdown('<div class="section-label">Key Risks</div>', unsafe_allow_html=True)
_cards(output.risks, "risk")
