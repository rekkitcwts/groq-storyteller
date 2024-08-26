import os
from dotenv import load_dotenv
import groq
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists
from sqlalchemy import func, exc
from groq import Groq
import json
import urllib.parse

load_dotenv()
app = Flask(__name__)
groq_api_key = os.getenv("GROQ_API_KEY")
db = SQLAlchemy()
db_name = "StackOverflow.db"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///'+db_name
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

from everglen_models import *

client = Groq(
    api_key=groq_api_key
)

if database_exists('sqlite:///instance/'+db_name):
    print(db_name + " already exists.")
else:
    print(db_name + " does not exist, will create " + db_name)
    # this is needed in order for database session calls (e.g. db.session.commit)
    with app.app_context():
        try:
            db.create_all()
        except exc.SQLAlchemyError as sqlalchemyerror:
        	print("got the following SQLAlchemyError: " + str(sqlalchemyerror))
        except Exception as exception:
        	print("got the following Exception: " + str(exception))
        finally:
        	print("db.create_all() was successfull - no exceptions were raised")
            
'''
Homepage.
Self explanatory.
'''
@app.route('/')
def hello():
	return render_template('mainpage.html', title="Everglen AI Engine")
    
@app.route('/new_ui')
def new_ui():
    return render_template('base_azimuth.html', title="Everglen AI Engine - Beta UI")
    
'''
Helper function for post requests - post requests are now parsed as bytes 
Takes bytes that go with something like foo=123def&bar=456abc
Should return a dictionary object
'''
def byteNonsense(bytesNonsense):
    data = bytesNonsense.decode('utf8')
    parsed_data = urllib.parse.parse_qs(data)
    outputCleaned = {}
    for key, value in parsed_data.items():
        keys = key.split('[')
        current_dict = outputCleaned
        for i, k in enumerate(keys):
            k = k.rstrip(']')
            if i == len(keys) - 1:
                current_dict[k] = value[0]
            else:
                if k not in current_dict:
                    current_dict[k] = {}
                current_dict = current_dict[k]
    return outputCleaned
    
'''
APIs for the characters.
'''
@app.route('/api/characters/list', methods=['GET'])
def api_characters_list():
    characters = CharacterDB.query.order_by(CharacterDB.character_name.asc()).all()
    character_list = []
    for row in characters:
        character_list.append({'id': row.id, 'character_name': row.character_name, 'character_age': row.character_age, 'character_gender': row.character_gender, 'character_personality': row.character_personality, 'high_school_clique': row.high_school_clique, 'cultural_background': row.cultural_background, 'current_job': row.current_job, 'additional_desc': row.additional_desc})
    return jsonify(character_list)
    
@app.route('/api/characters/scan', methods=['POST'])
def api_characters_scan():
    something = byteNonsense(request.data)
    story = something['story']
    characters = extract_characters(story)
    print(characters)
    return jsonify({"characters": characters})
    
@app.route('/api/characters/add', methods=['POST'])
def api_characters_add():
    something = byteNonsense(request.data)
    print(something)
    newCharacter = CharacterDB(
        character_name = something['name'],
        character_age = something['age'],
        character_gender = something['gender'],
        character_personality = something['personality'],
        high_school_clique = something['high_school_clique'],
        current_job = something['current_job'],
        additional_desc = something['additional_desc'],
        cultural_background = something['cultural_background']
    )
    db.session.add(newCharacter)
    db.session.commit()
    print(newCharacter.id)
    return jsonify({'character_id': newCharacter.id, 'message': 'CHARACTER_ADDED' , 'status': 'OK'})
    
# Intended to be unused, to trick Javascript side
@app.route('/api/characters', methods=['GET'])
def api_character_url_trick():
    pass
    
