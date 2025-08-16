#pragma once

#include <string>
#include <vector>

namespace CClean {

const std::string VERSION = "1.0.0";
const std::string APP_NAME = "CClean - Windows C Drive Cleaner";

const std::vector<std::string> TEMP_PATHS = {
    "%TEMP%",
    "%LOCALAPPDATA%\\Temp",
    "%WINDIR%\\Temp",
    "%WINDIR%\\SoftwareDistribution\\Download",
    "%WINDIR%\\Logs",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WebCache",
    "%WINDIR%\\Prefetch"
};

const std::vector<std::string> BROWSER_CACHE_PATHS = {
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache",
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Code Cache",
    "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache",
    "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2",
    "%LOCALAPPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2"
};

const std::vector<std::string> SYSTEM_CLEANUP_PATHS = {
    "%WINDIR%\\Logs\\CBS",
    "%WINDIR%\\Logs\\DISM",
    "%WINDIR%\\Logs\\DPX",
    "%WINDIR%\\Logs\\MoSetup",
    "%WINDIR%\\Panther",
    "%WINDIR%\\SoftwareDistribution\\DataStore\\Logs",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db",
    "%WINDIR%\\LiveKernelReports",
    "%WINDIR%\\Minidump"
};

const int MAX_LOG_SIZE = 10 * 1024 * 1024; // 10MB
const std::string LOG_FILE = "cclean.log";

enum class CleanupType {
    TEMP_FILES,
    BROWSER_CACHE, 
    SYSTEM_FILES,
    RECYCLE_BIN,
    ALL
};

struct CleanupResult {
    size_t filesScanned = 0;
    size_t filesDeleted = 0;
    size_t bytesFreed = 0;
    std::string errorMessage;
    bool success = true;
};

}