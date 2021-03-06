import os
import sys
import json
import time
from weather import Weather
weather = Weather()
import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world from the PiBot!", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    if (message_text.lower() == "date"):
                        send_message(sender_id, "Date is: "+str(time.gmtime().tm_mday) +"/"+ str(time.gmtime().tm_mon) +"/"+ str(time.gmtime().tm_year))
                    elif (message_text.lower() == "time"):
                        send_message(sender_id, "Time is: "+str(time.gmtime().tm_hour) +":"+ str(time.gmtime().tm_min) +":"+ str(time.gmtime().tm_sec)+" GMT")
                    elif (message_text.lower() == "avail"):
                        send_message(sender_id, "Available commands: date, time, weather")
                    elif (message_text.lower() == "hello" or message_text.lower() == "hi"):
                        send_message(sender_id, "Bonjour! Please type \'avail\' for available commands")
                    elif (message_text.lower()[:7] == "weather"):
                        try:
                            l_name = message_text[8:]
                            temp = (int(weather.lookup_by_location(l_name).condition()['temp'])-32)*5/9
                            send_message(sender_id, "Weather at this location is " + weather.lookup_by_location(l_name).condition()['text'] + ", " + str(temp))
                        except Exception as e: send_message(sender_id, "Unavailable location, or please check syntax: weather [location]")
                    else:
                        send_message(sender_id, "I read: "+message_text+". Please type \"avail\" to check for available commands!")


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
