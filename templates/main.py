from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder=None)

@app.route("/")
def home():
    return send_from_directory("templates", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
