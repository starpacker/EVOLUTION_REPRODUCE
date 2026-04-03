# Project Evolution-Reproduce: 上下文交接文档

**最后更新:** 2026-03-29 07:00 (UTC+8)  
**当前阶段:** Phase B 完成 + MAS/Judge 评估完成  
**下一步:** 多次重复实验 
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

## 四、运行命令

### 4.1 前置准备

每次运行前 **必须** 清理沙箱环境：

```bash
cd /home/yjh/Evolution_reproduce

# 清理残留进程
bash code/utils/sandbox_cleanup.sh
pkill -f jupyter-kernelgateway 2>/dev/null
pkill -f action_execution_server 2>/dev/null
tmux kill-server 2>/dev/null

# 确认 OpenHands config 正确
cat /home/yjh/OpenHands/config.toml
```

### 4.2 Phase B1: Test Set Baseline（无经验注入 — 对照组）

```bash
cd /home/yjh/Evolution_reproduce

# 运行全部 5 篇 Test 论文（顺序执行，每篇最多 90 分钟）
python scripts/run_test_baseline.py

# 运行单篇论文
python scripts/run_test_baseline.py --paper fpm_inr
python scripts/run_test_baseline.py --paper lensless
python scripts/run_test_baseline.py --paper lfm
python scripts/run_test_baseline.py --paper sparse_sim
python scripts/run_test_baseline.py --paper flfm

# 仅检查配置，不实际运行
python scripts/run_test_baseline.py --dry-run
```

**输出位置:**
- 结果 JSON: `data/reproduction_results_v5/test_b1/{paper_id}_result.json`
- Agent Prompt: `data/agent_prompts_v5/test_b1/{paper_id}_prompt.txt`
- 运行日志: `logs/run_logs/test_b1_{paper_id}_{timestamp}.log`
- 工作空间: `/home/yjh/openhands_workspace_v5/test_b1_{paper_id}_{timestamp}/`

### 4.3 Phase B2: Test Set + Experience（经验增强 — 实验组）

```bash
cd /home/yjh/Evolution_reproduce

# 运行全部 5 篇 Test 论文（带经验注入）
python scripts/run_test_experience.py

# 运行单篇论文
python scripts/run_test_experience.py --paper fpm_inr
python scripts/run_test_experience.py --paper lensless
python scripts/run_test_experience.py --paper lfm
python scripts/run_test_experience.py --paper sparse_sim
python scripts/run_test_experience.py --paper flfm

# 仅检查配置 + 经验匹配预览
python scripts/run_test_experience.py --dry-run
```

**输出位置:**
- 结果 JSON: `data/reproduction_results_v5/test_b2/{paper_id}_result.json`
- Agent Prompt: `data/agent_prompts_v5/test_b2/{paper_id}_prompt.txt`（含经验段落）
- 运行日志: `logs/run_logs/test_b2_{paper_id}_{timestamp}.log`
- 工作空间: `/home/yjh/openhands_workspace_v5/test_b2_{paper_id}_{timestamp}/`

### 4.4 Training Set Baseline

```bash
cd /home/yjh/Evolution_reproduce

# 运行全部新 Training 论文 (Tier 2/3: oopao, lenstronomy, pnp_cassi, dpi, ptyrad)
python scripts/run_training_baseline.py

# 运行单篇
python scripts/run_training_baseline.py --paper oopao

# 查看运行状态
python scripts/run_training_baseline.py --status

# 仅检查配置
python scripts/run_training_baseline.py --dry-run
```

### 4.5 评估命令

```bash
cd /home/yjh/Evolution_reproduce

# MAS (Metric Alignment Score) 评估 — 对比 B1 vs B2
python scripts/run_mas_evaluation.py

# LLM Judge (Code Faithfulness) 评估 — 对比 B1 vs B2
python scripts/run_llm_judge.py
```

---

## 五、复现报告规范（Reproduction Report Specification）

