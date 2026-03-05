from flask import request
from flask_restx import Resource

class Player(Resource):
    def get(self):
        dummy_dict = {
            "players" : ["John3729","Meilene5678"]
        }
        # [TODO] : Query the database and rturn each database name in chromadb 
        return dummy_dict
    
    def post(self):
        request_data = request.json
        print(request_data)
        # [TODO] : Check if a database with this name exists, if not create a new database
        #          for player
        return {
            "dummy_player_hash" : "sdaw1243"
        }
    

