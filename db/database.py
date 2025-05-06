# db/database.py

import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.gametimebot

users = db.users
sessions = db.sessions