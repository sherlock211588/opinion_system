"""
Full pipeline with 3.data: news_output.json + event_timeseries_result.json
"""
import sys, json, collections
sys.path.insert(0, '.')
from time_series.pipeline import Pipeline
from time_series.cross_event import CrossEventAnalyzer
from time_series.fake_detection import get_or_train_model, FakeDetector

out = open('full_result_3data.txt', 'w', encoding='utf-8')

def p(text=''):
    out.write(text + '\n')
    try:
        print(text)
    except:
        pass

# Load
with open('../3.data/event_timeseries_result.json', 'r', encoding='utf-8') as f:
    events_list = json.load(f)
events = {e['event_id']: e for e in events_list}

with open('../3.data/news_output.json', 'r', encoding='utf-8') as f:
    articles_all = json.load(f)

articles_valid = [a for a in articles_all if a['event_id'] != 'EVT_NOISE']
arts_by_event = collections.defaultdict(list)
for a in articles_valid:
    arts_by_event[a['event_id']].append(a)

p('=' * 70)
p('  FULL PIPELINE with 3.data')
p('  ' + str(len(events)) + ' events, ' + str(len(articles_valid)) + ' articles')
p('=' * 70)

# ================================================================
# MODULE 1
# ================================================================
p()
p('=' * 70)
p('  MODULE 1: Lifecycle Detection')
p('=' * 70)

pipe = Pipeline(data_interval_hours=6)
alerts = collections.Counter()
stage_counts = collections.Counter()
grade_counts = collections.Counter()
lifecycle_results = []

for eid, edata in events.items():
    try:
        r = pipe.lifecycle.detect(edata)
    except Exception:
        continue
    dq = r['data_quality']
    stage = r['current_stage']
    heat = r['current_heat_index']
    trend = r['trend_direction']
    warning = r['critical_early_warning']['warning_level']
    alerts[warning] = alerts.get(warning, 0) + 1
    stage_counts[stage] = stage_counts.get(stage, 0) + 1
    grade = dq['grade']
    grade_counts[grade] = grade_counts.get(grade, 0) + 1
    n_pred = len(r.get('predicted_next_24h', []))
    has_resurgence = r['resurgence']['is_resurgence']
    lifecycle_results.append({
        'eid': eid, 'stage': stage, 'heat': heat, 'trend': trend,
        'warning': warning, 'eff': dq['effective_nonzero_points'],
        'grade': grade, 'pred': n_pred, 'resurgence': has_resurgence,
        'news': edata.get('news_count', 0),
        'title': edata.get('event_title', '')[:50],
        'cat': edata.get('category', '')[:8]
    })

lifecycle_results.sort(key=lambda x: x['heat'], reverse=True)

p('Stage Distribution:')
for s, c in stage_counts.most_common():
    p('  ' + s + ': ' + str(c) + ' (' + str(round(c/114*100, 1)) + '%)')

p('Warning: RED=' + str(alerts.get('red',0)) + ' ORANGE=' + str(alerts.get('orange',0)) +
  ' YELLOW=' + str(alerts.get('yellow',0)) + ' NONE=' + str(alerts.get('none',0)))

p('Grades:')
for g in ['full', 'basic', 'minimal', 'sparse']:
    if grade_counts.get(g):
        p('  ' + g + ': ' + str(grade_counts[g]))

p('')
p('Top 15 Events:')
hdr = '{:<14} {:<10} {:<8} {:>5} {:<5} {:<7} {:>5} {:>5}  {}'
p(hdr.format('EventID', 'Cat', 'Stage', 'Heat', 'Trend', 'Warn', 'Eff', 'News', 'Title'))
for r in lifecycle_results[:15]:
    rm = ' *R' if r['resurgence'] else ''
    p(hdr.format(r['eid'], r['cat'], r['stage'] + rm, int(r['heat']), r['trend'],
                 r['warning'], r['eff'], r['news'], r['title'][:40]))

p('')
full_events = [r for r in lifecycle_results if r['grade'] == 'full']
p('Full-grade events (' + str(len(full_events)) + ' with predictions):')
for fe in full_events[:5]:
    p('  ' + fe['eid'] + ' [' + fe['cat'] + '] ' + fe['stage'] +
      ' heat=' + str(int(fe['heat'])) + ' trend=' + fe['trend'] +
      ' pred=' + str(fe['pred']) + 'steps resurgence=' + str(fe['resurgence']))

# ================================================================
# MODULE 2: Propagation Tracing (2 selected events only)
# ================================================================
p()
p('=' * 70)
p('  MODULE 2: Propagation Tracing')
p('=' * 70)

prop_path = '../1.data/backend_propagation_nodes.json'
prop_data_available = __import__('os').path.exists(prop_path)

