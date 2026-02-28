from src.server import Server

def main():
    print("Hello from backend!")
    api_server = Server(port=3500)
    api_server.run()

if __name__ == "__main__":
    main()