@app.route('/api/characters/view/<character_id>', methods=['GET'])
def api_characters_view(character_id):
    row = CharacterDB.query.filter_by(id=character_id).first()
    char_rel = getCharacterRelationships(row, "database")
    full_character_details = {
        "character": {'id': row.id, 'character_name': row.character_name, 'character_age': row.character_age, 'character_gender': row.character_gender, 'character_personality': row.character_personality, 'high_school_clique': row.high_school_clique, 'cultural_background': row.cultural_background, 'current_job': row.current_job, 'additional_desc': row.additional_desc},
        "relationships": char_rel
    }
    print(full_character_details)
    return jsonify(full_character_details)
    
@app.route('/api/characters/edit', methods=['POST'])
def api_characters_edit():
    something = byteNonsense(request.data)
    character_id = something['id']
    character = CharacterDB.query.filter_by(id=character_id).first()
    character.character_name = something['name']
    character.character_age = something['age']
    character.character_gender = something['gender']
    character.character_personality = something['personality']
    character.high_school_clique = something['high_school_clique']
    character.cultural_background = something['cultural_background']
    character.current_job = something['current_job']
    character.additional_desc = something['additional_desc']
    db.session.commit()
    return jsonify({'character_id': character_id, 'message': 'PROFILE_UPDATED' , 'status': 'OK'})

'''
APIs for handling character connections,
also known as Relationships in the database and in Groq.
'''
@app.route('/api/relationships/add', methods=['POST'])
def api_relationships_add():
    something = byteNonsense(request.data)
    print(something)
    newConnection = RelationshipDB(
        char_subject_id = something['relation_subject'],
        char_object_id = something['relation_object'],
        relation = something['relation']
    )
    db.session.add(newConnection)
    db.session.commit()
    return jsonify({'character_id': newConnection.id, 'message': 'CONNECTION_ADDED' , 'status': 'OK'})
    
@app.route('/api/relationships/edit', methods=['POST'])
def api_relationships_edit():
    something = byteNonsense(request.data)
    print(something)
    relationship_to_edit = RelationshipDB.query.filter_by(id=something['relation_id']).first()
    relationship_to_edit.char_subject_id = something['relation_subject']
    relationship_to_edit.char_object_id = something['relation_object']
    relationship_to_edit.relation = something['relation']
    db.session.commit()
    return jsonify({'character_id': relationship_to_edit.id, 'message': 'CONNECTION_UPDATED' , 'status': 'OK'})
    
'''
APIs for the list of stories and the series they belong to.
''' 
@app.route('/api/series/add', methods=['POST'])
def api_series_add():
    print(request.data)
    something = byteNonsense(request.data)
    print(something)
    newseries = SeriesDB(series_name = something['series_name'], series_desc = something['series_desc'])
    db.session.add(newseries)
    db.session.commit()
    print(newseries.id)
    return jsonify({'series_id': newseries.id, 'message': 'SERIES_ADDED' , 'status': 'OK'})
    
@app.route('/api/series/list', methods=['GET'])
def api_series_list():
    series = SeriesDB.query.all()
    series_list = []
    for row in series:
        stories = StoryDB.query.filter_by(series_id=row.id).all()
        series_list.append({
            'id': row.id, 
            'series_name': row.series_name, 
            'series_desc': row.series_desc,
            'stories': [
                {
                    'id': story.id,
                    'story_title': story.story_title,
                    'episode_number': story.episode_number,
                    'location': story.location,
                    'plot': story.plot,
                    'full_story': story.full_story
                }
                for story in stories
            ]
        })
    return jsonify(series_list)
    