> **核心原则：每一个任务完成后，必须产出一份严格、完整、可验证的复现报告。**

### 5.1 必须产出的文件

每个 paper 的工作空间中 **必须** 包含以下文件：

| 文件 | 说明 | 必须 |
|------|------|------|
| `results.json` | 结构化结果（见 5.2） | ✅ 必须 |
| `reproduction_report.md` | 人类可读的完整报告（见 5.3） | ✅ 必须 |
| `comparison_figure.png` | 视觉对比图（见 5.4） | ✅ 必须 |
| `reproduce.py` / `main.py` | 可独立运行的复现代码 | ✅ 必须 |
| `metrics_log.txt` | 所有中间指标的运行日志 | ⭐ 推荐 |

### 5.2 `results.json` 结构化结果格式

```json
{
  "paper_title": "论文全称",
  "paper_id": "short_id",
  "reproduction_status": "SUCCESS | PARTIAL | FAILED",
  "timestamp": "ISO-8601",

  "quantitative_metrics": {
    "PSNR_dB": {
      "paper_value": 25.3,
      "reproduced_value": 24.8,
      "unit": "dB",
      "direction": "higher",
      "description": "Peak Signal-to-Noise Ratio on test set"
    },
    "SSIM": {
      "paper_value": 0.92,
      "reproduced_value": 0.89,
      "unit": "",
      "direction": "higher",
      "description": "Structural Similarity Index"
    },
    "MSE": {
      "paper_value": 0.0012,
      "reproduced_value": 0.0015,
      "unit": "",
      "direction": "lower",
      "description": "Mean Squared Error"
    },
    "LPIPS": {
      "paper_value": null,
      "reproduced_value": null,
      "unit": "",
      "direction": "lower",
      "description": "Learned Perceptual Image Patch Similarity (if applicable)"
    }
  },

  "domain_specific_metrics": {
    "metric_name": {
      "paper_value": 0.0,
      "reproduced_value": 0.0,
      "unit": "",
      "direction": "higher|lower|target",
      "description": "论文特有的领域指标"
    }
  },

  "computational_metrics": {
    "runtime_seconds": 0.0,
    "peak_memory_MB": 0.0,
    "gpu_used": false,
    "device": "cpu"
  },

  "visual_outputs": {
    "comparison_figure": "comparison_figure.png",
    "additional_figures": []
  },

  "notes": "任何补充说明",
  "files_produced": ["reproduce.py", "results.json", "comparison_figure.png"]
}
```

**必须包含的量化指标（按优先级）：**

| 指标 | 说明 | 何时必须 |
|------|------|----------|
| **PSNR (dB)** | 峰值信噪比 | 所有涉及图像/信号重建的论文 |
| **SSIM** | 结构相似性 | 所有涉及图像/信号重建的论文 |
| **MSE / RMSE** | 均方误差 | 所有论文 |
| **MAE** | 平均绝对误差 | 推荐 |
| **LPIPS** | 感知相似度 | 有深度学习图像生成时 |
| **论文特有指标** | 如 L2 Error, Compression Ratio 等 | 论文中报告的所有指标 |

### 5.3 `reproduction_report.md` 报告模板

```markdown
# Reproduction Report: {Paper Title}

## 1. Paper Information
- **Title:** ...
- **Authors:** ...
- **Key Contribution:** 一句话概括

## 2. Reproduction Summary
- **Status:** SUCCESS / PARTIAL / FAILED
- **Reproduced Experiments:** Table X, Figure Y, ...
- **Environment:** Python 3.x, numpy, scipy, ...

## 3. Quantitative Results Comparison

| Metric | Paper Value | Reproduced Value | Deviation | MAS |
|--------|-------------|-------------------|-----------|-----|
| PSNR (dB) | 25.3 | 24.8 | -2.0% | 0.98 |
| SSIM | 0.92 | 0.89 | -3.3% | 0.97 |
| MSE | 0.0012 | 0.0015 | +25% | 0.80 |

## 4. Visual Comparison
![Comparison](comparison_figure.png)

- **Left:** Input / Measurement
- **Center:** Ground Truth (paper reference or simulated GT)
- **Right:** Reproduced Output

## 5. Implementation Details
- 算法实现的关键步骤
- 与论文的差异（如有）
- 参数设置

## 6. Limitations & Notes
- 与论文结果的差距原因分析
- 简化假设（如有）
```

