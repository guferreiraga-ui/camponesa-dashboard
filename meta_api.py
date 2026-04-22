import requests

BASE_URL = "https://graph.facebook.com/v19.0"


def _get(url, params):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def get_insights(account_id, token, date_preset="this_month", campaign_id=None):
    FIELDS = "spend,impressions,ctr,cpm,outbound_clicks,actions,cost_per_action_type"
    if campaign_id:
        url = f"{BASE_URL}/{campaign_id}/insights"
    else:
        url = f"{BASE_URL}/act_{account_id}/insights"
    data = _get(url, {"fields": FIELDS, "date_preset": date_preset, "access_token": token})
    rows = data.get("data", [])
    return rows[0] if rows else {}


def get_campaigns(account_id, token):
    data = _get(
        f"{BASE_URL}/act_{account_id}/campaigns",
        {
            "fields": "name,status,daily_budget,lifetime_budget,budget_remaining",
            "access_token": token,
        },
    )
    return data.get("data", [])


def _action_value(items, action_type):
    for item in items or []:
        if item.get("action_type") == action_type:
            return float(item["value"])
    return 0.0


def parse_metrics(insights):
    actions = insights.get("actions", [])
    cpa = insights.get("cost_per_action_type", [])

    # Cliques no link: link_click cobre tanto outbound quanto WhatsApp/Messenger
    link_clicks = _action_value(actions, "link_click")

    # Cliques-lead: conversas iniciadas no WhatsApp/Messenger
    lead_clicks = _action_value(actions, "onsite_conversion.messaging_conversation_started_7d")
    if lead_clicks == 0:
        lead_clicks = _action_value(actions, "onsite_conversion.total_messaging_connection")

    # Leads totais: primeira resposta = lead real engajado
    leads = _action_value(actions, "onsite_conversion.messaging_first_reply")
    if leads == 0:
        leads = _action_value(actions, "lead")
    if leads == 0:
        leads = _action_value(actions, "onsite_conversion.lead_grouped")

    # Custo por lead
    spend = float(insights.get("spend", 0))
    cost_per_lead = spend / leads if leads > 0 else 0.0

    return {
        "spend": spend,
        "impressions": int(insights.get("impressions", 0)),
        "ctr": float(insights.get("ctr", 0)),
        "cpm": float(insights.get("cpm", 0)),
        "link_clicks": link_clicks,
        "lead_clicks": lead_clicks,
        "leads": leads,
        "cost_per_lead": cost_per_lead,
    }


def calc_budget(campaigns):
    daily = sum(
        float(c["daily_budget"]) / 100
        for c in campaigns
        if c.get("status") == "ACTIVE" and c.get("daily_budget")
    )
    lifetime = sum(
        float(c["lifetime_budget"]) / 100
        for c in campaigns
        if c.get("lifetime_budget")
    )
    return daily or lifetime
