import os
import time
from flask import Flask, jsonify, Response, send_file, request

app = Flask(__name__)

NETWORK_LOGS = []
FINGERPRINTING_LOGS = []
FPD_LOGS = []

@app.post("/reset")
def reset():
    NETWORK_LOGS.clear()
    FINGERPRINTING_LOGS.clear()
    FPD_LOGS.clear()
    return "logs cleared"


@app.get("/logs")
def logs():
    return jsonify(NETWORK_LOGS)


@app.get("/fingerprinting-logs")
def fingerprinting_logs():
    return jsonify(FINGERPRINTING_LOGS)


@app.get("/fpd-logs")
def fpd_logs():
    return jsonify(FPD_LOGS)


@app.post("/fingerprinting-reset")
def fingerprinting_reset():
    FINGERPRINTING_LOGS.clear()
    return "fingerprinting logs cleared"


@app.post("/fpd-reset")
def fpd_reset():
    FPD_LOGS.clear()
    return "fpd logs cleared"


@app.get("/network")
def network():
    return send_file("network.html")


@app.get("/img")
def img():
    NETWORK_LOGS.append({
        "time": time.time(),
        "type": "img",
    })
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'
    return Response(svg, mimetype="image/svg+xml")


@app.get("/script")
def script():
    NETWORK_LOGS.append({
        "time": time.time(),
        "type": "script",
    })
    return Response("console.log('script loaded');", mimetype="application/javascript")


@app.get("/iframe")
def iframe():
    NETWORK_LOGS.append({
        "time": time.time(),
        "type": "iframe",
    })
    html = """
    <!doctype html>
    <html>
      <body>
        iframe loaded
        <script>
          window.parent.postMessage("iframe-loaded", "*");
        </script>
      </body>
    </html>
    """
    return Response(html, mimetype="text/html")


@app.post("/collect")
def collect():
    payload = request.get_json(force=True, silent=True) or {}
    FINGERPRINTING_LOGS.append({
        "time": time.time(),
        "payload": payload,
    })
    return jsonify({"ok": True})


@app.get("/fingerprinting")
def fingerprinting():
    return send_file("fingerprinting.html")

@app.post("/fpd-collect")
def fpd_collect():
    payload = request.get_json(force=True, silent=True) or {}
    FPD_LOGS.append({
        "time": time.time(),
        "payload": payload,
    })
    return jsonify({"ok": True})


@app.get("/fpd")
def fpd():
    return send_file("fpd.html")


@app.get("/geo")
def geo():
    return send_file("geo.html")


@app.get("/sensor")
def sensor():
    return send_file("sensor.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    ssl_context = "adhoc" if port == 5443 else None
    app.run(host="0.0.0.0", port=port, ssl_context=ssl_context)