### 5.4 视觉对比图规范（comparison_figure.png）

**必须** 生成至少一张对比图，包含以下内容：

```
┌──────────────┬──────────────┬──────────────┐
│    Input     │  Ground Truth│  Reproduced  │
│  (测量/输入)  │  (参考/GT)   │  (复现输出)   │
└──────────────┴──────────────┴──────────────┘
```

**具体要求：**

1. **三列对比布局**（或三张独立图片）：
   - **Input**: 原始输入数据 / 测量数据 / 退化图像
   - **Ground Truth (GT)**: 论文中的参考结果，或模拟生成的真值
   - **Reproduced Output**: Agent 复现代码实际产出的结果

2. **图片质量要求：**
   - 分辨率 ≥ 512×512（或与论文一致）
   - 使用 `matplotlib` 的 `savefig(dpi=150)` 或更高
   - 包含 colorbar（如适用）
   - 包含标题标注（Input / GT / Reproduced）
   - 如有多个实验，每个实验一行

3. **指标标注：**
   - 在 Reproduced 图上标注 PSNR/SSIM 值
   - 格式: `PSNR=24.8dB, SSIM=0.89`

4. **参考代码模板：**

```python
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(input_img, cmap='gray')
axes[0].set_title('Input / Measurement')
axes[0].axis('off')

axes[1].imshow(gt_img, cmap='gray')
axes[1].set_title('Ground Truth')
axes[1].axis('off')

axes[2].imshow(recon_img, cmap='gray')
axes[2].set_title(f'Reproduced\nPSNR={psnr:.2f}dB, SSIM={ssim:.4f}')
axes[2].axis('off')

plt.tight_layout()
plt.savefig('comparison_figure.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved comparison_figure.png")
```

---

## 六、框架完整性规范（Framework Integrity Policy）

> **⚠️ 本节面向所有后续修改本项目代码/框架的 Agent 和开发者。**
>
> 本项目的实验结果必须 **solid**——经得起任何审稿人的审查。作弊风险不在 OpenHands
> 里跑的复现 Agent（那个由 prompt RULE 7 约束，且运行在隔离沙箱中），而在于
> **我们自己的框架代码**：评估脚本、结果收集、MAS 计算、报告生成等环节。
> 如果框架本身不干净，Agent 跑得再好也没有意义。

### 6.1 框架层面绝对禁止的行为

| 编号 | 禁止行为 | 涉及文件 | 说明 |
|------|----------|----------|------|
| **F1** | **评估脚本中硬编码 paper_value** 时偷偷调整数值使 MAS 偏高 | `run_mas_evaluation.py`, `mas_calculator.py` | `paper_value` 必须严格来自论文原文，不可为了好看而微调 |
| **F2** | **MAS 计算公式中加入偏置/缩放** | `mas_calculator.py` | `compute_single_mas()` 必须是标准公式，不可加 `+ 0.1` 之类的修正项 |
| **F3** | **结果收集时篡改 reproduced_value** | `evaluate_run.py`, `run_mas_evaluation.py` | 从 workspace 的 `results.json` 读取的值必须原样使用，不可做任何变换 |
| **F4** | **选择性报告** | 所有评估脚本 | 不可只报告成功的 paper 而隐藏失败的；不可只报告高 MAS 的指标而丢弃低的 |
| **F5** | **B1/B2 使用不同配置** | `run_test_baseline.py`, `run_test_experience.py` | B1 和 B2 除了经验注入外，`max_iterations`、`timeout`、`model`、`temperature` 等必须完全一致 |
| **F6** | **经验注入中泄露 Test Set 信息** | `experience_db.py`, `run_test_experience.py` | 经验库中不可包含 Test Set 论文自身的经验；经验只能来自 Training Set |
| **F7** | **Prompt 模板不一致** | `run_test_baseline.py`, `run_test_experience.py` | B1 和 B2 的 `PROMPT_TEMPLATE` 除 `{experience_section}` 占位符外必须逐字相同 |
| **F8** | **LLM Judge 评分时给 B2 更宽松的标准** | `llm_judge.py`, `run_llm_judge.py` | Judge prompt 对 B1 和 B2 必须完全相同，不可包含任何暗示"这个应该更好"的内容 |

