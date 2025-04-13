"""
Template starter file for pyscript project

Works with the following html:

<h1>Polyglot 🦜 💬 🇬🇧 ➡️ 🏴‍☠️</h1>
<p>Translate English into Pirate speak...</p>
<input type="text" id="english" placeholder="Type English here..." />
<button py-click="translate_english">Translate</button>
<div id="output"></div>
<script type="py" src="{{ url_for('pyscript.static', path='src/main.py') }}" config="{{ url_for('pyscript.static', path='pyscript.json') }}"></script>

Put this html into the body of your html file
"""

import arrr
from pyscript import document

def translate_english(event):
    input_text = document.querySelector("#english")
    english = input_text.value
    output_div = document.querySelector("#output")
    output_div.innerText = arrr.translate(english)