# Define the 2 demo events and their seed keywords
prop_events_config = {
    "EVT_000088": {
        "name": "广西洪涝灾害",
        "keywords": ["暴雨", "洪水", "洪涝", "灾害", "救援", "消防", "救火", "水灾",
                     "淹", "台风", "气象", "塌陷", "塌方", "泥石流", "山体滑坡",
                     "自然灾害", "下沉", "灾害应对", "消防员", "救灾"],
        "description": "B站用户对各地暴雨、洪水、消防救援等自然灾害事件的讨论",
    },
    "EVT_000058": {
        "name": "中联油致癌物事件",
        "keywords": ["食品", "食安", "致癌", "毒性", "有毒", "安全", "超标",
                     "抽检", "监检", "油品", "添加剂", "蔬菜", "农药",
                     "食品安全", "卫生", "中毒", "315", "假冒", "消费"],
        "description": "B站用户对食品安全问题的科普与讨论",
    },
}

if prop_data_available:
    with open(prop_path, 'r', encoding='utf-8') as f:
        raw_nodes = json.load(f)

    from time_series.propagation import PropagationTracer
    tracer = PropagationTracer()
    all_prop_results = {}

    total_matched = 0
    for target_eid, config in prop_events_config.items():
        keywords = config["keywords"]

        # Filter videos whose title/text matches this event's keywords
        # Only video-type nodes can be roots; comments inherit titles
        matched_video_ids = set()
        for rn in raw_nodes:
            if rn.get("node_type", "") != "video":
                continue
            t = (rn.get("title", "") + rn.get("text", ""))
            if any(kw in t for kw in keywords):
                matched_video_ids.add(rn.get("node_id", rn.get("id", "")))

        # Collect all nodes that belong to matched video trees
        # (the video itself + all its child comments)
        event_nodes = []
        seen_ids = set()
        for rn in raw_nodes:
            nid = rn.get("node_id", rn.get("id", ""))
            pid = rn.get("parent_node_id")
            # Include if: it IS a matched video, OR its parent is in the matched set
            if nid in matched_video_ids or pid in matched_video_ids or pid in seen_ids:
                event_nodes.append(rn)
                seen_ids.add(nid)

        if not event_nodes:
            p('  ' + target_eid + ' (' + config["name"] + '): 0 nodes matched')
            continue

        # Convert to PropagationTracer format
        prop_nodes = []
        for rn in event_nodes:
            nid = rn.get("node_id", rn.get("id", ""))
            # Count immediate children for forward_count
            children = sum(1 for x in event_nodes
                          if x.get("parent_node_id") == nid)
            prop_nodes.append({
                "node_id":        nid,
                "account_name":   rn.get("account_name", rn.get("user_name", "")),
                "follower_count": rn.get("follower_count", 0),
                "is_verified":    rn.get("is_verified", False),
                "post_time":      rn.get("post_time", rn.get("time", "")),
                "source":         rn.get("source", ""),
                "parent_node_id": rn.get("parent_node_id"),
                "forward_count":  rn.get("forward_count",
                                   rn.get("comment_count", children)),
                "title":          rn.get("title", ""),
            })

        try:
            pr = tracer.analyze(prop_nodes)
        except Exception as e:
            p('  ' + target_eid + ': ERROR - ' + str(e))
            continue

        nv = len(matched_video_ids)
        nc = len(event_nodes) - nv
        depth = pr.get('propagation_depth', 0)
        n_key = len(pr.get('key_nodes', []))
        gs = pr.get('propagation_graph', {})

        p('')
        p('  ' + target_eid + ' (' + config["name"] + '):')
        p('    Nodes: ' + str(len(event_nodes)) + ' (videos=' + str(nv) +
          ', comments=' + str(nc) + ') | Depth=' + str(depth) +
          ' | Key: ' + str(n_key))
        p('    Graph: ' + str(gs.get('node_count', 0)) + ' nodes, ' +
          str(gs.get('edge_count', 0)) + ' edges, DAG=' + str(gs.get('is_dag', False)))
        p('    Description: ' + config["description"])

        if pr.get('key_nodes'):
            p('    Top discussion nodes:')
            for kn in pr['key_nodes'][:5]:
                gs2 = kn.get('graph_scores', {})
                p('      [' + str(kn.get('role', '?')) + '] ' +
                  str(kn.get('account_name', '')) +
                  ' | composite=' + str(round(gs2.get('composite', 0), 3)))

        cf = pr.get('counterfactual_analysis', {})
        if cf.get('results'):
            p('    Key information hubs (structural impact):')
            for cr in cf['results'][:3]:
                ci = cr.get('causal_impact', {})
                p('      ' + str(cr.get('account_name', '')) +
                  ' | reach_loss=' + str(ci.get('nodes_lost_if_removed', 0)) +
                  ' nodes')

        nv_nodes = len(pr.get('graph_for_visualization', {}).get('nodes', []))
        nv_links = len(pr.get('graph_for_visualization', {}).get('links', []))
        p('    Visualization: ' + str(nv_nodes) + ' nodes, ' +
          str(nv_links) + ' links (force-directed graph)')

        all_prop_results[target_eid] = pr
        total_matched += len(event_nodes)

    p('')
    p('  Coverage: ' + str(len(all_prop_results)) + '/' +
      str(len(events)) + ' events with propagation data (' +
      str(total_matched) + ' nodes matched)')
    p('  Other events: propagation analysis not available')

    n_nodes, depth, n_key, prop_result = total_matched, 2, 0, {}
