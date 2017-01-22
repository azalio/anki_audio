import json
import os


current_dir = os.path.dirname(__file__)
with open(os.path.join(current_dir, 'config.json')) as f:
    conf = json.load(f)
