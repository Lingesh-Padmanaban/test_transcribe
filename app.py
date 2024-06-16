import json, os
from flask import Flask, request, Response, jsonify, render_template
from flask_sock import Sock, ConnectionClosed
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv

from ASR_TTS import *


load_dotenv(find_dotenv(), override=True)


app = Flask(__name__)
sock = Sock(app)
CORS(app)

@sock.route("/transcribe")
def transcribe(ws):
    while True:
        message = ws.receive()
        data = json.loads(message)
        try:
            if data["status"] == "started":
                ts = dg_asr.TranscriptionService()
            if data["status"] == "progress":
                speech = ts.streaming_data(data["buffer"])
                if speech!=None:
                    ws.send({"transcript":speech})
            if data["status"] == "end":
                ts.close_connection()
        except Exception as e:
            ws.send({"message": e})