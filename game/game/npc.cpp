#include "npc.hpp"

#include "raylib.h"

#include "httplib.h"

#include <thread>

namespace Game {

namespace {

constexpr const char* kApiHost = "https://mlvoca.com";

} // namespace

void streamWorker(Npc& npc, std::string body, httplib::Headers headers)
{
    httplib::Client cli(kApiHost);
    auto result = httplib::stream::Post(cli, "/api/generate", headers, body, "");

    if (!result) {
        std::lock_guard<std::mutex> lock(npc.m_StreamMutex);
        npc.m_StreamOpenedOk = false;
        npc.m_WorkerFinished = true;
        return;
    }

    {
        std::lock_guard<std::mutex> lock(npc.m_StreamMutex);
        npc.m_StreamOpenedOk = true;
    }

    while (result.next()) {
        std::string chunk(result.data(), result.size());
        std::lock_guard<std::mutex> lock(npc.m_StreamMutex);
        npc.m_PendingChunks.push_back(std::move(chunk));
    }

    std::lock_guard<std::mutex> lock(npc.m_StreamMutex);
    npc.m_WorkerFinished = true;
}


Npc::Npc(std::string name)
    : Name{std::move(name)}
    , InputField{0}
{}

Npc::~Npc()
{
    if (m_WorkerThread.joinable()) {
        m_WorkerThread.join();
    }
}

void Npc::Update()
{
    if (m_NetworkState != NetworkState::kStreaming) {
        return;
    }

    std::vector<std::string> drained;
    bool worker_finished = false;
    {
        std::lock_guard<std::mutex> lock(m_StreamMutex);
        while (!m_PendingChunks.empty()) {
            drained.emplace_back(std::move(m_PendingChunks.front()));
            m_PendingChunks.pop_front();
        }
        worker_finished = m_WorkerFinished;
    }

    for (const std::string& chunk : drained) {
        TraceLog(LOG_INFO, "[Network] Streamed %.*s", static_cast<int>(chunk.size()),
                 chunk.c_str());
        Chat.back().Reply += chunk;
    }

    if (!worker_finished) {
        return;
    }

    if (m_WorkerThread.joinable()) {
        m_WorkerThread.join();
    }

    if (!m_StreamOpenedOk) {
        TraceLog(LOG_ERROR, "Invalid Request");
    }

    TraceLog(LOG_INFO, "Npc::%s Switched to Idle", Name.c_str());
    m_NetworkState = NetworkState::kIdle;
}

void Npc::GetResponse()
{
    m_NetworkState = NetworkState::kStreaming;

    TraceLog(LOG_INFO, "Npc::%s Switched to Streaming", Name.c_str());

    httplib::Headers headers = {};
    std::string body = TextFormat(
        "{                                      \
            \"prompt\": \"%s\",                 \
            \"prompt\": \"%s\"                  \
        }", InputField);

    {
        std::lock_guard<std::mutex> lock(m_StreamMutex);
        m_PendingChunks.clear();
        m_WorkerFinished = false;
        m_StreamOpenedOk = false;
    }

    Chat.emplace_back(InputField, "");
    InputField[0] = '\0';

    m_WorkerThread =
        std::thread(&streamWorker, std::ref(*this), std::move(body), std::move(headers));
}

} // namespace Game