else:
    p('  [SKIP] 1.data/backend_propagation_nodes.json not found')
    n_nodes, depth, n_key, all_prop_results = 0, 0, 0, {}

# ================================================================
# MODULE 3
# ================================================================
p()
p('=' * 70)
p('  MODULE 3: Fake Detection (3.data news_output.json)')
p('=' * 70)

model, report = get_or_train_model()
detector = FakeDetector(model=model)
p('Model CV accuracy: combined=' + str(round(report.get('cv_mean_accuracy', 0) * 100, 1)) +
  '%  text_only=' + str(round(report.get('text_only_cv_accuracy', 0) * 100, 1)) + '%')

verdicts = collections.Counter()
sent_cross = collections.defaultdict(collections.Counter)
cat_cross = collections.defaultdict(collections.Counter)
downgraded = 0
event_fake_stats = collections.defaultdict(lambda: {'total': 0, 'fake': 0, 'real': 0, 'uncertain': 0})
samples = []

for a in articles_valid:
    text = a.get('text', '')
    if not text or len(text) < 10:
        continue
    sent_str = a.get('sentiment', 'neutral')
    si = 0.3 if sent_str == 'positive' else (0.7 if sent_str == 'negative' else 0.5)
    meta = {
        'source_verified': False,
        'source_followers': 0,
        'similar_report_count': 0,
        'hours_since_event_start': 24.0,
        'sentiment_intensity': si,
    }
    r = detector.evaluate(text, meta)
    v = r['verdict']
    verdicts[v] = verdicts.get(v, 0) + 1
    if r.get('downgrade_reason'):
        downgraded += 1
    eid = a['event_id']
    cat = events.get(eid, {}).get('category', 'unknown')
    sent_cross[sent_str][v] = sent_cross[sent_str].get(v, 0) + 1
    cat_cross[cat][v] = cat_cross[cat].get(v, 0) + 1
    event_fake_stats[eid]['total'] += 1
    if v == '疑似虚假':
        event_fake_stats[eid]['fake'] += 1
    elif v == '可信':
        event_fake_stats[eid]['real'] += 1
    else:
        event_fake_stats[eid]['uncertain'] += 1
    if len(samples) < 8:
        samples.append({'v': v, 'dg': r.get('downgrade_reason', ''), 'prob': r['confidence_score'],
                        'sent': sent_str, 'text': text[:60]})

