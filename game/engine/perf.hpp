#pragma once
/*
 * Performance Timer — output viewable in Chromium's chrome://tracing
 *
 * Usage:
 *   PERF_SCOPE()              — times the current function (uses __PRETTY_FUNCTION__)
 *   PERF_SCOPE_NAME("myName") — times a named block
 *
 *
 */

#include <cstdint>
#include <cstdio>
#include <mutex>
#include <string>

namespace Engine {

#define PERF_LOG_FILE "perf.json"

/**
 * Call Perf::Init() once at startup, Perf::Shutdown() on exit.
*/
class Perf {
public:
	static void Init();
	static void Shutdown();
    static Perf& Get();

    // Called by PerfTimer to write perf data
    void WriteEntry(const char* name, uint64_t startUs, uint64_t endUs, uint32_t threadID);

private:
    Perf();
    ~Perf();


    // Shouldn't Copy ts
    Perf(const Perf&)            = delete;
    Perf& operator=(const Perf&) = delete;

    FILE* m_file;
    std::mutex m_mutex;
    bool m_firstEntry;

    static Perf* s_Instance;
};

struct PerfData {
    const char* name;
    uint64_t    startUs;
    uint64_t    endUs;
    uint32_t    threadID;
};

// Scoped Timer, writes shi on exit
class PerfTimer {
public:
    explicit PerfTimer(const char* name);
    ~PerfTimer();

	/**
	* So what happens when you call the macro in main() is the destructor is called
	* after the static variable is destroyed, so just call this in main istead of letting
	* it be called in the destructor
	*/

private:
    const char* m_Name;
    uint64_t    m_StartUs;
	bool m_IsDone;
};

#define PERF_SCOPE_NAME(name) ::Engine::PerfTimer __perfTimer##__LINE__(name)
#define PERF_SCOPE()          PERF_SCOPE_NAME(__PRETTY_FUNCTION__)

} // namespace Engine
