#!/usr/bin/env python3
"""
增强版快速C盘清理工具 - 高级分类版本
优化版本，新增垃圾文件类型，提升性能。
"""

import os
import sys
import time

# Add the cclean package to the path
sys.path.insert(0, os.path.dirname(__file__))

from cclean.cleaner import CCleaner
from cclean.config import CleanupType, format_bytes
from cclean.logger import CCleanLogger
from cclean.utils import get_free_disk_space, has_admin_rights, request_admin_rights
try:
    from optimized_cleaner import OptimizedCleaner
    from deep_cleaner import DeepCleaner
    from super_cleaner import SuperCleaner
    from system_optimizer import SystemOptimizer
except ImportError as e:
    print(f"⚠️ 导入清理器模块时出现问题: {e}")
    print("程序将使用标准清理器继续运行...")
    OptimizedCleaner = None
    DeepCleaner = None
    SuperCleaner = None
    SystemOptimizer = None

def print_banner():
    """打印增强版横幅。"""
    print("=" * 80)
    print("🧹 增强版C盘快速清理工具 v3.0 - 中文优化版")
    print("   ⚡ 多线程并行处理 | 🚀 高级清理分类 | 🛡️ 安全保护")
    print("=" * 80)
    print()

def display_categories():
    """显示可用的清理分类。"""
    categories = [
        ("1", "🔥 快速临时文件", "系统和用户临时文件（优化算法）"),
        ("2", "🌐 快速浏览器缓存", "所有浏览器缓存和数据（并行处理）"),
        ("3", "🗂️ 系统文件", "Windows日志和系统缓存"),
        ("4", "💻 开发工具", "IDE缓存、构建产物、包管理器"),
        ("5", "📁 媒体下载", "未完成下载、媒体缓存、Office临时文件"),
        ("6", "🎮 游戏平台", "Steam、Epic、Origin、战网缓存"),
        ("7", "⚙️ 标准系统优化", "Windows搜索、更新缓存、性能日志"),
        ("8", "🗑️ 回收站", "清空回收站"),
        ("9", "🚀 标准全面清理", "清理所有标准分类"),
        ("10", "💥 深度激进清理", "深度扫描+激进清理（最大效果）"),
        ("11", "🎯 智能深度清理", "AI智能选择最优清理策略"),
        ("12", "☢️ 核弹级超级清理", "最激进清理，最大化释放空间（谨慎使用）"),
        ("13", "🔧 深度系统优化", "全面系统性能优化，提升运行速度")
    ]

    print("📋 可用清理分类（按效果排序）：")
    print("-" * 70)
    for num, name, desc in categories:
        print(f"  {num:<3}. {name:<18} - {desc}")
    print()
    print("💡 推荐：选择 12 获得最大空间释放，选择 13 获得最佳性能优化！")
    print("⚠️  注意：选项 12 会删除所有临时文件和缓存，选项 13 会修改系统设置")
    print("📋 建议：先运行 13 优化系统性能，再运行 12 清理垃圾文件")
    print()

def get_initial_stats():
    """获取初始系统统计信息。"""
    try:
        free_space_before = get_free_disk_space("C:")
        return free_space_before
    except Exception:
        return 0

def show_results_summary(results, time_taken, space_before, space_after, cleaner=None):
    """显示详细的结果摘要。"""
    print("\n" + "=" * 80)
    print("🎉 清理完成！")
    print("=" * 80)

    total_files_scanned = sum(r.files_scanned for r in results)
    total_files_deleted = sum(r.files_deleted for r in results)
    total_space_freed = sum(r.bytes_freed for r in results)

    print(f"📊 清理统计：")
    print(f"   ├─ 扫描文件数：{total_files_scanned:,}")
    print(f"   ├─ 清理文件数：{total_files_deleted:,}")
    print(f"   ├─ 释放空间：{format_bytes(total_space_freed)}")
    print(f"   └─ 耗时：{time_taken:.2f} 秒")

    if space_after > space_before:
        actual_freed = space_after - space_before
        print(f"💽 磁盘空间变化：+{format_bytes(actual_freed)}")

    # 计算清理效率
    if time_taken > 0:
        files_per_second = total_files_deleted / time_taken
        mb_per_second = (total_space_freed / (1024 * 1024)) / time_taken
        print(f"⚡ 清理效率：{files_per_second:.1f} 文件/秒，{mb_per_second:.1f} MB/秒")

    # 显示失败信息
    if cleaner and hasattr(cleaner, 'failed_deletions') and cleaner.failed_deletions:
        failed_summary = cleaner.get_failed_deletions_summary()
        total_failed = len(cleaner.failed_deletions)
        print(f"\n⚠️  删除失败统计：{total_failed} 个文件")
        for error_type, count in failed_summary.items():
            print(f"   ├─ {error_type}: {count} 个文件")
        if total_failed > 5:
            print("   └─ 提示：以管理员身份运行可以删除更多文件")

    print()
    print("🌟 您的系统现在更加干净快速！")
    print("=" * 80)

