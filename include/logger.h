#pragma once

#include <string>
#include <fstream>
#include <memory>
#include "config.h"

namespace CClean {

enum class LogLevel {
    INFO,
    WARNING,
    ERROR,
    DEBUG
};

class Logger {
public:
    static Logger& getInstance();
    
    void log(LogLevel level, const std::string& message);
    void info(const std::string& message);
    void warning(const std::string& message);
    void error(const std::string& message);
    void debug(const std::string& message);
    
    void logCleanupResult(CleanupType type, const CleanupResult& result);
    void startSession();
    void endSession();
    
    void setLogFile(const std::string& filename);
    void setConsoleLogging(bool enabled);
    void setLogLevel(LogLevel level);
    
private:
    Logger();
    ~Logger();
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;
    
    std::string levelToString(LogLevel level);
    void writeToFile(const std::string& message);
    void writeToConsole(const std::string& message);
    void rotateLogs();
    
    std::unique_ptr<std::ofstream> logFile_;
    std::string logFilename_;
    bool consoleLogging_;
    LogLevel currentLevel_;
    size_t sessionStartTime_;
};

}