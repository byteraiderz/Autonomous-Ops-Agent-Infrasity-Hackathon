import html
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import app as agent_app
from email_reader import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, fetch_latest_customer_email


st.set_page_config(
    page_title="Operations Command Center",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

openai_configured = bool((os.getenv("OPENAI_API_KEY") or os.getenv("openai_key") or "").strip())
gmail_configured = bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)
slack_configured = bool(os.getenv("SLACK_WEBHOOK_URL", "").strip())
notion_configured = bool(os.getenv("NOTION_TOKEN", "").strip() and os.getenv("NOTION_DATABASE_ID", "").strip())

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      :root { --ink:#17243a; --muted:#65758d; --line:#e3e9f2; --accent:#5067df; --paper:#ffffff; }
      .stApp { background:radial-gradient(ellipse at 88% 0%,#e8edff 0,transparent 32%),#f4f6fb; color:var(--ink); font-family:'DM Sans',sans-serif; }
      [data-testid="stHeader"] { background:transparent; }
      [data-testid="stSidebar"] { background:#101a2b; border-right:1px solid rgba(255,255,255,.08); }
      [data-testid="stSidebar"] * { color:#e8edf6; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#9caac0; }
      [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.13); margin:1.15rem 0; }
      .block-container { max-width:1320px; padding-top:2rem; padding-bottom:3rem; }
      .brand-mark { display:flex; align-items:center; gap:.7rem; margin:.25rem 0 1.4rem; }
      .brand-icon { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:linear-gradient(135deg,#6379f0,#4259cc); color:white; font-size:1.15rem; box-shadow:0 8px 20px rgba(67,89,204,.3); }
      .brand-name { color:#f5f7fc; font-family:'Manrope',sans-serif; font-weight:800; letter-spacing:-.03em; font-size:1.08rem; }
      .brand-caption { color:#8998af; font-size:.67rem; letter-spacing:.14em; text-transform:uppercase; margin-top:.05rem; }
      .side-label { color:#8493aa; font-size:.68rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; margin:1rem 0 .6rem; }
      .side-status { display:flex; align-items:center; gap:.65rem; padding:.45rem 0; }
      .side-status-copy { display:flex; flex-direction:column; line-height:1.35; }
      .side-status-copy strong { color:#e9eef8; font-size:.85rem; font-weight:600; }
      .side-status-copy span { color:#94a2b8; font-size:.72rem; }
      .status-dot { width:8px; height:8px; border-radius:50%; background:#f1b95b; box-shadow:0 0 0 4px rgba(241,185,91,.13); flex:0 0 auto; }
      .status-dot.ready { background:#48d29a; box-shadow:0 0 0 4px rgba(72,210,154,.13); }
      .side-footer { color:#8090a8; font-size:.75rem; line-height:1.5; }
      .hero { padding:.45rem 0 1.35rem; }
      .eyebrow { color:#536de5; font-size:.7rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; margin-bottom:.55rem; }
      .hero-row { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; }
      .hero h1 { color:#152238; font-family:'Manrope',sans-serif; font-size:2.45rem; letter-spacing:-.055em; line-height:1.1; margin:0 0 .5rem; }
      .hero p { color:#6c7c93; font-size:1rem; margin:0; max-width:650px; }
      .hero-tag { display:inline-flex; align-items:center; gap:.5rem; border:1px solid #dce4f2; background:rgba(255,255,255,.75); color:#53627a; padding:.55rem .8rem; border-radius:999px; font-size:.77rem; font-weight:700; white-space:nowrap; }
      .hero-tag-dot { width:7px; height:7px; border-radius:50%; background:#536de5; }
      .integration-card { height:100%; min-height:94px; padding:1rem 1.05rem; border:1px solid var(--line); border-radius:15px; background:rgba(255,255,255,.88); box-shadow:0 6px 20px rgba(23,36,58,.035); }
      .integration-top { display:flex; justify-content:space-between; align-items:center; gap:.5rem; }
      .integration-name { color:#27364d; font-weight:700; font-size:.9rem; }
      .integration-state { border-radius:999px; padding:.25rem .5rem; font-size:.65rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
      .integration-state.ready { color:#197e5b; background:#e6f7ef; }
      .integration-state.pending { color:#8b6a2d; background:#fff4dc; }
      .integration-detail { color:#78879d; font-size:.76rem; margin-top:.4rem; }
      div[data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.3rem; box-shadow:0 10px 28px rgba(26,43,71,.045); }
      h2,h3 { color:#1d2c43; font-family:'Manrope',sans-serif !important; letter-spacing:-.025em; }
      h3 { font-size:1.05rem !important; }
      .panel-kicker { color:#7b8aa0; font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.25rem; }
      .stButton button[kind="primary"] { background:linear-gradient(100deg,#4d63d8,#6879ed); border:0; border-radius:12px; min-height:3.2rem; font-size:.96rem; font-weight:700; box-shadow:0 6px 15px rgba(78,99,216,.2); transition:transform .15s,box-shadow .15s; }
      .stButton button[kind="primary"]:hover { background:linear-gradient(100deg,#4358cb,#5d70e4); box-shadow:0 9px 20px rgba(78,99,216,.25); transform:translateY(-1px); }
      .empty-state { display:flex; align-items:center; gap:.9rem; margin-top:.85rem; padding:.9rem 1rem; border:1px dashed #d9e1ee; border-radius:13px; background:#f8faff; }
      .empty-icon { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:#edf1ff; color:#536de5; font-size:1.05rem; flex:0 0 auto; }
      .empty-copy strong { display:block; color:#2e3d54; font-size:.86rem; }
      .empty-copy span { color:#7b8aa0; font-size:.76rem; }
      .mail-meta { color:#687991; font-size:.82rem; margin:.15rem 0 .75rem; }
      .mail-meta strong { color:#27364d; }
      .customer-email-body { color:#111827 !important; background:#fff; border:1px solid #dbe2ea; border-radius:12px; padding:1.1rem 1.15rem; white-space:pre-wrap; overflow-wrap:anywhere; font-family:'DM Sans',sans-serif; font-size:.95rem; line-height:1.7; }
      .decision-badge { display:inline-flex; align-items:center; border-radius:999px; padding:.4rem .72rem; font-family:'Manrope',sans-serif; font-size:.79rem; font-weight:800; letter-spacing:.06em; }
      .decision-refund { color:#8c5712; background:#fff2dc; border:1px solid #f5ddb0; }
      .decision-ask { color:#3958b4; background:#eef2ff; border:1px solid #dce4ff; }
      .decision-escalate { color:#a43f4f; background:#fff0f0; border:1px solid #f3d2d6; }
      .decision-unknown { color:#59677c; background:#f0f3f7; border:1px solid #dce3eb; }
      .result-summary { color:#53627a; font-size:.9rem; margin:.7rem 0 .25rem; }
      .action-output { color:#27364d; background:#f8faff; border:1px solid #e1e7f1; border-radius:12px; padding:1rem; white-space:pre-wrap; overflow-wrap:anywhere; font-size:.88rem; line-height:1.6; }
      [data-testid="stAlert"] { border-radius:12px; }
      @media(max-width:800px) { .block-container{padding:1.25rem 1rem 2rem;} .hero-row{display:block;} .hero-tag{margin-top:1rem;} .hero h1{font-size:1.9rem;} }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_integration_card(column, name: str, detail: str, ready: bool) -> None:
    state = "Ready" if ready else "Needs setup"
    state_class = "ready" if ready else "pending"
    column.markdown(
        f'<div class="integration-card"><div class="integration-top">'
        f'<span class="integration-name">{html.escape(name)}</span>'
        f'<span class="integration-state {state_class}">{state}</span></div>'
        f'<div class="integration-detail">{html.escape(detail)}</div></div>',
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(
        '<div class="brand-mark"><div class="brand-icon">✦</div><div>'
        '<div class="brand-name">OpsDesk</div><div class="brand-caption">Customer operations</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    st.markdown("**Live inbox**")
    st.caption("Fetch unread customer email and route it through the operations agent.")
    st.divider()
    st.markdown('<div class="side-label">Configuration</div>', unsafe_allow_html=True)
    for label, ready, detail in (
        ("Gmail inbox", gmail_configured, "IMAP and SMTP credentials"),
        ("OpenAI agent", openai_configured, "Model API key"),
        ("Slack webhook", slack_configured, "Optional team notifications"),
        ("Notion audit", notion_configured, "Optional audit logging"),
    ):
        state_class = "ready" if ready else ""
        state_text = "Configured" if ready else "Not configured"
        st.markdown(
            f'<div class="side-status"><span class="status-dot {state_class}"></span>'
            f'<div class="side-status-copy"><strong>{html.escape(label)}</strong>'
            f'<span>{state_text}</span></div></div>',
            unsafe_allow_html=True,
        )
    st.divider()
    st.markdown(
        '<div class="side-footer">Track 6 · Operations automation prototype<br>'
        'Review external actions before using with real customer data.</div>',
        unsafe_allow_html=True,
    )


st.markdown(
    '<div class="hero"><div class="eyebrow">Operations workspace · Track 6</div>'
    '<div class="hero-row"><div><h1>Operations Command Center</h1>'
    '<p>Turn customer emails into clear, reviewable next steps with an AI operations agent.</p>'
    '</div><div class="hero-tag"><span class="hero-tag-dot"></span>Local workspace</div></div></div>',
    unsafe_allow_html=True,
)

status_columns = st.columns(4, gap="small")
render_integration_card(status_columns[0], "Gmail inbox", "Unread email intake · IMAP / SMTP", gmail_configured)
render_integration_card(status_columns[1], "AI triage", "Classification · GPT-4o mini", openai_configured)
render_integration_card(status_columns[2], "Slack", "Team notifications · optional", slack_configured)
render_integration_card(status_columns[3], "Notion", "Audit logging · optional", notion_configured)

st.write("")
with st.container(border=True, key="inbox_panel"):
    st.markdown('<div class="panel-kicker">Inbox control</div>', unsafe_allow_html=True)
    st.subheader("Fetch a customer email")
    st.write("The agent checks the inbox for the newest unread message and prepares the next step.")
    fetch_clicked = st.button("Fetch latest unread email", type="primary", use_container_width=True)
    st.markdown(
        '<div class="empty-state"><div class="empty-icon">✉</div><div class="empty-copy">'
        '<strong>Ready when you are</strong><span>Unread messages stay unread in Gmail after fetching.</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )


if fetch_clicked:
    try:
        with st.spinner("Connecting to Gmail and checking for unread email…"):
            fetched_data = fetch_latest_customer_email()

        if fetched_data is None:
            st.info("No unread emails found in the inbox.")
        else:
            live_email = fetched_data["body"]
            sender = fetched_data.get("sender", "Unknown sender")

            with st.container(border=True, key="fetched_customer_email"):
                st.markdown('<div class="panel-kicker">New message</div>', unsafe_allow_html=True)
                st.subheader("Fetched customer email")
                st.markdown(
                    f'<div class="mail-meta">From <strong>{html.escape(sender)}</strong></div>'
                    f'<div class="customer-email-body">{html.escape(live_email)}</div>',
                    unsafe_allow_html=True,
                )

            with st.spinner("The agent is analyzing the message and preparing actions…"):
                result = agent_app.invoke(
                    {
                        "email_content": live_email,
                        "customer_email": sender,
                        "decision": "",
                        "issue_summary": "",
                        "refund_amount": "",
                        "missing_info": [],
                        "action_result": "",
                    }
                )

            decision = str(result.get("decision", "UNKNOWN")).strip().upper()
            decision_classes = {
                "REFUND": "decision-refund",
                "ASK_INFO": "decision-ask",
                "ESCALATE": "decision-escalate",
            }
            decision_class = decision_classes.get(decision, "decision-unknown")
            decision_titles = {
                "REFUND": "Refund or replacement request",
                "ASK_INFO": "More information needed",
                "ESCALATE": "Technical issue escalated",
                "UNKNOWN": "Manual review recommended",
            }
            issue_summary = result.get("issue_summary") or "No issue summary returned."
            action_text = result.get("action_result") or "No actions recorded."

            st.markdown('<div class="panel-kicker">Agent output</div>', unsafe_allow_html=True)
            st.subheader("Workflow results")
            reasoning_col, actions_col = st.columns([0.9, 1.1], gap="large")
            with reasoning_col:
                with st.container(border=True):
                    st.markdown('<div class="panel-kicker">Triage decision</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<span class="decision-badge {decision_class}">{html.escape(decision)}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="result-summary"><strong>{html.escape(decision_titles.get(decision, "Manual review recommended"))}</strong><br>'
                        f'{html.escape(str(issue_summary))}</div>',
                        unsafe_allow_html=True,
                    )
                    if decision == "ASK_INFO" and result.get("missing_info"):
                        st.caption("Information requested")
                        for item in result["missing_info"]:
                            st.markdown(f"- {html.escape(str(item))}")
                    if decision == "REFUND" and result.get("refund_amount"):
                        st.caption(f"Requested amount: {result['refund_amount']}")
                    if decision == "REFUND":
                        st.caption("Prototype note: this workflow does not enforce a human approval gate.")
            with actions_col:
                with st.container(border=True):
                    st.markdown('<div class="panel-kicker">Workflow activity</div>', unsafe_allow_html=True)
                    st.subheader("Actions and notifications")
                    st.markdown(
                        f'<div class="action-output">{html.escape(str(action_text))}</div>',
                        unsafe_allow_html=True,
                    )
            st.success("Workflow finished")
    except Exception as error:
        st.error(f"Could not complete the email workflow: {error}")
