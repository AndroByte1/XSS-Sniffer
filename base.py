from flask import Flask, request, jsonify
from flask_cors import CORS
from curl_cffi import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import os
import secrets

app = Flask(__name__)
CORS(app)

LOG_FILE = "urls.log"
DISCORD_WEBHOOK = "discord_web_token_here"

# Base XSS probes (benign strings that test different contexts)
XSS_PROBES = [
    '"lol"',
    "'",
    '"',
    '">',
    "'>",
    '>',
    '<',
    '</x>',
    ' " onmouseover=',
    'javascript:',
    '&quot;',
    'expression(',
    "';",
    '";',
    '`',
    '${}',
    '<!--',
    '-->',
]

# Unique token to identify our injected values
UNIQUE_TOKEN = "XSSPROBE"

def log_entry(message):
    """Append to log file with timestamp"""
    with open(LOG_FILE, "a") as file:
        file.write(f"{datetime.now()} - {message}\n")

def test_xss_probes(original_url, cookie_string):
    """
    For each query parameter, replace its value with a token + probe,
    request the modified URL, and check if the token is reflected.
    """
    parsed = urlparse(original_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if not params:
        log_entry("No query parameters to test")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    if cookie_string:
        headers["Cookie"] = cookie_string

    for param_name, original_values in params.items():
        for probe in XSS_PROBES:
            # Combine token and probe to create a unique test string
            test_value = f"{UNIQUE_TOKEN}{probe}"

            # Create a new parameter set with the current test value
            new_params = params.copy()
            new_params[param_name] = [test_value]

            # Rebuild URL
            new_query = urlencode(new_params, doseq=True)
            new_url = urlunparse(parsed._replace(query=new_query))

            try:
                r = requests.get(
                    new_url,
                    headers=headers,
                    impersonate="chrome110",
                    allow_redirects=True,
                    timeout=10
                )

                # Check if our token appears in the response
                if UNIQUE_TOKEN in r.text:
                    # Determine if the full test value (token + probe) is reflected
                    full_reflected = test_value in r.text

                    discord_payload = {
                        "content": f"🔍 XSS Probe Reflected!",
                        "embeds": [{
                            "title": "Potential XSS Entry Point",
                            "description": (
                                f"**Parameter**: `{param_name}`\n"
                                f"**Probe**: `{probe}`\n"
                                f"**Token found?** Yes\n"
                                f"**Full probe reflected?** {'Yes' if full_reflected else 'No (maybe filtered/encoded)'}\n"
                                f"**URL**: {new_url}\n"
                                f"**Cookies**: {cookie_string[:1000]}\n"
                                f"**Response Length**: {len(r.text)} bytes"
                            ),
                            "color": 16776960  # Yellow
                        }]
                    }
                    requests.post(DISCORD_WEBHOOK, json=discord_payload)
                    log_entry(f"PROBE REFLECTED: {param_name} with '{probe}' on {new_url} (full={full_reflected})")
            except Exception as e:
                log_entry(f"Request failed for {new_url}: {str(e)}")

@app.route('/capture-har', methods=['POST'])
def capture_har():
    try:
        data = request.get_json()
        if not data:
            log_entry("ERROR: No data received")
            return jsonify({"status": "error", "message": "No data received"}), 400

        page_url = data.get("pageUrl", "")
        cookie_string = data.get("cookies", "")
        timestamp = data.get("timestamp", datetime.now().isoformat())

        if not page_url:
            log_entry("ERROR: Missing pageUrl")
            return jsonify({"status": "error", "message": "Missing pageUrl"}), 400

        log_entry(f"URL: {page_url}")
        if cookie_string:
            log_entry(f"COOKIES: {cookie_string}")
        else:
            log_entry("NO COOKIES RECEIVED")

        if "?" in page_url:
            test_xss_probes(page_url, cookie_string)
        else:
            log_entry("No query parameters - XSS probe skipped")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        log_entry(f"CRITICAL ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(f"Scoped HAR Logger - Started at {datetime.now()}\n")

    app.run(host="127.0.0.1", port=3000)
