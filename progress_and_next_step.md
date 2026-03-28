# Project Evolution-Reproduce: 上下文交接文档

**最后更新:** 2026-03-28 02:30 (UTC+8)  
**当前阶段:** Phase 2 Step 2 完成 → 准备 Phase A (Training Set 扩展)  
**文档目的:** 为下一个 Agent 提供系统架构、文件位置和下一步任务，无需重新探索即可立即工作。

---

## 一、项目进度总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0: 文献调研 & Benchmark | ✅ 完成 | 15篇论文分3个Tier |
| Phase 1: 基线框架 + Tier 1 V2 测试 | ✅ 完成 | 3/5 成功 (pyeit, pat, insar) |
| Phase 2 Step 1: V3 基线 (_full.md) | ✅ 完成 | 3/5 成功 (60%)，详见 `STAGE_REPORT_V3.md` |
| Phase 2 Step 2: V4 经验增强 | ✅ 完成 | 4/5 成功 (80%)，但归因不清，详见 `STAGE_REPORT_V4.md` |
| **Phase A: Training Set 扩展** | 🔴 **下一步** | 跑 5 篇新 Training 论文 baseline |
| Phase B: Test Set 严格评估 | ❌ 未开始 | 5 篇 Test 论文的对照实验 |

### 关键发现 (V4 修订)

| 论文 | V2 | V3 | V4 | 说明 |
|------|----|----|----|----|
| pyeit | ✅ | ✅ | — | 稳定成功 |
| pat | ✅ | ✅ | — | 稳定成功 |
| insar | ✅ | ✅ | — | 稳定成功 |
| bpm | ❌ | ❌ | ❌ (改善) | 经验被采纳但不足以解决核心问题 |
| diff | ❌ | ❌ | ✅ 🎉 | 成功但归因不清 (API修复 vs 经验) |

> ⚠️ **V4 的 60%→80% 提升无法归因于经验注入**，因为同时改了 API 端点、max_iterations、prompt 规则。需要严格对照实验。

---

## 二、Train/Test 数据划分

### Training Set (10 篇) — 用于经验提取

| 论文 | Tier | 领域 | 已有数据 | 状态 |
|------|------|------|---------|------|
| pyeit | 1 | biomedical_imaging | V2✅ V3✅ | 有轨迹 |
| pat | 1 | biomedical_imaging | V2✅ V3✅ | 有轨迹 |
| insar | 1 | remote_sensing | V2✅ V3✅ | 有轨迹 |
| bpm | 1 | computational_optics | V2❌ V3❌ V4❌ | 有轨迹 |
| diff | 1 | computational_optics | V2❌ V3❌ V4✅ | 有轨迹 |
| oopao | 2 | adaptive_optics | — | **需要跑** |
| lenstronomy | 2 | astrophysics | — | **需要跑** |
| pnp_cassi | 2 | computational_imaging | — | **需要跑** |
| dpi | 3 | scientific_computing | — | **需要跑** |
| ptyrad | 3 | computational_imaging | — | **需要跑** |

### Test Set (5 篇) — 用于验证经验效果

| 论文 | Tier | 领域 | 状态 |
|------|------|------|------|
| fpm_inr | 2 | computational_imaging | 未跑 |
| lensless | 2 | computational_imaging | 未跑 |
| lfm | 2 | computational_imaging | 未跑 |
| sparse_sim | 3 | computational_imaging | 未跑 |
| flfm | 3 | computational_imaging | 未跑 |

---

## 三、项目目录结构

```
Evolution_reproduce/
├── code/
│   ├── agent/planner.py              # 经验增强规划器
│   ├── baseline/run_baseline.py      # B2 基线框架（核心入口）
│   ├── evaluation/                   # evaluate_run.py, llm_judge.py, mas_calculator.py
│   ├── experience_db/                # experience_db.py, trajectory_parser.py
│   └── utils/                        # sandbox_cleanup.sh, sandbox_manager.py, ...
├── data/
│   ├── agent_prompts_v2/             # V2 Tier 1 prompts
│   ├── agent_prompts_v4/             # V4 经验增强 prompts (bpm, diff)
│   ├── paper_markdowns_v2/           # 15篇论文 Markdown (*_full.md + *_task.md)
│   ├── ReproduceBench/               # paper_registry_v2.json + pdfs/
│   ├── reproduction_results_v2/      # V2 结果 (Tier 1, _task.md)
│   ├── reproduction_results_v3/      # V3 结果 (Tier 1, _full.md)
│   ├── reproduction_results_v4/      # V4 结果 (bpm, diff 经验增强)
│   ├── v3_outputs/                   # V3 工作空间副本
│   ├── v4_outputs/                   # V4 工作空间副本
│   └── experience_db/                # vectors.json + experience_meta.db
├── scripts/
│   ├── run_v3_tier1.sh               # V3 批量启动
│   ├── run_v4_tier1.py               # V4 经验增强启动器
│   └── extract_v3_experiences.py     # V3 经验提取
├── logs/
├── STAGE_REPORT_V3.md
├── STAGE_REPORT_V4.md                # ← 修订版，含诚实归因分析
├── progress_and_next_step.md         # 本文档
└── config_llm.yaml                   # LLM API 配置参考
```