### 6.2 修改框架代码时的检查清单

后续 Agent 在修改以下文件时，**必须** 逐条确认：

#### 修改 `mas_calculator.py` 时：
- [ ] `compute_single_mas()` 的三个分支（higher/lower/target）公式是否与 `reproduce_readme.md` §6.1.2 一致？
- [ ] 没有引入任何 clamp/offset/scaling 使得 MAS 系统性偏高？
- [ ] `EPSILON` 仅用于防除零，不影响正常值的计算？

#### 修改 `run_mas_evaluation.py` 时：
- [ ] `PAPER_METRICS` 中每个 `paper_value` 是否有论文原文出处（Table/Figure 编号）？
- [ ] `extract` lambda 是否忠实读取 workspace 中的原始值，没有做任何变换？
- [ ] 所有 paper 和所有 metric 都被包含在报告中，没有选择性遗漏？

#### 修改 `run_test_baseline.py` 或 `run_test_experience.py` 时：
- [ ] 两个文件的 `PROMPT_TEMPLATE` 是否一致（diff 只有 `{experience_section}`）？
- [ ] `MAX_ITERATIONS`、`MAX_WAIT_SECONDS` 两边是否相同？
- [ ] `TEST_PAPERS` 字典两边是否完全相同？
- [ ] B1 的 prompt 中没有意外包含任何经验/hint 内容？

#### 修改 `experience_db.py` 或经验提取脚本时：
- [ ] 经验库中是否只包含 Training Set 论文的经验？
- [ ] 没有 Test Set 论文（fpm_inr, lensless, lfm, sparse_sim, flfm）的经验泄露进去？
- [ ] 经验检索的 `min_sim` 阈值对 B1/B2 是否一致（B1 不检索，B2 检索）？

#### 修改 `llm_judge.py` 时：
- [ ] Judge prompt 中没有包含 group 标签（不可让 Judge 知道这是 B1 还是 B2）？
- [ ] 评分标准（full/partial/missing）的定义没有被放宽或收紧？
- [ ] `temperature=0.0` 保持不变，确保评分可复现？

### 6.3 实验控制变量一览

B1 vs B2 的对比实验中，**唯一的自变量**是经验注入。以下变量必须严格一致：

| 变量 | B1 值 | B2 值 | 必须一致 |
|------|-------|-------|----------|
| LLM Model | `global.anthropic.claude-opus-4-6-v1` | 同左 | ✅ |
| `max_iterations` | 100 | 100 | ✅ |
| `timeout` (sandbox) | 3600s | 3600s | ✅ |
| `MAX_WAIT_SECONDS` | 5400s | 5400s | ✅ |
| `native_tool_calling` | true | true | ✅ |
| `temperature` | default | default | ✅ |
| Prompt Template | 基础模板 | 基础模板 + `{experience_section}` | ✅ 仅此差异 |
| Test Papers | 5 篇 | 同样 5 篇 | ✅ |
| Paper Markdown | `paper_markdowns_v2/` | 同左 | ✅ |
| 沙箱环境 | 干净启动 | 干净启动 | ✅ |

