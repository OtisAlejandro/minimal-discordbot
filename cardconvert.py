import os
import json
import base64
from PIL import Image
from pathlib import Path
import shutil
import io

CHARACTERS_FOLDER = "Characters"
CARDS_FOLDER = "CardAndJsonFolder"

def save_character(json_data, img, tavern=False):
    """Saves the character data and associated image."""
    json_data = json_data if isinstance(json_data, str) else json_data.decode("utf-8")
    data = json.loads(json_data)
    outfile_name = data["char_name"]
    i = 1
    while Path(f'{CHARACTERS_FOLDER}/{outfile_name}.json').exists():
        outfile_name = f'{data["char_name"]}_{i:03d}'
        i += 1
    if tavern:
        outfile_name = f'TavernAI-{outfile_name}'
    with open(Path(f'{CHARACTERS_FOLDER}/{outfile_name}.json'), 'w') as f:
        f.write(json_data)
    if img is not None:
        img = Image.open(io.BytesIO(img))
        img.save(Path(f'{CHARACTERS_FOLDER}/{outfile_name}.png'))
    print(f'New character saved to "{CHARACTERS_FOLDER}/{outfile_name}.json".')
    return outfile_name

def process_card(img_path):
    """Processes a card file."""
    with open(img_path, 'rb') as read_file:
        img = read_file.read()
    _img = Image.open(io.BytesIO(img))
    decoded_string = base64.b64decode(_img.info['chara'])
    _json = json.loads(decoded_string)
    _json = {"char_name": _json['name'], "char_persona": _json['description'], "char_greeting": _json["first_mes"],
             "example_dialogue": _json['mes_example'], "world_scenario": _json['scenario']}
    _json['example_dialogue'] = _json['example_dialogue'].replace(
        '{{user}}', "User").replace('{{char}}', _json['char_name'])
    return save_character(json.dumps(_json), img, tavern=True)

def process_json(filename):
    """Processes a JSON file."""
    # This function is not necessary since we're not doing any extra processing for json files.
    # I'm keeping it here in case you need to add any extra processing in the future.
    pass

def load_character_from_json(json_path):
    """Loads character data from a JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        char_name = data["char_name"]
        char_persona = data["char_persona"]
        world_scenario = data["world_scenario"]
        example_dialogue = data["example_dialogue"]
    return char_name, char_persona, world_scenario, example_dialogue

def main():
    """Main function to handle the entire process."""
    for filename in os.listdir(CARDS_FOLDER):
        file_path = os.path.join(CARDS_FOLDER, filename)
        
        if filename.endswith('.png'):
            json_filename = process_card(file_path)
            json_path = os.path.join(CHARACTERS_FOLDER, f"{json_filename}.json")
            char_name, char_persona, world_scenario, example_dialogue = load_character_from_json(json_path)
            
        elif filename.endswith('.json'):
            char_name, char_persona, world_scenario, example_dialogue = load_character_from_json(file_path)
            
        else:
            print(f"Unsupported file type: {filename}")
            continue
            
        # Now, you can use the variables `char_name`, `char_persona`, `world_scenario`, `example_dialogue`
        # ...

if __name__ == "__main__":
    main()
