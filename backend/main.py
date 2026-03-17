import sys
import tomli as toml
import logging
from pathlib import Path

from src.server import Server
from src.services.database_service import DatabaseService

def readVersioningInfo(path : str) -> dict :
    """
        Read versioning information from pyproject.toml
            path : Filepath of pyproject.toml
    """
    try: 
        with open(path,mode = "rb") as fp:
            project_data = toml.load(fp)
            return project_data.get("project",{
            "name" : "unknown",
            "version" : "unknown",
            "description" : "unknown"
        })
    except FileNotFoundError:
        print(f"[ERROR] : {path} file doest not exist")
        return {
            "name" : "unknown",
            "version" : "unknown",
            "description" : "unknown"
        }

        


def main():
    # logging setup 
    logging.basicConfig(
        filename="server.log",
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


    versioning_info = readVersioningInfo("pyproject.toml")
    character_model_path = Path("src/models/character_model.json")
    database_service = DatabaseService(versioning_info.get("version",""))
    session_2 = database_service.createSession("MySession2",character_model_path) 
    print(session_2)
    print(database_service.getSessions())
    print(database_service.loadSession("sWMvmPZxENIE_3uv"))
    print(database_service.resetSession("sWMvmPZxENIE_3uv"))
    print(database_service.unloadSession())

    api_server = Server(port=3500,
                        route_prefix=f"/{versioning_info.get("name","")}/{versioning_info.get("version","")}")
    api_server.run()


if __name__ == "__main__": 
    main()
# 