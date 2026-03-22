#pragma once

#include "npc.hpp"

namespace Game {

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