### 6.4 结果可验证性要求

为确保结果 solid，每次实验运行后必须保留完整的证据链：

1. **Prompt 存档**: `data/agent_prompts_v5/{group}/{paper_id}_prompt.txt` — 实际发送给 Agent 的完整 prompt，可事后审计 B1 是否真的没有经验、B2 注入了哪些经验
2. **Workspace 快照**: 工作空间完整保留，包含 Agent 产出的所有代码和输出文件
3. **LLM 调用日志**: `logs/llm_completions/` — 每次 LLM 调用的 request/response，可追溯 Agent 的完整推理过程
4. **运行日志**: `logs/run_logs/` — 启动时间、结束时间、退出状态、迭代次数
5. **Result JSON**: 从 workspace 中原样复制，不经过任何后处理

### 6.5 快速自检命令

在提交最终结果前，运行以下检查：

```bash
# 1. 确认 B1/B2 prompt 模板一致性（除经验段落外应无差异）
diff <(grep -v "experience" scripts/run_test_baseline.py | grep -A999 'PROMPT_TEMPLATE') \
     <(grep -v "experience" scripts/run_test_experience.py | grep -A999 'PROMPT_TEMPLATE')

# 2. 确认 B1/B2 配置参数一致
grep -E "MAX_ITERATIONS|MAX_WAIT" scripts/run_test_baseline.py scripts/run_test_experience.py

# 3. 确认 MAS 计算无偏置
grep -n "offset\|bias\|+ 0\.\|bonus" code/evaluation/mas_calculator.py
# 期望输出: 无匹配

# 4. 确认经验库中无 Test Set 论文
python -c "
from code.experience_db.experience_db import ExperienceDB
db = ExperienceDB()
test_papers = {'fpm_inr', 'lensless', 'lfm', 'sparse_sim', 'flfm'}
for exp in db.all():
    src = exp.get('source_paper', '')
    if any(t in src.lower() for t in test_papers):
        print(f'⚠️ LEAK: {exp[\"id\"]} from {src}')
print('✅ No test set leakage') if not any(...) else None
"

# 5. 确认 LLM Judge prompt 不含 group 信息
grep -n "b1\|b2\|baseline\|experience\|treatment\|control" code/evaluation/llm_judge.py
# 期望: 仅在文件头注释中出现，不在 judge prompt 中
```

---

## 七、下一步实验计划

> **核心目标：系统性地探索"经验"在整个 pipeline 中到底起什么作用、如何让它起到更好更合理的作用。**

### ⚠️ 工作范围约束（Scope Constraint）

> **本计划只关注 Experience 相关的三个环节：Generation（生成/提取）、Matching（检索/匹配）、Injection（注入）。**
>
> 不要修改多智能体框架本身（OpenHands 核心代码、sandbox 机制、Agent loop 等）。
> 框架层面的优化由其他 Agent 负责。本文档的后续执行者只需要改动以下文件：
>
> | 允许修改 | 文件 | 说明 |
> |----------|------|------|
> | ✅ 经验生成 | `code/experience_db/trajectory_parser.py` | 从 trajectory 提取经验的逻辑 |
> | ✅ 经验生成 | `code/experience_db/seed_from_trajectories.py` | 批量提取入口 |
> | ✅ 经验生成 | `scripts/extract_v3_experiences.py` | 提取脚本 |
> | ✅ 经验存储 | `code/experience_db/experience_db.py` | DB 结构、检索、过滤、评分 |
> | ✅ 经验注入 | `scripts/run_test_experience.py` | B2 prompt 中经验段落的格式化 |
> | ✅ 评估脚本 | `scripts/run_mas_evaluation.py`, `scripts/run_llm_judge.py` | 评估流程 |
> | ✅ 运行脚本 | `scripts/run_test_baseline.py`, `scripts/run_training_baseline.py` | 运行入口 |
> | ❌ 禁止修改 | `/home/yjh/OpenHands/` 下的任何文件 | 多智能体框架代码 |
> | ❌ 禁止修改 | `config.toml` 中 Agent 行为相关的配置 | 如 `max_iterations`, `timeout` 等 |
> | ❌ 禁止修改 | `code/agent/planner.py` | Agent 规划逻辑 |

