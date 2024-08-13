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
@app.route('/tests/dummycharacters')
def generate_dummy_characters():
    character_count = CharacterDB.query.count()
    
    if character_count == 0:
        test_nerd = CharacterDB(character_name="Max Supernova", character_age=24, character_gender="male", character_personality="shy", high_school_clique="nerd", cultural_background="American", native_languages=' '.join(["English","Polish"]), current_job="Everglen High Science Teacher")
        test_bully = CharacterDB(character_name="Cameron Bandage", character_age=25, character_gender="male", character_personality="bold", high_school_clique="bully", cultural_background="American", native_languages=' '.join(["English"]), current_job="Everglen High Boxing Coach", additional_desc="always has a bandage on the forehead since his high school days due to terrible luck where he falls to the floor if that is removed")
        db.session.add(test_nerd)
        db.session.add(test_bully)
        db.session.commit()
        print("Testing AI model generation")
        print(test_nerd.getAIModel())
        print("Nerd's database ID")
        print(test_nerd.id)
        print("Bully's database ID")
        print(test_bully.id)
        print("Generating relationship sample - nerd and bully are boyfriends")
        test_relationship = RelationshipDB(char_subject_id = test_nerd.id, char_object_id = test_bully.id, relation = "boyfriends")
        db.session.add(test_relationship)
        db.session.commit()
        print("Checking if relationship status is saved")
        print(test_relationship.id)
        return "Check the command line for the ID of the characters to use in the other dummy pages"
    else:
        return "Table not empty -- check database for the ID of the characters"
        
@app.route('/tests/storygenerator')
def generate_test_story():
    '''
    DOES NOT SAVE STORY TO DATABASE
    Only tests the core story-generating code below
    '''
    character_count = CharacterDB.query.count()
    
    if character_count > 0:
        test_nerd = CharacterDB.query.filter_by(id=1).first() # Max Supernova
        test_bully = CharacterDB.query.filter_by(id=2).first() # Cameron Bandage
        location = "Juche Sasang Avenue, the street outside Everglen High"
        scenario = "two guys, Max and Cameron, who both graduated from Everglen High long time ago and now teach there, decide to have a date at a restaurant outside Everglen High called 'Food Out of Nowhere'. This restaurant is notorious for not having menus and instead surprises customers which leads to mixed results. Instead of informing the customer on what they will receive, any waiter in the restaurant will automatically hand a random food the moment someone sits down, even if it's an exotic food like the ones served in other countries that are so exotic it could be repulsive to others. Despite the outcome of the food served, both Max and Cameron still enjoy their date as long as they have each other."
        custom_characters=[test_nerd.getAIModel(), test_bully.getAIModel()]
        character_relationships = getCharacterRelationships(test_nerd)
        print("Testing character_relationships variable")
        print(character_relationships)
        generated_story = generate_story(scenario=scenario, custom_characters=custom_characters, location=location, relationships = character_relationships)
        print(generated_story)
        output = expand_plot_to_story(json.loads(generated_story)['plot'])
        print(output)
        return output
    else:
        return "Please generate dummy characters first."
        
@app.route('/tests/storygenerator/multilingual')
def generate_test_story_multilingual():
    '''
    DOES NOT SAVE STORY TO DATABASE
    Only tests the core story-generating code below
    '''
    character_count = CharacterDB.query.count()
    
    if character_count > 0:
        test_nerd = CharacterDB.query.filter_by(id=1).first() # Max Supernova
        test_bully = CharacterDB.query.filter_by(id=2).first() # Cameron Bandage
        location = "Juche Sasang Avenue, the street outside Everglen High"
        scenario = "two guys, Max (a nerd) and his boyfriend Cameron (a bully), who both graduated from Everglen High long time ago and now teach there, decide to have a date at a restaurant outside Everglen High called 'Food Out of Nowhere'. This restaurant is notorious for not having menus and instead surprises customers which leads to mixed results. Instead of informing the customer on what they will receive, any waiter in the restaurant will automatically hand a random food the moment someone sits down. Despite the outcome of the food served, both Max and Cameron still enjoy their date as long as they have each other."
        custom_characters=[test_nerd.getAIModel(), test_bully.getAIModel()]
        character_relationships = getCharacterRelationships(test_nerd)
        print("Testing character_relationships variable")
        print(character_relationships)
        generated_story = generate_story(scenario=scenario, custom_characters=custom_characters, location=location, language="Dutch")
        print("DEBUG: generated_story variable")
        print(json.loads(generated_story)['plot'])
        print("Testing story generation in another language")
        output = expand_plot_to_story(json.loads(generated_story)['plot'], "Dutch")
        print(output)
        return "Check command prompt / Controleer de opdrachtregel / Mira el terminal"
    else:
        return "Please generate dummy characters first."
        
