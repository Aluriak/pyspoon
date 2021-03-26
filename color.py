import json
import random
import itertools
from PIL import Image
from flask import Flask, request, Response

import pyspoon


CURRENT_COLOR = None
FOUND_COLORS = {}  # color (R,G,B) -> label
NON_FOUND_COLORS = set(itertools.product(range(0, 255), repeat=3))
HOST = 'https://localhost'
HOST = 'https://3c48eafd04b4.ngrok.io'


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


def learn_colors(intent, query:dict):
    detected_color = ' '.join(query['parameters']['color']).lower()
    print('GLOBAL:', CURRENT_COLOR)
    print('COLOR:', detected_color)
    if detected_color and CURRENT_COLOR:
        FOUND_COLORS[CURRENT_COLOR] = detected_color
        return [
            pyspoon.spoon_text(f"RGB {','.join(CURRENT_COLOR)}, c'est du {detected_color}, c'est noté !"),
            pyspoon.spoon_wait(2),
            pyspoon.spoon_text("Et ça, c'est quoi ?"),
            pyspoon.spoon_image(f'{HOST}/img.jpg', duration=5),
        ]
    else:  # no color given, user must just have triggered the activity
        return [
            pyspoon.spoon_text("C'est quelle couleur, ça ?"),
            pyspoon.spoon_image(f'{HOST}/img.jpg', duration=5),
        ]


def access_img():
    color = yield_new_color()
    create_image(color)
    global CURRENT_COLOR
    CURRENT_COLOR = color
    with open('img.jpg', 'rb') as fd:
        data = fd.read()
    return Response(response=data, mimetype='image/jpg', status=200)


def populate(app):
    app.route('/img.jpg')(access_img)
    return {
        'EE-color-me-surprised': learn_colors,
    }


if __name__ == '__main__':
    app = Flask(__name__)
    pyspoon.make_app(app, populate(app))
    app.run(debug=True, port=5000, host='127.0.0.1')

