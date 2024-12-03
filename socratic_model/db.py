import uuid

from . import seminar

import firebase_admin
from firebase_admin import firestore, credentials


class DB:
    """
    Create a DB object to store and access seminar objects stored in Firebase
    """
    is_init = False

    def __init__(self, db: str = 'seminars', p_key_path: str = "private_key.json"):
        self.init_firebase(p_key_path)
        self.db = firestore.client()
        self.seminar_collection = self.db.collection(db)

    @classmethod
    def init_firebase(cls, p_key_path: str):
        if not cls.is_init:
            cred = credentials.Certificate(p_key_path)
            cls._firebase = firebase_admin.initialize_app(cred)
            cls.is_init = True

    def get(self, uid: str) -> seminar.Seminar | None:
        """
        Get a seminar object by UID. Returns None otherwise (like other get functions)
        """
        seminar_dict = self.seminar_collection.document(uid).get()
        if not seminar_dict.exists:
            return None
        return seminar.Seminar.from_dict(seminar_dict.to_dict())

    def add(self, seminar: seminar.Seminar, uid: str = None) -> str:
        """
        Add a seminar object to the db and return its UID
        """
        if uid is None:
            uid = self.__get_new_uid()
        self.seminar_collection.document(uid).set(seminar.to_dict())
        return uid

    def update(self, uid: str, seminar: seminar.Seminar):
        self.seminar_collection.document(uid).update(
            seminar.last_content_embedded())

    def has(self, uid) -> bool:
        return uid in [seminar.id for seminar in self.seminar_collection.stream()]

    def __get_new_uid(self):
        """
        Generate a unique ID
        """
        # Generate a UID with uuid4 and looping
        uids = [seminar.id for seminar in self.seminar_collection.stream()]
        while (new_id := uuid.uuid4().hex) in uids:
            pass

        return new_id
