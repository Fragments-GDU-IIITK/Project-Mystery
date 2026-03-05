import sys
import tomli as toml

from src.server import Server

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
    print("Hello from backend!")
    versioning_info = readVersioningInfo("pyproject.toml")
    api_server = Server(port=3500,
                        route_prefix=f"/{versioning_info.get("name","")}/{versioning_info.get("version","")}")
    api_server.run()

if __name__ == "__main__":
    main()
