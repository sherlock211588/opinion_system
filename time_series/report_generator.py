"""
智能分析报告生成 & 问答 (Report Generator)
===========================================
把 Pipeline 输出的 JSON 转换成自然语言分析报告，支持用户追问。

两种模式：
  - 有 LLM API：接入大模型，生成高质量报告和回答
  - 无 LLM API：规则兜底，基于模板生成报告（不依赖外部服务）

使用方式：
    from time_series.report_generator import ReportGenerator

    gen = ReportGenerator(api_key="your_key")   # 有 Key 就接 LLM
    gen = ReportGenerator()                     # 无 Key 纯规则兜底

    # 生成自然语言报告
    text = gen.generate_narrative(event_report)

    # 自由问答
    answer = gen.answer_question(event_report, "事件什么时候到高潮？")
"""

from __future__ import annotations
from typing import Any


class ReportGenerator:
    """智能分析报告生成器。

    5号调用方式：
        gen = ReportGenerator(api_key="sk-xxx", base_url="https://api.openai.com/v1")
        # 或者不传 Key，用规则兜底：
        gen = ReportGenerator()

        narrative = gen.generate_narrative(event_report)
        answer = gen.answer_question(event_report, "这个事件风险大吗？")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def has_llm(self) -> bool:
        return self.api_key is not None

    # ================================================================
    #  5号调的两个入口
    # ================================================================

    def generate_narrative(self, event_report: dict[str, Any]) -> str:
        """生成事件分析报告（200-300字自然语言）。

        参数 event_report 就是 pipe.event_report() 的返回值。
        """
        if self.has_llm:
            return self._llm_generate(self._build_report_prompt(event_report))
        else:
            return self._rule_based_report(event_report)

    def answer_question(
        self, event_report: dict[str, Any], question: str,
    ) -> str:
        """回答用户对事件的提问。

        参数 event_report 同上，question 是用户的自然语言问题。
        """
        if self.has_llm:
            return self._llm_generate(self._build_qa_prompt(event_report, question))
        else:
            return self._rule_based_qa(event_report, question)

    # ================================================================
    #  Prompt 构造
    # ================================================================

    def _build_report_prompt(self, r: dict[str, Any]) -> str:
        lifecycle = r.get("lifecycle", {})
        stats = r.get("article_stats") or {}
        sentiment = r.get("sentiment_distribution", {})
        prop = r.get("propagation") or {}

        parts = [
            "你是专业的网络舆情分析师。请根据以下数据生成一份简洁的分析报告（200-300字），包含：",
            "1. 事件当前状态和趋势判断",
            "2. 主要风险点",
            "3. 建议行动",
            "",
            "【事件信息】",
            f"- 事件标题：{r.get('event_title', '未知')}",
            f"- 事件分类：{r.get('category', '未知')}",
            f"- 当前阶段：{lifecycle.get('current_stage', '未知')}",
            f"- 阶段概率：{lifecycle.get('stage_probabilities', {})}",
            f"- 综合热度指数：{lifecycle.get('current_heat_index', 0):.0f}/100",
            f"- 趋势方向：{lifecycle.get('trend_direction', '未知')}",
            f"- 趋势斜率：{lifecycle.get('trend_slope', 0):+.2f}",
            f"- 峰值报道量：{lifecycle.get('peak_count', 0)} 篇/时",
            f"- 总持续时长：{lifecycle.get('total_duration_hours', 0)} 小时",
            "",
            "【情感分布】",
            f"- 正面：{sentiment.get('positive', 0):.1%}",
            f"- 负面：{sentiment.get('negative', 0):.1%}",
            f"- 中性：{sentiment.get('neutral', 0):.1%}",
            "",
            "【预警信息】",
        ]

        cew = lifecycle.get("critical_early_warning", {})
        parts.append(f"- 临界减速预警：{cew.get('warning_level', 'none')}")
        if cew.get("message"):
            parts.append(f"- 预警详情：{cew['message']}")

        resurgence = lifecycle.get("resurgence", {})
        parts.append(f"- 二次爆发：{'是' if resurgence.get('is_resurgence') else '否'}")

        parts.extend([
            "",
            "【虚假信息统计】",
            f"- 总文章数：{stats.get('total', 0)}",
            f"- 疑似虚假：{stats.get('fake', 0)} 篇",
            f"- 待验证：{stats.get('uncertain', 0)} 篇",
            f"- 可信：{stats.get('real', 0)} 篇",
            f"- 虚假占比：{stats.get('fake_ratio', 0):.1%}",
            "",
            "【传播概况】",
        ])

        if prop and "error" not in str(prop):
            parts.extend([
                f"- 最长传播链：{prop.get('propagation_depth', 0)} 层",
                f"- 关键节点数：{len(prop.get('key_nodes', []))}",
                f"- 估计触达：{prop.get('total_reach', {}).get('estimated_unique_reach', 0):,} 人次",
            ])
        else:
            parts.append("- 暂无传播链数据")

        parts.extend([
            "",
            "请用中文输出分析报告，语气客观专业，不要超过300字。",
        ])
        return "\n".join(parts)

    def _build_qa_prompt(self, r: dict[str, Any], question: str) -> str:
        lifecycle = r.get("lifecycle", {})
        stats = r.get("article_stats") or {}
        sentiment = r.get("sentiment_distribution", {})

        return "\n".join([
            "你是专业的网络舆情分析师。用户正在查看一个舆情事件的详情，向你提问。",
            "请基于以下数据回答问题，用简洁的中文，不超过200字。如果数据不足以回答，请诚实说明。",
            "",
            "【事件数据】",
            f"- 事件：{r.get('event_title', '')}",
            f"- 分类：{r.get('category', '')}",
            f"- 当前阶段：{lifecycle.get('current_stage', '未知')}",
            f"- 热度指数：{lifecycle.get('current_heat_index', 0):.0f}/100",
            f"- 趋势：{lifecycle.get('trend_direction', '未知')}",
            f"- 正面{ sentiment.get('positive', 0):.1%} / 负面{ sentiment.get('negative', 0):.1%} / 中性{ sentiment.get('neutral', 0):.1%}",
            f"- 疑似虚假占比：{stats.get('fake_ratio', 0):.1%}",
            f"- 预警等级：{lifecycle.get('critical_early_warning', {}).get('warning_level', 'none')}",
            "",
            f"【用户问题】{question}",
            "",
            "请回答：",
        ])

    # ================================================================
    #  LLM 调用
    # ================================================================

    def _llm_generate(self, prompt: str) -> str:
        """通用 LLM 调用，兼容 OpenAI / 国内大模型（智谱/DeepSeek/通义等）。"""
        if self._client is None:
            self._client = self._build_client()

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的网络舆情分析师。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=600,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[LLM 调用失败: {e}]"

    def _build_client(self):
        """根据 base_url 自动适配不同厂商的 SDK。"""
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    # ================================================================
    #  规则兜底（无 LLM 时使用）
    # ================================================================

    def _rule_based_report(self, r: dict[str, Any]) -> str:
        """基于模板生成分析报告，不依赖 LLM。"""
        lifecycle = r.get("lifecycle", {})
        stats = r.get("article_stats") or {}
        sentiment = r.get("sentiment_distribution", {})

        stage = lifecycle.get("current_stage", "未知")
        heat = lifecycle.get("current_heat_index", 0)
        trend = lifecycle.get("trend_direction", "未知")
        warning = lifecycle.get("critical_early_warning", {}).get("warning_level", "none")
        fake_ratio = stats.get("fake_ratio", 0)
        neg = sentiment.get("negative", 0)

        # 阶段判断 → 建议
        stage_advice = {
            "潜伏期": "事件尚在早期，建议持续监控，提前准备应对方案。",
            "成长期": "事件正在快速升温，建议密切关注舆情走向，及时发布权威信息。",
            "高潮期": "事件已到达峰值，公众关注度极高，建议立即启动应急响应，加强信息发布频率。",
            "衰退期": "事件热度正在下降，建议做好善后工作，避免二次发酵。",
            "二次爆发": "事件出现二次反弹，需警惕新的舆论风暴，建议排查反弹原因。",
        }

        # 风险判断
        risks = []
        if warning == "red":
            risks.append("系统临界减速预警为红色，舆情状态高度不稳定，存在失控风险")
        elif warning == "orange":
            risks.append("系统临界减速预警为橙色，需保持警惕")
        if fake_ratio > 0.1:
            risks.append(f"虚假信息占比较高（{fake_ratio:.1%}），需及时辟谣")
        if neg > 0.5:
            risks.append("公众负面情绪占比过半，需关注舆论引导")
        if trend == "上升" and heat > 60:
            risks.append("事件热度高且仍在上升，可能进一步扩大影响")

        advice = stage_advice.get(stage, "建议持续关注事件发展。")

        report = f"""【{r.get('event_title', '')}】事件分析报告

