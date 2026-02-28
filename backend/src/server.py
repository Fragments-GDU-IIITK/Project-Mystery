from flask import Flask
from flask_restx import Resource, Api


class BackendAPI(Resource):
    def get(self):
        return {"message": "hello"}


class Server:

    def __init__(self, name: str = __name__, port: int = 3000):
        self.__port = port
        self.__name = name

        print(f"Server Name : {self.__name}")

        self.__app = Flask(self.__name)
        self.__api = Api(self.__app)

        self.__api.add_resource(BackendAPI, "/hello")

    def run(self):
        self.__app.run(port=self.__port)
