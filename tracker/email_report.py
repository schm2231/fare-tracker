"""Send the daily fare email via Gmail SMTP.

Needs GMAIL_USER and GMAIL_APP_PASSWORD. EMAIL_TO (comma-separated)
defaults to GMAIL_USER. Skips quietly when the secrets aren't set.
"""
import datetime as dt
import html
import json
import os
import smtplib
import urllib.parse
from email.message import EmailMessage

from .report import DOCS

PAGE_URL = os.environ.get("PAGE_URL", "https://schm2231.github.io/fare-tracker/")


def gf(r):
    q = f"Flights from MSP to {r['dest']} on {r['depart']} through {r['return']}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(q)


def fdate(s):
    return dt.date.fromisoformat(s).strftime("%a %b %-d")


def table(rows):
    if not rows:
        return "<p style='color:#666'>Nothing yet.</p>"
    out = ["<table cellpadding='6' style='border-collapse:collapse;font-size:14px'>"]
    for r in rows:
        pct = r.get("pct_vs_typical")
        tag = "" if pct is None else (
            f"<span style='color:#15803d;font-weight:600'>{pct}%</span>" if pct <= -10 else
            f"<span style='color:#888'>{pct:+d}%</span>")
        out.append(
            "<tr style='border-bottom:1px solid #eee'>"
            f"<td>{'★ ' if r.get('watched') else ''}<b>{html.escape(r['city'])}</b> {r['dest']}</td>"
            f"<td><b>${r['price']}</b></td><td>{tag}</td>"
            f"<td>{fdate(r['depart'])} – {fdate(r['return'])}</td>"
            f"<td><a href='{gf(r)}'>check</a></td></tr>")
    out.append("</table>")
    return "".join(out)


def build(d):
    ch = d.get("cheapest", [])
    watched = [r for r in ch if r["watched"]]
    deals = d.get("deals", [])
    parts = [f"<div style='font-family:system-ui,sans-serif;max-width:640px'>",
             f"<h2 style='margin:0'>MSP fares, {fdate(d['latest'])}</h2>",
             f"<p style='color:#666;margin-top:4px'>{d['n_days']} days of history, {d['n_rows']:,} fares logged. "
             f"<a href='{PAGE_URL}'>Open the full page</a></p>"]
    if watched:
        parts += ["<h3>Your watchlist</h3>", table(watched)]
    parts.append("<h3>Deals (20%+ below typical)</h3>")
    if deals:
        parts.append(table(deals))
    elif d["n_days"] < d["min_history_days"]:
        parts.append(f"<p style='color:#666'>Building history: {d['n_days']} of {d['min_history_days']} days logged before deal alerts start.</p>")
    else:
        parts.append("<p style='color:#666'>No deals today.</p>")
    for kind, label in [("wknd", "Cheapest weekends"), ("week", "Cheapest week-long trips")]:
        for region in ["USA", "Canada", "Europe", "South America"]:
            rows = sorted([r for r in ch if r["kind"] == kind and r["region"] == region], key=lambda r: r["price"])[:3]
            if rows:
                parts += [f"<h4 style='margin-bottom:2px'>{label}: {region}</h4>", table(rows)]
    parts.append("</div>")
    n = len(deals)
    subject = f"MSP fares: {n} deal{'s' if n != 1 else ''}" if n else f"MSP fares {fdate(d['latest'])}"
    if watched and any(r in deals for r in watched):
        subject = "★ Watched route deal! " + subject
    return subject, "".join(parts)


def main():
    user, pw = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD")
    d = json.loads((DOCS / "data.json").read_text())
    if not d.get("n_rows"):
        print("email: no data, skipping")
        return
    subject, body = build(d)
    if not (user and pw):
        print(f"email: secrets not set, skipping (would send: {subject})")
        return
    msg = EmailMessage()
    msg["Subject"], msg["From"] = subject, user
    msg["To"] = os.environ.get("EMAIL_TO") or user
    msg.set_content("Open this email in an HTML-capable client, or visit " + PAGE_URL)
    msg.add_alternative(body, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw.replace(" ", ""))
        s.send_message(msg)
    print(f"email: sent '{subject}'")


if __name__ == "__main__":
    main()
