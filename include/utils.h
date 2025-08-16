#pragma once

#include <string>
#include <vector>
#include <windows.h>

namespace CClean {
namespace Utils {

std::string expandEnvironmentVariables(const std::string& path);

std::vector<std::string> findFiles(const std::string& path, const std::string& pattern = "*");

size_t getFileSize(const std::string& filePath);

size_t getDirectorySize(const std::string& dirPath);

bool deleteFileSecure(const std::string& filePath);

bool deleteDirectoryRecursive(const std::string& dirPath);

bool isFileInUse(const std::string& filePath);

std::string formatBytes(size_t bytes);

std::string getCurrentTimestamp();

bool hasAdminRights();

void requestAdminRights();

std::string getRecycleBinPath();

bool emptyRecycleBin();

bool pathExists(const std::string& path);

std::string getLastError();

}
}