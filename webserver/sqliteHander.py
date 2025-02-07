import sqlite3
from typing import Dict, Optional, List
import json

class VibeDb:
    def __init__(self, db_path: str = 'storage/db.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vibeconf (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                thumbnail TEXT,
                video TEXT,
                frame INTEGER,
                pose TEXT
            )
        ''')
        self.conn.commit()

    def add(self, title: str, thumbnail: str, video: str, frame: int, pose: Dict):
        self.cursor.execute(
            "INSERT INTO vibeconf (title, thumbnail, video, frame, pose) VALUES (?, ?, ?, ?, ?)",
            (title, thumbnail, video, frame, json.dumps(pose))
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update(self, id: int, title: str = None, thumbnail: str = None, 
               video: str = None, frame: int = None, pose: Dict = None):
        updates = []
        values = []
        if title: 
            updates.append("title = ?")
            values.append(title)
        if thumbnail:
            updates.append("thumbnail = ?")
            values.append(thumbnail)
        if video:
            updates.append("video = ?")
            values.append(video)
        if frame:
            updates.append("frame = ?")
            values.append(frame)
        if pose:
            updates.append("pose = ?")
            values.append(json.dumps(pose))
        
        if updates:
            values.append(id)
            query = f"UPDATE vibeconf SET {', '.join(updates)} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()

    def delete(self, id: int):
        self.cursor.execute("DELETE FROM vibeconf WHERE id = ?", (id,))
        self.conn.commit()

    def get(self, id: int) -> Optional[Dict]:
        self.cursor.execute("SELECT * FROM vibeconf WHERE id = ?", (id,))
        row = self.cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "thumbnail": row[2],
                "video": row[3],
                "frame": row[4],
                "pose": json.loads(row[5]) if row[5] else None
            }
        return None

    def get_all(self) -> List[Dict]:
        self.cursor.execute("SELECT * FROM vibeconf")
        rows = self.cursor.fetchall()
        return [{
            "id": row[0],
            "title": row[1],
            "thumbnail": row[2],
            "video": row[3],
            "frame": row[4],
            "pose": json.loads(row[5]) if row[5] else None
        } for row in rows]

    def __del__(self):
        self.conn.close()