def run_category_cleanup(cleaner, optimized_cleaner, deep_cleaner, super_cleaner, system_optimizer, cleanup_type, category_name):
    """运行特定分类的清理，带有增强的进度显示。"""
    print(f"\n{'='*60}")
    print(f"🧹 正在处理：{category_name}")
    print(f"{'='*60}")

    start_time = time.time()

    # 深度系统优化
    if cleanup_type == "SYSTEM_OPTIMIZE":
        if not system_optimizer:
            print("❌ 系统优化器不可用，使用标准清理...")
            cleanup_result = cleaner.clean_system_files()
        else:
            print("🔧 执行深度系统优化 - 全面提升系统性能...")
            optimization_results = system_optimizer.perform_system_optimization()

            # 合并所有结果
            total_scanned = sum(r.files_deleted for r in optimization_results.values())  # 使用处理数作为扫描数
            total_deleted = sum(r.files_deleted for r in optimization_results.values())
            total_bytes = sum(r.bytes_freed for r in optimization_results.values())

            from cclean.config import CleanupResult
            cleanup_result = CleanupResult()
            cleanup_result.files_scanned = total_scanned
            cleanup_result.files_deleted = total_deleted
            cleanup_result.bytes_freed = total_bytes
            cleanup_result.success = True

    # 核弹级超级清理
    elif cleanup_type == "NUCLEAR":
        if not super_cleaner:
            print("❌ 超级清理器不可用，使用标准全面清理...")
            cleanup_result = cleaner.perform_full_cleanup()
        else:
            print("☢️ 执行核弹级超级清理 - 最大化空间释放...")
            cleanup_results = super_cleaner.perform_nuclear_cleanup()

            # 合并所有结果
            total_scanned = sum(r.files_deleted for r in cleanup_results.values())  # 使用删除数作为扫描数
            total_deleted = sum(r.files_deleted for r in cleanup_results.values())
            total_bytes = sum(r.bytes_freed for r in cleanup_results.values())

            from cclean.config import CleanupResult
            cleanup_result = CleanupResult()
            cleanup_result.files_scanned = total_scanned
            cleanup_result.files_deleted = total_deleted
            cleanup_result.bytes_freed = total_bytes
            cleanup_result.success = True

    # 深度激进清理
    elif cleanup_type == "DEEP_AGGRESSIVE":
        if not deep_cleaner:
            print("❌ 深度清理器不可用，使用标准全面清理...")
            cleanup_result = cleaner.perform_full_cleanup()
        else:
            print("💥 执行深度激进清理 - 最大化清理效果...")
            cleanup_results = deep_cleaner.perform_deep_cleanup()

            # 合并所有结果
            total_scanned = sum(r.files_scanned for r in cleanup_results.values())
            total_deleted = sum(r.files_deleted for r in cleanup_results.values())
            total_bytes = sum(r.bytes_freed for r in cleanup_results.values())

            from cclean.config import CleanupResult
            cleanup_result = CleanupResult()
            cleanup_result.files_scanned = total_scanned
            cleanup_result.files_deleted = total_deleted
            cleanup_result.bytes_freed = total_bytes
            cleanup_result.success = True

    # 智能深度清理
    elif cleanup_type == "SMART_DEEP":
        if not deep_cleaner:
            print("❌ 深度清理器不可用，使用标准清理策略...")
            cleanup_result = cleaner.perform_full_cleanup()
        else:
            print("🎯 执行智能深度清理 - 平衡效果与安全...")

            # 智能选择最有效的清理方法
            smart_results = []

            # 优先清理用户区域（更安全）
            user_result = deep_cleaner.deep_user_cleanup()
            smart_results.append(user_result)

            # 浏览器深度清理
            browser_result = deep_cleaner.deep_browser_cleanup()
            smart_results.append(browser_result)

            # 缩略图缓存清理
            thumb_result = deep_cleaner.thumbnail_cache_cleanup()
            smart_results.append(thumb_result)

            # 内存转储清理
            dump_result = deep_cleaner.memory_dump_cleanup()
            smart_results.append(dump_result)

            # 合并结果
            from cclean.config import CleanupResult
            cleanup_result = CleanupResult()
            cleanup_result.files_scanned = sum(r.files_scanned for r in smart_results)
            cleanup_result.files_deleted = sum(r.files_deleted for r in smart_results)
            cleanup_result.bytes_freed = sum(r.bytes_freed for r in smart_results)
            cleanup_result.success = True

    # 对于临时文件和浏览器缓存，使用优化清理器
    elif cleanup_type in [CleanupType.TEMP_FILES, CleanupType.BROWSER_CACHE]:
        if optimized_cleaner:
            print("⚡ 使用高性能优化算法...")
            cleanup_result = optimized_cleaner.smart_cleanup(cleanup_type)
        else:
            print("⚡ 使用标准清理算法...")
            if cleanup_type == CleanupType.TEMP_FILES:
                cleanup_result = cleaner.clean_temp_files()
            else:
                cleanup_result = cleaner.clean_browser_cache()
    elif cleanup_type == CleanupType.ALL:
        # 全面清理时，混合使用优化和标准清理器
        print("🚀 使用智能混合清理算法...")
        cleanup_result = cleaner.perform_full_cleanup()
    else:
        # 其他类型使用标准清理器
        cleanup_functions = {
            CleanupType.SYSTEM_FILES: cleaner.clean_system_files,
            CleanupType.DEVELOPMENT_FILES: cleaner.clean_development_files,
            CleanupType.MEDIA_FILES: cleaner.clean_media_files,
            CleanupType.GAMING_FILES: cleaner.clean_gaming_files,
            CleanupType.SYSTEM_OPTIMIZATION: cleaner.clean_system_optimization,
            CleanupType.RECYCLE_BIN: cleaner.clean_recycle_bin
        }

        cleanup_function = cleanup_functions.get(cleanup_type)
        if cleanup_function:
            cleanup_result = cleanup_function()
        else:
            print(f"❌ 未知的清理类型：{cleanup_type}")
            return None

    end_time = time.time()
    category_time = end_time - start_time

    # 确保进度行完成
    print()  # 新行以完成任何进度显示

    # 摘要
    if cleanup_result.files_scanned == 0:
        print(f"✅ {category_name} 已经很干净了！")
    else:
        print(f"✨ {category_name} 清理完成：")
        print(f"   📁 处理文件：{cleanup_result.files_deleted:,}/{cleanup_result.files_scanned:,}")
        print(f"   💾 释放空间：{format_bytes(cleanup_result.bytes_freed)}")
        print(f"   ⏱️ 用时：{category_time:.2f} 秒")

        # 显示清理效率
        if category_time > 0 and cleanup_result.files_deleted > 0:
            efficiency = cleanup_result.files_deleted / category_time
            print(f"   ⚡ 效率：{efficiency:.1f} 文件/秒")

    return cleanup_result

