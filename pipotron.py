import json
import random
from flask import Flask, request, Response

import pyspoon

app = Flask(__name__)

def random_pipo(intent:str, query:dict) -> dict:
    "Return a pipotron line, ready to be given to spoon"
    with open('pipotron.json') as fd:
        data = json.load(fd)
    s = ' '.join(random.choice(group) for group in data)
    for l in 'aoiueéè':
        s = s.replace(f' le {l}', f' l\'{l}').replace(f' de {l}', f' d\'{l}')
    return pyspoon.spoon_text(s)

pyspoon.make_app(app, {
    'EE-stratégie': random_pipo,
})


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')

