import os
import time
import base64

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

from meta_api import calc_budget, get_campaigns, get_insights, parse_metrics

load_dotenv()

TOKEN      = os.getenv("META_ACCESS_TOKEN") or st.secrets.get("META_ACCESS_TOKEN", "")
ACCOUNT_ID = os.getenv("META_ACCOUNT_ID") or st.secrets.get("META_ACCOUNT_ID", "512456638065694")
REFRESH_MS = 15 * 60 * 1000

BG      = "#0A0812"
CARD    = "#130F1F"
CARD2   = "#1A1430"
GOLD    = "#C8A000"
GOLD2   = "#E8C200"
RED     = "#8B1A1A"
RED2    = "#C0392B"
GREEN   = "#00C48C"
PURPLE  = "#6C63FF"
TEXT    = "#F0EEF5"
MUTED   = "#7B748F"
BORDER  = "rgba(200,160,0,0.15)"

st.set_page_config(page_title="Camponesa Decor · Ads", page_icon="📊", layout="wide")
st_autorefresh(interval=REFRESH_MS, key="auto_refresh")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
}}
.stApp {{ background-color: {BG}; }}
section[data-testid="stSidebar"] {{ background: {CARD}; }}

.header {{
    background: linear-gradient(135deg, #150F25 0%, #1F1535 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
}}
.header-title {{ color: {TEXT}; font-size: 22px; font-weight: 800; margin: 0; letter-spacing: -0.3px; }}
.header-sub {{ color: {MUTED}; font-size: 12px; margin: 3px 0 0 0; }}
.header-badge {{
    margin-left: auto;
    background: rgba(200,160,0,0.12);
    border: 1px solid {GOLD};
    color: {GOLD};
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}}

.kpi {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
}}
.kpi::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, {GOLD}, transparent);
}}
.kpi.green::before {{ background: linear-gradient(90deg, {GREEN}, transparent); }}
.kpi.red::before   {{ background: linear-gradient(90deg, {RED2}, transparent); }}
.kpi.purple::before{{ background: linear-gradient(90deg, {PURPLE}, transparent); }}
.kpi-label {{ color: {MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 6px; }}
.kpi-val   {{ color: {TEXT}; font-size: 26px; font-weight: 800; line-height: 1; }}
.kpi-delta {{ font-size: 11px; font-weight: 600; margin-top: 4px; }}
.kpi-delta.up   {{ color: {GREEN}; }}
.kpi-delta.down {{ color: {RED2}; }}
.kpi-delta.neu  {{ color: {MUTED}; }}

.panel {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px;
}}
.panel-title {{
    color: {GOLD};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.panel-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {BORDER};
}}

