from peewee import *
import json

# Database configuration
db = SqliteDatabase('storage/db.db', pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = db

class Content(BaseModel):
    title = CharField()
    thumbnail = CharField()
    type = CharField(choices=[
        ('vibe', 'Vibe'),
        ('reward', 'Reward'),
        ('llm', 'LLM')
    ])
    data = TextField()  # JSON storage as text

    def get_data(self):
        return json.loads(self.data)

    def set_data(self, data_dict):
        self.data = json.dumps(data_dict)

    @classmethod
    def get_all(cls):
        with db.connection_context():
            rows = cls.select()
            return [{
                "id": row.id,
                "title": row.title,
                "thumbnail": row.thumbnail,
                "type": row.type,
                "data": row.get_data()
            } for row in rows]

    def add(self, title, thumbnail, type, data):
        with db.connection_context():
            content = Content.create(
                title=title,
                thumbnail=thumbnail,
                type=type,
                data=json.dumps(data)
            )
            return content.id

    def update(self, id, title=None, thumbnail=None, type=None, data=None):
        with db.connection_context():
            update_dict = {}
            if title is not None:
                update_dict['title'] = title
            if thumbnail is not None:
                update_dict['thumbnail'] = thumbnail
            if type is not None:
                update_dict['type'] = type
            if data is not None:
                update_dict['data'] = json.dumps(data)
                
            query = Content.update(update_dict).where(Content.id == id)
            query.execute()

    def deleteItem(self, id):
        with db.connection_context():
            query = Content.delete().where(Content.id == id)
            query.execute()
def initialize_database():
    """Initialize the database and create tables if they don't exist."""
    db.connect(reuse_if_open=True)
    db.create_tables([Content], safe=True)
    db.close()
