from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["github_events"]
collection = db["events"]

@app.route("/webhook", methods=["POST"])
def github_webhook():
    data = request.json
    event = request.headers.get("X-GitHub-Event")

    payload = None

    if event == "push":
        payload = {
            "request_id": data["after"],
            "author": data["pusher"]["name"],
            "action": "PUSH",
            "from_branch": None,
            "to_branch": data["ref"].split("/")[-1],
            "timestamp": datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
        }

    elif event == "pull_request":
        pr = data["pull_request"]
        payload = {
            "request_id": str(pr["id"]),
            "author": pr["user"]["login"],
            "action": "MERGE" if pr["merged"] else "PULL_REQUEST",
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
        }

    if payload:
        collection.insert_one(payload)

    return jsonify({"message": "Event processed"}), 200


@app.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find({}, {"_id": 0}).sort("timestamp", -1))
    return jsonify(events)

