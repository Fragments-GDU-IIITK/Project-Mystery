#pragma once

#include <string>
#include <vector>

namespace Game {

struct ChatEntry
{
    std::string Message;
    std::string Reply;
};

#define MAX_INPUT_FIELD_SIZE 256
struct Npc
{
    std::string Name;
    std::vector<ChatEntry> Chat;
    char InputField[MAX_INPUT_FIELD_SIZE];

    // will be used to hold the streamed text, temporarily
    std::string StreamedText;

    Npc(std::string name) 
        : Name{std::move(name)}
        , InputField{0}
    {}
};

class Global
{
public:

    // NPCs
    Npc GoodGuy;
    Npc BadGuy;


    // Singleton Accessing
    static Global& Get()
    {
        static Global instance{};
        return instance;
    }

private:
    Global()
        : GoodGuy("Good Guy")
        , BadGuy("Bad Guy")
    {}
};

} // namespace Game
