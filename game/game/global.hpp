#pragma once

#include "npc.hpp"
#include <array>

namespace Game {

class Global
{
public:

    // NPCs
    enum class NpcID 
    {
        kGoodGuy,
        kBadGuy,
        kCount
    };

    std::array<Npc, static_cast<int>(NpcID::kCount)> NPCs;

    // Singleton Accessing
    static Global& Get()
    {
        static Global instance{};
        return instance;
    }

private:
    Global()
    {
        for (int i = 0; i < static_cast<int>(NpcID::kCount); i++)
        {
            switch (static_cast<NpcID>(i))
            {
                #define NAME_NPC(name) \
                    case NpcID::k##name: NPCs[i].Name = #name; break
                    
                    NAME_NPC(GoodGuy);
                    NAME_NPC(BadGuy);

                #undef NAME_NPC

                case NpcID::kCount: break;
            }
        }
    }

    ~Global() {
    for (auto& npc : NPCs) {
        if (npc.m_WorkerThread.joinable()) {
            npc.m_WorkerThread.join();
        }
    }
}
};

} // namespace Game