**外部路径：**
- OpenHands: `/home/yjh/OpenHands/`
- OpenHands 配置: `/home/yjh/OpenHands/config.toml`
- 工作空间: `/home/yjh/openhands_workspace_v{3,4}/`
- 轨迹: `/data/yjh/openhands_results_v2/trajectories/`

---

## 四、关键配置

### LLM (已验证可用)
```yaml
# 推荐 (稳定)
model: "global.anthropic.claude-opus-4-6-v1"
base_url: "https://ai-gateway-internal.dp.tech/v1"
api_key: "sk-Zj3a7RQDVCXr-Axg-0gtkg"

# 备选
model: "zhangli/claude-4.6-opus"

# ⚠️ 不推荐 (频繁宕机)
model: "cds/Claude-4.6-opus"
```

### OpenHands
- Runtime: `local`（非 Docker）
- Config: `/home/yjh/OpenHands/config.toml`
- Python: `/home/yjh/local_openhands_env/bin/python3`
- max_iterations: 100
- 轨迹保存: `/data/yjh/openhands_results_v2/trajectories/`

---

## 五、下一步详细计划

### 🔴 Phase A: Training Set 扩展 (立即开始)

**目标:** 对 5 篇新 Training 论文运行 baseline，收集轨迹用于经验提取。

**步骤:**
```bash
# 1. 清理沙箱
bash code/utils/sandbox_cleanup.sh

# 2. 逐篇运行 (每篇约 1h)
for paper in oopao lenstronomy pnp_cassi dpi ptyrad; do
  bash code/utils/sandbox_cleanup.sh
  python code/baseline/run_baseline.py \
    --markdown data/paper_markdowns_v2/${paper}_full.md \
    --paper-id ${paper} \
    --max-iterations 100
done

# 3. 收集结果
ls data/reproduction_results_v3/  # 或新建 v5 目录
```

**注意事项:**
- 使用 `global.anthropic.claude-opus-4-6-v1` 模型
- 每篇之间清理沙箱
- 结果保存到 `data/reproduction_results_v3/` (与 Tier 1 一起)
- 轨迹自动保存到 `/data/yjh/openhands_results_v2/trajectories/`

### 🟡 Phase A2: 经验提取 (A1 完成后)

**目标:** 从全部 10 篇 Training 轨迹中提取高质量结构化经验。

**改进点:**
1. 使用新的 4 元组 schema (condition + diagnosis + action + verification)
2. 添加算法标签 (tags) 用于精确匹配
3. 区分 algorithm/implementation/debugging 三个层级
4. 记录 adoption_rate 和 effectiveness

### 🟢 Phase B: Test Set 严格评估 (A 完成后)

**目标:** 在 5 篇从未见过的论文上验证经验的因果效应。

**关键:** B1 (无经验) 和 B2 (有经验) 使用完全相同的配置，唯一区别是经验注入。

---

## 六、常用命令速查

```bash
# 沙箱清理 (每次启动前必做)
bash code/utils/sandbox_cleanup.sh

# 单篇运行
python code/baseline/run_baseline.py \
  --markdown data/paper_markdowns_v2/oopao_full.md \
  --paper-id oopao --max-iterations 100

# V4 经验增强运行
python scripts/run_v4_tier1.py --failed-only --dry-run  # 先预览
python scripts/run_v4_tier1.py --failed-only             # 实际运行

# 查看结果
for p in pyeit pat insar bpm diff; do
  f="data/reproduction_results_v3/${p}_result.json"
  [ -f "$f" ] && echo "$p: $(python3 -c "import json; d=json.load(open('$f')); print(d.get('agent_state','?'))")" || echo "$p: 无结果"
done

# 测试 API
curl -s --max-time 30 https://ai-gateway-internal.dp.tech/v1/chat/completions \
  -H "Authorization: Bearer sk-Zj3a7RQDVCXr-Axg-0gtkg" \
  -H "Content-Type: application/json" \
  -d '{"model":"global.anthropic.claude-opus-4-6-v1","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'
```

### ⚠️ 注意事项
1. **不要同时运行多个 OpenHands 任务**（端口冲突）
2. **每次启动前先运行沙箱清理**
3. **使用 `global.anthropic.claude-opus-4-6-v1`**，不要用 `cds/Claude-4.6-opus`
4. **V4 报告已修订** — 经验效果需要严格对照实验验证
