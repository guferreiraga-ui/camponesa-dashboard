import os
import time

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

RED    = "#8B1A1A"
GOLD   = "#C8A000"
DARK   = "#1A1A2E"
GRAY   = "#6B7280"
LIGHT  = "#F4F6F9"
WHITE  = "#FFFFFF"
GREEN  = "#16A34A"
ORANGE = "#EA580C"

st.set_page_config(page_title="Camponesa Decor · Ads", page_icon="📊", layout="wide")
st_autorefresh(interval=REFRESH_MS, key="auto_refresh")

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}

  .header-bar {{
    background: linear-gradient(135deg, {RED} 0%, #6B0F0F 100%);
    border-radius: 16px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(139,26,26,0.18);
  }}
  .header-title {{
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
  }}
  .header-sub {{
    color: rgba(255,255,255,0.65);
    font-size: 13px;
    margin: 2px 0 0 0;
  }}
  .kpi-card {{
    background: {WHITE};
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04);
    border-top: 4px solid {RED};
    margin-bottom: 12px;
  }}
  .kpi-card.gold  {{ border-top-color: {GOLD}; }}
  .kpi-card.green {{ border-top-color: {GREEN}; }}
  .kpi-card.gray  {{ border-top-color: #94A3B8; }}
  .kpi-label {{
    color: {GRAY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 6px;
  }}
  .kpi-value {{
    color: {DARK};
    font-size: 28px;
    font-weight: 800;
    line-height: 1.1;
  }}
  .kpi-sub {{
    color: {GRAY};
    font-size: 12px;
    margin-top: 4px;
  }}
  .section-label {{
    color: {GRAY};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 28px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: #E5E7EB;
  }}
  .badge-active {{
    background: #DCFCE7;
    color: #16A34A;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
  }}
  .badge-paused {{
    background: #FEF9C3;
    color: #854D0E;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
  }}
  .progress-bar-bg {{
    background: #E5E7EB;
    border-radius: 8px;
    height: 8px;
    margin: 8px 0 4px 0;
    overflow: hidden;
  }}
  .progress-bar-fill {{
    height: 8px;
    border-radius: 8px;
    background: linear-gradient(90deg, {RED}, {GOLD});
  }}
  footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
logo_b64 = ""
if os.path.exists("logo.png"):
    import base64
    with open("logo.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

logo_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height:54px;border-radius:8px;background:white;padding:4px">' if logo_b64 else "🐓"

col_h, col_btn = st.columns([5, 1])
with col_h:
    st.markdown(f"""
    <div class="header-bar">
      {logo_tag}
      <div>
        <p class="header-title">Dashboard de Campanhas</p>
        <p class="header-sub">Camponesa Decor · Meta Ads · Atualização automática a cada 15 min</p>
      </div>
    </div>""", unsafe_allow_html=True)
with col_btn:
    st.write("")
    st.write("")
    st.write("")
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

if not TOKEN:
    st.error("TOKEN não configurado. Crie o arquivo `.env` com META_ACCESS_TOKEN.")
    st.stop()

# ── Filtros ───────────────────────────────────────────────────────────────────
PRESETS = {
    "today": "Hoje",
    "yesterday": "Ontem",
    "this_week_mon_today": "Esta semana",
    "this_month": "Este mês",
    "last_7d": "Últimos 7 dias",
    "last_30d": "Últimos 30 dias",
    "last_month": "Mês passado",
}

f1, f2 = st.columns(2)
with f1:
    preset = st.selectbox("Período", list(PRESETS.keys()), index=3, format_func=lambda k: PRESETS[k])

try:
    with st.spinner(""):
        campaigns = get_campaigns(ACCOUNT_ID, TOKEN)

    campaign_options = {"Todas as campanhas": None}
    for c in campaigns:
        campaign_options[c["name"]] = c["id"]

    with f2:
        selected_name = st.selectbox("Campanha", list(campaign_options.keys()))
    selected_id = campaign_options[selected_name]

    with st.spinner("Buscando dados..."):
        insights_raw = get_insights(ACCOUNT_ID, TOKEN, preset, campaign_id=selected_id)

    m = parse_metrics(insights_raw)
    valor_disponivel = calc_budget(campaigns)
    pct_usado = (m["spend"] / valor_disponivel * 100) if valor_disponivel > 0 else 0

    # ── Orçamento KPIs ────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">💰 Orçamento</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)

    def kpi(col, label, value, sub="", accent=""):
        col.markdown(f"""
        <div class="kpi-card {accent}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
        </div>""", unsafe_allow_html=True)

    kpi(k1, "Valor Disponível",  f"R$ {valor_disponivel:,.2f}")
    kpi(k2, "Valor Usado",       f"R$ {m['spend']:,.2f}",  f"{pct_usado:.1f}% consumido", "gold")
    kpi(k3, "CPM",               f"R$ {m['cpm']:.2f}",    "por mil impressões", "gray")
    kpi(k4, "Custo por Lead",    f"R$ {m['cost_per_lead']:.2f}" if m["cost_per_lead"] > 0 else "—", "", "green")

    if valor_disponivel > 0:
        pct_w = min(pct_usado, 100)
        st.markdown(f"""
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width:{pct_w}%"></div>
        </div>
        <p style="color:{GRAY};font-size:12px;margin:0">{pct_usado:.1f}% do orçamento utilizado</p>
        """, unsafe_allow_html=True)

    # ── Funil ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">🎯 Funil de Leads</div>', unsafe_allow_html=True)
    col_kpis, col_chart = st.columns([1, 1], gap="large")

    with col_kpis:
        r1, r2 = st.columns(2)
        kpi(r1, "Impressões",           f"{m['impressions']:,}")
        kpi(r2, "CTR",                  f"{m['ctr']:.2f}%",          "", "gold")
        kpi(r1, "Cliques no Link",      f"{int(m['link_clicks']):,}", "", "gray")
        kpi(r2, "Conversas Iniciadas",  f"{int(m['lead_clicks']):,}", "", "gold")
        kpi(r1, "Leads Totais",         f"{int(m['leads']):,}",       "", "green")
        kpi(r2, "Custo por Lead",       f"R$ {m['cost_per_lead']:.2f}" if m["cost_per_lead"] > 0 else "—", "", "green")

    with col_chart:
        labels = ["Impressões", "Cliques no Link", "Conversas", "Leads"]
        values = [m["impressions"], int(m["link_clicks"]), int(m["lead_clicks"]), int(m["leads"])]
        base   = values[0] if values[0] > 0 else 1
        colors = [RED, ORANGE, GOLD, GREEN]

        def vscale(v):
            return max((v / base) ** 0.38, 0.15) * base

        vtexts = [
            f"<b>{labels[i]}</b><br>{values[i]:,} · {values[i]/base*100:.1f}%"
            for i in range(len(labels))
        ]

        fig = go.Figure(go.Funnel(
            y=labels,
            x=[vscale(v) for v in values],
            text=vtexts,
            textposition="inside",
            textinfo="text",
            textfont=dict(size=14, color="#FFFFFF", family="Inter"),
            marker=dict(color=colors, line=dict(width=2, color=WHITE)),
            connector=dict(line=dict(color="#E5E7EB", width=1), fillcolor=LIGHT),
            opacity=1,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=DARK, size=13, family="Inter"),
            margin=dict(l=0, r=0, t=8, b=8),
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(tickfont=dict(size=13, color=GRAY, family="Inter")),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tabela campanhas ──────────────────────────────────────────────────────
    if campaigns:
        st.markdown('<div class="section-label">📋 Campanhas</div>', unsafe_allow_html=True)
        rows = []
        for c in campaigns:
            budget_raw = float(c.get("daily_budget") or c.get("lifetime_budget") or 0)
            status = "Ativa" if c["status"] == "ACTIVE" else c["status"]
            rows.append({"Campanha": c["name"], "Status": status, "Orçamento (R$)": f"{budget_raw/100:,.2f}"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown(
        f'<p style="color:#9CA3AF;font-size:11px;margin-top:16px;text-align:right">Última atualização: {time.strftime("%d/%m/%Y %H:%M:%S")} · Auto-refresh 15 min</p>',
        unsafe_allow_html=True,
    )

except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    st.info("Verifique se o token tem permissão `ads_read` e está válido.")
