import chromadb 
from pathlib import Path
import logging
from logging import Logger

class DatabaseStatusCodes:
    @staticmethod
    def success(data):
        return {
            "status" : 200,
            "data": data,
        }
    @staticmethod
    def resourceDoesNotExist():
        return {
            "status" : 404,
            "description" : "Resource Does Not Exist"
        }
    @staticmethod
    def resourceAlradyExists():
        return {
            "status" : 100,
            "description" : "Resource already exists"
        }
    @staticmethod
    def invalidCollectionName():
        return {
            "status" : 101,
            "description" : "Invalid Collection Name"
        }
    @staticmethod
    def internalError():
        return {
            "status": 500,
            "message": "Internal database error"
        }


class DatabaseService:
    @staticmethod
    def generate_session_id(text: str) -> str:
        import hashlib, base64
        digest = hashlib.sha256(text.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode()[:16]

    def __init__(self, version:str, data_path : str = "./session_data", create_dirs : bool = True):
        """
            Initializes the database client for accessing the session datas

            Attributes :
            
                data_path : relative path string to the local persistent storage location 
                create_dirs : set to false to disable automatic creation of necessary dirrectories
        """
        self.__version = version
        self.__logger : Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__logger.setLevel(logging.INFO)
        data_path : Path = Path(data_path)
        full_data_path = data_path.resolve()
        if not data_path.is_dir():
            print(f"[INFO] : {full_data_path} dir does not exists")
            if create_dirs:
                data_path.mkdir(parents = True, exist_ok = True)
                self.__logger.info("%s created successfully", full_data_path)
        else:
            self.__logger.info(f"Directory already exists at %s",full_data_path) 
        
        self.__path : Path = data_path 

    def createSession(self, session_name: str) -> dict:
        """
            Creates a new game session and initializes a database with a client. Also stores metadata about the session

            Attributes :
            
                session_name : Name of the session. the session ID will be derived from this string
        """
        session_id = DatabaseService.generate_session_id(session_name)
        session_path = self.__path/session_id
        if session_path.is_dir():
            return DatabaseStatusCodes.resourceAlradyExists()
        self.__client = chromadb.PersistentClient(path = session_path)
        try:
            self.__client.create_collection(
                name = "Database_Metadata",
                metadata={
                "version" : self.__version,
                "session_name":session_name,
                "session_id" : session_id
            })
            return DatabaseStatusCodes.success({
                "version" : self.__version,
                "session_name":session_name,
                "session_id" : session_id
            })
        except ValueError as _error:
            self.__logger.error(f" [ERROR] : {_error}")
            return DatabaseStatusCodes.invalidCollectionName()

    def loadSession(self, session_id: str) -> dict:
        """
            Loads an existing session database and initializes runtime components.

            Attributes :

                session_id : Unique identifier of the session to load
        """

        session_path = self.__path / session_id

        if not session_path.is_dir():
            return DatabaseStatusCodes.resourceDoesNotExist()
        try:
            self.__client = chromadb.PersistentClient(path=str(session_path))
            metadata_collection = self.__client.get_collection("Database_Metadata")
            metadata = metadata_collection.metadata
            # self.__initializeCharacters()
            # [TODO] : Initialize Characters Here

            return DatabaseStatusCodes.success({
                "version": metadata.get("version"),
                "session_name": metadata.get("session_name"),
                "session_id": metadata.get("session_id")
            })

        except ValueError as e:
            self.__logger.error("Invalid collection while loading session: %s", e)
            return DatabaseStatusCodes.invalidCollectionName()

        except Exception as e:
            self.__logger.error("Failed to load session %s : %s", session_id, e)
            return DatabaseStatusCodes.internalError()