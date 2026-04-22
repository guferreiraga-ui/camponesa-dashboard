import os, time, base64, html
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh
from meta_api import calc_budget, get_campaigns, get_insights, parse_metrics

load_dotenv()
TOKEN      = os.getenv("META_ACCESS_TOKEN") or st.secrets.get("META_ACCESS_TOKEN", "")
ACCOUNT_ID = os.getenv("META_ACCOUNT_ID")   or st.secrets.get("META_ACCOUNT_ID", "512456638065694")
REFRESH_MS = 15 * 60 * 1000

st.set_page_config(page_title="Camponesa · Ads", page_icon="📊", layout="wide")
st_autorefresh(interval=REFRESH_MS, key="ar")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#08060F!important}
.stApp{background:#08060F}
div[data-testid="stVerticalBlock"]{gap:0}
/* remove default streamlit padding */
.block-container{padding-top:1rem!important}
/* selectbox */
div[data-baseweb="select"]>div{background:#130F1F!important;border-color:rgba(200,160,0,.2)!important;color:#F0EEF5!important}

.hdr{background:linear-gradient(135deg,#120D22,#1C1535);border:1px solid rgba(200,160,0,.18);border-radius:14px;padding:14px 22px;display:flex;align-items:center;gap:14px;margin-bottom:18px}
.hdr-title{color:#F0EEF5;font-size:21px;font-weight:800;margin:0}
.hdr-sub{color:#7B748F;font-size:11px;margin:2px 0 0}
.live{margin-left:auto;background:rgba(0,196,140,.12);border:1px solid #00C48C;color:#00C48C;font-size:10px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:.8px}

.kcard{background:#130F1F;border:1px solid rgba(200,160,0,.15);border-radius:11px;padding:15px 17px;position:relative;overflow:hidden;margin-bottom:14px}
.kcard::after{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.kcard.g::after{background:linear-gradient(90deg,#00C48C,transparent)}
.kcard.y::after{background:linear-gradient(90deg,#C8A000,transparent)}
.kcard.r::after{background:linear-gradient(90deg,#C0392B,transparent)}
.kcard.p::after{background:linear-gradient(90deg,#6C63FF,transparent)}
.kcard.w::after{background:linear-gradient(90deg,#8B85A0,transparent)}
.klbl{color:#7B748F;font-size:9px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;margin-bottom:5px}
.kval{color:#F0EEF5;font-size:24px;font-weight:800;line-height:1.1}
.ksub{color:#7B748F;font-size:10px;margin-top:3px}

.panel{background:#130F1F;border:1px solid rgba(200,160,0,.15);border-radius:12px;padding:16px;margin-bottom:14px}
.ptitle{color:#C8A000;font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid rgba(200,160,0,.12)}

.crow{display:flex;align-items:center;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);gap:8px}
.crow:last-child{border-bottom:none}
.cname{color:#D0CCDF;font-size:11px;font-weight:500;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cval{color:#E8C200;font-size:11px;font-weight:700;min-width:65px;text-align:right}
.bon{background:rgba(0,196,140,.12);color:#00C48C;font-size:9px;padding:2px 6px;border-radius:8px;font-weight:700}
.boff{background:rgba(192,57,43,.15);color:#C0392B;font-size:9px;padding:2px 6px;border-radius:8px;font-weight:700}

.funnel-wrap{padding:8px 0}
.fstep{text-align:center;padding:18px 0;margin-bottom:3px;position:relative;transition:.2s}
.fstep-inner{display:flex;justify-content:space-between;align-items:center;padding:0 12%}
.fname{color:rgba(255,255,255,.85);font-size:11px;font-weight:600;text-align:left}
.fval{color:#fff;font-size:15px;font-weight:800}
.fpct{color:rgba(255,255,255,.6);font-size:10px;text-align:right}

.rate-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.rate-row:last-child{border-bottom:none}
.rlbl{color:#7B748F;font-size:11px}
.rval{font-size:12px;font-weight:700}

.ts{color:#3D3652;font-size:10px;text-align:right;margin-top:12px;padding-top:8px;border-top:1px solid rgba(255,255,255,.04)}
</style>
""", unsafe_allow_html=True)

# ── Logo ──────────────────────────────────────────────────────────────────────
logo_tag = "🐓"
if os.path.exists("logo.png"):
    with open("logo.png","rb") as f:
        b = base64.b64encode(f.read()).decode()
    logo_tag = f'<img src="data:image/png;base64,{b}" style="height:46px;border-radius:7px;background:#fff;padding:3px">'

hcol, bcol = st.columns([6,1])
with hcol:
    st.markdown(f'<div class="hdr">{logo_tag}<div><p class="hdr-title">Dashboard de Campanhas</p><p class="hdr-sub">Camponesa Decor · Meta Ads</p></div><span class="live">● LIVE</span></div>', unsafe_allow_html=True)
with bcol:
    st.write(""); st.write(""); st.write("")
    if st.button("⟳ Atualizar", use_container_width=True): st.rerun()

if not TOKEN:
    st.error("TOKEN não configurado."); st.stop()

# ── Filtros ───────────────────────────────────────────────────────────────────
PRESETS = {"today":"Hoje","yesterday":"Ontem","this_week_mon_today":"Esta semana",
           "this_month":"Este mês","last_7d":"Últ. 7 dias","last_30d":"Últ. 30 dias"}
f1,f2 = st.columns(2)
with f1: preset = st.selectbox("Período", list(PRESETS.keys()), index=3, format_func=lambda k:PRESETS[k])

try:
    campaigns = get_campaigns(ACCOUNT_ID, TOKEN)
    opts = {"Todas as campanhas": None, **{c["name"]: c["id"] for c in campaigns}}
    with f2: sel = st.selectbox("Campanha", list(opts.keys()))
    raw = get_insights(ACCOUNT_ID, TOKEN, preset, campaign_id=opts[sel])
    m   = parse_metrics(raw)
    vd  = calc_budget(campaigns)
    pct = (m["spend"]/vd*100) if vd>0 else 0

    # ── KPIs ─────────────────────────────────────────────────────────────────
    def kcard(col, lbl, val, sub="", acc="w"):
        col.markdown(f'<div class="kcard {acc}"><div class="klbl">{lbl}</div><div class="kval">{val}</div>{"<div class=ksub>"+sub+"</div>" if sub else ""}</div>', unsafe_allow_html=True)

    k = st.columns(6)
    kcard(k[0],"Orçamento",    f"R$ {vd:,.0f}",           "",                           "y")
    kcard(k[1],"Gasto",        f"R$ {m['spend']:,.0f}",   f"{pct:.1f}% consumido",       "r")
    kcard(k[2],"Impressões",   f"{m['impressions']:,}",   "",                           "p")
    kcard(k[3],"CTR",          f"{m['ctr']:.2f}%",        "taxa de cliques",             "w")
    kcard(k[4],"Leads",        f"{int(m['leads']):,}",    "conversas fechadas",          "g")
    kcard(k[5],"Custo/Lead",   f"R$ {m['cost_per_lead']:.2f}" if m["cost_per_lead"]>0 else "—","","y")

    # ── 3 colunas ─────────────────────────────────────────────────────────────
    cl, cm, cr = st.columns([1, 1.3, 0.9])

    # ── Esquerda: campanhas + métricas ────────────────────────────────────────
    with cl:
        rows = ""
        for c in campaigns:
            b2 = float(c.get("daily_budget") or c.get("lifetime_budget") or 0)/100
            badge = '<span class="bon">ATIVA</span>' if c["status"]=="ACTIVE" else '<span class="boff">PAUSADA</span>'
            name  = html.escape(c["name"])
            rows += f'<div class="crow">{badge}<span class="cname" title="{name}">{name}</span><span class="cval">R$ {b2:,.0f}</span></div>'
        st.markdown(f'<div class="panel"><div class="ptitle">📋 Campanhas</div>{rows}</div>', unsafe_allow_html=True)

        extras = [
            ("CPM",            f"R$ {m['cpm']:.2f}",         "por mil impressões", "y"),
            ("Cliques no Link",f"{int(m['link_clicks']):,}", "acessos à página",   "w"),
            ("Conversas",      f"{int(m['lead_clicks']):,}", "iniciadas",           "g"),
        ]
        for lbl,val,sub,acc in extras:
            kcard(cl, lbl, val, sub, acc)

    # ── Centro: funil CSS ─────────────────────────────────────────────────────
    with cm:
        labels = ["Impressões","Cliques no Link","Conversas","Leads"]
        values = [m["impressions"], int(m["link_clicks"]), int(m["lead_clicks"]), int(m["leads"])]
        base   = values[0] if values[0]>0 else 1
        colors = ["#8B1A1A","#B83232","#C8A000","#00C48C"]
        clips  = [
            "polygon(0% 0%,100% 0%,91% 100%,9% 100%)",
            "polygon(9% 0%,91% 0%,82% 100%,18% 100%)",
            "polygon(18% 0%,82% 0%,73% 100%,27% 100%)",
            "polygon(27% 0%,73% 0%,68% 100%,32% 100%)",
        ]
        steps = ""
        for i,(lbl,val) in enumerate(zip(labels,values)):
            p = val/base*100
            steps += f"""
            <div style="clip-path:{clips[i]};background:{colors[i]};padding:22px 0;margin-bottom:4px;border-radius:3px">
              <div style="display:flex;justify-content:space-between;align-items:center;padding:0 18%">
                <span style="color:rgba(255,255,255,.8);font-size:11px;font-weight:600">{lbl}</span>
                <span style="color:#fff;font-size:15px;font-weight:800">{val:,}</span>
                <span style="color:rgba(255,255,255,.55);font-size:10px">{p:.1f}%</span>
              </div>
            </div>"""
        st.markdown(f'<div class="panel"><div class="ptitle">🎯 Funil de Leads</div><div style="padding:4px 0">{steps}</div></div>', unsafe_allow_html=True)

    # ── Direita: gauge + taxas ────────────────────────────────────────────────
    with cr:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(pct,100),
            number={"suffix":"%","font":{"color":"#F0EEF5","size":30,"family":"Inter"}},
            title={"text":"Orçamento Usado","font":{"color":"#7B748F","size":10,"family":"Inter"}},
            gauge={
                "axis":{"range":[0,100],"tickcolor":"#3D3652","tickfont":{"color":"#3D3652","size":8}},
                "bar":{"color":"#C8A000"},
                "bgcolor":"#1A1430",
                "bordercolor":"rgba(200,160,0,.15)",
                "steps":[
                    {"range":[0,50],"color":"rgba(200,160,0,.06)"},
                    {"range":[50,80],"color":"rgba(200,160,0,.12)"},
                    {"range":[80,100],"color":"rgba(192,57,43,.18)"},
                ],
                "threshold":{"line":{"color":"#C0392B","width":3},"value":80},
            }
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=10,r=10,t=30,b=5),height=200,font=dict(family="Inter"))
        st.markdown('<div class="panel"><div class="ptitle">💰 Orçamento</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<p style="color:#3D3652;font-size:10px;text-align:center;margin:-8px 0 8px">R$ {m["spend"]:,.2f} de R$ {vd:,.2f}</p></div>', unsafe_allow_html=True)

        pairs = [
            ("Imp → Clique",  m["impressions"],        int(m["link_clicks"])),
            ("Clique → Conv.",int(m["link_clicks"]),   int(m["lead_clicks"])),
            ("Conv. → Lead",  int(m["lead_clicks"]),   int(m["leads"])),
        ]
        rrows = ""
        for lbl,a,b2 in pairs:
            r = (b2/a*100) if a>0 else 0
            col = "#00C48C" if r>5 else "#C8A000" if r>1 else "#C0392B"
            rrows += f'<div class="rate-row"><span class="rlbl">{lbl}</span><span class="rval" style="color:{col}">{r:.1f}%</span></div>'
        st.markdown(f'<div class="panel"><div class="ptitle">📈 Taxas de Conversão</div>{rrows}</div>', unsafe_allow_html=True)

    st.markdown(f'<p class="ts">● LIVE · Auto-refresh 15min · {time.strftime("%d/%m/%Y %H:%M:%S")}</p>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")
