"""
时序算法模块 (4号工程师)
========================
子模块：
  lifecycle/      — 舆情生命周期预测
  propagation/    — 事件传播溯源
  fake_detection/ — 虚假文本检测
  cross_event.py  — 跨事件格兰杰因果 + 符号化传递熵
  pipeline.py     — 统一报表接口（5号只调一个类）
  utils/          — 模拟数据生成
"""
from .lifecycle import LifecycleDetector
from .propagation import PropagationTracer
from .fake_detection import FakeDetector, FakeDetectorTrainer
from .cross_event import CrossEventAnalyzer
from .pipeline import Pipeline

__version__ = "0.4.0"
__all__ = [
    "LifecycleDetector", "PropagationTracer",
    "FakeDetector", "FakeDetectorTrainer",
    "CrossEventAnalyzer", "Pipeline",
]
