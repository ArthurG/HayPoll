from flask import Flask, request
import requests
import json
from keys import *
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asker_id = db.Column(db.String(50))
    questionSentence = db.Column(db.String(50))
    def __init__(self, asker, q_string):
        self.asker_id = asker
        self.questionSentence = q_string

class Possibleresponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50))
    question_id =  db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('possibleresponses', lazy='dynamic'))
    def __init__(self, text, question):
        self.question = question
        self.text = text


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    responder_id = db.Column(db.String(50))
    response_value = db.Column(db.String(50))
    question_id =  db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('responses', lazy='dynamic'))
    possibleresponse_id =  db.Column(db.Integer, db.ForeignKey('possibleresponse.id'))
    possibleresponse = db.relationship('Possibleresponse', backref=db.backref('responses', lazy='dynamic'))
    def __init__(self, responder_id, question_id, possibleresponse_id):
        self.responder_id = responder_id
        self.question_id = question_id
        self.possibleresponse_id = possibleresponse_id


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/webhook', methods=['POST'])
def process_webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    print("incoming msg " + str(data))  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                try:
                    if "ask" in messaging_event["message"].get("text", ""):
                        process_new_question(messaging_event)
                    elif "vote" in messaging_event["message"].get("text", ""):
                        process_want_to_vote(messaging_event)
                    elif "view" in messaging_event["message"].get("text", ""):
                        view_vote(messaging_event)
                    elif messaging_event["message"].get("quick_reply", False):
                        process_vote(messaging_event)
                    else:
                        send_message(messaging_event["sender"]["id"], messaging_event["message"].get("text", ""))
                except Exception as e:
                    print(e)
                #message_controller.route(messaging_event)
    return "ok", 200

def send_message(recipient, text):
    data = json.dumps({
        "recipient": {
            "id": recipient
            },
        "message": {

            "text": text,

            }
        })
    params = {
            "access_token": ACCESS_TOKEN
            }
    headers = {
            "Content-Type": "application/json"
            }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)

def send_message_raw(recipient, data):
    params = {
            "access_token": ACCESS_TOKEN
            }
    headers = {
            "Content-Type": "application/json"
            }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)

def process_new_question(msg):
    ques_csv = msg["message"].get("text", "").lstrip("ask ").strip()
    question=ques_csv.split(",")[0]
    possibleresponses=ques_csv.split(",")[1:]
    asker = msg["sender"]["id"]

    new_question = Question(asker, question)
    db.session.add(new_question)
    for p_resp in possibleresponses:
        new_resp = Possibleresponse(p_resp, new_question)
        db.session.add(new_resp)
    db.session.commit()
    send_message(asker, "Your new question has an id of {}".format(new_question.id))

def process_vote(msg) :
    reply_payload = msg["message"]["quick_reply"]["payload"]
    responder=msg['sender']['id']
    reply_obj = {}
    try:
        reply_obj = json.loads(reply_payload)
    except json.decoder.JSONDecodeError:
        send_message(responder, "We could not parse your response :(" )
        return
    q_id = reply_obj['QUESTION_ID']
    resp_id = reply_obj['POSSIBLERESPONSE_ID']
    new_resp = Response(responder, q_id, resp_id)
    db.session.add(new_resp)
    db.session.commit()
    send_message(responder, "Thank you for responding to our survey. Send us 'view {}' to view current standings".format(q_id))

def view_vote(msg):
    question_id = msg["message"]["text"].lstrip("view ")
    sender = msg["sender"]["id"]
    view_vote_two(question_id, sender)

def view_vote_two(question_id, inquirier):
    question = Question.query.filter_by(id=question_id).first()
    responses_and_votes={}
    for possible_response in question.possibleresponses:
        print(possible_response)
        responses_and_votes[possible_response.text] = possible_response.responses.count()

    send_message(inquirier, "Here is your tally for {}".format(question.questionSentence))
    [send_message(inquirier, "{}: {}".format(question, responses_and_votes[question])) for question in responses_and_votes]


def process_want_to_vote(msg):
    question_to_vote_for = msg["message"].get("text","").lstrip("vote ").strip()
    recipient = msg["sender"]["id"]
    question=Question.query.filter_by(id=question_to_vote_for).first()
    send_message(recipient, "The question is, {}".format(question.questionSentence))
    replies=[]
    for possible_response in question.possibleresponses:
        print(possible_response)
        payload = json.dumps({"QUESTION_ID": question.id, "POSSIBLERESPONSE_ID":possible_response.id})
        resp_map = {
                "content_type": "text",
                "title": possible_response.text,
                "payload": payload
                }
        replies.append(resp_map)
    data = json.dumps({
        "recipient": {
            "id": recipient
            },
        "message": {
            "text": "Please select your vote :)",
            "quick_replies":replies
            }
        })
    send_message_raw(msg["sender"]["id"], data)

