#include "utils.h"
#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <iostream>
#include <sstream>
#include <filesystem>
#include <iomanip>

namespace CClean {
namespace Utils {

std::string expandEnvironmentVariables(const std::string& path) {
    std::vector<char> buffer(MAX_PATH);
    DWORD result = ExpandEnvironmentStringsA(path.c_str(), buffer.data(), buffer.size());
    
    if (result == 0) {
        return path;
    }
    
    if (result > buffer.size()) {
        buffer.resize(result);
        result = ExpandEnvironmentStringsA(path.c_str(), buffer.data(), buffer.size());
    }
    
    return std::string(buffer.data());
}

std::vector<std::string> findFiles(const std::string& path, const std::string& pattern) {
    std::vector<std::string> files;
    
    try {
        std::string expandedPath = expandEnvironmentVariables(path);
        std::string searchPath = expandedPath + "\\" + pattern;
        
        WIN32_FIND_DATAA findData;
        HANDLE hFind = FindFirstFileA(searchPath.c_str(), &findData);
        
        if (hFind == INVALID_HANDLE_VALUE) {
            return files;
        }
        
        do {
            if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                std::string fileName = expandedPath + "\\" + findData.cFileName;
                files.push_back(fileName);
            }
        } while (FindNextFileA(hFind, &findData));
        
        FindClose(hFind);
        
        if (std::filesystem::exists(expandedPath) && std::filesystem::is_directory(expandedPath)) {
            for (const auto& entry : std::filesystem::recursive_directory_iterator(expandedPath)) {
                if (entry.is_regular_file()) {
                    files.push_back(entry.path().string());
                }
            }
        }
    } catch (const std::exception&) {
        // Directory may not exist or access denied
    }
    
    return files;
}

size_t getFileSize(const std::string& filePath) {
    try {
        return std::filesystem::file_size(filePath);
    } catch (const std::exception&) {
        return 0;
    }
}

size_t getDirectorySize(const std::string& dirPath) {
    size_t totalSize = 0;
    
    try {
        std::string expandedPath = expandEnvironmentVariables(dirPath);
        
        if (std::filesystem::exists(expandedPath) && std::filesystem::is_directory(expandedPath)) {
            for (const auto& entry : std::filesystem::recursive_directory_iterator(expandedPath)) {
                if (entry.is_regular_file()) {
                    totalSize += entry.file_size();
                }
            }
        }
    } catch (const std::exception&) {
        // Directory may not exist or access denied
    }
    
    return totalSize;
}

bool deleteFileSecure(const std::string& filePath) {
    try {
        return std::filesystem::remove(filePath);
    } catch (const std::exception&) {
        return false;
    }
}

bool deleteDirectoryRecursive(const std::string& dirPath) {
    try {
        std::string expandedPath = expandEnvironmentVariables(dirPath);
        return std::filesystem::remove_all(expandedPath) > 0;
    } catch (const std::exception&) {
        return false;
    }
}

bool isFileInUse(const std::string& filePath) {
    HANDLE hFile = CreateFileA(
        filePath.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        0,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL
    );
    
    if (hFile == INVALID_HANDLE_VALUE) {
        DWORD error = GetLastError();
        if (error == ERROR_SHARING_VIOLATION || error == ERROR_ACCESS_DENIED) {
            return true;
        }
    } else {
        CloseHandle(hFile);
    }
    
    return false;
}

std::string formatBytes(size_t bytes) {
    const char* units[] = { "B", "KB", "MB", "GB", "TB" };
    int unitIndex = 0;
    double size = static_cast<double>(bytes);
    
    while (size >= 1024 && unitIndex < 4) {
        size /= 1024;
        unitIndex++;
    }
    
    std::ostringstream ss;
    ss.precision(2);
    ss << std::fixed << size << " " << units[unitIndex];
    return ss.str();
}

std::string getCurrentTimestamp() {
    SYSTEMTIME st;
    GetLocalTime(&st);
    
    std::ostringstream ss;
    ss << st.wYear << "-"
       << std::setfill('0') << std::setw(2) << st.wMonth << "-"
       << std::setfill('0') << std::setw(2) << st.wDay << " "
       << std::setfill('0') << std::setw(2) << st.wHour << ":"
       << std::setfill('0') << std::setw(2) << st.wMinute << ":"
       << std::setfill('0') << std::setw(2) << st.wSecond;
    
    return ss.str();
}

bool hasAdminRights() {
    BOOL isElevated = FALSE;
    HANDLE hToken = NULL;
    
    if (OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        TOKEN_ELEVATION elevation;
        DWORD cbSize = sizeof(TOKEN_ELEVATION);
        
        if (GetTokenInformation(hToken, TokenElevation, &elevation, sizeof(elevation), &cbSize)) {
            isElevated = elevation.TokenIsElevated;
        }
        
        CloseHandle(hToken);
    }
    
    return isElevated == TRUE;
}

void requestAdminRights() {
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    
    ShellExecuteA(NULL, "runas", exePath, NULL, NULL, SW_SHOWNORMAL);
}

std::string getRecycleBinPath() {
    char path[MAX_PATH];
    
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_BITBUCKET, NULL, SHGFP_TYPE_CURRENT, path))) {
        return std::string(path);
    }
    
    return "C:\\$Recycle.Bin";
}

bool emptyRecycleBin() {
    return SUCCEEDED(SHEmptyRecycleBinA(NULL, NULL, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND));
}

bool pathExists(const std::string& path) {
    try {
        std::string expandedPath = expandEnvironmentVariables(path);
        return std::filesystem::exists(expandedPath);
    } catch (const std::exception&) {
        return false;
    }
}

std::string getLastError() {
    DWORD error = GetLastError();
    LPSTR messageBuffer = nullptr;
    
    FormatMessageA(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        error,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPSTR)&messageBuffer,
        0,
        NULL
    );
    
    std::string message(messageBuffer);
    LocalFree(messageBuffer);
    
    return message;
}

}
}