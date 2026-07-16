"""
一键运行整个预处理流程
全部在同一个进程中执行，不创建子进程，彻底避免 Windows 管道卡死
"""

import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime

from config import LOG_DIR, OUTPUT_DIR

# 确保日志目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 创建带时间戳的日志文件
run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f'run_all_{run_timestamp}.log'


def log_message(msg: str):
    """同时输出到控制台和日志文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {msg}"
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')


def run_script(module_name: str, description: str) -> bool:
    """
    直接导入并执行脚本的 main() 函数
    不创建子进程，永不卡死
    """
    log_message(f"\n{'='*60}")
    log_message(f"[RUN] [{description}] 运行: {module_name}")
    log_message(f"{'='*60}")

    start_time = time.time()

    try:
        # 动态导入模块（去掉 .py 后缀）
        module_path = f"scripts.{module_name.replace('.py', '')}"
        module = __import__(module_path, fromlist=['main'])

        # 执行 main() 函数
        if hasattr(module, 'main'):
            module.main()
        else:
            # 如果没有 main 函数，执行模块整体（相当于 python scripts/xxx.py）
            with open(Path(__file__).parent / module_name, encoding='utf-8') as f:
                code = f.read()
            exec(code, module.__dict__)

        elapsed = time.time() - start_time
        log_message(f"[OK] {module_name} 执行成功！耗时: {elapsed:.2f} 秒")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        log_message(f"[ERROR] {module_name} 执行失败: {e}，耗时 {elapsed:.2f} 秒")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# 所有脚本列表（按依赖顺序排列）
# 格式：(文件名, 描述)
# ==========================================
ALL_SCRIPTS = [
    ('01_load_data.py', '数据加载'),
    ('02_extract_body.py', '正文提取'),
    ('03_clean_deduplicate.py', '清洗去重'),
    ('04_segment.py', '中文分词'),
    ('05_feature_extract.py', 'TF-IDF特征提取'),
    ('06_generate_report.py', '生成统计报告'),
    ('07_advanced_analysis.py', '高级分析（情感/摘要/实体）'),
]


def main():
    log_message("=" * 60)
    log_message("[START] 舆情数据预处理流水线启动（纯净模式）")
    log_message(f"[TIME] 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message("[INFO] 将执行 7 个步骤（同一进程，不创建子进程）:")

    # ✅ 修正：正确的解包方式
    for step_num, (script, desc) in enumerate(ALL_SCRIPTS, 1):
        log_message(f"   {step_num:02d}. {desc} ({script})")
    log_message("=" * 60)

    overall_start = time.time()
    success_count = 0

    for script, desc in ALL_SCRIPTS:
        if run_script(script, desc):
            success_count += 1
        else:
            log_message(f"[ERROR] 步骤 [{desc}] 执行失败，流水线中断")
            break

    total_time = time.time() - overall_start

    # ==========================================
    # 最终总结
    # ==========================================
    log_message("\n" + "=" * 60)
    log_message("[SUMMARY] 执行总结")
    log_message("=" * 60)
    log_message(f"[OK] 成功步骤: {success_count}/{len(ALL_SCRIPTS)}")
    if success_count < len(ALL_SCRIPTS):
        log_message("[ERROR] 有步骤执行失败")
    log_message(f"[TIME] 总耗时: {total_time:.2f} 秒")
    log_message(f"[DIR] 输出目录: {OUTPUT_DIR}")

    # 列出输出文件
    if OUTPUT_DIR.exists():
        files = list(OUTPUT_DIR.glob('*'))
        log_message(f"\n[FILES] 输出文件列表 ({len(files)} 个):")
        for f in sorted(files):
            if f.is_dir():
                log_message(f"   [DIR] {f.name}/")
            else:
                size = f.stat().st_size / 1024
                log_message(f"   [FILE] {f.name} ({size:.1f} KB)")

    log_message("=" * 60)

    if success_count == len(ALL_SCRIPTS):
        log_message("[SUCCESS] 恭喜！所有步骤执行成功！")
        log_message(f"[INFO] 日志已保存至: {LOG_FILE}")
        return 0
    else:
        log_message("[WARN] 部分步骤执行失败，请检查日志")
        log_message(f"[INFO] 日志已保存至: {LOG_FILE}")
        return 1


if __name__ == '__main__':
    sys.exit(main())