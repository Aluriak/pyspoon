import json
import math
import random
import itertools
from PIL import Image
from flask import Flask, request, Response
from functools import partial
from collections import defaultdict, Counter

import pyspoon


HOST = 'https://localhost'
HOST = 'https://1b9efab66a15.ngrok.io'

CONTEXT_COLOR_ASKED = {
    'name': 'projects/spoon-305314/agent/sessions/8838e966-fe17-5fc4-d909-2d884f6ac3b3/contexts/couleur-trouvee',
    'lifespanCount': 3, 'parameters': {'color': [], 'color.original': []}
}

CURRENT_COLOR = None  # Color currently presented to the user
CURRENT_PREDICTION = None  # prediction made for this color, or None


def initialize_found_colors():
    "Read saved colors from local file, initialize global variables"
    try:
        with open('color-state.json') as fd:
            found_colors = json.loads(fd.read().strip() or '{}')
            found_colors = {tuple(map(int, rgb_as_str.split(','))): label
                            for rgb_as_str, label in found_colors.items()}
    except FileNotFoundError:
        found_colors = {(255,0,0): 'rouge', (0,255,0): 'vert', (0,0,255): 'bleu'}
    non_found_colors = set(itertools.product(list(range(0, 240, 20)) + [255], repeat=3))
    non_found_colors = list(non_found_colors - set(found_colors))
    random.shuffle(non_found_colors)
    global FOUND_COLORS, NON_FOUND_COLORS
    FOUND_COLORS, NON_FOUND_COLORS = found_colors, non_found_colors

initialize_found_colors()

def save_found_colors():
    with open('color-state.json', 'w') as fd:
        fd.write(json.dumps({','.join(map(str, rgb)): label for rgb, label in FOUND_COLORS.items()}))
    return {'message': 'saved'}

def reset_found_colors():
    with open('color-state.json', 'w') as fd:
        fd.write(json.dumps({}))
    initialize_found_colors()
    return {'message': 'reset'}

def show_found_colors():
    return {','.join(map(str, rgb)): label for rgb, label in FOUND_COLORS.items()}


def yield_new_color():
    return NON_FOUND_COLORS.pop()

def set_color_label(color:(int, int, int), label:str) -> bool:
    if color in FOUND_COLORS:
        raise ValueError(f'color {color} Already set with label {FOUND_COLORS[color]}!')
    FOUND_COLORS[color] = label.lower().replace(' ')

def predict_color(rgb:(int, int, int), *, knowns:dict=None, k:int=5) -> str:
    "return label predicted for the given rgb color"
    knowns = knowns or FOUND_COLORS
    def dist(one, two):
        # print('DIST:', one, two)
        return math.sqrt((sum(((a - b) ** 2) for a, b in zip(one, two))))
    if len(tuple(knowns.values())) < 2:
        return None
    # get mean distance to existing labels
    distances = defaultdict(list)  # label: distances to known colors
    for known_rgb, label in knowns.items():
        distances[label].append(dist(rgb, known_rgb))
    for label in distances:
        distances[label] = sum(distances[label]) / len(distances[label])
    # get distance to existing colors
    distances = {known_rgb: dist(rgb, known_rgb) for known_rgb in knowns}
    nearests = sorted(distances.items(), key=(lambda t: t[0]))  # smaller distance first
    # get the k nearest neighbors
    if len(distances) > k:
        nearests = nearests[:k]
    counts = Counter(nearests)
    print('PRED:', counts.most_common(1), knowns[counts.most_common(1)[0][0][0]])
    return knowns[counts.most_common(1)[0][0][0]]

def create_image_and_update_state():
    global CURRENT_COLOR, CURRENT_PREDICTION
    CURRENT_COLOR = yield_new_color()
    CURRENT_PREDICTION = predict_color(CURRENT_COLOR)
    img = Image.new('RGB', (200, 200), CURRENT_COLOR)
    img.save('img.jpg')

def color_was_annotated(label:str):
    FOUND_COLORS[CURRENT_COLOR] = label
    create_image_and_update_state()

def get_prediction_text():
    return random.choice([
        "Et ça, est-ce du {} ?",
        "Et ça, serait-ce du {} ?",
        "Et ça, serait-ce {} ?",
        "Je suis sûr que ça c'est {} !",
    ]).format(CURRENT_PREDICTION) if CURRENT_PREDICTION else "C'est quelle couleur, ça ?"


def learn_colors(intent, query:dict, successful_prediction:bool=False):
    # no color was set yet, let's define one
    if CURRENT_COLOR is None:
        create_image_and_update_state()
        return [
            pyspoon.spoon_text("Apprenons les couleurs ensemble !"),
            pyspoon.spoon_text(get_prediction_text()),
            pyspoon.spoon_image(f'{HOST}/img.jpg', duration=5),
        ]

    if successful_prediction:
        detected_color = CURRENT_PREDICTION
    else:  # a color was expected to be predicted by user
        detected_color = query['parameters'].get('color', [])
        detected_color = ' '.join(detected_color if isinstance(detected_color, list) else [detected_color]).lower()
    print(f'GLOBAL: {CURRENT_COLOR=}, {CURRENT_PREDICTION=}')
    print(f'COLOR: {detected_color=}')
    if detected_color:
        color_was_annotated(detected_color)
        return {
            'fulfillmentMessages': [
                # pyspoon.spoon_text(f"RGB {','.join(map(str, CURRENT_COLOR))}, c'est du {detected_color}, c'est noté !"),
                pyspoon.spoon_text(f"Super ! Merci !" if successful_prediction else f"C'est du {detected_color}, c'est noté !"),
                # pyspoon.spoon_wait(2),
                pyspoon.spoon_text(get_prediction_text()),
                pyspoon.spoon_image(f'{HOST}/img.jpg', duration=5),
            ],
            'outputContexts': [] if successful_prediction else [CONTEXT_COLOR_ASKED],
        }
    else:  # no color given, user must just have triggered the activity
        return [
            pyspoon.spoon_text(get_prediction_text()),
            pyspoon.spoon_image(f'{HOST}/img.jpg', duration=5),
        ]


def access_img():
    with open('img.jpg', 'rb') as fd:
        data = fd.read()
    return Response(response=data, mimetype='image/jpg', status=200)


def populate(app):
    app.route('/img.jpg')(access_img)
    app.route('/save_colors')(save_found_colors)
    app.route('/reset_colors')(reset_found_colors)
    app.route('/show_colors')(show_found_colors)
    return {
        'EE-color-learning': learn_colors,
        'EE-bravo-apres-couleur': partial(learn_colors, successful_prediction=True),
    }


if __name__ == '__main__':
    app = Flask(__name__)
    pyspoon.make_app(app, populate(app))
    app.run(debug=True, port=5000, host='127.0.0.1')

