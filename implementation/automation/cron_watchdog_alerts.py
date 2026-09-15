#!/usr/bin/env python3
"""
cron_watchdog_alerts.py
Extension of cron_watchdog: when an alert is raised, send notifications to configured channels (Slack webhook, Telegram via bot token/chat_id).
Config file example: cron_watchdog_config.json (see repo)
"""
import os
import json
import requests

HOME = os.path.expanduser('~')
ALERT_DIR = os.path.join(HOME, '.hermes', 'cron', 'alerts')
CONFIG_PATH = os.path.join(HOME, 'Hermes', 'implementation', 'automation', 'cron_watchdog_config.json')


def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def send_slack(webhook, text):
    if not webhook:
        return False, 'no webhook'
    try:
        resp = requests.post(webhook, json={"text": text}, timeout=5)
        return resp.ok, resp.text
    except Exception as e:
        return False, str(e)


def send_telegram(bot_token, chat_id, text):
    if not bot_token or not chat_id:
        return False, 'missing token/chat'
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
        return resp.ok, resp.text
    except Exception as e:
        return False, str(e)


if __name__ == '__main__':
    cfg = load_config()
    # Example usage: python3 cron_watchdog_alerts.py '{"job_id":"x","msg":"..."}'
    import sys
    if len(sys.argv) < 2:
        print('usage: cron_watchdog_alerts.py <json_payload>')
        raise SystemExit(2)
    payload = json.loads(sys.argv[1])
    job_id = payload.get('job_id')
    msg = payload.get('msg')
    cfg_alerts = cfg.get('alerts', {})
    summary = f"CronWatchdog Alert: {job_id} - {msg}"
    results = {}
    if 'slack_webhook' in cfg_alerts:
        ok, res = send_slack(cfg_alerts['slack_webhook'], summary)
        results['slack'] = {'ok': ok, 'res': res}
    if 'telegram' in cfg_alerts:
        t = cfg_alerts['telegram']
        ok, res = send_telegram(t.get('bot_token'), t.get('chat_id'), summary)
        results['telegram'] = {'ok': ok, 'res': res}
    print(json.dumps({'summary': summary, 'results': results}))
