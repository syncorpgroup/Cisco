from pprint import pprint
import requests
import json
import sys
import os
from flask import Flask
from flask import request

bearer = os.getenv("TOKEN_BOT")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer
}

expected_messages = {"help me": "help",
                     "need help": "help",
                     "can you help me": "help",
                     "ayuda me": "help",
                     "help": "help",
                     "ayudame": "help",
                     "ayuda": "help",
                     "greetings": "greetings",
                     "hello": "greetings",
                     "hi": "greetings",
                     "how are you": "greetings",
                     "what's up": "greetings",
                     "what's up doc": "greetings",
                     "hola": "greetings",
                     "que tal": "greetings",
                     "quiero una cita": "appointment",
                     "Schedule an appointment": "appointment",
                     "appointment": "appointment",
                     "blog": "blog",
                     "blogs": "blog",
                     "post": "blog"
                     }


def send_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js == True:
        request= request.json()
    return request


def send_post(url, data):

    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request


def help_me():

    return "¡Seguro! Puedo ayudar. Aquí los comandos que puedo entender:<br/>" \
           "`ayuda` - Te mostraré una ayuda de lo que puedo hacer.<br/>" \
           "`hola` - Te mostraré un saludo de bienvenida <br/>" \
           "`Repeat after me` - Repetiré todo lo que digas <br/>" \
           "`blogs` - Quiero ver los blogs de **SYNCORP** <br/>" \
           "`Quiero una cita` - Solicitar una cita con **SYNCORP** <br/>"


def greetings():

    return "Hola, mi nombre es %s.<br/>" \
           "Fuí creado por la compañía **SYNCORP**.<br/>" \
           "Escribe `ayuda` para que veas que puedo hacer.<br/>" % bot_name

def appointment():

    return "Como no, no hay problema. Yo, **%s**, te indico como agendarla.<br/>" \
           "Haz click en el enlace, escogiendo un día y hora disponible que más se adapte a su tiempo.<br/>" \
           "- [Agendar cita](https://www.syncorpgroup.com/?hsLeadFlowPreview=868361)<br/>" % bot_name

def blog():

    return "Por supuesto. Aquí el enlace para todos los blogs de **SYNCORP**:<br/>" \
           "> [Blogs de SYNCORP](https://www.syncorpgroup.com/blog/). <br/>" \
           "Uno muy particular es casualmente este bot. Aquí su enlace: <br/>" \
           "> [¿Qué es un Webhook?, un ejemplo con bot](https://www.syncorpgroup.com/2020/06/21/un-delicioso-codigo-pizza-con-python/). <br/>" \

app = Flask('app')
@app.route('/', methods=['GET', 'POST'])
def teams_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        if webhook['data']['personEmail']!= bot_email:
            pprint(webhook)
        if webhook['resource'] == "memberships" and webhook['data']['personEmail'] == bot_email:
            send_post("https://api.ciscospark.com/v1/messages",
                            {
                                "roomId": webhook['data']['roomId'],
                                "markdown": (greetings() +
                                             "**Nota: Este es un cuarto grupal. Debes llamarme"
                                             "especificamente con `@%s` para poder responderte**" % bot_name)
                            }
                            )
        msg = None
        if "@webex.bot" not in webhook['data']['personEmail']:
            result = send_get(
                'https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            translation_table = dict.fromkeys(map(ord, '!@#$.?<>;:%^&'), None)
            in_message = in_message.translate(translation_table)
            if in_message in expected_messages and expected_messages[in_message] == "help":
                msg = help_me()
            elif in_message in expected_messages and expected_messages[in_message] == "greetings":
                msg = greetings()
            elif in_message.startswith("repeat after me"):
                message = in_message.split('repeat after me ')[1]
                if len(message) > 0:
                    msg = "{0}".format(message)
                else:
                    msg = "Oh... no esperaba esto. Disculpe :("
            elif in_message in expected_messages and expected_messages[in_message] == "appointment":
                msg = appointment()
            elif in_message in expected_messages and expected_messages[in_message] == "blog":
                msg = blog()
            else:
                msg = "Lo siento, pero no entendí su solicitud. Por favor escriba `Help me` o `Ayuda` para que vea que puedo hacer"
            if msg != None:
                send_post("https://api.ciscospark.com/v1/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})
        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Webex Teams Bot\" style=\"width:256; height:256;\" </center>" \
                  "<center><h2><b>¡Felicidades! El Bot <i style=\"color:#ff8000;\">%s</i> está `arriba` y funcionando.</b></h2></center>" \
                  "<center><b><i>Se requiere Webhooks de Webex Teams para que funcione este bot. </i></b></center>" \
                  "<center><b><i>Para mayor información sobre sus usos, aquí el enlace: </i></b></center>" \
                  "<center><b><i><a href='https://developer.webex.com/docs/api/v1/webhooks/list-webhooks' target='_blank'>Cisco Webwooks</a> </i></b></center>" \
                  "<center><img src='https://www.syncorpgroup.com/wp-content/uploads/2020/01/cropped-SYNCORP_logo.png' alt='SYNCORP logo' </center>" % bot_name
        return message


def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_get("https://api.ciscospark.com/v1/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.webex.com/my-apps "
                  "and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName","")
            bot_email = test_auth.get("emails","")[0]
    else:
        print("'bearer' variable is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access token, view it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token for your Bot.")
        sys.exit()
    else:
        app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()