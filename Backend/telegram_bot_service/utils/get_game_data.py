from pymongo.collection import Collection
def clean_text(text: str) -> str:
    return text.replace("\n", " ")

def get_game_data(game_id: int, collection: Collection) -> dict:
    sheets = collection.find({})
    for sheet in sheets:
        for data_entry in sheet.get('data', []):
            if data_entry.get('id') == game_id:
                return {
                    "id": data_entry.get('id'),
                    "stream": clean_text(data_entry['data'][0]),
                    "title": clean_text(data_entry['data'][1]),
                    "date": clean_text(data_entry['data'][2]),
                    "speaker": clean_text(data_entry['data'][4]),
                    "link": data_entry.get('link', 'No link provided'),
                    "description": data_entry['data'][5]
                }
    return None