@app.route('/tests/storygenerator/twoparter')
def generate_test_story_twoparter():
    '''
    DOES NOT SAVE STORY TO DATABASE
    Only tests the core story-generating code below for continuity
    '''
    character_count = CharacterDB.query.count()
    
    if character_count > 0:
        test_nerd = CharacterDB.query.filter_by(id=1).first() # Max Supernova
        test_bully = CharacterDB.query.filter_by(id=2).first() # Cameron Bandage
        location = "Everglen High Library"
        scenario1 = "two guys, Max (a nerd) and his boyfriend Cameron (a bully), who both graduated from Everglen High long time ago and now teach there, decide to look for a random book using the library's catalog system in a kiosk, and to up the challenge, a book that is beyond their specialty knowledge. Both of them took 5 minutes to find a book. End with cliffhanger at the moment both Max and Cameron returned to their table."
        custom_characters=[test_nerd.getAIModel(), test_bully.getAIModel()]
        generated_story_p1 = generate_story(scenario=scenario1, custom_characters=custom_characters, location=location)
        output1 = expand_plot_to_story(json.loads(generated_story_p1)['plot'])
        print("CLIFFHANGER TEST: story 1")
        print(output1)
        scenario2 = "both Max and his boyfriend Cameron already picked a book and revealed the books they randomly picked at their table."
        generated_story_p2 = generate_story(scenario=scenario2, custom_characters=custom_characters, location=location, previous_story=output1)
        output2 = expand_plot_to_story(json.loads(generated_story_p2)['plot'])
        print("CLIFFHANGER TEST: story 2")
        print(output2)
        return "Check command line for outputs"
    else:
        return "Please generate dummy characters first."
    