### 7.0 当前瓶颈分析

| 问题 | 现状 | 影响 |
|------|------|------|
| 经验库太小 | 仅 19 条，全部 Bronze 级 | 检索命中率低，注入内容可能不相关 |
| 检索相似度低 | 平均 0.50-0.57 | 跨论文迁移效果存疑 |
| 单次实验 | B1/B2 各只跑了 1 次 | 无法区分"经验的作用"和"LLM 随机性" |
| 经验来源单一 | 仅来自 V3 的 5 篇 Tier 1 | 缺少 Tier 2/3 的经验，领域覆盖不足 |
| 无消融实验 | 不知道哪类经验有用 | 正面经验 vs 负面经验？领域内 vs 跨领域？ |

---

### 7.1 Step 1: 扩大 Training Set 经验库（重新提取）

**目标**: 从当前已完成的 Training Set 运行中提取更多、更高质量的经验。

**当前 Training Set (10 篇)**:

| Paper | Tier | 状态 | 经验已提取? |
|-------|------|------|------------|
| pyeit | 1 | ✅ 成功 | ✅ V3 已提取 |
| pat | 1 | ✅ 成功 | ✅ V3 已提取 |
| insar | 1 | ✅ 成功 | ✅ V3 已提取 |
| bpm | 1 | ❌ 失败 | ✅ V3 已提取（负面经验） |
| diff | 1 | ✅ 成功 | ✅ V3 已提取 |
| oopao | 2 | ✅ 成功 | ❌ **待提取** |
| lenstronomy | 2 | ✅ 成功 | ❌ **待提取** |
| pnp_cassi | 2 | ✅ 成功 | ❌ **待提取** |
| dpi | 3 | ❌ 超时 | ❌ **待提取（负面经验）** |
| ptyrad | 3 | ✅ 成功 | ❌ **待提取** |

**操作步骤**:
```bash
# 1. 从 V5 Training 运行中提取新经验
#    需要编写/扩展 extract 脚本，处理 oopao, lenstronomy, pnp_cassi, dpi, ptyrad 的 trajectory
# 2. 提取后经验库目标: ≥ 40 条（当前 19 条 + 新增 ~20 条）
# 3. 确保正面/负面经验均衡
```

**⚠️ 关键约束**: 经验只能来自 Training Set 的 10 篇论文。Test Set 的 5 篇（fpm_inr, lensless, lfm, sparse_sim, flfm）绝对不可出现在经验库中。

---

### 7.2 Step 2: 多次重复实验（统计显著性）

**目标**: B1/B2 各跑 3 次，用统计方法证明经验注入的效果不是随机波动。

**实验设计**:

| 实验 | 经验 | 重复次数 | 经验库版本 |
|------|------|----------|-----------|
| B1-run1, B1-run2, B1-run3 | ❌ 无 | 3 | N/A |
| B2-run1, B2-run2, B2-run3 | ✅ 有 | 3 | 各自独立（见 7.3） |

**⚠️ 关键约束: 每次 B2 重复实验必须使用独立的经验库**

每次重新训练（重跑 Training Set）时，必须：
1. **新建一个全新的 experience DB**（不可复用上一轮的）
2. 从该轮 Training 运行的 trajectory 中重新提取经验
3. 用该轮的经验库去跑对应的 B2 Test

这样做的原因：经验提取本身依赖 LLM，有随机性。如果所有 B2 共用同一个经验库，就无法区分"经验内容的作用"和"特定经验库的偶然匹配"。