@app.route('/api/stories/generate', methods=['POST'])
def api_story_generate():
    something = byteNonsense(request.data)
    print(something)
    location = something['location']
    summary = something['summary']
    series = something['series']
    series_title = SeriesDB.query.filter_by(id=series['id']).first()
    characters = something['characters']
    character_AI_models = []
    character_relationships = []
    print(series_title.series_name)
    for key in characters:
        character = characters[key]
        character_db_model = CharacterDB.query.filter_by(id=character['id']).first()
        character_AI_models.append(character_db_model.getAIModel())
        char_rel = getCharacterRelationships(character_db_model)
        character_relationships = character_relationships + char_rel

    
    try:
        if character_relationships:
            generated_story = generate_story(scenario=summary, custom_characters=character_AI_models, location=location, relationships=character_relationships)
        else:
            generated_story = generate_story(scenario=summary, custom_characters=character_AI_models, location=location)

        story_title = json.loads(generated_story)['title']
        output = expand_plot_to_story(json.loads(generated_story)['plot'])
        print(output)
        return jsonify({"story_title": story_title, "story": output})
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/stories/humanize', methods=['POST'])
def api_story_humanize():
    something = byteNonsense(request.data)
    #print(something)
    story_original = something['original_story']
    characters = something['story_characters']
    character_AI_models = []
    character_relationships = []
    for key in characters:
        character = characters[key]
        character_db_model = CharacterDB.query.filter_by(id=character['id']).first()
        character_AI_models.append(character_db_model.getAIModel())
        char_rel = getCharacterRelationships(character_db_model)
        character_relationships = character_relationships + char_rel
    
    output = story_humanizer_nonjson(story_original, character_AI_models, character_relationships)
    print(output)
    return jsonify({"output": output}), 200
    

@app.route('/api/stories/save', methods=['POST'])
def api_story_save():
    story_title = ""
    plot = ""
    location = ""

    something = byteNonsense(request.data)
    print(something['story_origin'])
    series = SeriesDB.query.filter_by(id=something['series']['id']).first()
    characters = something['characters']
    
    full_story = something['full_story']
    num_episodes = StoryDB.query.filter_by(series_id=something['series']['id']).count()
    new_episode_number = num_episodes + 1
    
    if something['story_origin'] == "generated_from_plot":
        story_title = something['story_title']
        plot = something['plot']
        location = something['location']
    if something['story_origin'] == "imported":
        character_AI_models = []
        character_relationships = []
        for key in characters:
            character = characters[key]
            character_db_model = CharacterDB.query.filter_by(id=character['id']).first()
            character_AI_models.append(character_db_model.getAIModel())
            char_rel = getCharacterRelationships(character_db_model)
            character_relationships = character_relationships + char_rel
        
        output = story_humanizer_nonjson(full_story, character_AI_models, character_relationships)
        sumloc = summary_and_location_generator(full_story, character_AI_models, character_relationships)
        print(sumloc)
        if something['story_title'] or something['story_title'] != "":
            story_title = something['story_title']
        else:
            story_title = output['title']
        plot = sumloc['summary']
        location = sumloc['location']
    
    newStory = StoryDB(
        story_title = story_title,
        episode_number = new_episode_number,
        location = location,
        plot = plot,
        full_story = full_story,
        series_id = something['series']['id']
    )
    db.session.add(newStory)
    db.session.commit()
    print(newStory.id)
    new_story_id = newStory.id
    
    for key in characters:
        character = characters[key]
        story_character = StoryCharactersDB(
            story_id = new_story_id,
            char_id = character['id']
        )
        db.session.add(story_character)
        db.session.commit()
    
    return jsonify({'story_id': new_story_id, 'message': 'STORY_ADDED', 'status': 'OK'})
    
    
