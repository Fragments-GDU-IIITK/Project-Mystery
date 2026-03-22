#pragma once

#include "httplib.h"

#include <string>
#include <vector>

namespace Game {

struct ChatEntry
{
    std::string Message;
    std::string Reply;
};

#define MAX_INPUT_FIELD_SIZE 256
class Npc
{
public:
    enum class NetworkState
    {
        kIdle,
        kStreaming,
    };

    std::string Name;
    std::vector<ChatEntry> Chat;
    char InputField[MAX_INPUT_FIELD_SIZE];

    Npc(std::string name)
        : Name{std::move(name)}
        , InputField{0}
        , m_Client{"https://mlvoca.com/api"}
        , m_Result{}
    {}

    void GetResponse();

    void Update();

    NetworkState GetNetworkState() const { return m_NetworkState; }

private:
    httplib::Client m_Client;
    httplib::stream::Result m_Result;

    NetworkState m_NetworkState{NetworkState::kIdle};
};

} // namespace Game