**目录结构**:
```
data/
├── experience_db_round1/     # 第 1 轮 Training 提取的经验库
│   ├── experience_meta.db
│   └── vectors.json
├── experience_db_round2/     # 第 2 轮 Training 提取的经验库
├── experience_db_round3/     # 第 3 轮 Training 提取的经验库
├── reproduction_results_v5/
│   ├── test_b1_run1/         # B1 第 1 次
│   ├── test_b1_run2/         # B1 第 2 次
│   ├── test_b1_run3/         # B1 第 3 次
│   ├── test_b2_run1/         # B2 第 1 次 (用 experience_db_round1)
│   ├── test_b2_run2/         # B2 第 2 次 (用 experience_db_round2)
│   └── test_b2_run3/         # B2 第 3 次 (用 experience_db_round3)
```

**统计分析**:
- 对每篇 paper 的 MAS 做 paired t-test 或 Wilcoxon signed-rank test
- 报告 mean ± std，以及 p-value
- 如果 p < 0.05，才能声称经验注入有统计显著效果

---

### 7.3 Step 3: 经验消融实验（Ablation Study）

**目标**: 搞清楚经验库中**哪类经验**真正有用。

**消融组设计**:

| 实验组 | 注入内容 | 目的 |
|--------|----------|------|
| B1 (baseline) | 无经验 | 对照组 |
| B2-full | 全部经验（正面 + 负面） | 当前默认方案 |
| B2-positive-only | 仅正面经验 | 负面经验是否有用？ |
| B2-negative-only | 仅负面经验（已知失败的方法） | 负面警告是否比正面建议更有价值？ |
| B2-same-domain | 仅同领域经验 | 跨领域迁移是否有效？ |
| B2-cross-domain | 仅跨领域经验 | 通用策略 vs 领域特定策略 |
| B2-meta-only | 仅 meta-experience（通用策略） | 手工策略 vs 自动提取经验 |

**实现方式**: 修改 `experience_db.py` 的 `retrieve()` 方法，增加 `filter_type` 参数：
```python
def retrieve(self, query, max_inject=3, filter_type=None):
    # filter_type: "positive" | "negative" | "same_domain" | "cross_domain" | "meta" | None
```

**优先级**: 先跑 B2-positive-only 和 B2-negative-only（最重要的消融），再考虑其他组。

---

### 7.4 Step 4: 经验检索质量改进

**目标**: 提升检索相似度（当前 0.50-0.57 → 目标 ≥ 0.70）。

**改进方向**:

| 方向 | 具体方案 | 优先级 |
|------|----------|--------|
| **Query 构造优化** | 当前 query 是 paper 前 2000 字 + domain 标签，太粗糙。改为提取论文的 method keywords + problem type 作为 query | 🔴 高 |
| **Embedding 模型升级** | 当前用 `aliyun/text-embedding-v4`，尝试用更强的 embedding 模型或 fine-tune | 🟡 中 |
| **经验粒度细化** | 当前每条经验是一整个 episode，太长。拆分为更细粒度的 tip（如"数据生成技巧"、"调参策略"、"常见 bug"） | 🔴 高 |
| **Reranker 阈值调优** | Stage 2 的 RELEVANT/PARTIAL/IRRELEVANT 阈值可能过严，导致有用经验被过滤 | 🟡 中 |
| **经验标签系统** | 给每条经验打标签（如 `data_generation`, `algorithm_impl`, `debugging`, `parameter_tuning`），检索时按标签匹配 | 🟢 低 |

---

### 7.5 Step 5: 经验注入策略探索

**目标**: 在不修改 OpenHands 框架的前提下，探索不同的经验注入方式，找到最优策略。

**⚠️ 范围约束**: 所有策略只通过修改 `run_test_experience.py` 中的 prompt 构造逻辑实现，不改动 OpenHands 本身。

