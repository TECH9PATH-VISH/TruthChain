"""
app.py — TruthChain
Streamlit frontend: Hybrid AI + Blockchain news verification.
"""

import time
import datetime
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be FIRST Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TruthChain",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Global CSS — Dark Cyberpunk Theme
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Exo+2:wght@300;400;600&display=swap');

    /* ── Root palette ───────────────────────────────────────────────────── */
    :root {
        --bg:           #080c12;
        --bg-panel:     #0d1520;
        --bg-card:      #111a27;
        --border:       #1c2d42;
        --border-glow:  #1e4976;
        --text:         #c9d8eb;
        --text-dim:     #5a7a9a;
        --text-bright:  #e8f4ff;
        --cyan:         #00d4ff;
        --cyan-dim:     #007a99;
        --green:        #00ff9f;
        --green-dim:    #006644;
        --yellow:       #ffcc00;
        --yellow-dim:   #7a5f00;
        --red:          #ff3860;
        --red-dim:      #7a0025;
        --mono:         'Share Tech Mono', monospace;
        --head:         'Rajdhani', sans-serif;
        --body:         'Exo 2', sans-serif;
    }

    /* ── Global reset ───────────────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"], .main {
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: var(--body) !important;
    }

    /* Scanline overlay */
    [data-testid="stApp"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0,212,255,0.012) 2px,
            rgba(0,212,255,0.012) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }

    /* ── Header strip ───────────────────────────────────────────────────── */
    .tc-header {
        border-bottom: 1px solid var(--border);
        padding: 2rem 0 1.4rem;
        margin-bottom: 2rem;
        position: relative;
    }
    .tc-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 220px;
        height: 1px;
        background: linear-gradient(90deg, var(--cyan), transparent);
    }
    .tc-title {
        font-family: var(--head) !important;
        font-size: 2.6rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em;
        color: var(--text-bright) !important;
        margin: 0 !important;
        line-height: 1.1 !important;
    }
    .tc-title span { color: var(--cyan); }
    .tc-subtitle {
        font-family: var(--mono);
        font-size: 0.72rem;
        color: var(--text-dim);
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-top: 0.4rem;
    }
    .tc-live-dot {
        display: inline-block;
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--green);
        box-shadow: 0 0 6px var(--green);
        margin-right: 6px;
        animation: pulse 1.8s ease-in-out infinite;
        vertical-align: middle;
    }
    @keyframes pulse {
        0%,100% { opacity: 1; }
        50%      { opacity: 0.3; }
    }

    /* ── Labels / badges ────────────────────────────────────────────────── */
    .tc-label {
        font-family: var(--mono);
        font-size: 0.65rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: var(--text-dim);
        margin-bottom: 0.3rem;
    }

    /* ALREADY VERIFIED badge */
    .badge-verified {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(0,255,159,0.08);
        border: 1px solid var(--green);
        border-radius: 4px;
        padding: 0.55rem 1.1rem;
        font-family: var(--head);
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.12em;
        color: var(--green);
        box-shadow: 0 0 18px rgba(0,255,159,0.12), inset 0 0 12px rgba(0,255,159,0.04);
    }

    /* UNIQUE / NEW badge */
    .badge-new {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255,204,0,0.07);
        border: 1px solid var(--yellow);
        border-radius: 4px;
        padding: 0.55rem 1.1rem;
        font-family: var(--head);
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.12em;
        color: var(--yellow);
        box-shadow: 0 0 18px rgba(255,204,0,0.10), inset 0 0 12px rgba(255,204,0,0.03);
    }

    /* ── Cards ──────────────────────────────────────────────────────────── */
    .tc-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1.4rem 1.6rem;
        margin-top: 1rem;
        position: relative;
        overflow: hidden;
    }
    .tc-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 3px; height: 100%;
    }
    .tc-card.cyan::before  { background: var(--cyan); }
    .tc-card.green::before { background: var(--green); }
    .tc-card.yellow::before{ background: var(--yellow);}
    .tc-card.red::before   { background: var(--red);  }

    .tc-card-title {
        font-family: var(--head);
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .tc-card.cyan   .tc-card-title { color: var(--cyan);   }
    .tc-card.green  .tc-card-title { color: var(--green);  }
    .tc-card.yellow .tc-card-title { color: var(--yellow); }
    .tc-card.red    .tc-card-title { color: var(--red);    }

    /* ── Stat rows ──────────────────────────────────────────────────────── */
    .tc-stat {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        border-bottom: 1px solid var(--border);
        padding: 0.45rem 0;
        font-size: 0.88rem;
    }
    .tc-stat:last-child { border-bottom: none; }
    .tc-stat-key  { color: var(--text-dim); font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.1em; }
    .tc-stat-val  { color: var(--text-bright); font-family: var(--mono); font-size: 0.82rem; word-break: break-all; text-align: right; max-width: 62%; }
    .tc-stat-val.green  { color: var(--green);  }
    .tc-stat-val.yellow { color: var(--yellow); }
    .tc-stat-val.cyan   { color: var(--cyan);   }
    .tc-stat-val.red    { color: var(--red);    }

    /* ── Confidence bar ─────────────────────────────────────────────────── */
    .tc-bar-wrap {
        margin-top: 0.8rem;
    }
    .tc-bar-label {
        display: flex;
        justify-content: space-between;
        font-family: var(--mono);
        font-size: 0.68rem;
        color: var(--text-dim);
        margin-bottom: 0.3rem;
    }
    .tc-bar-track {
        height: 5px;
        background: var(--border);
        border-radius: 99px;
        overflow: hidden;
    }
    .tc-bar-fill {
        height: 100%;
        border-radius: 99px;
        transition: width 0.8s ease;
    }
    .tc-bar-fill.green  { background: linear-gradient(90deg, var(--green-dim), var(--green)); }
    .tc-bar-fill.red    { background: linear-gradient(90deg, var(--red-dim),   var(--red));   }

    /* ── Hash display ───────────────────────────────────────────────────── */
    .tc-hash {
        font-family: var(--mono);
        font-size: 0.68rem;
        color: var(--cyan-dim);
        word-break: break-all;
        line-height: 1.7;
        padding: 0.5rem 0.8rem;
        background: rgba(0,212,255,0.03);
        border: 1px solid var(--border);
        border-radius: 4px;
        margin-top: 0.6rem;
    }

    /* ── Divider ─────────────────────────────────────────────────────────  */
    .tc-divider {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.8rem 0;
    }

    /* ── Streamlit widget overrides ──────────────────────────────────────  */
    /* Text area */
    .stTextArea textarea {
        background-color: var(--bg-panel) !important;
        border: 1px solid var(--border-glow) !important;
        border-radius: 4px !important;
        color: var(--text) !important;
        font-family: var(--body) !important;
        font-size: 0.92rem !important;
        caret-color: var(--cyan) !important;
        resize: vertical;
    }
    .stTextArea textarea:focus {
        border-color: var(--cyan) !important;
        box-shadow: 0 0 0 1px var(--cyan), 0 0 14px rgba(0,212,255,0.1) !important;
        outline: none !important;
    }
    .stTextArea label, .stTextArea p {
        font-family: var(--mono) !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.14em !important;
        color: var(--text-dim) !important;
        text-transform: uppercase !important;
    }

    /* Primary button */
    .stButton > button {
        background: transparent !important;
        border: 1px solid var(--cyan) !important;
        border-radius: 4px !important;
        color: var(--cyan) !important;
        font-family: var(--head) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase !important;
        padding: 0.65rem 2.2rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 0 0 rgba(0,212,255,0) !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: rgba(0,212,255,0.08) !important;
        box-shadow: 0 0 20px rgba(0,212,255,0.25) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Spinner */
    .stSpinner > div { border-top-color: var(--cyan) !important; }

    /* Alerts */
    .stAlert { border-radius: 4px !important; }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; max-width: 1060px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="tc-header">
        <div class="tc-title">🔗 Truth<span>Chain</span></div>
        <div class="tc-subtitle">
            <span class="tc-live-dot"></span>
            Hybrid Verification Protocol &nbsp;·&nbsp; AI + Blockchain
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Input area
# ---------------------------------------------------------------------------
article_text = st.text_area(
    "Article / News Input",
    placeholder="Paste the news article or statement you want to verify and mint on-chain…",
    height=180,
)

col_btn, col_pad = st.columns([1, 3])
with col_btn:
    verify_clicked = st.button("⬡  Verify & Mint")

st.markdown('<hr class="tc-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_timestamp(ts: int | None) -> str:
    if ts is None:
        return "—"
    try:
        return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ts)


def _confidence_bar(score: float, label: str) -> str:
    pct   = round(score * 100, 1)
    color = "green" if label == "REAL" else "red"
    return f"""
    <div class="tc-bar-wrap">
        <div class="tc-bar-label">
            <span>CONFIDENCE</span><span>{pct}%</span>
        </div>
        <div class="tc-bar-track">
            <div class="tc-bar-fill {color}" style="width:{pct}%"></div>
        </div>
    </div>
    """


def _stat(key: str, val: str, color: str = "") -> str:
    cls = f' class="{color}"' if color else ""
    return f'<div class="tc-stat"><span class="tc-stat-key">{key}</span><span class="tc-stat-val{" " + color if color else ""}">{val}</span></div>'


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

if verify_clicked:
    if not article_text.strip():
        st.warning("⚠️  Please paste an article before verifying.")
        st.stop()

    # ── Step 1: import modules (defer to show errors gracefully) ────────────
    try:
        import blockchain_recorder as br
    except ConnectionError as e:
        st.error(
            f"**Ganache connection failed.**\n\n"
            f"Make sure Ganache is running at `http://127.0.0.1:7545` before verifying.\n\n"
            f"```\n{e}\n```"
        )
        st.stop()
    except EnvironmentError as e:
        st.error(
            f"**Configuration error.**\n\n"
            f"Check that your `.env` file contains `CONTRACT_ADDRESS` and `PRIVATE_KEY`.\n\n"
            f"```\n{e}\n```"
        )
        st.stop()
    except Exception as e:
        st.error(f"**Unexpected import error:** `{e}`")
        st.stop()

    # ── Step 2: hash check ──────────────────────────────────────────────────
    try:
        with st.spinner("Querying blockchain…"):
            existence = br.check_hash_exists(article_text)
    except Exception as e:
        st.error(f"**Blockchain query failed.** Is Ganache running?\n\n`{e}`")
        st.stop()

    article_hash = existence["article_hash"]
    already_verified = existence["exists"]

    # ── Case A: Already on-chain ────────────────────────────────────────────
    if already_verified:
        st.markdown(
            '<div class="badge-verified">🔒 &nbsp;ALREADY VERIFIED — ON-CHAIN RECORD FOUND</div>',
            unsafe_allow_html=True,
        )

        try:
            with st.spinner("Fetching on-chain record…"):
                record = br.analyze_and_record(article_text)   # returns existing record
        except Exception as e:
            st.error(f"**Failed to fetch on-chain record:** `{e}`")
            st.stop()

        label      = record["label"]
        raw_score  = record["raw_score"]
        timestamp  = record.get("timestamp")
        label_color = "green" if label == "REAL" else "red"

        col_ai, col_chain = st.columns(2, gap="large")

        # Left — AI result
        with col_ai:
            st.markdown(
                f"""
                <div class="tc-card {'green' if label == 'REAL' else 'red'}">
                    <div class="tc-card-title">◈ AI Credibility Result</div>
                    {_stat("VERDICT", label, label_color)}
                    {_stat("RAW SCORE", f"{raw_score:.6f}", label_color)}
                    {_stat("CONFIDENCE", f"{raw_score*100:.1f}%")}
                    {_confidence_bar(raw_score, label)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Right — Blockchain status
        with col_chain:
            short_hash = f"{article_hash[:16]}…{article_hash[-8:]}"
            st.markdown(
                f"""
                <div class="tc-card green">
                    <div class="tc-card-title">⛓ Blockchain Status</div>
                    {_stat("STATUS", "VERIFIED ✔", "green")}
                    {_stat("TIMESTAMP", _fmt_timestamp(timestamp))}
                    {_stat("TX HASH", "—")}
                    {_stat("BLOCK", "—")}
                    <div class="tc-label" style="margin-top:0.9rem">ARTICLE SHA-256</div>
                    <div class="tc-hash">{article_hash}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Case B: New article ─────────────────────────────────────────────────
    else:
        st.markdown(
            '<div class="badge-new">⚠️ &nbsp;UNIQUE VERSION DETECTED — MINTING TO CHAIN</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Run AI detector first so user sees the score before the tx wait
        try:
            with st.spinner("Running AI credibility analysis…"):
                from detector import get_credibility
                credibility = get_credibility(article_text)
        except Exception as e:
            st.error(f"**AI detector failed:** `{e}`")
            st.stop()

        label      = credibility["label"]
        raw_score  = credibility["raw_score"]
        confidence = credibility["confidence"]
        label_color = "green" if label == "REAL" else "red"

        col_ai, col_chain = st.columns(2, gap="large")

        # Left — AI result (show immediately)
        with col_ai:
            st.markdown(
                f"""
                <div class="tc-card {'green' if label == 'REAL' else 'red'}">
                    <div class="tc-card-title">◈ AI Credibility Result</div>
                    {_stat("VERDICT", label, label_color)}
                    {_stat("RAW SCORE", f"{raw_score:.6f}", label_color)}
                    {_stat("CONFIDENCE", f"{confidence*100:.1f}%")}
                    {_confidence_bar(raw_score, label)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Right — send transaction
        with col_chain:
            try:
                with st.spinner("Signing & broadcasting transaction…"):
                    result = br.analyze_and_record(article_text)

                tx_hash    = result.get("tx_hash", "—") or "—"
                block_num  = result.get("block_number", "—")
                short_tx   = f"{tx_hash[:14]}…{tx_hash[-8:]}" if tx_hash != "—" else "—"

                st.markdown(
                    f"""
                    <div class="tc-card cyan">
                        <div class="tc-card-title">⛓ Blockchain Status</div>
                        {_stat("STATUS", "MINTED ✔", "cyan")}
                        {_stat("BLOCK NUMBER", str(block_num), "cyan")}
                        {_stat("TX HASH", short_tx, "cyan")}
                        {_stat("TIMESTAMP", _fmt_timestamp(int(time.time())))}
                        <div class="tc-label" style="margin-top:0.9rem">ARTICLE SHA-256</div>
                        <div class="tc-hash">{article_hash}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            except ConnectionError as e:
                with col_chain:
                    st.error(
                        f"**Ganache unreachable.** Make sure it's running at "
                        f"`http://127.0.0.1:7545`.\n\n`{e}`"
                    )
            except Exception as e:
                with col_chain:
                    st.error(f"**Transaction failed:** `{e}`")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="
        margin-top: 4rem;
        padding-top: 1rem;
        border-top: 1px solid #1c2d42;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.18em;
        color: #2a4060;
        text-align: center;
    ">
        TRUTHCHAIN &nbsp;·&nbsp; HYBRID VERIFICATION PROTOCOL &nbsp;·&nbsp;
        AI MODEL: roberta-base-openai-detector &nbsp;·&nbsp; CHAIN: GANACHE LOCAL
    </div>
    """,
    unsafe_allow_html=True,
)