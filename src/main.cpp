#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <windows.h>
#include "config.h"
#include "cleaner.h"
#include "logger.h"
#include "utils.h"

using namespace CClean;

void printUsage() {
    std::cout << "\n" << APP_NAME << " v" << VERSION << "\n";
    std::cout << "Usage: cclean [options]\n\n";
    std::cout << "Options:\n";
    std::cout << "  -s, --scan         Scan for files without deleting\n";
    std::cout << "  -c, --clean        Clean files (default action)\n";
    std::cout << "  -t, --temp         Only process temporary files\n";
    std::cout << "  -b, --browser      Only process browser cache\n";
    std::cout << "  -r, --recycle      Only empty recycle bin\n";
    std::cout << "  -y, --system       Only process system files\n";
    std::cout << "  -a, --all          Process all categories (default)\n";
    std::cout << "  -d, --dry-run      Show what would be deleted without deleting\n";
    std::cout << "  -v, --verbose      Enable verbose output\n";
    std::cout << "  -q, --quiet        Suppress console output\n";
    std::cout << "  -l, --log FILE     Specify log file (default: cclean.log)\n";
    std::cout << "  -h, --help         Show this help message\n";
    std::cout << "\nExamples:\n";
    std::cout << "  cclean --scan      # Scan all categories\n";
    std::cout << "  cclean --temp -d   # Dry run temp file cleanup\n";
    std::cout << "  cclean --all -v    # Clean all with verbose output\n";
    std::cout << "\n";
}

void printHeader() {
    std::cout << "\n";
    std::cout << "╔══════════════════════════════════════════════════════════════╗\n";
    std::cout << "║                     " << APP_NAME << "                      ║\n";
    std::cout << "║                         Version " << VERSION << "                          ║\n";
    std::cout << "╚══════════════════════════════════════════════════════════════╝\n";
    std::cout << "\n";
}

void progressCallback(const std::string& message, int percentage) {
    std::cout << "\r[" << std::string(percentage / 2, '█') << std::string(50 - percentage / 2, '░') << "] ";
    std::cout << percentage << "% - " << message << std::flush;
    
    if (percentage == 100) {
        std::cout << "\n";
    }
}

void printResult(const CleanupResult& result, const std::string& operation) {
    std::cout << "\n" << operation << " Results:\n";
    std::cout << "  Files Scanned: " << result.filesScanned << "\n";
    
    if (result.filesDeleted > 0) {
        std::cout << "  Files Deleted: " << result.filesDeleted << "\n";
    }
    
    std::cout << "  Space Freed: " << Utils::formatBytes(result.bytesFreed) << "\n";
    
    if (!result.success && !result.errorMessage.empty()) {
        std::cout << "  Warnings: " << result.errorMessage << "\n";
    }
    
    std::cout << "\n";
}

bool confirmCleanup(const CleanupResult& scanResult) {
    std::cout << "\nScan Summary:\n";
    std::cout << "  Files Found: " << scanResult.filesScanned << "\n";
    std::cout << "  Space to Free: " << Utils::formatBytes(scanResult.bytesFreed) << "\n\n";
    
    std::cout << "Do you want to proceed with cleanup? (y/N): ";
    std::string input;
    std::getline(std::cin, input);
    
    return !input.empty() && (input[0] == 'y' || input[0] == 'Y');
}

