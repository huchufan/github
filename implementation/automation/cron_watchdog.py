#!/usr/bin/env python3
"""
cron_watchdog.py
Simple watchdog for cron job outputs: given a list of job records (job_id, expected_path_pattern, max_wait_seconds, retries)
- If expected output not present within max_wait_seconds after job last run time, will trigger `hermes cron run <job_id>` to retry up to retries times.
- Logs alerts to ~/.hermes/cron/alerts/<job_id>_<timestamp>.log and writes a short summary to the Obsidian Hermes inbox.

Usage: python3 cron_watchdog.py --config /path/to/config.json
If no config provided, embedded defaults are used for known jobs.
"""

import argparse
import json
import os
import subprocess
import time
import datetime
import glob

HOME = os.path.expanduser('~')
ALERT_DIR = os.path.join(HOME, '.hermes', 'cron', 'alerts')
OBSIDIAN_INBOX = os.path.expanduser('/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes')

DEFAULT_JOBS = [
    {
        "job_id": "f2c85fc1ce2e",
        "name": "Hermes daily progress (auto)",
        "expected_glob": os.path.join(HOME, '.hermes', 'cron', 'output', 'f2c85fc1ce2e', datetime.datetime.now().strftime('%Y-%m-%d').replace('-','') + '*'),
        "max_wait_seconds": 300,
        "retries": 1
    },
    {
        "job_id": "1e603de2005b",
        "name": "benchmark-weekly",
        "expected_glob": os.path.join(os.path.expanduser('/Users/huchufan/Hermes/implementation/automation/benchmarks'), datetime.datetime.now().strftime('%Y%m%d') + '*'),
        "max_wait_seconds": 300,
        "retries": 1
    }
]


def ensure_dirs():
    os.makedirs(ALERT_DIR, exist_ok=True)
    os.makedirs(OBSIDIAN_INBOX, exist_ok=True)


def find_matching(path_glob):
    return glob.glob(path_glob)


def hermes_cron_run(job_id):
    try:
        subprocess.run(['hermes', 'cron', 'run', job_id], check=True)
        return True, ''
    except subprocess.CalledProcessError as e:
        return False, str(e)


def write_alert(job, msg):
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = os.path.join(ALERT_DIR, f'{job["job_id"]}_{ts}.log')
    with open(fn, 'w') as f:
        f.write(msg)
    # also append brief to Obsidian inbox daily progress
    inbox_file = os.path.join(OBSIDIAN_INBOX, 'CRON_WATCHDOG_ALERTS.md')
    with open(inbox_file, 'a') as ib:
        ib.write(f"- {ts} {job['job_id']} {job.get('name','')} : {msg}\n")
    return fn


def check_and_maybe_retry(job):
    start = time.time()
    waited = 0
    found = False
    reason = ''
    while waited < job['max_wait_seconds']:
        matches = find_matching(job['expected_glob'])
        if matches:
            found = True
            break
        time.sleep(2)
        waited = time.time() - start
    if found:
        return True, f'found {len(matches)} files'

    # not found, attempt retries
    attempts = 0
    while attempts < job.get('retries', 1):
        attempts += 1
        ok, err = hermes_cron_run(job['job_id'])
        if ok:
            # wait briefly for output
            time.sleep(5)
            matches = find_matching(job['expected_glob'])
            if matches:
                return True, f'retry success, found {len(matches)} files after attempt {attempts}'
        else:
            reason = err
    # still not found
    msg = f"Watchdog: job {job['job_id']} ({job.get('name')}) missing expected output after {job['max_wait_seconds']}s and {attempts} retries. last_err: {reason}"
    alert_path = write_alert(job, msg)
    return False, f'failed, alert written to {alert_path}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='path to json config')
    args = parser.parse_args()

    ensure_dirs()
    jobs = DEFAULT_JOBS
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config) as f:
                jobs = json.load(f)
        except Exception:
            pass

    summary = []
    for job in jobs:
        ok, info = check_and_maybe_retry(job)
        summary.append({'job_id': job['job_id'], 'ok': ok, 'info': info})

    # write summary
    out = os.path.join(ALERT_DIR, 'watchdog_summary_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    with open(out, 'w') as f:
        json.dump({'ts': datetime.datetime.now().isoformat(), 'summary': summary}, f, indent=2)
    print(out)

if __name__ == '__main__':
    main()
