from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from event_service import EventService
from news_service import NewsService
from history_service import HistorySearchService
from similar_service import SimilarEventService

app = FastAPI(title="舆情事件智能分析系统")

# 全局跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 全局单例，全局仅加载一次数据
event_service = EventService()
news_service = NewsService()
history_service = HistorySearchService(event_service)
similar_service = SimilarEventService(event_service)

# 请求模型定义
class FilterQuery(BaseModel):
    category: Optional[str] = None
    keyword: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class SimilarQuery(BaseModel):
    query: str
    top_k: int = 5

# 1. 获取全部精简事件列表
@app.get("/api/analysis/events")
def get_event_list():
    return event_service.get_event_list()

# 2. 单事件完整详情
@app.get("/api/analysis/event/{eid}")
def get_event_detail(eid: str):
    data = event_service.get_single_event(eid)
    if not data:
        raise HTTPException(status_code=404, detail="事件ID不存在")
    return data

# 3. 获取事件关联全部新闻
@app.get("/api/analysis/event/{eid}/articles")
def get_event_news(eid: str):
    return news_service.get_articles_by_event(eid)

# 4. 条件筛选接口（类别/关键词/时间）
@app.post("/api/history/filter")
def filter_history_events(filter_info: FilterQuery):
    params = filter_info.model_dump()
    return history_service.condition_filter(**params)

# 5. FAISS语义相似检索
@app.post("/api/similar/search")
def search_similar_events(req: SimilarQuery):
    return similar_service.search(req.query, req.top_k)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)