int main(int argc, char* argv[]) {
    SetConsoleOutputCP(CP_UTF8);
    
    bool scanOnly = false;
    bool dryRun = false;
    bool verbose = false;
    bool quiet = false;
    CleanupType cleanupType = CleanupType::ALL;
    std::string logFile = LOG_FILE;
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        if (arg == "-s" || arg == "--scan") {
            scanOnly = true;
        } else if (arg == "-c" || arg == "--clean") {
            scanOnly = false;
        } else if (arg == "-t" || arg == "--temp") {
            cleanupType = CleanupType::TEMP_FILES;
        } else if (arg == "-b" || arg == "--browser") {
            cleanupType = CleanupType::BROWSER_CACHE;
        } else if (arg == "-r" || arg == "--recycle") {
            cleanupType = CleanupType::RECYCLE_BIN;
        } else if (arg == "-y" || arg == "--system") {
            cleanupType = CleanupType::SYSTEM_FILES;
        } else if (arg == "-a" || arg == "--all") {
            cleanupType = CleanupType::ALL;
        } else if (arg == "-d" || arg == "--dry-run") {
            dryRun = true;
        } else if (arg == "-v" || arg == "--verbose") {
            verbose = true;
        } else if (arg == "-q" || arg == "--quiet") {
            quiet = true;
        } else if ((arg == "-l" || arg == "--log") && i + 1 < argc) {
            logFile = argv[++i];
        } else if (arg == "-h" || arg == "--help") {
            printUsage();
            return 0;
        } else {
            std::cerr << "Unknown option: " << arg << "\n";
            printUsage();
            return 1;
        }
    }
    
    if (quiet && verbose) {
        std::cerr << "Error: Cannot use both --quiet and --verbose options\n";
        return 1;
    }
    
    Logger& logger = Logger::getInstance();
    logger.setLogFile(logFile);
    logger.setConsoleLogging(!quiet);
    logger.setLogLevel(verbose ? LogLevel::DEBUG : LogLevel::INFO);
    
    if (!quiet) {
        printHeader();
        
        std::cout << "System Information:\n";
        std::cout << "  Admin Rights: " << (Utils::hasAdminRights() ? "Yes" : "No") << "\n";
        std::cout << "  Log File: " << logFile << "\n";
        
        if (dryRun) {
            std::cout << "  Mode: DRY RUN (no files will be deleted)\n";
        }
        
        std::cout << "\n";
    }
    
    logger.startSession();
    
    try {
        CCleaner cleaner;
        cleaner.setDryRun(dryRun);
        cleaner.setVerbose(verbose);
        cleaner.setProgressCallback(quiet ? nullptr : progressCallback);
        
        CleanupResult result;
        std::string operation;
        
        if (scanOnly) {
            operation = "Scan";
            
            switch (cleanupType) {
                case CleanupType::TEMP_FILES:
                    result = cleaner.scanTempFiles();
                    break;
                case CleanupType::BROWSER_CACHE:
                    result = cleaner.scanBrowserCache();
                    break;
                case CleanupType::SYSTEM_FILES:
                    result = cleaner.scanSystemFiles();
                    break;
                case CleanupType::RECYCLE_BIN:
                    // For recycle bin, we need to scan it manually
                    result.filesScanned = 1;
                    result.bytesFreed = Utils::getDirectorySize(Utils::getRecycleBinPath());
                    result.success = true;
                    break;
                case CleanupType::ALL:
                    result = cleaner.performFullScan();
                    break;
            }
        } else {
            if (!dryRun && !Utils::hasAdminRights()) {
                std::cout << "Warning: Running without administrator privileges may limit cleanup effectiveness.\n";
                std::cout << "Some system files may not be accessible.\n\n";
            }
            
            if (!dryRun && !quiet) {
                CleanupResult scanResult;
                
                std::cout << "Performing initial scan...\n";
                
                switch (cleanupType) {
                    case CleanupType::TEMP_FILES:
                        scanResult = cleaner.scanTempFiles();
                        break;
                    case CleanupType::BROWSER_CACHE:
                        scanResult = cleaner.scanBrowserCache();
                        break;
                    case CleanupType::SYSTEM_FILES:
                        scanResult = cleaner.scanSystemFiles();
                        break;
                    case CleanupType::RECYCLE_BIN:
                        scanResult.filesScanned = 1;
                        scanResult.bytesFreed = Utils::getDirectorySize(Utils::getRecycleBinPath());
                        scanResult.success = true;
                        break;
                    case CleanupType::ALL:
                        scanResult = cleaner.performFullScan();
                        break;
                }
                
                if (scanResult.filesScanned == 0) {
                    std::cout << "No files found to clean.\n";
                    logger.endSession();
                    return 0;
                }
                
                if (!confirmCleanup(scanResult)) {
                    std::cout << "Cleanup cancelled by user.\n";
                    logger.endSession();
                    return 0;
                }
            }
            
            operation = dryRun ? "Dry Run" : "Cleanup";
            
            switch (cleanupType) {
                case CleanupType::TEMP_FILES:
                    result = cleaner.cleanTempFiles();
                    break;
                case CleanupType::BROWSER_CACHE:
                    result = cleaner.cleanBrowserCache();
                    break;
                case CleanupType::SYSTEM_FILES:
                    result = cleaner.cleanSystemFiles();
                    break;
                case CleanupType::RECYCLE_BIN:
                    result = cleaner.cleanRecycleBin();
                    break;
                case CleanupType::ALL:
                    result = cleaner.performFullClean();
                    break;
            }
        }
        
        logger.logCleanupResult(cleanupType, result);
        
        if (!quiet) {
            printResult(result, operation);
        }
        
        logger.endSession();
        
        return result.success ? 0 : 1;
        
    } catch (const std::exception& e) {
        logger.error("Fatal error: " + std::string(e.what()));
        std::cerr << "Fatal error: " << e.what() << "\n";
        logger.endSession();
        return 1;
    }
}