'''
Dummy pages.
'''
@app.route('/tests/plothole')
def test_plothole():
    # NOTE FROM THE DEVELOPER
    # Do not run this test if the Groq API key used is the free tier.
    # This will result in a rate limit error.
    
    # Get all stories in the series with id=1
    max_diary = StoryDB.query.filter_by(series_id=1).all()

    # Initialize empty lists to store stories, characters, character AI models, and character relationships
    stories = []
    characters = []
    character_AI_models = []
    character_relationships = []

    # Loop through each story in the series
    for story in max_diary:
        # Add the full story to the stories list
        stories.append(story.full_story)

        # Get all characters in the story
        story_char_db = StoryCharactersDB.query.filter_by(story_id=story.id).all()

        # Loop through each character in the story
        for character_id in story_char_db:
            # Check if the character is already in the characters list
            if character_id.char_id not in characters:
                # If the character is not in the characters list, add it
                characters.append(character_id.char_id)

                # Get the character from the CharacterDB model
                character = CharacterDB.query.filter_by(id=character_id.char_id).first()

                # Add the character's AI model to the character_AI_models list
                character_AI_models.append(character.getAIModel())

                # Get the character's relationships and add them to the character_relationships list
                char_rel = getCharacterRelationships(character)
                character_relationships = character_relationships + char_rel

    # Call the plot_hole_detector function with the stories list as an argument
    plot_holes = plot_hole_detector(stories)

    # Print the plot holes to the console
    print(plot_holes)

    # Return a message to indicate that the output is printed to the console
    return "Check command line for output"


'''
Core story-generating code
'''
def getCharacterRelationships(character_db, mode = "groq"):
    # This accepts the CharacterDB object, not the one used by Groq
    relationships = []

    # Query for all relationships where the given character is the subject
    leftside_relationships = RelationshipDB.query.filter_by(char_subject_id=character_db.id).all()

    # Query for all relationships where the given character is the object
    rightside_relationships = RelationshipDB.query.filter_by(char_object_id=character_db.id).all()

    # Combine the leftside and rightside relationships into a single list
    relationships = leftside_relationships + rightside_relationships

    # Convert the RelationshipDB objects into Relationship objects if mode is set to groq (default mode)
    if mode == "groq":
        relationships = [rel.getAIModel() for rel in relationships]
        return relationships
    else:
        relationships = [rel.__json__() for rel in relationships]
        return relationships
    

def generate_story(scenario: str, custom_characters: Optional[List[Character]] = None, series_title: Optional[str] = None, story_title: Optional[str] = None, location: Optional[str] = None, previous_story: Optional[str] = None, continuity_type: Optional[str] = "usual", language: Optional[str] = "English", relationships: Optional[List[Relationship]] = None) -> str:
    character_data = ""
    if custom_characters:
        character_data = ", ".join([f"{char.name} (gender: {char.gender}, age: {char.age}, personality: {char.personality}, high_school_clique: {char.high_school_clique}, cultural_background: {char.cultural_background}, native_languages: {char.native_languages}, current_job: {char.current_job}, outfit: {char.outfit}, additional_desc: {char.additional_desc})" for char in custom_characters])
        # character_data = ", ".join([f"{char.dict()}" for char in custom_characters])

    # Prepare optional parameters
    optional_params = ""
    if series_title:
        optional_params += f" 'series_title': '{series_title}',"
    if story_title:
        optional_params += f" 'story_title': '{story_title}',"
    if location:
        optional_params += f" 'location': '{location}',"
    if previous_story:
        optional_params += f" 'previous_story': '{previous_story}',"
    if relationships:
        relationship_data = ", ".join([f"{rel.dict()}" for rel in relationships])
        optional_params += f" 'relationships': [{relationship_data}],"

    try:
        completion = client.with_options(max_retries=5).chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a story generator. Generate a story about high school cliques in {language}. "
                        "The story should have a title, characters, and a brief plot. "
                        "Ensure that the story is in JSON format with the following schema:\n"
                        "{\n"
                        "  \"title\": {\"type\": \"string\"},\n"
                        "  \"characters\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
                        "  \"plot\": {\"type\": \"string\"}\n"
                        "}\n"
                        f"If a previous story is provided, ensure that the new story is a continuation of it using the {continuity_type} approach. "
                        f"Ensure that the output is in {language}."
                    )
                },
                {
                    "role": "user",
                    "content": f"Generate a story involving the following scenario: {scenario}. "
                        f"{', and use the following custom characters: [' + character_data + ']' if custom_characters else ''}"
                        f"{', and apply the following additional information to the story: {' + optional_params + '}' if optional_params else ''}"
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )
        print(completion.choices[0].message.content)
        story = json.loads(completion.choices[0].message.content)
        
        story_json = json.dumps(story, indent=4)  # Pretty-print the JSON
        return story_json
    except groq.BadRequestError as bre:
        print("Error in generate_story:")
        print(bre.message)
        return {"error": "Groq - Bad Request", "contents": bre.message}
    except groq.InternalServerError as ire:
        print("Error in generate_story:")
        print(ire.message)
        return {"error": "Groq - Internal Server Error", "contents": ire.message}
    except Exception as ge:
        print("Error in generate_story:")
        print(ge)
        print(type(ge).__name__)
        return ge

