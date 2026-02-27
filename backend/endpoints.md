# Backend Endpoints

## Requirements
- Start Flask Server 
- Ideally Load the SLM onto memory for predictions
- 3 Types of Endpoints:
    - HTTP Get Endpoints
    - HTTP Post Endpoints
    - Streamable Endpoint to stream Generated Tokens to frontend from backend  

## Starting Backend
- [ ] Initialize chromaDB database in a persistent directory
- [ ] Register Characters to the DB
    - Read characters.json, see if all ids are present and corresponding db stores are also present
- [ ] Start the server with active endpoints
- [ ] Intialize the slm and its lora adaptors

## Additional Backend Functionalities
- [ ] Define the actual suspect and method to check it
- [ ] Methods to load SLM backend and shift LORA adapters
- [ ] Prompt composer to compose prompt using:
    - Top n elements of conversational history
    - world knowldege
    - current question

## Endpoints

- Endpoint Prefix : `/<GameName>/<Version>/`
- POST - `checkSuspect`
    - Request
    ```json
        {
            "player_id" : "<player id>",
            "player_id": "player_001"
        }
    ```
    - Response
    ```json
        {
            "is_correct_suspect" : <bool>
        }
    ```
- GET - `characters`
    - returns a json object of the form
        ```json
            {
              "character": [
                    {
                      "id" : "<character id>"
                      "name": "<character name>",
                      "lm_type": "<character lm type>"
                    }
                ]
            }


            Example
            {
              "characters": [
                {
                  "id": "guard_01",
                  "name": "City Guard",
                  "lm_type": "TinyLlama"
                },
                {
                  "id": "merchant_01",
                  "name": "Merchant",
                  "lm_type": "TinyLlama"
                }
              ]
            }
        ```
- POST - `resetSession`
    - reset the game from game client
        - Delata all converstational history of NPCs
    - For multiple players session ids will be taken
    ```json
        {
          "player_id": "player_001"
        }
    ```

- Stream  - `talk`
    - refer : [Medium Article On Streaming AI Responses Using Flask](https://medium.com/@mr.murga/streaming-ai-responses-with-flask-a-practical-guide-677c15e82cdd)
    - Request 
    ```json
        {
          "player_id": "player_001",<Optional>
          "character_id": "guard_01",
          "message": "Why is the gate closed?"
        }
    ```
    - Stream Response
    ```
        data: Orders
        data: from
        data: the
        data: captain.
        data: [DONE]
    ```
    - compose prompt
    - switch LoRa adapter before generating 
    - attrib : characterName (as obtained from GET request)
    - SSE is by far easiest