.camp-row {{
    display: flex;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    gap: 10px;
}}
.camp-row:last-child {{ border-bottom: none; }}
.camp-name {{ color: {TEXT}; font-size: 12px; font-weight: 500; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.camp-val  {{ color: {GOLD2}; font-size: 12px; font-weight: 700; min-width: 70px; text-align: right; }}
.camp-badge-on  {{ background: rgba(0,196,140,0.15); color: {GREEN}; font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 600; }}
.camp-badge-off {{ background: rgba(139,26,26,0.2); color: {RED2}; font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 600; }}

.ts {{ color: {MUTED}; font-size: 10px; text-align: right; margin-top: 16px; }}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
logo_tag = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    logo_tag = f'<img src="data:image/png;base64,{b64}" style="height:48px;border-radius:8px;background:white;padding:3px">'

h1, h2 = st.columns([5, 1])
with h1:
    st.markdown(f"""
    <div class="header">
      {logo_tag}
      <div>
        <p class="header-title">Dashboard de Campanhas</p>
        <p class="header-sub">Camponesa Decor · Meta Ads</p>
      </div>
      <span class="header-badge">● LIVE</span>
    </div>""", unsafe_allow_html=True)
with h2:
    st.write("")
    st.write("")
    st.write("")
    if st.button("⟳ Atualizar", use_container_width=True):
        st.rerun()

if not TOKEN:
    st.error("TOKEN não configurado.")
    st.stop()

# ── Filtros ───────────────────────────────────────────────────────────────────
PRESETS = {"today":"Hoje","yesterday":"Ontem","this_week_mon_today":"Esta semana",
           "this_month":"Este mês","last_7d":"Últ. 7 dias","last_30d":"Últ. 30 dias","last_month":"Mês passado"}

f1, f2 = st.columns(2)
with f1:
    preset = st.selectbox("Período", list(PRESETS.keys()), index=3, format_func=lambda k: PRESETS[k],
                          label_visibility="collapsed")

try:
    with st.spinner(""):
        campaigns = get_campaigns(ACCOUNT_ID, TOKEN)

    camp_opts = {"Todas as campanhas": None}
    for c in campaigns:
        camp_opts[c["name"]] = c["id"]

    with f2:
        sel_name = st.selectbox("Campanha", list(camp_opts.keys()), label_visibility="collapsed")
    sel_id = camp_opts[sel_name]

    with st.spinner("Carregando..."):
        raw = get_insights(ACCOUNT_ID, TOKEN, preset, campaign_id=sel_id)

    m  = parse_metrics(raw)
    vd = calc_budget(campaigns)
    pct = (m["spend"] / vd * 100) if vd > 0 else 0

    # ── KPI row ───────────────────────────────────────────────────────────────
    def kpi(col, label, val, delta="", dtype="neu", accent=""):
        col.markdown(f"""
        <div class="kpi {accent}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-val">{val}</div>
          {'<div class="kpi-delta ' + dtype + '">' + delta + '</div>' if delta else ''}
        </div>""", unsafe_allow_html=True)

    k = st.columns(6)
    kpi(k[0], "Orçamento Total",   f"R$ {vd:,.0f}")
    kpi(k[1], "Valor Gasto",       f"R$ {m['spend']:,.0f}", f"{pct:.1f}% usado", "down" if pct>80 else "neu", "red")
    kpi(k[2], "Impressões",        f"{m['impressions']:,}", "", "neu", "purple")
    kpi(k[3], "CTR",               f"{m['ctr']:.2f}%", "taxa de cliques", "up" if m['ctr']>1 else "neu")
    kpi(k[4], "Leads Totais",      f"{int(m['leads']):,}", "conversas fechadas", "up" if m['leads']>0 else "neu", "green")
    kpi(k[5], "Custo por Lead",    f"R$ {m['cost_per_lead']:.2f}" if m['cost_per_lead']>0 else "—", "", "neu")

    st.write("")

    # ── Layout principal: campanhas | funil | métricas ────────────────────────
    col_left, col_mid, col_right = st.columns([1.1, 1.4, 0.9])

    # Campanhas
    with col_left:
        rows_html = ""
        for c in campaigns:
            b = float(c.get("daily_budget") or c.get("lifetime_budget") or 0) / 100
            badge = '<span class="camp-badge-on">ATIVA</span>' if c["status"]=="ACTIVE" else '<span class="camp-badge-off">PAUSADA</span>'
            rows_html += f"""
            <div class="camp-row">
              {badge}
              <span class="camp-name" title="{c['name']}">{c['name']}</span>
              <span class="camp-val">R$ {b:,.0f}</span>
            </div>"""
        st.markdown(f"""
        <div class="panel">
          <div class="panel-title">📋 Campanhas</div>
          {rows_html}
        </div>""", unsafe_allow_html=True)

        st.write("")

        # Mini métricas extras
        extras = [
            ("CPM", f"R$ {m['cpm']:.2f}", "por mil impressões"),
            ("Cliques no Link", f"{int(m['link_clicks']):,}", "acessos à página"),
            ("Conversas", f"{int(m['lead_clicks']):,}", "iniciadas no WhatsApp"),
        ]
        for label, val, sub in extras:
            st.markdown(f"""
            <div class="kpi" style="margin-bottom:8px">
              <div class="kpi-label">{label}</div>
              <div class="kpi-val" style="font-size:20px">{val}</div>
              <div class="kpi-delta neu">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # Funil
    with col_mid:
        labels = ["Impressões", "Cliques no Link", "Conversas", "Leads"]
        values = [m["impressions"], int(m["link_clicks"]), int(m["lead_clicks"]), int(m["leads"])]
        base   = values[0] if values[0] > 0 else 1

        def vscale(v):
            return max((v/base)**0.38, 0.15) * base

        vtexts = [
            f"<b>{labels[i]}</b><br>{values[i]:,}  ·  {values[i]/base*100:.1f}%"
            for i in range(len(labels))
        ]

        fig = go.Figure(go.Funnel(
            y=labels,
            x=[vscale(v) for v in values],
            text=vtexts,
            textposition="inside",
            textinfo="text",
            textfont=dict(size=14, color="#FFFFFF", family="Inter"),
            marker=dict(
                color=[RED, "#9B2D2D", GOLD, GREEN],
                line=dict(width=2, color=BG),
            ),
            connector=dict(line=dict(color=BORDER, width=1), fillcolor=CARD2),
            opacity=1,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT, size=13, family="Inter"),
            margin=dict(l=0, r=0, t=4, b=4),
            height=420,
            xaxis=dict(visible=False),
            yaxis=dict(tickfont=dict(size=12, color=MUTED)),
        )
        st.markdown('<div class="panel"><div class="panel-title">🎯 Funil de Leads</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Métricas direita
    with col_right:
        # Gauge orçamento
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(pct, 100),
            number={"suffix": "%", "font": {"color": TEXT, "size": 28, "family": "Inter"}},
            title={"text": "Orçamento Usado", "font": {"color": MUTED, "size": 11, "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"color": MUTED, "size": 9}},
                "bar": {"color": GOLD},
                "bgcolor": CARD2,
                "bordercolor": BORDER,
                "steps": [
                    {"range": [0, 50],  "color": "rgba(200,160,0,0.08)"},
                    {"range": [50, 80], "color": "rgba(200,160,0,0.15)"},
                    {"range": [80, 100],"color": "rgba(192,57,43,0.2)"},
                ],
                "threshold": {"line": {"color": RED2, "width": 3}, "value": 80},
            }
        ))
        fig_g.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            height=220,
            font=dict(family="Inter"),
        )
        st.markdown('<div class="panel"><div class="panel-title">💰 Orçamento</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_g, use_container_width=True)

        spend_disp = f"R$ {m['spend']:,.2f} / R$ {vd:,.2f}"
        st.markdown(f'<p style="color:{MUTED};font-size:11px;text-align:center;margin-top:-10px">{spend_disp}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")

        # Conversão funil
        conv_pairs = [
            ("Imp → Clique", m["impressions"], int(m["link_clicks"])),
            ("Clique → Conv.", int(m["link_clicks"]), int(m["lead_clicks"])),
            ("Conv. → Lead",  int(m["lead_clicks"]), int(m["leads"])),
        ]
        rows2 = ""
        for label, a, b2 in conv_pairs:
            rate = (b2/a*100) if a > 0 else 0
            color = GREEN if rate > 5 else GOLD if rate > 1 else RED2
            rows2 += f"""
            <div class="camp-row">
              <span class="camp-name">{label}</span>
              <span class="camp-val" style="color:{color}">{rate:.1f}%</span>
            </div>"""
        st.markdown(f"""
        <div class="panel">
          <div class="panel-title">📈 Taxas de Conversão</div>
          {rows2}
        </div>""", unsafe_allow_html=True)

    st.markdown(f'<p class="ts">● LIVE · Atualiza a cada 15 min · {time.strftime("%d/%m/%Y %H:%M:%S")}</p>',
                unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")
