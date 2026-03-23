from flask import Flask
from flask_restx import Resource, Api, Namespace
from pathlib import Path

from src.resources.chat import create_chat_namespace
from src.resources.session import create_session_namespace
from src.services.database_service import init_db_service

class Server:
    def __init__(self,version : str, name: str = __name__, port: int = 3000, route_prefix = ""):
        self.__port = port
        self.__name = name
        self.__app = Flask(self.__name)

        self.__app.config['SWAGGER_UI_BUNDLE_JS'] = 'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.min.js'
        self.__app.config['SWAGGER_UI_STANDALONE_PRESET_JS'] = 'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui-standalone-preset.min.js'
        self.__app.config['SWAGGER_UI_CSS'] = 'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui.min.css'

        self.__api = Api(self.__app,prefix = route_prefix)
        init_db_service(version=version)
        ns_sessions = create_session_namespace(character_model_path=Path(__file__).parent/"models/character_model.json")
        self.__api.add_namespace(ns_sessions,"/sessions")
        ns_chat = create_chat_namespace()
        self.__api.add_namespace(ns_chat,"/chat")
        
        
    

    def run(self):
        self.__app.run(port=self.__port)
        
    def get_app(self):
        return self.__app  # needed for testing
