#include "cleaner.h"
#include "utils.h"
#include "logger.h"
#include <iostream>
#include <algorithm>

namespace CClean {

CCleaner::CCleaner() 
    : dryRun_(false)
    , verbose_(false)
    , totalBytesFound_(0)
    , totalFilesFound_(0) {
}

CCleaner::~CCleaner() = default;

CleanupResult CCleaner::scanTempFiles() {
    updateProgress("Scanning temporary files...", 0);
    return processPaths(TEMP_PATHS, false);
}

CleanupResult CCleaner::cleanTempFiles() {
    updateProgress("Cleaning temporary files...", 0);
    return processPaths(TEMP_PATHS, true);
}

CleanupResult CCleaner::scanBrowserCache() {
    updateProgress("Scanning browser cache...", 0);
    return processPaths(BROWSER_CACHE_PATHS, false);
}

CleanupResult CCleaner::cleanBrowserCache() {
    updateProgress("Cleaning browser cache...", 0);
    return processPaths(BROWSER_CACHE_PATHS, true);
}

CleanupResult CCleaner::scanSystemFiles() {
    updateProgress("Scanning system files...", 0);
    return processPaths(SYSTEM_CLEANUP_PATHS, false);
}

CleanupResult CCleaner::cleanSystemFiles() {
    updateProgress("Cleaning system files...", 0);
    return processPaths(SYSTEM_CLEANUP_PATHS, true);
}

CleanupResult CCleaner::cleanRecycleBin() {
    CleanupResult result;
    updateProgress("Cleaning Recycle Bin...", 0);
    
    try {
        std::string recycleBinPath = Utils::getRecycleBinPath();
        size_t sizeBeforeClean = Utils::getDirectorySize(recycleBinPath);
        
        if (dryRun_) {
            result.bytesFreed = sizeBeforeClean;
            result.filesScanned = 1;
            Logger::getInstance().info("DRY RUN: Would empty Recycle Bin (" + 
                                     Utils::formatBytes(sizeBeforeClean) + ")");
        } else {
            bool success = Utils::emptyRecycleBin();
            if (success) {
                result.bytesFreed = sizeBeforeClean;
                result.filesDeleted = 1;
                result.success = true;
                Logger::getInstance().info("Recycle Bin emptied successfully");
            } else {
                result.success = false;
                result.errorMessage = "Failed to empty Recycle Bin: " + Utils::getLastError();
                Logger::getInstance().error(result.errorMessage);
            }
        }
        
        updateProgress("Recycle Bin cleanup completed", 100);
    } catch (const std::exception& e) {
        result.success = false;
        result.errorMessage = "Exception during Recycle Bin cleanup: " + std::string(e.what());
        Logger::getInstance().error(result.errorMessage);
    }
    
    return result;
}

CleanupResult CCleaner::performFullScan() {
    updateProgress("Performing full system scan...", 0);
    
    CleanupResult totalResult;
    
    auto tempResult = scanTempFiles();
    totalResult.filesScanned += tempResult.filesScanned;
    totalResult.bytesFreed += tempResult.bytesFreed;
    
    updateProgress("Full scan: temp files completed", 25);
    
    auto browserResult = scanBrowserCache();
    totalResult.filesScanned += browserResult.filesScanned;
    totalResult.bytesFreed += browserResult.bytesFreed;
    
    updateProgress("Full scan: browser cache completed", 50);
    
    auto systemResult = scanSystemFiles();
    totalResult.filesScanned += systemResult.filesScanned;
    totalResult.bytesFreed += systemResult.bytesFreed;
    
    updateProgress("Full scan: system files completed", 75);
    
    std::string recycleBinPath = Utils::getRecycleBinPath();
    size_t recycleBinSize = Utils::getDirectorySize(recycleBinPath);
    totalResult.filesScanned += 1;
    totalResult.bytesFreed += recycleBinSize;
    
    updateProgress("Full scan completed", 100);
    
    Logger::getInstance().info("Full scan completed: " + 
                              std::to_string(totalResult.filesScanned) + " items found, " +
                              Utils::formatBytes(totalResult.bytesFreed) + " can be freed");
    
    return totalResult;
}

CleanupResult CCleaner::performFullClean() {
    updateProgress("Performing full system cleanup...", 0);
    
    CleanupResult totalResult;
    
    auto tempResult = cleanTempFiles();
    totalResult.filesScanned += tempResult.filesScanned;
    totalResult.filesDeleted += tempResult.filesDeleted;
    totalResult.bytesFreed += tempResult.bytesFreed;
    
    updateProgress("Full cleanup: temp files completed", 25);
    
    auto browserResult = cleanBrowserCache();
    totalResult.filesScanned += browserResult.filesScanned;
    totalResult.filesDeleted += browserResult.filesDeleted;
    totalResult.bytesFreed += browserResult.bytesFreed;
    
    updateProgress("Full cleanup: browser cache completed", 50);
    
    auto systemResult = cleanSystemFiles();
    totalResult.filesScanned += systemResult.filesScanned;
    totalResult.filesDeleted += systemResult.filesDeleted;
    totalResult.bytesFreed += systemResult.bytesFreed;
    
    updateProgress("Full cleanup: system files completed", 75);
    
    auto recycleBinResult = cleanRecycleBin();
    totalResult.filesScanned += recycleBinResult.filesScanned;
    totalResult.filesDeleted += recycleBinResult.filesDeleted;
    totalResult.bytesFreed += recycleBinResult.bytesFreed;
    
    updateProgress("Full cleanup completed", 100);
    
    Logger::getInstance().info("Full cleanup completed: " + 
                              std::to_string(totalResult.filesDeleted) + "/" +
                              std::to_string(totalResult.filesScanned) + " items cleaned, " +
                              Utils::formatBytes(totalResult.bytesFreed) + " freed");
    
    return totalResult;
}

void CCleaner::setProgressCallback(std::function<void(const std::string&, int)> callback) {
    progressCallback_ = callback;
}

void CCleaner::setDryRun(bool enabled) {
    dryRun_ = enabled;
}

void CCleaner::setVerbose(bool enabled) {
    verbose_ = enabled;
}

CleanupResult CCleaner::processPaths(const std::vector<std::string>& paths, bool cleanMode) {
    CleanupResult totalResult;
    
    for (size_t i = 0; i < paths.size(); ++i) {
        const std::string& path = paths[i];
        
        CleanupResult pathResult;
        if (cleanMode) {
            pathResult = cleanPath(path);
        } else {
            pathResult = scanPath(path);
        }
        
        totalResult.filesScanned += pathResult.filesScanned;
        totalResult.filesDeleted += pathResult.filesDeleted;
        totalResult.bytesFreed += pathResult.bytesFreed;
        
        if (!pathResult.success && !pathResult.errorMessage.empty()) {
            if (totalResult.errorMessage.empty()) {
                totalResult.errorMessage = pathResult.errorMessage;
            } else {
                totalResult.errorMessage += "; " + pathResult.errorMessage;
            }
            totalResult.success = false;
        }
        
        int progress = static_cast<int>((i + 1) * 100 / paths.size());
        updateProgress(cleanMode ? "Cleaning..." : "Scanning...", progress);
    }
    
    return totalResult;
}

CleanupResult CCleaner::scanPath(const std::string& path) {
    CleanupResult result;
    
    if (!Utils::pathExists(path)) {
        if (verbose_) {
            Logger::getInstance().debug("Path does not exist: " + path);
        }
        return result;
    }
    
    try {
        std::string expandedPath = Utils::expandEnvironmentVariables(path);
        auto files = Utils::findFiles(expandedPath);
        
        for (const auto& file : files) {
            if (shouldDeleteFile(file)) {
                size_t fileSize = Utils::getFileSize(file);
                result.filesScanned++;
                result.bytesFreed += fileSize;
                
                if (verbose_) {
                    Logger::getInstance().debug("Found: " + file + " (" + Utils::formatBytes(fileSize) + ")");
                }
            }
        }
        
        result.success = true;
    } catch (const std::exception& e) {
        result.success = false;
        result.errorMessage = "Error scanning " + path + ": " + e.what();
        Logger::getInstance().warning(result.errorMessage);
    }
    
    return result;
}

CleanupResult CCleaner::cleanPath(const std::string& path) {
    CleanupResult result;
    
    if (!Utils::pathExists(path)) {
        if (verbose_) {
            Logger::getInstance().debug("Path does not exist: " + path);
        }
        return result;
    }
    
    try {
        std::string expandedPath = Utils::expandEnvironmentVariables(path);
        auto files = Utils::findFiles(expandedPath);
        
        for (const auto& file : files) {
            if (shouldDeleteFile(file)) {
                size_t fileSize = Utils::getFileSize(file);
                result.filesScanned++;
                
                if (dryRun_) {
                    if (verbose_) {
                        Logger::getInstance().debug("DRY RUN: Would delete " + file + " (" + Utils::formatBytes(fileSize) + ")");
                    }
                    result.bytesFreed += fileSize;
                    result.filesDeleted++;
                } else {
                    if (Utils::deleteFileSecure(file)) {
                        result.filesDeleted++;
                        result.bytesFreed += fileSize;
                        
                        if (verbose_) {
                            Logger::getInstance().debug("Deleted: " + file + " (" + Utils::formatBytes(fileSize) + ")");
                        }
                    } else {
                        std::string error = "Failed to delete " + file + ": " + Utils::getLastError();
                        Logger::getInstance().warning(error);
                        
                        if (result.errorMessage.empty()) {
                            result.errorMessage = error;
                        }
                    }
                }
            }
        }
        
        result.success = true;
    } catch (const std::exception& e) {
        result.success = false;
        result.errorMessage = "Error cleaning " + path + ": " + e.what();
        Logger::getInstance().error(result.errorMessage);
    }
    
    return result;
}

void CCleaner::updateProgress(const std::string& message, int percentage) {
    if (progressCallback_) {
        progressCallback_(message, percentage);
    }
    
    if (verbose_) {
        Logger::getInstance().info(message + " (" + std::to_string(percentage) + "%)");
    }
}

bool CCleaner::shouldDeleteFile(const std::string& filePath) {
    if (Utils::isFileInUse(filePath)) {
        return false;
    }
    
    std::string fileName = filePath.substr(filePath.find_last_of("\\/") + 1);
    
    if (fileName == "desktop.ini" || fileName == "thumbs.db") {
        return false;
    }
    
    return true;
}

}