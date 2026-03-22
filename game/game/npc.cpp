#include "npc.hpp"
#include "raylib.h"
#include <httplib.h>

namespace Game {

void Npc::Update()
{
    if (m_NetworkState == NetworkState::kStreaming)
    {
        if (!m_Result) m_NetworkState = NetworkState::kIdle;

        Chat.end()->Reply += std::string(m_Result.data(), 
                                         m_Result.size());
    }
}

void Npc::GetResponse()
{
    m_NetworkState = NetworkState::kStreaming;
    std::string prompt{InputField};

    Chat.emplace_back(InputField, "");
    InputField[0] = '\0';

    // If i ever need them later
    httplib::Headers headers = {};
    std::string body = TextFormat("");

    m_Result = httplib::stream::Post(m_Client, "/generate", headers, body, "");

    /*
    httplib::Client cli("https://mlvoca.com/api/generate");

    auto result = httplib::stream::Get(cli, "/stream");

    if (result) {
        while (result.next()) {
            // std::cout.write(result.data(), result.size());
        }
    }
    */
}

} // namespace Game
