from everglen_web import db
from sqlalchemy import func, select
from pydantic import BaseModel, Field
from typing import List, Optional, Union
'''
Classes used by the Groq AI
'''
class Series(BaseModel):
    series_name: str
    series_desc: str

class Character(BaseModel):
    name: str
    age: int
    gender: str
    personality: str
    high_school_clique: Optional[str] = Field(None, description="The high school clique of the character")
    cultural_background: Optional[str] = Field(None, description="The cultural background of the character")
    native_languages: Optional[List[str]] = Field(None, description="Native languages spoken by the character")
    current_job: Optional[str] = Field(None, description="The current job if the character is an adult")
    outfit: Optional[str] = Field(None, description="The character's trademark attire or piece of clothing that they are rarely seen without")
    additional_desc: Optional[str] = Field(None, description="Additional description that does not fit in the other attributes")

class Relationship(BaseModel):
    characters: List[Character]
    relation: str
    
    class Config:
        arbitrary_types_allowed = True

class Story(BaseModel):
    series: Series
    story_title: str
    location: str
    characters: List[Character]
    relationships: Optional[List[Relationship]] = Field(None, description="Relationships between characters")
    plot: dict

    class Config:
        arbitrary_types_allowed = True
        

'''
Classes used by SQLAlchemy
'''
class SeriesDB(db.Model):
    __tablename__ = 'series'
    
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    series_name = db.Column(db.String(150), nullable=False,  unique=False)
    series_desc = db.Column(db.String(300), nullable=False,  unique=False)
    
    def getAIModel(self):
        seriesAImodel = Series(series_name = self.series_name, series_desc = self.series_desc)
        return seriesAImodel
        
    def __eq__(self, other):
        if isinstance(other, SeriesDB):
            return (self.series_name == other.series_name and
                    self.series_desc == other.series_desc)
        return NotImplemented
    
class StoryDB(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    story_title = db.Column(db.String(150), nullable=False,  unique=False)
    episode_number = db.Column(db.Integer, nullable=False, unique=False)
    location = db.Column(db.String(150), nullable=False,  unique=False)
    plot = db.Column(db.Text, nullable=False,  unique=False)
    full_story = db.Column(db.Text, nullable=False,  unique=False)
    series_id = db.Column(db.Integer, db.ForeignKey(SeriesDB.id))
    series = db.relationship('SeriesDB', foreign_keys='StoryDB.series_id')
    
    def getAIModel(self):
        pass
    
class CharacterDB(db.Model):
    __tablename__ = 'characters'
    
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    character_name = db.Column(db.String(150), nullable=False,  unique=False)
    character_age = db.Column(db.Integer, nullable=False, unique=False)
    character_gender = db.Column(db.String(50), nullable=False,  unique=False)
    character_personality = db.Column(db.Text, nullable=False,  unique=False)
    high_school_clique = db.Column(db.String(150), nullable=True,  unique=False)
    cultural_background = db.Column(db.Text, nullable=True, unique=False)
    native_languages = db.Column(db.Text, nullable=True, unique=False)
    current_job = db.Column(db.String(150), nullable=True,  unique=False)
    outfit = db.Column(db.Text, nullable=True, unique=False)
    additional_desc = db.Column(db.Text, nullable=True, unique=False)
    
    def getAIModel(self):
        # Create the Character object
        characterAIModel = Character(
            name=self.character_name,
            age=self.character_age,
            gender = self.character_gender,
            personality=self.character_personality,
            high_school_clique=self.high_school_clique,
            cultural_background = self.cultural_background,
            current_job = self.current_job,
            additional_desc = self.additional_desc
        )
        
        return characterAIModel
        
    def __eq__(self, other):
        if isinstance(other, CharacterDB):
            return (self.character_name == other.character_name and
                    self.character_age == other.character_age and
                    self.character_gender == other.character_gender and
                    self.character_personality == other.character_personality and
                    self.high_school_clique == other.high_school_clique and
                    self.cultural_background == other.cultural_background and
                    self.native_languages == other.native_languages and
                    self.current_job == other.current_job and
                    self.outfit == other.outfit and
                    self.additional_desc == other.additional_desc)
        return NotImplemented
        
class RelationshipDB(db.Model):
    __tablename__ = 'relationships'
    
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    char_subject_id = db.Column(db.Integer, db.ForeignKey(CharacterDB.id))
    char_subject = db.relationship('CharacterDB', foreign_keys='RelationshipDB.char_subject_id')
    char_object_id = db.Column(db.Integer, db.ForeignKey(CharacterDB.id))
    char_object = db.relationship('CharacterDB', foreign_keys='RelationshipDB.char_object_id')
    relation = db.Column(db.String(150), nullable=False,  unique=False)
    
    def getAIModel(self):
        subjectCharacter = CharacterDB.query.filter_by(id=self.char_subject_id).first()
        objectCharacter = CharacterDB.query.filter_by(id=self.char_object_id).first()
        
        relationshipAImodel = Relationship(
            characters = [subjectCharacter.getAIModel(), objectCharacter.getAIModel()],
            relation = self.relation
        )
        
        return relationshipAImodel
    
    def __eq__(self, other):
        if isinstance(other, RelationshipDB):
            return (self.char_subject_id == other.char_subject_id and
                    self.char_object_id == other.char_object_id and
                    self.relation == other.relation)
        return NotImplemented
    
    def __json__(self):
        jsonRelation = {
            "relation_id": self.id,
            "relation_subject": self.char_subject_id,
            "relation_object": self.char_object_id,
            "relation": self.relation
        }
        
        return jsonRelation
        
        
class StoryCharactersDB(db.Model):
    __tablename__ = 'story_characters'
    
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey(StoryDB.id))
    story = db.relationship('StoryDB', foreign_keys='StoryCharactersDB.story_id')
    char_id = db.Column(db.Integer, db.ForeignKey(CharacterDB.id))
    char = db.relationship('CharacterDB', foreign_keys='StoryCharactersDB.char_id')
    
    def getAIModel(self):
        pass