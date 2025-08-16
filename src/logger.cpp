#include "logger.h"
#include "utils.h"
#include <iostream>
#include <sstream>
#include <filesystem>

namespace CClean {

Logger& Logger::getInstance() {
    static Logger instance;
    return instance;
}

Logger::Logger() 
    : logFilename_(LOG_FILE)
    , consoleLogging_(true)
    , currentLevel_(LogLevel::INFO)
    , sessionStartTime_(0) {
}

Logger::~Logger() {
    if (logFile_ && logFile_->is_open()) {
        logFile_->close();
    }
}

void Logger::log(LogLevel level, const std::string& message) {
    if (level < currentLevel_) {
        return;
    }
    
    std::string timestamp = Utils::getCurrentTimestamp();
    std::string levelStr = levelToString(level);
    
    std::ostringstream ss;
    ss << "[" << timestamp << "] [" << levelStr << "] " << message;
    
    std::string logMessage = ss.str();
    
    if (consoleLogging_) {
        writeToConsole(logMessage);
    }
    
    writeToFile(logMessage);
}

void Logger::info(const std::string& message) {
    log(LogLevel::INFO, message);
}

void Logger::warning(const std::string& message) {
    log(LogLevel::WARNING, message);
}

void Logger::error(const std::string& message) {
    log(LogLevel::ERROR, message);
}

void Logger::debug(const std::string& message) {
    log(LogLevel::DEBUG, message);
}

void Logger::logCleanupResult(CleanupType type, const CleanupResult& result) {
    std::string typeStr;
    switch (type) {
        case CleanupType::TEMP_FILES:
            typeStr = "Temp Files";
            break;
        case CleanupType::BROWSER_CACHE:
            typeStr = "Browser Cache";
            break;
        case CleanupType::SYSTEM_FILES:
            typeStr = "System Files";
            break;
        case CleanupType::RECYCLE_BIN:
            typeStr = "Recycle Bin";
            break;
        case CleanupType::ALL:
            typeStr = "All Categories";
            break;
    }
    
    std::ostringstream ss;
    ss << typeStr << " cleanup completed: "
       << result.filesDeleted << "/" << result.filesScanned << " files processed, "
       << Utils::formatBytes(result.bytesFreed) << " freed";
    
    if (!result.success && !result.errorMessage.empty()) {
        ss << " (Error: " << result.errorMessage << ")";
        error(ss.str());
    } else {
        info(ss.str());
    }
}

void Logger::startSession() {
    sessionStartTime_ = GetTickCount64();
    info("=== CClean Session Started ===");
    info("Version: " + VERSION);
    info("Admin Rights: " + std::string(Utils::hasAdminRights() ? "Yes" : "No"));
}

void Logger::endSession() {
    size_t sessionDuration = GetTickCount64() - sessionStartTime_;
    double durationSeconds = sessionDuration / 1000.0;
    
    std::ostringstream ss;
    ss << "=== CClean Session Ended (Duration: " << durationSeconds << "s) ===";
    info(ss.str());
}

void Logger::setLogFile(const std::string& filename) {
    logFilename_ = filename;
    if (logFile_ && logFile_->is_open()) {
        logFile_->close();
    }
    logFile_.reset();
}

void Logger::setConsoleLogging(bool enabled) {
    consoleLogging_ = enabled;
}

void Logger::setLogLevel(LogLevel level) {
    currentLevel_ = level;
}

std::string Logger::levelToString(LogLevel level) {
    switch (level) {
        case LogLevel::INFO:    return "INFO";
        case LogLevel::WARNING: return "WARN";
        case LogLevel::ERROR:   return "ERROR";
        case LogLevel::DEBUG:   return "DEBUG";
        default:                return "UNKNOWN";
    }
}

void Logger::writeToFile(const std::string& message) {
    if (!logFile_) {
        rotateLogs();
        logFile_ = std::make_unique<std::ofstream>(logFilename_, std::ios::app);
    }
    
    if (logFile_ && logFile_->is_open()) {
        *logFile_ << message << std::endl;
        logFile_->flush();
    }
}

void Logger::writeToConsole(const std::string& message) {
    std::cout << message << std::endl;
}

void Logger::rotateLogs() {
    try {
        if (std::filesystem::exists(logFilename_)) {
            size_t fileSize = std::filesystem::file_size(logFilename_);
            
            if (fileSize > MAX_LOG_SIZE) {
                std::string backupName = logFilename_ + ".old";
                
                if (std::filesystem::exists(backupName)) {
                    std::filesystem::remove(backupName);
                }
                
                std::filesystem::rename(logFilename_, backupName);
            }
        }
    } catch (const std::exception&) {
        // Ignore rotation errors
    }
}

}