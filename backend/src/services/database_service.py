import chromadb 

class DatabaseService:
    def __init__(self):
        self.__client = chromadb.AdminClient(
            
        )
