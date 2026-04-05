import chromadb 
import logging
import json
import uuid
from pathlib import Path
from logging import Logger

from src.services.database_status_codes import ServiceStatusCodes
from src.models.conversation import Conversation



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
        self.__conversational_mem_suffix = "conversational_mem"
        self.__world_knowledge_suffix = "world_knowledge"
        self.__logger : Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__logger.setLevel(logging.DEBUG)
        data_path : Path = Path(data_path)
        full_data_path = data_path.resolve()
        self.__metadata_collection_name : str = "Database_Metadata"
        if not data_path.is_dir():
            self.__logger.info("%s dir does not exist", full_data_path)
            if create_dirs:
                data_path.mkdir(parents = True, exist_ok = True)
                self.__logger.info("%s created successfully", full_data_path)
        else:
            self.__logger.info("Directory already exists at %s",full_data_path) 
        
        self.__path : Path = data_path 

    def __loadCharacterData(self, character_model_path: Path) -> list:
        """
            Helper function to fetch character data from model file
        """
        if not character_model_path.is_file():
            self.__logger.error("character_model.json not found")
            raise Exception("character_model.json not found")
        try:
            with open(character_model_path, "r") as f:
                model = json.load(f)

            model_version = model.get("version")

            if model_version != self.__version:
                self.__logger.error(
                    "Character model version mismatch (model=%s, db=%s)",
                    model_version,
                    self.__version
                )
                raise Exception("character_model.json version mismatch with server")
            characters = model.get("characters", [])
            return characters
        except Exception as e:
            self.__logger.error("Failed to load character data : %s", e)
            raise Exception("Failed to load character data")
        
    def __initializeCharacters(self, characters) -> None:
        """
            Initializes character knowledge collections from character_model.json.
        """

        try:
            for character in characters:

                character_id = character["character_id"]
                world_knowledge = character.get("world_knowledge", [])

                conversational_mem_collection_name = character_id + self.__conversational_mem_suffix 
                world_knowledge_collection_name = character_id + self.__world_knowledge_suffix

                self.__client.create_collection(name=conversational_mem_collection_name)
                world_knowledge_collection = self.__client.create_collection(name=world_knowledge_collection_name)

                ids = []
                documents = []

                for i, knowledge in enumerate(world_knowledge):
                    ids.append(f"{character_id}_{i}")
                    documents.append(knowledge)

                world_knowledge_collection.add(
                    ids=ids,
                    documents=documents
                )

                result = world_knowledge_collection.get()

                self.__logger.info(
                    "Initialized character collection %s : %s",
                    world_knowledge_collection,
                    result
                )

        except Exception as e:
            self.__logger.error("Failed to initialize characters: %s", e)
            raise Exception("Character Initialization Failed")

    def createSession(self, session_name: str, character_model_path : Path) -> dict:
        """
            Creates a new game session and initializes a database with a client. Also stores metadata about the session

            Attributes :
            
                session_name : Name of the session. the session ID will be derived from this string
                
                character_model_path : path to character_model.json
        """
        session_id = DatabaseService.generate_session_id(session_name)
        session_path = self.__path/session_id
        if session_path.is_dir():
            return ServiceStatusCodes.resourceAlreadyExists()
        try:
            self.__client = chromadb.PersistentClient(path = session_path)
            self.__characters = self.__loadCharacterData(character_model_path)
            self.__session_metadata = {
                "version" : self.__version,
                "session_name":session_name,
                "session_id" : session_id,
                "session_character_model_path" : str(character_model_path)
            }
            self.__client.create_collection(
                name = self.__metadata_collection_name,
                metadata=self.__session_metadata
            )
            self.__initializeCharacters(self.__characters)
            return ServiceStatusCodes.success({
                "version" : self.__version,
                "session_name":session_name,
                "session_id" : session_id,
            })
        except ValueError as _error:
            self.__client = None
            self.__logger.error(f" [ERROR] : {_error}")
            return ServiceStatusCodes.invalidCollectionName()

    def __loadSession(self, session_path:Path):
        """
            Helper function to load Session
        """
        try:
            self.__client = chromadb.PersistentClient(path=str(session_path))
            metadata_collection = self.__client.get_collection(self.__metadata_collection_name)
            self.__session_metadata = dict(metadata_collection.metadata)
            character_model_path = self.__session_metadata.get("session_character_model_path")
            self.__characters = self.__loadCharacterData(Path(character_model_path))
            self.__logger.info("loaded characters %s", self.__characters)
            return {
                "version": self.__session_metadata.get("version"),
                "session_name": self.__session_metadata.get("session_name"),
                "session_id": self.__session_metadata.get("session_id"),
            }

        except ValueError as e:
            raise e
        except Exception as e:
            raise e
        
    def loadSession(self, session_id: str) -> dict:
        """
            Loads an existing session database and initializes runtime components.

            Attributes :

                session_id : Unique identifier of the session to load
        """

        session_path = self.__path / session_id

        if not session_path.is_dir():
            return ServiceStatusCodes.resourceDoesNotExist()
        try:
            session_dict = self.__loadSession(session_path)
            return ServiceStatusCodes.success(session_dict)

        except ValueError as e:
            self.__client = None
            self.__logger.error("Invalid collection while loading session: %s", e)
            return ServiceStatusCodes.invalidCollectionName()

        except Exception as e:
            self.__client = None
            self.__logger.error("Failed to load session %s : %s", session_id, e)
            return ServiceStatusCodes.internalError()

        
    # [NOTE] : Some OS Internal issue, chroma also doesn't have an elegant solution,just delte save files manually
    # def deleteSession(self, session_id: str) -> dict:
    #     """
    #         Deletes an existing session from persistent storage.

    #         Attributes :

    #             session_id : Unique identifier of the session to delete
    #     """

    #     session_path = self.__path / session_id

    #     if not session_path.is_dir():
    #         return DatabaseStatusCodes.resourceDoesNotExist()

    #     try:
    #         self.unloadSession()
    #         gc.collect()
    #         time.sleep(0.2)

    #         shutil.rmtree(session_path)

    #         self.__logger.info("Session %s deleted successfully", session_id)

    #         return DatabaseStatusCodes.success({
    #             "session_id": session_id,
    #             "log" : f"{session_id} deleted successfully"
    #         })

    #     except Exception as e:
    #         self.__logger.error("Failed to delete session %s : %s", session_id, e)
    #         return DatabaseStatusCodes.internalError()

    def unloadSession(self) -> dict:
        """
            Unloads an existing session database and initializes runtime components.
        """
        if self.__client is not None:
            try:
                del self.__client
                del self.__characters
                del self.__session_metadata
            finally:
                self.__client = None
                self.__characters = None
                self.__session_metadata = None
        return ServiceStatusCodes.success("Session Unloaded Successfully")
    
    def resetSession(self, session_id: str):
        """
            Resets a particular session conversational memory

            Attributes:

            session_id : Unique identifier of the session
        """
        load_result = self.loadSession(session_id)
        if load_result["status"] != 200:
            return load_result
        try:
            for character in self.__characters:
                collection_name = character['character_id'] + self.__conversational_mem_suffix

                try:
                    collection = self.__client.get_collection(collection_name)
                    while True:
                        data = collection.get(limit=1000)
                        ids = data.get("ids", [])

                        if not ids:
                            break
                        collection.delete(ids=ids)
                    self.__logger.info("Cleared collection %s", collection_name)

                except Exception as e:
                    self.__logger.warning(
                        "Skipping collection %s (reason: %s)",
                        collection_name,
                        e
                    )
            return ServiceStatusCodes.success("Successfully Reset Collection")
        except Exception as e:
            self.__logger.error("Reset session failed: %s", e)
            return ServiceStatusCodes.internalError() 
        finally:
            self.unloadSession()
    
    def getSessions(self):
        """
            Iterates through entire session directory and fetches all session metadata
        """
        session_dirs = [item for item in self.__path.iterdir() if item.is_dir()]
        sessions = []
        for session_path in session_dirs:
            try:
                temp_client = chromadb.PersistentClient(path=str(session_path))
                metadata = temp_client.get_collection(self.__metadata_collection_name).metadata
                sessions.append({
                    "version": metadata.get("version"),
                    "session_name": metadata.get("session_name"),
                    "session_id": metadata.get("session_id"),
                })
            except Exception:
                continue
        return ServiceStatusCodes.success(sessions)
    
    def query_world_knowledge(self, prompt : str, character_id: str, k : int = 5):
        """
            Given a user prompt and character id, query and return k relevant docs 
            from the character world knowledge
            
            Attributes:

                prompt : User given prompt

                character_id : unique identifier of the character

                k : integer representing maximum number of relevant docs to be queried
        """
        if(self.__client == None or 
           self. __characters == None or
           self.__session_metadata == None):
            self.__logger.error("Session loading errror, No session currently loaded")
            return ServiceStatusCodes.internalError()
        
        for character in self.__characters:
            try:
                if character_id == character.get('character_id',''):
                    collection_name = character['character_id'] + self.__world_knowledge_suffix
                    collection : chromadb.Collection = self.__client.get_collection(collection_name)
                    result : chromadb.QueryResult = collection.query(query_texts=[prompt],n_results=k)
                    result : dict = {
                            "documents" : result.get("documents")[0],
                            "distances" : result.get("distances")[0]
                    }
                    self.__logger.debug("reult_world_knowledge : %s",result)
                    return ServiceStatusCodes.success(data=result.get("documents",[]))
            except Exception as e:
                self.__logger.error(e)
                return ServiceStatusCodes.internalError()



    def query_conv_memory(self, prompt : str, character_id: str, k : int = 5):
        """
            Given a user prompt and character id, query and return k relevant docs 
            from the character conversational memory
            
            Attributes:

                prompt : User given prompt

                character_id : unique identifier of the character

                k : integer representing maximum number of relevant docs to be queried
        """
        if(self.__client == None or 
           self. __characters == None or
           self.__session_metadata == None):
            self.__logger.error("Session loading errror, No session currently loaded")
            return ServiceStatusCodes.internalError()
        
        for character in self.__characters:
            try:
                if character_id == character.get('character_id',''):
                    collection_name = character['character_id'] + self.__conversational_mem_suffix
                    collection : chromadb.Collection = self.__client.get_collection(collection_name)
                    result : chromadb.QueryResult = collection.query(query_texts=[prompt],n_results=k)
                    result : dict = {
                            "documents" : result.get("documents")[0],
                            "distances" : result.get("distances")[0]
                    }
                    self.__logger.debug("result_conv_memory : %s",result)
                    return ServiceStatusCodes.success(data=result.get("documents",[]))
            except Exception as e:
                self.__logger.error(e)
                return ServiceStatusCodes.internalError()

    def add_conv_memory(self, conversation : Conversation, character_id: str):
        """
            Given a piece of conversation and character id, add the conversation to
            corresponding conversational memory of the character
            
            Attributes:

                Conversation : Single piece of conversation needed to be added to  the conv_memory

                character_id : unique identifier of the character
        """
        if(self.__client == None or 
           self. __characters == None or
           self.__session_metadata == None):
            self.__logger.error("Session loading errror, No session currently loaded")
            return ServiceStatusCodes.internalError()
        
        for character in self.__characters:
            try:
                if character_id == character.get('character_id',''):
                    collection_name = character['character_id'] + self.__conversational_mem_suffix
                    collection : chromadb.Collection = self.__client.get_collection(collection_name)
                    formatted_conv = f"The investigator asked {conversation['player']}\nI replied {conversation['llm']}"
                    collection.add(
                        ids=[str(uuid.uuid4())],
                        documents=[formatted_conv]
                    )
                    self.__logger.debug("Added Conversation : %s",formatted_conv)
                    return ServiceStatusCodes.success
            except Exception as e:
                self.__logger.error(e)
                return ServiceStatusCodes.internalError()
    

# Singleton instance
_db_service_instance: DatabaseService = None

def get_db_service() -> DatabaseService:
    return _db_service_instance

def init_db_service(version: str, data_path: str = "./session_data") -> DatabaseService:
    global _db_service_instance
    _db_service_instance = DatabaseService(version=version, data_path=data_path)
    return _db_service_instance