def safe_input(prompt: str, default: str = "") -> str:
    """安全的输入函数，处理EOFError和其他异常。"""
    try:
        return input(prompt).strip()
    except EOFError:
        print(f"\n❌ 无法读取输入（可能是在没有控制台的环境中运行）")
        print(f"自动使用默认值: {default}")
        print("程序将在3秒后继续...")
        time.sleep(3)
        return default
    except KeyboardInterrupt:
        print("\n👋 用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 输入错误: {e}")
        print(f"自动使用默认值: {default}")
        print("程序将在3秒后继续...")
        time.sleep(3)
        return default

def create_optimized_progress_callback():
    """创建优化的进度回调函数。"""
    last_update_time = [0]  # 使用列表以便在闭包中修改

    def progress_update(message, current, total):
        current_time = time.time()
        # 限制更新频率，避免过度刷新
        if current_time - last_update_time[0] < 0.1 and current < total:
            return

        last_update_time[0] = current_time

        if total > 0:
            percentage = (current / total) * 100
            bar_length = 40
            filled_length = int(bar_length * current / total)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f'\r[{bar}] {current:,}/{total:,} ({percentage:.1f}%) - {message}', end='', flush=True)
        else:
            print(f'\r⏳ {message} - 已处理 {current:,} 项', end='', flush=True)

    return progress_update

