import json
from openai import OpenAI
import json

with open("config.json") as f:
    config = json.load(f)

openai_api_key = config["openai_credentials"]["api_key"]
organization = config["openai_credentials"].get("organization")
project_id = config["openai_credentials"].get("project_id")

from openai import OpenAI

client = OpenAI(
    api_key=openai_api_key,
    organization=organization,
    project=project_id
)


def get_all_metadata(input_metadata: dict, model="gpt-4o") -> dict:
    function_schema = {
        "name": "fill_song_metadata",
        "description": "Fill in the missing or incorrect metadata for the song details",
        "parameters": {
            "type": "object",
            "required": [
                "title", "subtitle", "rating", "comments", "contributing_artist",
                "album_artist", "album", "year", "track_number", "genre", "length",
                "bit_rate", "publisher", "encoded_by", "author_url", "copyright",
                "parental_rating_reason", "composers", "conductors", "group_description",
                "mood", "part_of_set", "initial_key", "beats_per_minute_bpm", "protected",
                "part_of_compilation", "disc_number", "isrc", "album_art_url"
            ],
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "rating": {"type": "number"},
                "comments": {"type": "string"},
                "contributing_artist": {"type": "string"},
                "album_artist": {"type": "string"},
                "album": {"type": "string"},
                "year": {"type": "integer"},
                "track_number": {"type": "integer"},
                "disc_number": {"type": "integer"},
                "isrc": {"type": "string"},
                "spotify_url": { "type": "string" },
                "spotify_album_art_url": { "type": "string" },
                "genre": {"type": "string"},
                "length": {"type": "string"},
                "bit_rate": {"type": "number"},
                "publisher": {"type": "string"},
                "encoded_by": {"type": "string"},
                "author_url": {"type": "string"},
                "copyright": {"type": "string"},
                "parental_rating_reason": {"type": "string"},
                "composers": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "conductors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "group_description": {"type": "string"},
                "mood": {"type": "string"},
                "part_of_set": {"type": "string"},
                "initial_key": {"type": "string"},
                "beats_per_minute_bpm": {"type": "number"},
                "protected": {"type": "boolean"},
                "part_of_compilation": {"type": "boolean"}
            },
            "additionalProperties": False
        }
    }

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a music metadata assistant."},
                {"role": "user", "content": "Fill in any missing or incorrect fields for this song metadata:"},
                {"role": "user", "content": json.dumps(input_metadata)}
            ],
            functions=[function_schema],
            function_call={"name": "fill_song_metadata"}
        )

        args_str = response.choices[0].message.function_call.arguments
        return json.loads(args_str)

    except Exception as e:
        print("Error in get_all_metadata:", e)
        return {"error": str(e)}

    
# test_metadata = {
#     "title": "Aquemini",
#     "album_artist": "Outkast",
#     "album": "Aquemini"
# }

# filled = get_all_metadata(test_metadata)
# print(json.dumps(filled, indent=2))