一、当前状态：事件处于「{stage}」，综合热度指数 {heat:.0f}/100，整体趋势{trend}。"""

        if lifecycle.get("stage_probabilities"):
            probs = lifecycle["stage_probabilities"]
            probs_str = "，".join(f"{k}可能性{v:.0%}" for k, v in probs.items())
            report += f"\n阶段概率分布：{probs_str}。"

        report += f"""

二、情感概况：正面{sentiment.get('positive', 0):.1%}，负面{sentiment.get('negative', 0):.1%}，中性{sentiment.get('neutral', 0):.1%}。"""

        if neg > 0.5:
            report += "负面情绪占主导，需加强正面引导。"
        elif neg < 0.3:
            report += "总体情绪偏正面，舆论态势良好。"

        report += f"""

三、虚假信息：共监测 {stats.get('total', 0)} 篇相关文章，其中疑似虚假 {stats.get('fake', 0)} 篇（占比 {fake_ratio:.1%}）。"""

        report += "\n\n四、风险评估：\n"
        if risks:
            for i, risk in enumerate(risks, 1):
                report += f"  {i}. {risk}\n"
        else:
            report += "  当前未发现显著风险信号。\n"

        report += f"\n五、行动建议：{advice}"

        return report

    def _rule_based_qa(self, r: dict[str, Any], question: str) -> str:
        """关键词匹配回答，覆盖常见问题。"""
        lifecycle = r.get("lifecycle", {})
        stats = r.get("article_stats") or {}

        q_lower = question.lower()

        # 阶段类
        if any(w in q_lower for w in ["阶段", "什么期", "哪个阶段", "状态"]):
            stage = lifecycle.get("current_stage", "未知")
            probs = lifecycle.get("stage_probabilities", {})
            probs_str = "，".join(f"{k} {v:.0%}" for k, v in probs.items())
            return f"当前事件处于「{stage}」。阶段概率：{probs_str}。"

        # 趋势类
        if any(w in q_lower for w in ["趋势", "走向", "会怎样", "发展"]):
            trend = lifecycle.get("trend_direction", "未知")
            slope = lifecycle.get("trend_slope", 0)
            return f"当前趋势为「{trend}」（斜率{slope:+.2f}）。"

        # 热度类
        if any(w in q_lower for w in ["热度", "热", "指数"]):
            return f"当前综合热度指数 {lifecycle.get('current_heat_index', 0):.0f}/100。"

        # 风险类
        if any(w in q_lower for w in ["风险", "危险", "严重", "预警"]):
            cew = lifecycle.get("critical_early_warning", {})
            level = cew.get("warning_level", "none")
            msg = cew.get("message", "")
            level_cn = {"red": "🔴 高危", "orange": "🟠 关注", "yellow": "🟡 注意", "none": "🟢 正常"}
            return f"预警等级：{level_cn.get(level, level)}。{msg}"

        # 虚假类
        if any(w in q_lower for w in ["虚假", "假", "谣", "辟谣"]):
            fake_ratio = stats.get("fake_ratio", 0)
            fake_count = stats.get("fake", 0)
            total = stats.get("total", 0)
            if fake_ratio > 0.1:
                return f"当前事件虚假信息占比较高，{total}篇文章中 {fake_count} 篇疑似虚假（{fake_ratio:.1%}），建议关注并及时辟谣。"
            else:
                return f"当前虚假信息占比 {fake_ratio:.1%}（{fake_count}/{total}），风险较低。"

        # 情感类
        if any(w in q_lower for w in ["情感", "情绪", "正面", "负面", "态度"]):
            sd = r.get("sentiment_distribution", {})
            return (f"正面{sd.get('positive', 0):.1%}，负面{sd.get('negative', 0):.1%}，"
                    f"中性{sd.get('neutral', 0):.1%}。")

        # 预测类
        if any(w in q_lower for w in ["预测", "未来", "接下", "明天"]):
            forecast = lifecycle.get("forecast", [])
            if forecast:
                next_6 = forecast[:6]
                lines = [f"未来{p['hours_from_now']}h：预计 {p['predicted_count']:.0f} 篇"
                         for p in next_6]
                return "未来趋势预测：\n" + "\n".join(lines)
            return "暂无足够的预测数据。"

        # 传播类
        if any(w in q_lower for w in ["传播", "转发", "扩散"]):
            prop = r.get("propagation")
            if prop and "error" not in str(prop):
                return (f"传播深度 {prop.get('propagation_depth', 0)} 层，"
                        f"估计触达 {prop.get('total_reach', {}).get('estimated_unique_reach', 0):,} 人次。")
            return "暂无传播链数据。"

        # 兜底
        return (
            f"关于「{question}」，当前数据中未找到直接相关信息。"
            f"建议查看事件详情页的趋势图和情感分布获取更多信息。"
        )


# ====== 自测 ======
if __name__ == "__main__":
    from time_series.pipeline import Pipeline
    from time_series.utils.mock_data import generate_mock_events, generate_mock_propagation_data

    print("=" * 60)
    print("智能报告生成 — 自测")
    print("=" * 60)

    pipe = Pipeline()
    events = generate_mock_events(num_events=1)
    event_data = events[0]
    prop_nodes = generate_mock_propagation_data()

    articles = [
        {"article_id": "1", "title": "官方通报", "text": "卫健委通报今日新增3例...",
         "source": "央视新闻", "publish_time": "2026-07-06 10:00",
         "sentiment_intensity": 0.2, "hours_since_event": 8.0},
        {"article_id": "2", "title": "网友爆料", "text": "听说隔壁小区被封了...",
         "source": "微博", "publish_time": "2026-07-06 14:00",
         "sentiment_intensity": 0.5, "hours_since_event": 2.0},
        {"article_id": "3", "title": "可疑消息", "text": "震惊！绝密内幕！紧急扩散！",
         "source": "未知", "publish_time": "2026-07-06 15:00",
         "sentiment_intensity": 0.95, "hours_since_event": 0.5},
    ]

    event_report = pipe.event_report(event_data, articles, prop_nodes)

    # ---- 规则兜底模式 ----
    gen = ReportGenerator()
    print("\n[规则兜底模式] 无 LLM API Key\n")

    narrative = gen.generate_narrative(event_report)
    print("--- 分析报告 ---")
    print(narrative)

    print("\n--- 问答测试 ---")
    questions = [
        "这个事件现在处于什么阶段？",
        "热度有多高？",
        "有没有虚假信息？",
        "事件走向趋势如何？",
        "公众情绪怎么样？",
        "需要辟谣吗？",
    ]
    for q in questions:
        a = gen.answer_question(event_report, q)
        print(f"\n问：{q}")
        print(f"答：{a}")

    # ---- LLM 模式提示 ----
    print("\n" + "=" * 60)
    print("[LLM 模式] 接入方式提示：")
    print("  OpenAI:")
    print('    gen = ReportGenerator(api_key="sk-xxx")')
    print("  国内模型（智谱/DeepSeek/通义等）：")
    print('    gen = ReportGenerator(api_key="your_key", base_url="https://open.bigmodel.cn/api/paas/v4/", model="glm-4-flash")')
    print("  DeepSeek:")
    print('    gen = ReportGenerator(api_key="your_key", base_url="https://api.deepseek.com/v1", model="deepseek-chat")')
    print("=" * 60)