def expand_plot_to_story(plot: str, language: Optional[str] = "English") -> str:
    full_story = ""
    #for day, summary in plot.items():
    #    detailed_scene = generate_detailed_scene(day, summary)
    #    full_story += detailed_scene + "\n\n"
    
    return generate_detailed_scene("1", plot)

def generate_detailed_scene(day: str, summary: str, language: Optional[str] = "English") -> str:
    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a story generator. Expand this following plot summary written in {language} into a detailed scene in {language}, in a witty, engaging, and emotionally resonant tone that is suitable for a high school setting. Here are some examples of the type of story I'm looking for: 'Nick and Charlie' by Alice Oseman, 'The Perks of Being a Wallflower' by Stephen Chbosky, and 'Paper Towns' by John Green."
                    )
                },
                {
                    "role": "user",
                    "content": f"Day: {day}\nPlot Summary: {summary}\n\nDetailed Scene:"
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        detailed_scene = completion.choices[0].message.content
        return detailed_scene
    except Exception as ge:
        print("Error in generate_detailed_scene:")
        print(str(ge))
        return jsonify({"error": ge})

    
def extract_characters(story: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a story analyzer. Get the names of the characters, their high school cliques, a brief and concise summary of their personalities, their ages, their genders, and their current jobs based on their actions and dialogs in the story. "
                        "Ensure that the output is in JSON format with the following schema:\n"
                        "{\n"
                        "  \"characters\": {\"type\": \"array\", \"items\": {\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}, \"high_school_clique\": {\"type\": \"string\"}, \"personality\": {\"type\": \"string\"}, \"age\": {\"type\": \"integer\"}, \"gender\": {\"type\": \"string\"}, \"current_job\": {\"type\": \"string\"}, \"additional_desc\": {\"type\": \"string\"}}}}\n"
                        "}\n"
                        "Ensure that the ages of the characters are appropriate based on their roles and backgrounds. The 'gender' field should indicate the character's gender, taking into account their names and the context of the story. The 'current_job' field should indicate the character's current job, taking into account their relationships and backgrounds. The 'additional_desc' field should provide additional information about the character, such as their species or profession."
                    )
                },
                {
                    "role": "user",
                    "content": f"Story: {story}"
                }
            ],
            temperature=0.8,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )
        characters = json.loads(completion.choices[0].message.content)
        characters_json = json.dumps(characters, indent=4)  # Pretty-print the JSON
        return characters_json
    except json.JSONDecodeError as e:
        return f"Failed to parse JSON: {e}"
    except Exception as ge:
        return f"Bad Request: {ge}"

