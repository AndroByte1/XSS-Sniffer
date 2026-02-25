from flask import Flask, request, jsonify
from flask_cors import CORS
from curl_cffi import requests

app = Flask(__name__)
CORS(app)

LOG_FILE = "urls.log"

@app.route('/capture-har', methods=['POST'])
def capture_har():
    try:
        data = request.get_json()

        if not data or "pageUrl" not in data:
            return jsonify({"status": "error", "message": "Missing pageUrl"}), 400

        page_url = data["pageUrl"]
        if "?" in page_url:
            try:
                param = page_url.split("&")
                new_param = []
                for i in range(len(param)):
                    key, value = param[i].split("=")
                    value = '"lol"'
                    new_param.append(f"{key}={value}")

                new_url = "&".join(new_param)
                if '"lol"' in r.content.decode('utf-8'):
                    requests.post("your_discord_webhook_token_goes_here",json={"content": f'maybe xss here:- {new_url}'})
                else:
                    print("not posible")
            except Exception as e:
                print(f"Error processing URL: {e}")

        with open(LOG_FILE, "a") as file:
            file.write(f"{page_url}\n")

        print("Captured:", page_url)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=3000)

