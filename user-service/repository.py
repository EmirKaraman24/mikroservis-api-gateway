from pymongo import MongoClient
import os

class UserRepository:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/user_db")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.get_database()
        self.collection = self.db.get_collection("users")

    def create_user(self, user_data):
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def get_user(self, user_id):
        from bson.objectid import ObjectId
        return self.collection.find_one({"_id": ObjectId(user_id)})

    def update_user(self, user_id, update_data):
        from bson.objectid import ObjectId
        self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    def delete_user(self, user_id):
        from bson.objectid import ObjectId
        self.collection.delete_one({"_id": ObjectId(user_id)})
