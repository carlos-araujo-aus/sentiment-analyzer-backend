# api/models.py
from . import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class Analysis(db.Model):
    """
    Represents a single analysis record in the database.
    """
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    text_content = db.Column(db.Text, nullable=False)
    
    sentiment_label = db.Column(db.String(10), nullable=False)
    sentiment_score = db.Column(db.Float, nullable=False)
    
    emotion_joy = db.Column(db.Float)
    emotion_sadness = db.Column(db.Float)
    emotion_fear = db.Column(db.Float)
    emotion_disgust = db.Column(db.Float)
    emotion_anger = db.Column(db.Float)

    keywords = db.Column(JSONB)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        """
        Serializes the Analysis object into a dictionary,
        making it easy to convert to JSON.
        """
        return {
            'id': self.id,
            'text_snippet': f"{self.text_content[:75]}..." if len(self.text_content) > 75 else self.text_content,
            'sentiment_label': self.sentiment_label,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the object,
        useful for debugging.
        """
        return f"<Analysis id={self.id} sentiment='{self.sentiment_label}'>"