@app.route('/tests/character/extract')
def test_character_extractor():
    '''
    DOES NOT SAVE CHARACTERS TO DATABASE
    Only tests the core character extracting code below
    '''
    story = """
    Claude, a walking wonder in the world of Everglen High School, was a peculiar combination: a stellar student with an uncanny knack for football. A nerd under a footballer's shell. His life resonated flawlessly with trigonometry problems, historical timelines, and the exhilarating rhythm of charging down the football pitch.

    Northrop, on the contrary, was the quintessence of a high school bully. He was the leader of the Malice Marauders, a notorious clique known for their menacing hall loitering and relentless bullying. Despite his grim exterior, Northrop concealed a rare sensitivity, only shared in secret poetry which never saw the light of day.

    Claude's unusual blend of brawn and brains often invited Northrop's attention and, unfortunately, his taunts. Though initially hesitant, Claude stood his ground. His resilience started stirring an unfamiliar respect in Northrop's heart: he began to see his victim as an equal, a comrade — a feeling he concealed within the crumpled pages of his private verses.

    One day, Northrop discovered an anonymous love letter in his locker, filled with beautiful words that echoed his clandestine thoughts. Intrigued and secretly elated, Northrop played detective to find the writer. Little did he know that this venture would forever change his world.

    In pursuit of the anonymous admirer, Northrop encountered Claude outside football practice one evening. Observing some shared phrases between Claude's casual conversation and the mystery letter, Northrop held his breath: could Claude be the secret admirer?

    Wanting clarity, Northrop carefully approached Claude. They found themselves engaged in a genuine talk, a first between them, sharing a heartfelt discourse about their passions and fears. Claude, surprised and touched by Northrop's vulnerability, decided to divulge his secret: yes, he was the writer of the letter. He admitted he'd been secretly admiring Northrop's poetic side, something he discovered by stumbling upon a lost piece of Northrop's poetry.

    Taken aback, Northrop took a minute to process. Then, with an unexpected smile, he reached into his jacket, revealing a collection of poems he'd written about Claude's strength, his intelligence and his perseverance. That was the moment they understood the unique bond forming between them among shared words and affectionate expressions.

    A new tale began at Everglen High, one where the sterling student-athlete and the bullish brute found common ground and an unlikely but beautiful romance. They learned from each other, Northrop laying off his bullying, investing more in his poetry, while Claude stood as a beacon for those who defied stereotypes. And so, they championed an age-old quote - love could, indeed, blossom in the unlikeliest places.
    """
    print("Extracting Characters from 'Unlikely Hearts and Football Charts' -- same age test")
    print(extract_characters(story))
    
    story2 = """
    It was a typical busy day at the Everglen High IT office. Clyde Stackoverflow, proudly wearing his lab coat, and his boyfriend Mattie Drachenboren were at their desks, keeping an eye on the school’s computer systems. Among their responsibilities was monitoring the printer queue with the help of an automated system they had nicknamed Francis Dimmsdale.

    Suddenly, an alert popped up on Stackoverflow’s screen.

    “Hey, Mattie, check this out,” Stackoverflow said, pointing to the screen. “Francis just flagged an odd file in the printer queue.”

    Mattie leaned over, squinting at the monitor. “What’s so odd about it?”

    Stackoverflow opened the file, and they were greeted by a confusing mistranslation at the top of the page:

    Hebrew: "השבת אבדה"
    English (mistranslated): "The Sabbath was lost"

    Below that, the document continued in English: "Bicycle with flat tire found near the gym, please reach out to Yitzhak from the Malice Marauders."

    Stackoverflow scratched his head. “I’ve been studying Hebrew through the Aleph with Beth series, but this has me stumped. I read the first word as ‘ha-Shabat,’ but that doesn’t make sense here.”

    Mattie chuckled. “You’re the one with the Hebrew knowledge, rusty as it may be. I can’t make heads or tails of it.”

    Just then, the door to the IT office opened, and in walked Yitzhak, a known member of the Malice Marauders. He looked a bit apprehensive as he approached the desk.

    “Hey, Stackoverflow, Mattie,” Yitzhak greeted. “I think there might be an issue with my print job.”

    Stackoverflow waved him over. “Yitzhak, perfect timing. We were just looking at it. Can you explain this Hebrew part? It’s translated as ‘The Sabbath was lost,’ and we’re confused.”

    Yitzhak laughed nervously. “Oh, that’s a classic mistranslation. It’s supposed to mean ‘Lost and Found.’ The phrase ‘השבת אבדה’ actually translates to ‘return of lost property,’ but the software must have translated it literally.”

    Stackoverflow nodded, finally understanding. “Got it. So, you were trying to notify about a lost bicycle near the gym?”

    “Exactly,” Yitzhak confirmed. “I found a bike with a flat tire, and I thought using some Hebrew would make the notice stand out. But I guess the translation software had other plans.”

    Mattie grinned. “Well, it definitely stood out. We were imagining someone losing the Sabbath, like it’s gone missing.”

    Yitzhak chuckled. “Yeah, that would be quite a predicament. I’ll reprint the notice without the Hebrew part to avoid confusion.”

    Stackoverflow smiled. “Good idea. Thanks for clearing that up, Yitzhak. And good on you for trying to help out with the lost bike.”

    As Yitzhak left to correct his print job, Stackoverflow and Mattie shared a relieved laugh.

    “Well, that was interesting,” Mattie said, shaking his head. “Only at Everglen High could we end up in a conversation about losing the Sabbath because of a mistranslated notice.”

    Stackoverflow nodded. “True. And it’s a good reminder that even with tech, sometimes you need the human touch to make sense of things.”

    They returned to their work, grateful for the unexpected moment of humor and the clarification provided by Yitzhak, another day of unique challenges and quirky encounters at Everglen High.
    """
    
    print("Extracting Characters from 'Crimson Sword and Lavender Shield' -- mixed age test")
    print(extract_characters(story2))
    
    story3 = """
    It was another bustling afternoon in the Everglen High IT office. Clyde Stackoverflow was browsing the alumni-contributed recipes on the Everglen High network portal, eager to try something new from the Peruvian category. Mattie Drachenboren, his boyfriend, was perched on the couch nearby, flipping through a strategy guide for Skyrim. Their colleagues — Harold Conagher, with his hard hat and wrench; Nikolai Lynsuyevich Uravneniy, with his big arms and sandwich; and Jervey McTavish, wearing his iconic eye patch — were gathered around the newly refurbished kitchen, discussing potential lunch ideas.

    “Hey, guys, check this out,” Stackoverflow called out, catching everyone’s attention. “I’m looking at some Peruvian recipes here, but the translations are wild.”

The rest of the IT team gathered around, curious about what Stackoverflow had found.

“First item,” Stackoverflow began, trying to suppress a laugh, “Causa Limeña, mistranslated as ‘It causes limena.’”

Mattie snickered. “What is this mysterious ‘it’ that causes limena? Sounds like a plot twist in a bad horror movie.”

Harold raised an eyebrow. “What the heck is a limena anyway?”

Stackoverflow shrugged. “No idea. Moving on. Second item: Medallon de alpaca, mistranslated as ‘German nickel locket.’”

Nikolai chuckled, his deep voice rumbling. “So, we’re eating jewelry now? Fancy.”

Jervey shook his head, laughing. “Sounds like something out of a steampunk novel.”

“And the third item,” Stackoverflow continued, “Papa a la huancaina, mistranslated as ‘Pope wing huancaina.’”

Mattie burst into laughter. “A flying Pope? That’s a new one.”

Harold scratched his head. “How do you even get ‘wing’ from ‘huancaina’?”

As they all laughed at the absurd mistranslations, a voice from behind them interrupted. “Actually, I can explain those,” said Ines, a nerd from the same clique as Stackoverflow, who happened to pass by and overheard the conversation. She was of Peruvian descent and was well-versed in her culture’s cuisine.

“Oh, hey Ines!” Stackoverflow greeted her. “Perfect timing. Do enlighten us.”

Ines smiled and took a closer look at the screen. “Sure thing. Causa Limeña is a traditional Peruvian dish made from layers of seasoned mashed potatoes with fillings like tuna or chicken. The mistranslation should have said ‘Limeña Causa,’ referring to the dish from Lima.”

“Got it. So, no mysterious ‘it,’ just mashed potatoes,” Stackoverflow said with a grin.

Ines continued. “Medallon de alpaca is a dish made from alpaca meat, similar to a steak or medallion cut. The translation got mixed up somehow. It’s definitely not a locket made of German nickel.”

Nikolai nodded appreciatively. “I’d rather eat alpaca than a piece of metal.”

“And finally,” Ines said, looking at the screen, “Papa a la huancaina is boiled potatoes covered in a spicy, creamy cheese sauce. It’s a popular Peruvian dish. The word ‘papa’ means potato, not Pope, and ‘a la huancaina’ refers to the style from Huancayo.”

“Aha, that makes so much more sense!” Stackoverflow exclaimed. “Thanks, Ines.”

As Stackoverflow decided to view the recipe for Papa a la Huancaina, Ines peered over his shoulder. “Wait a second,” she said, recognizing the author’s name. “That recipe was uploaded by my older sister, Juana Maria. She’s an Everglen High alum and now works as an archeologist specializing in Peruvian history.”

“Small world!” Mattie exclaimed. “So, your sister is the one who contributed this?”

Ines nodded proudly. “Yep, she lives on the East Coast now, but she travels to our hometown of Huancayo frequently for her job.”

“Well then, looks like we have the perfect recipe to try out,” Stackoverflow said, clicking on the recipe to print it. “Let’s make some Papa a la Huancaina for lunch.”

Harold, Nikolai, and Jervey nodded in agreement, eager to try the dish. As they gathered the ingredients and got to work, the IT office was filled with the aroma of traditional Peruvian cuisine, and the camaraderie of friends enjoying a culinary adventure together.
    """
    
    print("Extracting Characters from 'Crimson Sword and Lavender Shield' -- mixed-gender test")
    print(extract_characters(story3))
    
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
                        f"{', and include the following optional parameters: {' + optional_params + '}' if optional_params else ''}"
                }
            ],
            temperature=0.8,
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
                        f"{', and include the following optional parameters: ' + json.dumps(optional_params) if optional_params else ''}"
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
                    "content": "You are a title generator. Generate a catchy and relevant title for the following story."
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
                    "content": "You are a story descriptor. Summarize a plot of the entire story."

                },
                {
                    "role": "user",
                    "content": f"Summarize the following story: {story}. "
                        f"{', and use the following custom characters when they are mentioned by name within the story: ' + json.dumps(character_data) if custom_characters else ''}"
                        f"{', and include the following optional parameters: ' + json.dumps(optional_params) if optional_params else ''}"
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
                    "content": f"Get the location of the following story: {story}."
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