def main():
    """主执行函数。"""
    print_banner()

    # 检查管理员权限
    if not has_admin_rights():
        print("⚠️  检测到非管理员权限运行")
        print("   某些系统文件可能无法清理，建议以管理员身份运行")
        choice = safe_input("是否以管理员身份重新启动？(y/N): ", "n").lower()
        if choice == 'y':
            try:
                request_admin_rights()
                return
            except Exception as e:
                print(f"❌ 无法获取管理员权限: {e}")
                print("继续以普通权限运行...")
        print()
    else:
        print("✅ 已获得管理员权限，可以清理所有文件")
        print()

    # 获取初始系统状态
    free_space_before = get_initial_stats()
    print(f"💽 C盘可用空间：{format_bytes(free_space_before)}")
    print()

    display_categories()

    # 获取用户选择
    while True:
        try:
            choice = safe_input("请选择清理分类 (1-13) 或输入 'q' 退出：", "q").lower()

            if choice == 'q':
                print("👋 再见！")
                return 0

            choice_num = int(choice)
            if 1 <= choice_num <= 13:
                # 对于核弹级清理，需要用户确认
                if choice_num == 12:
                    print("\n⚠️  警告：核弹级清理将删除所有临时文件、缓存和系统垃圾文件")
                    print("这可能会影响某些程序的启动速度（首次启动时需要重建缓存）")
                    confirm = safe_input("确定要继续吗？(y/N): ", "n").lower()
                    if confirm not in ['y', 'yes', '是']:
                        print("已取消核弹级清理")
                        continue
                # 对于深度系统优化，需要用户确认
                elif choice_num == 13:
                    print("\n⚠️  警告：深度系统优化将修改系统设置和清理系统缓存")
                    print("这包括清理事件日志、重置网络设置、优化注册表等操作")
                    print("建议在执行前创建系统还原点")
                    confirm = safe_input("确定要继续吗？(y/N): ", "n").lower()
                    if confirm not in ['y', 'yes', '是']:
                        print("已取消深度系统优化")
                        continue
                break
            else:
                print("❌ 请输入 1-13 之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")

    # 映射选择到清理类型
    category_map = {
        1: (CleanupType.TEMP_FILES, "快速临时文件"),
        2: (CleanupType.BROWSER_CACHE, "快速浏览器缓存"),
        3: (CleanupType.SYSTEM_FILES, "系统文件"),
        4: (CleanupType.DEVELOPMENT_FILES, "开发工具"),
        5: (CleanupType.MEDIA_FILES, "媒体下载"),
        6: (CleanupType.GAMING_FILES, "游戏平台"),
        7: (CleanupType.SYSTEM_OPTIMIZATION, "系统优化"),
        8: (CleanupType.RECYCLE_BIN, "回收站"),
        9: (CleanupType.ALL, "标准全面清理"),
        10: ("DEEP_AGGRESSIVE", "深度激进清理"),
        11: ("SMART_DEEP", "智能深度清理"),
        12: ("NUCLEAR", "核弹级超级清理"),
        13: ("SYSTEM_OPTIMIZE", "深度系统优化")
    }

    cleanup_type, category_name = category_map[choice_num]

    # 初始化日志记录器和清理器
    logger = CCleanLogger.get_instance("enhanced_cleanup.log", console_output=False)  # 减少日志噪音
    logger.start_session()

    # 创建清理器
    cleaner = CCleaner(logger)
    cleaner.set_verbose(False)  # 保持输出简洁

    # 创建可选的增强清理器（如果可用）
    optimized_cleaner = OptimizedCleaner(logger) if OptimizedCleaner else None
    deep_cleaner = DeepCleaner(logger) if DeepCleaner else None  
    super_cleaner = SuperCleaner(logger) if SuperCleaner else None
    system_optimizer = SystemOptimizer(logger) if SystemOptimizer else None

    # 使用优化的进度显示
    progress_callback = create_optimized_progress_callback()
    cleaner.set_progress_callback(progress_callback)
    
    # 为可用的增强清理器设置进度回调
    if optimized_cleaner:
        optimized_cleaner.set_progress_callback(progress_callback)
    if deep_cleaner:
        deep_cleaner.set_progress_callback(progress_callback)
    if super_cleaner:
        super_cleaner.set_progress_callback(progress_callback)
    if system_optimizer:
        system_optimizer.set_progress_callback(progress_callback)

    print("⚡ 使用五引擎清理系统：标准 + 优化 + 深度 + 超级 + 系统优化引擎...")

    print(f"\n🚀 开始 {category_name} 清理...")

    # 根据选择显示不同的算法信息
    if cleanup_type == "SYSTEM_OPTIMIZE":
        print("🔧 使用深度系统优化算法 - 全面提升系统性能...")
    elif cleanup_type == "NUCLEAR":
        print("☢️ 使用核弹级超级清理算法 - 最大化空间释放...")
    elif cleanup_type == "DEEP_AGGRESSIVE":
        print("💥 使用深度激进清理算法 - 最大化清理效果...")
    elif cleanup_type == "SMART_DEEP":
        print("🎯 使用AI智能深度清理算法 - 平衡效果与安全...")
    else:
        print("⚡ 智能选择最优清理算法...")

    start_time = time.time()

    try:
        # 执行清理
        results = []

        # 特殊处理深度清理、超级清理和系统优化
        if cleanup_type in ["SYSTEM_OPTIMIZE", "NUCLEAR", "DEEP_AGGRESSIVE", "SMART_DEEP"]:
            result = run_category_cleanup(cleaner, optimized_cleaner, deep_cleaner, super_cleaner, system_optimizer, cleanup_type, category_name)
            if result:
                results.append(result)
        elif cleanup_type == CleanupType.ALL:
            # 逐个运行所有分类以获得更好的进度跟踪
            all_categories = [
                (CleanupType.TEMP_FILES, "临时文件"),
                (CleanupType.BROWSER_CACHE, "浏览器缓存"),
                (CleanupType.SYSTEM_FILES, "系统文件"),
                (CleanupType.DEVELOPMENT_FILES, "开发工具"),
                (CleanupType.MEDIA_FILES, "媒体下载"),
                (CleanupType.GAMING_FILES, "游戏平台"),
                (CleanupType.SYSTEM_OPTIMIZATION, "系统优化"),
                (CleanupType.RECYCLE_BIN, "回收站")
            ]

            print(f"📋 将按顺序清理 {len(all_categories)} 个分类...")

            for i, (cat_type, cat_name) in enumerate(all_categories, 1):
                print(f"\n🔄 进度：{i}/{len(all_categories)} - 准备清理 {cat_name}")
                result = run_category_cleanup(cleaner, optimized_cleaner, deep_cleaner, super_cleaner, system_optimizer, cat_type, cat_name)
                if result:
                    results.append(result)
        else:
            result = run_category_cleanup(cleaner, optimized_cleaner, deep_cleaner, super_cleaner, system_optimizer, cleanup_type, category_name)
            if result:
                results.append(result)

        end_time = time.time()
        time_taken = end_time - start_time

        # 获取最终系统状态
        free_space_after = get_free_disk_space("C:")

        # 显示结果
        show_results_summary(results, time_taken, free_space_before, free_space_after, cleaner)

        # 提供后续建议
        print("\n💡 建议：")
        print("   • 定期运行此工具以保持系统清洁")
        print("   • 考虑使用磁盘清理计划任务")
        print("   • 检查启动程序以提升开机速度")
        
        # 防止程序立即关闭
        print("\n按任意键退出...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

    except KeyboardInterrupt:
        print("\n⏹️  用户中断了清理过程")
        print("按任意键退出...")
        try:
            input()
        except:
            pass
        return 130
    except Exception as e:
        print(f"\n❌ 清理过程中出现错误：{e}")
        print("程序将自动退出...")
        logger.error(f"清理错误：{e}")
        time.sleep(5)  # 给用户时间查看错误信息
        return 1
    finally:
        logger.end_session()

    return 0

if __name__ == "__main__":
    sys.exit(main())