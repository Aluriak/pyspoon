import json
import random
import itertools
from PIL import Image
from flask import Flask, request, Response


CURRENT_COLOR = None
FOUND_COLORS = {}  # color (R,G,B) -> label
NON_FOUND_COLORS = set(itertools.product(range(0, 255), repeat=3))

def yield_new_color():
    return random.choice(tuple(NON_FOUND_COLORS))

def set_color_label(color:(int, int, int), label:str) -> bool:
    if color in FOUND_COLORS:
        raise ValueError(f'color {color} Already set with label {FOUND_COLORS[color]}!')
    FOUND_COLORS[color] = label.lower().replace(' ')

def create_image(rgb) -> str:
    img = Image.new('RGB', (200, 200), rgb)
    img.save('img.jpg')
    return '/img.jpg'

def random_pipo() -> str:
    with open('pipotron.json') as fd:
        data = json.load(fd)
    s = ' '.join(random.choice(group) for group in data)
    for l in 'aoiueéè':
        s = s.replace(f' le {l}', f' l\'{l}').replace(f' de {l}', f' d\'{l}')
    return s

app = Flask(__name__)

data1 = {
  "spoon": {
    "viewerId": "Image",
    "imagePath": "https://intra-science.anaisequey.com/images/stories/observations/bio-polaire%20(18).jpg",
    "id": "DisplayImage",
  }
}

data2 = {
  "spoon": {
    "answers": [
      {
        "displayText": "La joie !",
        "content": "la joie"
      },
      {
        "displayText": "la tristesse",
        "content": "la tristesse"
      }
    ],
    "id": "MCQ"
  }
}

data3 = {
  "spoon": {
    "id": "EndScenario",
    "afterEndType": "Passive",
    "status:": "Succeeded"
  }
}


def spoon_text(message:str) -> dict:
    return {"payload": {"spoon": { "id": "Say", "text": message }}}

def spoon_image(url:str, *, duration:float=5) -> dict:
    return {"payload": {"spoon": {
            "viewerId": "Image",
            "id": "DisplayImage",
            "imagePath": url,
            "duration": duration
    }}}
def spoon_wait(duration:float=5) -> dict:
    return {"payload": { "spoon": {
                "id": "Wait",
                "duration": duration,
    }}}



@app.route('/', methods=['POST'])
def respond():
    print('REQUEST:', request.json)
    intent = request.json['queryResult']['intent']['displayName']
    if intent != 'EE-color-me-surprised':
        print('Unhandled intent:', intent)
        return
    detected_color = request.json['queryResult']['parameters']['color'].lower()
    print('GLOBAL:', CURRENT_COLOR)
    print('COLOR:', detected_color)
    if detected_color and CURRENT_COLOR:
        FOUND_COLORS[CURRENT_COLOR] = detected_color
        data = {"fulfillmentMessages": [
            spoon_text(f"RGB {','.join(CURRENT_COLOR)}, c'est du {detected_color}, c'est noté !"),
            spoon_wait(2),
            spoon_text("Et ça, c'est quoi ?"),
            spoon_image('https://9e228c08e9b7.ngrok.io/img.jpg', duration=5),
        ]}
    else:  # no color given, user must just have triggered the activity
        data = {"fulfillmentMessages": [
            {"text": {"text": ["Ok."]}},
            spoon_text("C'est quelle couleur, ça ?"),
            spoon_image('https://9e228c08e9b7.ngrok.io/img.jpg', duration=5),
            # {"text": {"text": ["Ok."]}},
            # {"payload": {"spoon": {
                # "id": "Say",
                # "text": "C'est quelle couleur, ça ?",
            # }}},
            # {"payload": {"spoon": {
                # "viewerId": "Image",
                # "id": "DisplayImage",
                # "imagePath": "https://9e228c08e9b7.ngrok.io/img.jpg",
                # "duration": 5
            # }}},
        ]}
    print('DATA:', data)
    return Response(response=json.dumps(data), mimetype='application/json', status=202)
    # return data, 200

@app.route('/img.jpg')
def access_img():
    color = yield_new_color()
    create_image(color)
    global CURRENT_COLOR
    CURRENT_COLOR = color
    with open('img.jpg', 'rb') as fd:
        data = fd.read()
    return Response(response=data, mimetype='image/jpg', status=200)
# help(Response)

app.run(debug=True, port=5000, host='127.0.0.1')