total = sum(verdicts.values())
p('')
p('Verdicts (' + str(total) + ' articles):')
for v in ['可信', '待验证', '疑似虚假']:
    c = verdicts.get(v, 0)
    bar = '#' * (c * 50 // max(total, 1))
    p('  ' + v + ': ' + str(c) + ' (' + str(round(c/total*100, 1)) + '%) ' + bar)
p('Downgraded (short text no metadata): ' + str(downgraded))

p('')
p('Sentiment vs Verdict:')
p('  {:<10} {:>6} {:>10} {:>8}'.format('Sent', 'Real', 'Uncertain', 'Fake'))
for sl in ['positive', 'negative', 'neutral']:
    p('  {:<10} {:>6} {:>10} {:>8}'.format(sl,
        sent_cross[sl].get('可信', 0), sent_cross[sl].get('待验证', 0),
        sent_cross[sl].get('疑似虚假', 0)))

p('')
p('Category vs Verdict:')
cat_sorted = sorted(cat_cross.items(), key=lambda x: sum(x[1].values()), reverse=True)
p('  {:<15} {:>6} {:>10} {:>8} {:>8}'.format('Category', 'Real', 'Uncertain', 'Fake', 'Total'))
for cat, vd in cat_sorted[:10]:
    tot_cat = sum(vd.values())
    p('  {:<15} {:>6} {:>10} {:>8} {:>8}'.format(cat[:15],
        vd.get('可信', 0), vd.get('待验证', 0), vd.get('疑似虚假', 0), tot_cat))

p('')
p('Events with highest fake ratio:')
fake_sorted = sorted(event_fake_stats.items(),
                     key=lambda x: x[1]['fake']/max(x[1]['total'], 1), reverse=True)
p('  {:<14} {:>5} {:>5} {:>5} {:>5} {:>6}  {}'.format('Event', 'Tot', 'Real', 'Unc', 'Fake', 'Fake%', 'Title'))
for eid, st in fake_sorted[:10]:
    tot_e = st['total']
    fr = st['fake']/max(tot_e, 1)*100
    etitle = events.get(eid, {}).get('event_title', eid)[:40]
    p('  {:<14} {:>5} {:>5} {:>5} {:>5} {:>5.0f}%  {}'.format(
        eid, tot_e, st['real'], st['uncertain'], st['fake'], fr, etitle))

p('')
p('Sample verdicts:')
for s in samples:
    dg = ' [DG]' if s['dg'] else ''
    p('  [' + s['v'] + ']' + dg + ' conf=' + str(int(s['prob'])) +
      '% sent=' + s['sent'] + ' | ' + s['text'][:55])

# ================================================================
# MODULE 4
# ================================================================
p()
p('=' * 70)
p('  MODULE 4: Cross-Event Causality')
p('=' * 70)

events_qualified = {}
for eid, edata in events.items():
    ts = edata.get('timeseries', [])
    nonzero_days = len(set(r['time'][:10] for r in ts if r.get('news_count', 0) > 0)) if ts else 0
    if nonzero_days >= 3 and edata.get('news_count', 0) >= 5:
        events_qualified[eid] = ts

p('Qualified: ' + str(len(events_qualified)) + '/114')
analyzer = CrossEventAnalyzer(max_lag=4, significance_level=0.05)
result = analyzer.analyze(events_qualified)

# TE 作为主输出（不受零值填充影响，非线性因果更全面）
te_total = len(result.get('transfer_entropy_pairs', []))
te_sig = result.get('significant_te_pairs', 0)
granger_total = result['total_pairs_tested']
granger_sig = result['significant_pairs']

p('')
p('  Primary: Symbolic Transfer Entropy (nonlinear, robust to sparse data)')
p('    Total pairs: ' + str(te_total) + ' | Significant: ' + str(te_sig) +
  ' (' + str(round(te_sig/max(te_total,1)*100, 1)) + '%)')

sig_te = [tp for tp in result.get('transfer_entropy_pairs', []) if tp['is_significant']][:10]
if sig_te:
    p('    Top causal pairs:')
    for tp in sig_te:
        p('      ' + tp['from_title'][:30] + ' -> ' + tp['to_title'][:30])
        p('        TE=' + str(round(tp['te_effective'], 4)) +
          '  p=' + str(round(tp['p_value'], 4)) +
          (' ***' if tp['is_significant'] else ''))

p('')
p('  Secondary: Granger Causality (linear, sensitive to zero-padding)')
p('    Total pairs: ' + str(granger_total) + ' | Significant: ' + str(granger_sig) +
  ' (' + str(round(granger_sig/max(granger_total,1)*100, 1)) + '%)')

sig_g = [gp for gp in result['pairs'] if gp['is_significant']][:5]
if sig_g:
    p('    Top Granger pairs:')
    for gp in sig_g:
        p('      ' + gp['from_title'][:30] + ' -> ' + gp['to_title'][:30])
        p('        lag=' + str(gp['best_lag_hours']) + 'steps(' +
          str(gp['best_lag_hours']*6) + 'h) p=' + str(round(gp['p_value'], 6)))

# ================================================================
# SUMMARY
# ================================================================
p()
p('=' * 70)
p('  SUMMARY')
p('=' * 70)
fe_count = len([r for r in lifecycle_results if r['grade'] == 'full'])
ba_count = len([r for r in lifecycle_results if r['grade'] == 'basic'])
p('Module 1: ' + str(len(lifecycle_results)) + ' events, ' + str(fe_count) +
  ' full-grade, ' + str(ba_count) + ' basic')
prop_event_count = len(all_prop_results) if 'all_prop_results' in dir() else 0
p('Module 2: ' + str(prop_event_count) + ' events with propagation (' +
  str(n_nodes) + ' matched nodes total)')
p('Module 3: ' + str(total) + ' articles checked, ' +
  str(round(verdicts.get('疑似虚假', 0)/max(total, 1)*100, 1)) + '% fake')
p('Module 4: ' + str(result['significant_pairs']) + ' Granger + ' +
  str(result.get('significant_te_pairs', 0)) + ' TE significant')

p()
p('ALL DONE')
out.close()
print('Done - see full_result_3data.txt')
