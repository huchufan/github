import time

from flask import Flask, jsonify, request

app = Flask('hermes-runner')

@app.route('/run-skill', methods=['POST'])
def run_skill():
    data = request.json or {}
    skill = data.get('skill', 'echo')
    payload = data.get('payload', {})
    # simulate work
    time.sleep(0.5)
    return jsonify({'ok': True, 'skill': skill, 'payload': payload, 'result': f"ran {skill}"})

if __name__ == '__main__':
    import os
port = int(os.environ.get('PORT', '5001'))
app.run(host='0.0.0.0', port=port)
