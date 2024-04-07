import warnings
import os
import datetime
import threading
import logging

from flask import Flask, request, jsonify, render_template
import joblib
from connect_database import add_entry, fetch_all_entries

from utils.url_parser import URLParser

from logs.git_logger import commit_to_github


app = Flask(__name__)


model_path = os.path.join(
    os.path.dirname(__file__), "utils/trained_models/phishing_model.pkl"
)
model = joblib.load(model_path)

date = datetime.datetime.now().strftime("%Y-%m-%d")
filepath = os.path.join(os.path.dirname(__file__), "logs", date + ".log")

logging.basicConfig(filename=filepath, format="%(levelname)s:%(name)s:%(message)s")


@app.route("/predict", methods=["POST"])
def predict():
    ip_address = request.remote_addr

    data = request.get_json()
    url = data["url"]

    parser = URLParser(url)

    prediction = model.predict(parser.np_array())

    output = prediction[0].item()  # Convert numpy integer to Python integer
    # Add an entry
    result = "safe" if output == 0 else "phishing"

    store_thread = threading.Thread(
        target=add_entry,
        args=(
            ip_address,
            datetime.datetime.now(),
            url,
            result,
        ),
    )
    store_thread.start()

    return jsonify(
        {
            "prediction": output,
            "url": url,
            "message": (
                "Prediction says it's a phishing URL"
                if output == 1
                else "Prediction says it's a safe browsing URL"
            ),
        }
    )


@app.route("/fetch", methods=["GET"])
def fetch():
    all_entries = fetch_all_entries()
    for entry in all_entries:
        print(entry)

    return jsonify(all_entries)


@app.route("/history", methods=["GET"])
def fetchui():
    all_entries = fetch_all_entries()

    return render_template("history.html", history=all_entries)


@app.route("/", methods=["POST", "GET"])
def predictui():
    if request.method == "GET":
        return render_template("index.html", prediction="", url=None)
    elif request.method == "POST":
        url = request.form["url"]
        try:
            ip_address = request.remote_addr

            parser = URLParser(url)

            prediction = model.predict(parser.np_array())

            output = prediction[0].item()  # Convert numpy integer to Python integer
            # Add an entry
            result = "safe" if output == 0 else "phishing"
            print(parser.np_array())
            store_thread = threading.Thread(
                target=add_entry,
                args=(
                    ip_address,
                    datetime.datetime.now(),
                    url,
                    result,
                ),
            )
            store_thread.start()
            message = (
                "Prediction says phishing URL"
                if output == 1
                else "Prediction says safe browsing URL"
            )
            return render_template("index.html", prediction=message, url=url)
        except Exception as e:
            print(e)
            return render_template("index.html", prediction="broken url", url=url)


@app.after_request
def after_request(response):
    print("Request processed Successfully!")
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Updating log for {date}"

    commit_to_github(commit_message=commit_message)
    return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)
