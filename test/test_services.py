# test/test_services.py
import sys
import os

# 精确添加 interface 目录到模块搜索路径
current_file_dir = os.path.dirname(__file__)
interface_folder = os.path.abspath(os.path.join(current_file_dir, "..", "interface"))
sys.path.append(interface_folder)

from event_service import EventService
from news_service import NewsService
from history_service import HistorySearchService
import json

def test_event_service():
    print("\n===== 测试 EventService =====")
    es = EventService()
    all_events = es.get_event_list()
    print(f"读取事件总数: {len(all_events)}")
    if len(all_events) > 0:
        first_id = all_events[0]["event_id"]
        single_event = es.get_single_event(first_id)
        print(f"读取单个事件 {first_id}:")
        print(json.dumps(single_event, ensure_ascii=False, indent=2))
        empty_event = es.get_single_event("EVT_999999")
        print(f"不存在事件返回: {empty_event}, 预期: None")

def test_news_service():
    print("\n===== 测试 NewsService =====")
    ns = NewsService()
    test_event_id = "EVT_000001"
    articles = ns.get_articles_by_event(test_event_id)
    print(f"事件 {test_event_id} 关联新闻数量: {len(articles)}")
    if len(articles) > 0:
        print(json.dumps(articles[0], ensure_ascii=False, indent=2))
    empty_articles = ns.get_articles_by_event("EVT_999999")
    print(f"不存在事件新闻返回: {empty_articles}, 预期: []")

def test_history_service():
    print("\n===== 测试 HistorySearchService =====")
    hs = HistorySearchService()
    search_result = hs.semantic_search("哈兰德 食谱")
    print(f"语义检索结果数量: {len(search_result)}")
    if len(search_result) > 0:
        print(json.dumps(search_result[0], ensure_ascii=False, indent=2))
    filter_result = hs.condition_filter(category="山洪灾害", start_time="2026-01-01", end_time="2026-07-31")
    print(f"条件筛选结果数量: {len(filter_result)}")

if __name__ == "__main__":
    test_event_service()
    test_news_service()
    test_history_service()