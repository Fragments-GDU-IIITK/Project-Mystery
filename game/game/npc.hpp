#pragma once

#include <cstring>
#include <deque>
#include <mutex>
#include <string>
#include <thread>
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

    explicit Npc(std::string name);
    ~Npc();

    Npc(const Npc&) = delete;
    Npc& operator=(const Npc&) = delete;
    Npc(Npc&&) = delete;
    Npc& operator=(Npc&&) = delete;

    void GetResponse();
    void GetResponse(const char* Buffer, size_t len)
    {
        memcpy(InputField, Buffer, len);
        InputField[len] = 0;
        GetResponse();
    }

    void Update();

    NetworkState GetNetworkState() const { return m_NetworkState; }

public:
    std::mutex m_StreamMutex;
    std::deque<std::string> m_PendingChunks;
    bool m_WorkerFinished{false};
    bool m_StreamOpenedOk{false};
    std::thread m_WorkerThread;

    NetworkState m_NetworkState{NetworkState::kIdle};
};

} // namespace Game
