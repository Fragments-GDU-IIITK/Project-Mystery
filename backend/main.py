import sys
import tomli as toml
import logging
from pathlib import Path

from src.server import Server
from src.services.database_service import get_db_service 
from src.services.slm_service import SLM_Service

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
    api_server = Server(version= versioning_info.get("version",""),
                        route_prefix=f"/{versioning_info.get("name","")}/{versioning_info.get("version","")}")
    
    # ******* Test Code *******
    get_db_service().loadSession("Oq_AZ99Zh7RZEtEP")
    get_db_service().add_conv_memory({
        "player" : "What are you doing?",
        "llm" : "I am the best scientist in the world, who are you to question my authority"
    },"scientist_001")
    
    slm_service = SLM_Service()
    print(slm_service.prompt_composer("Hello, Tell me about yourself...", "scientist_001"))

    get_db_service().resetSession("Oq_AZ99Zh7RZEtEP")
    get_db_service().unloadSession()
    # ******* Test Code *******

    api_server.run()


if __name__ == "__main__": 
    main()