| 策略 | 说明 | 修改范围 | 假设 |
|------|------|----------|------|
| **当前方案: Prompt Prepend** | 经验作为 prompt 开头的一部分，一次性注入 | 无需改动 | 简单但 Agent 可能忽略 |
| **经验数量实验** | max_inject = 1 / 3 / 5 / 10，观察注入数量对效果的影响 | `experience_db.py` 的 `retrieve()` 参数 | 太多经验可能造成信息过载 |
| **经验格式优化** | 改变注入格式：纯文本 vs 结构化 checklist vs code snippet 优先 | `run_test_experience.py` 的格式化逻辑 | 格式影响 Agent 对经验的利用率 |
| **经验摘要注入** | 不注入原始经验，而是用 LLM 先将多条经验总结为一段简洁的 guidance | `run_test_experience.py` 增加摘要步骤 | 精炼信息比原始信息更有效 |
| **分区注入** | 将经验按类型分区：`[PITFALLS]` 负面经验 + `[STRATEGIES]` 正面经验 + `[CODE HINTS]` 代码片段 | `run_test_experience.py` 的格式化逻辑 | 结构化呈现帮助 Agent 按需取用 |

**优先级**: 先做"经验数量实验"（改一个参数即可），再做"分区注入"和"经验摘要注入"。

---

### 7.6 Step 6: 扩大 Test Set（可选，增强说服力）

**目标**: 如果 15 篇论文不够，考虑扩大 benchmark。

**当前规模**: Training 10 + Test 5 = 15 篇

**扩展方案**:
- 新增 5-10 篇 Tier 2/3 论文到 Test Set（需要新的 paper markdown）
- 或者做 **交叉验证**: 将 15 篇论文做 3-fold CV，每 fold 用 10 篇训练 + 5 篇测试
- 交叉验证的好处：每篇论文都既当过训练集又当过测试集，结果更 robust

**⚠️ 约束**: 如果做交叉验证，每个 fold 必须有独立的经验库，不可跨 fold 泄露。

---

### 7.7 执行优先级与时间线

| 优先级 | Step | 预计工作量 | 依赖 | 修改范围 |
|--------|------|-----------|------|----------|
| 🔴 P0 | 7.1 扩大经验库 | 1 天 | 无 | `experience_db/`, `scripts/extract_*` |
| 🔴 P0 | 7.2 多次重复实验 (3×B1 + 3×B2) | 3-4 天（机器时间） | 7.1 | `scripts/run_test_*.py` |
| 🔴 P0 | 7.4 Query 构造优化 + 经验粒度细化 | 1 天 | 7.1 | `experience_db.py`, `trajectory_parser.py` |
| 🟡 P1 | 7.3 消融实验 (positive-only, negative-only) | 2 天 | 7.2 | `experience_db.py` 增加 filter |
| 🟡 P1 | 7.5 经验数量实验 (max_inject=1/3/5) | 1 天 | 7.2 | `experience_db.py` 参数 |
| 🟡 P1 | 7.5 经验格式优化 + 分区注入 | 1 天 | 7.2 | `run_test_experience.py` |
| 🟢 P2 | 7.3 消融实验 (same-domain, cross-domain) | 2 天 | 7.3 P1 部分 | `experience_db.py` 增加 filter |
| 🟢 P2 | 7.5 经验摘要注入 | 1 天 | 7.5 P1 部分 | `run_test_experience.py` |
| 🟢 P2 | 7.6 扩大 Test Set 或交叉验证 | 3 天 | 7.2 | `scripts/`, 新 paper markdown |

**总计**: 完成 P0+P1，P2 视结果决定是否执行。

> **再次强调**: 以上所有 Step 的改动范围仅限于 `code/experience_db/`、`scripts/`、`data/` 目录。
> **不要**修改 OpenHands 框架代码、Agent loop、sandbox 机制、`config.toml` 中的 Agent 行为参数。