def story_humanizer_nonjson(story: str, custom_characters: Optional[List[Character]] = None, relationships: Optional[List[Relationship]] = None) -> dict[str, str]:
    # Construct character data
    character_data = []
    if custom_characters:
        character_data = [char.dict() for char in custom_characters]

    optional_params = {}
    if relationships:
        optional_params['relationships'] = [rel.dict() for rel in relationships]
        
    try:
        completion1 = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": "You are a story improver. Rewrite this story in a witty, engaging, and emotionally resonant tone that is suitable for a high school setting. Here are some examples of the type of story I'm looking for: 'Nick and Charlie' by Alice Oseman, 'The Perks of Being a Wallflower' by Stephen Chbosky, and 'Paper Towns' by John Green."

                },
                {
                    "role": "user",
                    "content": f"Rewrite the following story: {story}. "
                        f"{', and use the following custom characters when they are mentioned by name within the story: ' + json.dumps(character_data) if custom_characters else ''}"
                        f"{', and incorporate the relationships between the mentioned characters when writing the story : ' + json.dumps(optional_params) if optional_params else ''}"
                        f"{', Do not append the custom characters and relationships at the end of the story as these are only to be used while rewriting the story.' if custom_characters or optional_params else '' }"
                }
            ],
            temperature=0.8,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        improved_story = completion1.choices[0].message.content
        
        completion2 = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": "You are a title generator. Generate a catchy and relevant title for the following story. Please provide only one title option. Do not make the title too long."
                },
                {
                    "role": "user",
                    "content": f"Generate a title for the story: {improved_story}."
                }
            ],
            temperature=0.8,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        title = completion2.choices[0].message.content
        output = {"improved_story": improved_story, "title": title}
        
        return output
    except Exception as e:
        print("Error in story_humanizer_nonjson:")
        
def summary_and_location_generator(story: str, custom_characters: Optional[List[Character]] = None, relationships: Optional[List[Relationship]] = None) -> dict[str, str]:
    # Construct character data
    character_data = []
    if custom_characters:
        character_data = [char.dict() for char in custom_characters]

    optional_params = {}
    if relationships:
        optional_params['relationships'] = [rel.dict() for rel in relationships]
    
    try:
        completion1 = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": "You are a story descriptor. Summarize a plot of the entire story in one paragraph."

                },
                {
                    "role": "user",
                    "content": f"Summarize the following story: {story}. "
                        f"{', and use the following custom characters when they are mentioned by name within the story: ' + json.dumps(character_data) if custom_characters else ''}"
                        f"{', and apply the following optional parameters: ' + json.dumps(optional_params) if optional_params else ''}"
                }
            ],
            temperature=0.8,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        shortened_plot = completion1.choices[0].message.content
        
        completion2 = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": "You are a story analyzer. Extract the location of the story. If the location is given in the story as Everglen, assume it is Everglen, NY."
                },
                {
                    "role": "user",
                    "content": f"Get the location of the following story: {story}. Only provide the location in the form city and/or state, for example, Everglen, NY, and do not add other details."
                }
            ],
            temperature=0.8,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        story_location = completion2.choices[0].message.content
        output = {"summary": shortened_plot, "location": story_location}
        
        return output
    except Exception as e:
        print("Error in story_humanizer_nonjson:")
        print(str(e))
        
def plot_hole_detector(stories: List[str], custom_characters: Optional[List[Character]] = None, relationships: Optional[List[Relationship]] = None) -> str:
    # Construct character data
    character_data = []
    if custom_characters:
        character_data = [char.dict() for char in custom_characters]

    optional_params = {}
    if relationships:
        optional_params['relationships'] = [rel.dict() for rel in relationships]
        
    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a story analyzer. The stories are arranged in chronological order from the first story to the latest. Find any plot holes in the series of stories, also checking if a later story is inconsistent with any previous ones."
                        "Ensure that the output is in JSON format with the following schema:\n"
                        "{\n"
                        "  \"plot_holes\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}\n"
                        "}\n"
                    )
                },
                {
                    "role": "user",
                    "content": f"Analyze these stories: {stories}, and list all plot holes."
                        f"{', and use the following custom characters when they are mentioned by name within each plot hole: ' + json.dumps(character_data) if custom_characters else ''}"
                        f"{', and apply the following optional parameters: ' + json.dumps(optional_params) if optional_params else ''}"
                }
            ],
            temperature=0.8,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )
        
        plot_holes = json.loads(completion.choices[0].message.content)
        plot_holes_json = json.dumps(plot_holes, indent=4)  # Pretty-print the JSON
        return plot_holes_json
    except Exception as e:
        print("Error in story_humanizer_nonjson:")
        print(str(e))
