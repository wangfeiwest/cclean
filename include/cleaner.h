#pragma once

#include <vector>
#include <functional>
#include "config.h"

namespace CClean {

class CCleaner {
public:
    CCleaner();
    ~CCleaner();
    
    CleanupResult scanTempFiles();
    CleanupResult cleanTempFiles();
    
    CleanupResult scanBrowserCache();
    CleanupResult cleanBrowserCache();
    
    CleanupResult scanSystemFiles();
    CleanupResult cleanSystemFiles();
    
    CleanupResult cleanRecycleBin();
    
    CleanupResult performFullScan();
    CleanupResult performFullClean();
    
    void setProgressCallback(std::function<void(const std::string&, int)> callback);
    void setDryRun(bool enabled);
    void setVerbose(bool enabled);
    
private:
    CleanupResult scanPath(const std::string& path);
    CleanupResult cleanPath(const std::string& path);
    CleanupResult processPaths(const std::vector<std::string>& paths, bool cleanMode);
    
    void updateProgress(const std::string& message, int percentage);
    bool shouldDeleteFile(const std::string& filePath);
    
    std::function<void(const std::string&, int)> progressCallback_;
    bool dryRun_;
    bool verbose_;
    size_t totalBytesFound_;
    size_t totalFilesFound_;
};

}