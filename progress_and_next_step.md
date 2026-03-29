# Project Evolution-Reproduce: 上下文交接文档

**最后更新:** 2026-03-29 07:00 (UTC+8)  
**当前阶段:** Phase B 完成 + MAS/Judge 评估完成  
**下一步:** 多次重复实验 + 论文撰写

---

## 一、项目进度总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0: 文献调研 | ✅ | 15篇论文, 3个Tier |
| Phase 1: 基线框架 | ✅ | OpenHands + run_baseline.py |
| Phase 2: V3/V4 Tier 1 | ✅ | 4/5 成功 (80%), diff 首次成功 |
| Phase A: Training Set | ✅ | 8/10 成功 (80%), 含 Tier 2/3 |
| Phase B: Test B1/B2 | ✅ | **B1: 4/5 (80%), B2: 5/5 (100%)** |
| MAS 评估 | ✅ | B1 MAS=0.598, B2 MAS=0.875 (+46%) |
| LLM Judge 评估 | ✅ | B1=2.58/5, B2=2.74/5 (+6%) |
| 多次重复实验 | 🔴 下一步 | 评估随机性 |

### 关键结果

| 集合 | 成功率 | 说明 |
|------|--------|------|
| Training Tier 1 | 4/5 (80%) | bpm 失败 |
| Training Tier 2/3 | 4/5 (80%) | dpi 超时 |
| **Test B1 (无经验)** | **4/5 (80%)** | lensless ERROR |
| **Test B2 (有经验)** | **5/5 (100%)** | 全部 FINISHED |
| **全项目** | **13/15 (87%)** | |

---

## 二、关键配置

```toml
# /home/yjh/OpenHands/config.toml
[llm]
model = "openai/global.anthropic.claude-opus-4-6-v1"
api_key = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
base_url = "https://ai-gateway-internal.dp.tech/v1"
native_tool_calling = true  # 关键修复!
log_completions = true

[core]
max_iterations = 100

[sandbox]
timeout = 3600
```

---

## 三、文件位置

```
data/reproduction_results_v5/
├── test_b1/          # Test Set B1 (无经验) 结果
├── test_b2/          # Test Set B2 (有经验) 结果
├── training/         # Training Set 结果 (部分)
├── oopao_result.json # Training Tier 2/3 结果
├── lenstronomy_result.json
├── pnp_cassi_result.json
├── dpi_result.json
├── ptyrad_result.json
└── workspaces/       # 工作空间副本

scripts/
├── run_training_baseline.py  # Training Set 运行器
├── run_test_baseline.py      # Test B1 运行器
├── run_test_experience.py    # Test B2 运行器 (经验增强)
└── extract_v3_experiences.py # 经验提取

logs/llm_completions/         # LLM 调用日志 (每次调用一个JSON)
```

---

## 四、下一步

1. **多次重复实验** — B1/B2 各跑 2-3 次，评估随机性
2. **经验匹配策略改进** — 当前相似度偏低 (0.50-0.57)
3. **论文撰写**
