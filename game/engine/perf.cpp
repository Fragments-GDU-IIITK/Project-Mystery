#include "perf.hpp"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <thread>

namespace Engine {

Perf* Perf::s_Instance = nullptr;

static uint64_t NowMicros() {
    using namespace std::chrono;
    return 
		static_cast<uint64_t>(
			duration_cast<microseconds>(steady_clock::now().time_since_epoch()).count()
		);
}

static uint32_t CurrentThreadID() {
    return 
		static_cast<uint32_t>(
			std::hash<std::thread::id>{}(std::this_thread::get_id())
		);
}

Perf::Perf()
    : m_file(nullptr), m_firstEntry(true)
{
    m_file = fopen(PERF_LOG_FILE, "w");
    assert(m_file && "Perf: failed to open log file");

    fprintf(m_file, "[\n");
}

Perf::~Perf()
{
    if (m_file) {
        fprintf(m_file, "\n]\n");
        fclose(m_file);
        m_file = nullptr;
    }
}

void Perf::Init() {
    assert(!s_Instance && "Perf::Init() called twice");
    s_Instance = new Perf();
}

void Perf::Shutdown() {
    assert(s_Instance && "Perf::Shutdown() called before Init()");
    delete s_Instance;
    s_Instance = nullptr;
}

Perf& Perf::Get() {
    assert(s_Instance && "Perf::Get() called before Init()");
    return *s_Instance;
}

void Perf::WriteEntry(const char* name, uint64_t startUs, uint64_t endUs, uint32_t threadID) {
    // { "name":"shi", "ph":"X", "ts":<start_us>, "dur":<dur_us>, "pid":0, "tid":<tid> }
    const uint64_t durUs = (endUs >= startUs) ? (endUs - startUs) : 0;

    std::lock_guard<std::mutex> lock(m_mutex);

    if (!m_firstEntry)
        fprintf(m_file, ",\n");
    m_firstEntry = false;

    fprintf(m_file,
            R"(  {"name":"%s","ph":"X","ts":%llu,"dur":%llu,"pid":0,"tid":%u})",
            name,
            static_cast<unsigned long long>(startUs),
            static_cast<unsigned long long>(durUs),
            threadID);
}

PerfTimer::PerfTimer(const char* name)
    : m_Name(name), m_StartUs(NowMicros()) {}

PerfTimer::~PerfTimer()
{
    const uint64_t endUs = NowMicros();
    Perf::Get().WriteEntry(m_Name, m_StartUs, endUs, CurrentThreadID());
}

} // namespace Engine
