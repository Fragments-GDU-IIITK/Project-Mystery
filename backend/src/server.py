from flask import Flask
from flask_restx import Resource, Api, Namespace
from pathlib import Path

from src.resources.session import create_session_namespace
from src.services.database_service import init_db_service

class Server:
    def __init__(self,version : str, name: str = __name__, port: int = 3000, route_prefix = ""):
        self.__port = port
        self.__name = name
        self.__app = Flask(self.__name)
        self.__api = Api(self.__app,prefix = route_prefix)
        init_db_service(version=version)
        ns = create_session_namespace(character_model_path=Path(__file__).parent/"models/character_model.json")
        self.__api.add_namespace(ns,"/sessions")
    

    def run(self):
        self.__app.run(port=self.__port)
        
    def get_app(self):
        return self.__app  # needed for testing
