# Project Evolution-Reproduce: 上下文交接文档

**最后更新:** 2026-03-20 03:07 (UTC+8)
**当前阶段:** Phase 1 — 基线测试阶段（接近完成）
**文档目的:** 为下一个 Agent 提供完整的系统架构、文件位置、实验状态和下一步任务信息，使其无需重新探索即可立即工作。

---

## 一、项目当前状态

### 1.1 总体进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0: 文献调研 & Benchmark 创建 | ✅ 已完成 | 15篇论文分3个Tier，registry v2已建立 |
| Phase 1a: arxiv→markdown 管道 | ✅ 已完成 | PaddleOCR方案，已在 arxiv:2301.10137 上端到端测试 |
| Phase 1b: OpenHands-only B2 基线框架 | ✅ 已完成 | `run_baseline.py` 支持单篇/批量/状态监控 |
| Phase 1c: Tier 1 测试 & 验证 | 🔄 进行中 | 4/5 有 results.json，diff Round 4 运行中 |
| Phase 1d: 沙箱稳定性修复 | ✅ 已完成 | 根因：孤儿进程，已修复 `kill_action_servers()` |
| Phase 2: 经验提取 | ❌ 未开始 | 需从成功轨迹中提取复现经验 |
| Phase 3-5: 经验驱动复现/融合/论文 | ❌ 未开始 | — |

### 1.2 当前活跃任务

- **diff 论文 Round 4** 正在运行
  - PID: `1294007`（运行中，已56+分钟，385MB RSS）
  - Workspace: `/data/yjh/openhands_workspace/tier1_v2_diff_20260320_003202/`
  - Log: `/home/yjh/Evolution_reproduce/logs/sandbox_stdout/diff.log`（168行，持续增长）
  - Agent 状态: `AgentState.RUNNING`，已经在生成复现计划和代码
  - 无 ConnectError，沙箱稳定

### 1.3 检查 diff 状态的命令

```bash
# 检查进程是否存活
ps -p 1294007 -o pid,etime,rss --no-headers

# 检查日志增长（行数应持续增加）
wc -l /home/yjh/Evolution_reproduce/logs/sandbox_stdout/diff.log

# diff 完成后检查结果
cat /home/yjh/Evolution_reproduce/data/reproduction_results_v2/diff_result.json | python3 -m json.tool | head -30

# 检查 workspace 中是否有 results.json
ls /data/yjh/openhands_workspace/tier1_v2_diff_20260320_003202/results.json 2>&1
```

---

## 二、基线框架架构 (B2 Baseline)

### ⚠️ 2.0 重要发现：任务难度问题（需要调整）

**问题**: 当前 Tier 1 测试使用的是 `_task.md`（代码脚本），而非 `_full.md`（真正的学术论文）。

| 文件类型 | 内容 | 难度 | 示例（pyeit） |
|----------|------|------|--------------|
| `*_task.md` | **纯 Python 代码脚本**，包含完整的函数定义、类、imports | 极低 — Agent 只需读代码并重写 | 324行 Python 代码，JAC 3D EIT demo |
| `*_full.md` | **真正的 OCR 学术论文**，含摘要、方法论、公式、图表描述 | 正常 — 需要理解论文并从零实现 | pyEIT 论文全文，含 motivation、software description |

**根因**: `run_baseline.py` 中 `launch_from_registry()` 优先使用 `markdown_task_path`：
```python
md_task = info.get("markdown_task_path")
md_full = info.get("markdown_full_path")
md_path = md_task if md_task and Path(md_task).exists() else md_full
```

**影响**: 当前 80% 成功率被严重高估。Agent 实际上是在"抄写"可见代码，而非真正"复现"论文。

**修复方案**: 
1. 修改 `run_baseline.py`，将优先级改为 `_full.md`
2. 或在 registry 中删除 `markdown_task_path` 字段
3. 用 `_full.md` 重新跑 Tier 1，对比成功率差异（这才是有意义的基线数据）

**具体的 pyeit 例子**:
- `_task.md` 输入: Agent 收到完整的 Python 脚本，包含 `class JAC`, `def solve()`, `def eit_scan_lines()` 等函数，只需理解代码逻辑并重现
- `_full.md` 输入: Agent 收到学术论文 "pyEIT: A python based framework for Electrical Impedance Tomography"，需要从论文描述中理解 FEM 方法、JAC 重建算法、Tikhonov 正则化，然后从零实现
- 当前结果（使用 _task.md）: ✅ 成功，43 events，1128s
- 预期结果（使用 _full.md）: 成功率大幅下降，这才是有意义的基线

### 2.1 整体流程

```
Paper (arxiv ID / local PDF)
  ↓ PaddleOCR
Markdown 文本
  ↓ PROMPT_TEMPLATE 模板化
Agent Prompt (含7条强制规则)
  ↓ OpenHands CodeActAgent
results.json (复现结果)
```

### 2.2 OpenHands LocalRuntime 工作原理

1. **进程模型**: OpenHands 在本机（非 Docker）启动 `action_execution_server.py` 作为 FastAPI/Uvicorn 子进程
2. **端口范围**: 每个 server 监听 TCP 端口 30000-39999
3. **通信方式**: 主进程通过 HTTP POST 向 action_execution_server 发送命令（bash/IPython）
4. **关键风险**: 如果父进程被 kill，子进程（jupyter kernel、tmux、file viewer 等）会成为孤儿进程，占用端口
5. **Python 环境**: `/data/yjh/conda_envs/openhands/bin/python3`（OpenHands 专用 conda 环境）

### 2.3 LLM 配置

| 参数 | 值 |
|------|-----|
| model | `openai/cds/Claude-4.6-opus` |
| api_key | `sk-Zj3a7RQDVCXr-Axg-0gtkg` |
| base_url | `https://ai-gateway-internal.dp.tech/v1` |
| temperature | 0.7 |
| max_message_chars | 30000 |
| num_retries | 5 |

### 2.4 Prompt 模板关键规则

Agent Prompt 包含 **7 条强制规则**（在 `run_baseline.py` 的 `PROMPT_TEMPLATE` 中定义）：

1. **REPRODUCTION PLAN FIRST** — 必须先写复现计划再写代码
2. **TOY-FIRST PRINCIPLE** — 先用最小 toy test 验证代码正确性
3. **SANITY CHECK** — 每次执行后检查 NaN/Inf/异常范围
4. **FILE PERSISTENCE** — 使用 `cat > file.py << 'PYEOF'` 模式写多行文件
5. **RESULTS FORMAT** — 必须保存 `results.json`（含 paper_title, metrics, files_produced 等）
6. **BUDGET AWARENESS** — 到 70% 迭代预算时必须收尾出结果
7. **NO CHEATING** — 不得硬编码期望结果

### 2.5 OpenHands 配置文件

配置位于 `/home/yjh/OpenHands/config.toml`：

```toml
[core]
runtime = "local"                           # 非 Docker，直接本机
workspace_base = "/data/yjh/openhands_workspace"
save_trajectory_path = "/data/yjh/openhands_results_v2/trajectories"
enable_browser = false
file_store = "memory"
max_iterations = 30                         # 配置文件中是 30，但 CLI 传 100 覆盖
default_agent = "CodeActAgent"

[llm]
model = "openai/cds/Claude-4.6-opus"
api_key = "sk-Zj3a7RQDVCXr-Axg-0gtkg"
base_url = "https://ai-gateway-internal.dp.tech/v1"
temperature = 0.7
max_message_chars = 30000
num_retries = 5
drop_params = true

[sandbox]
timeout = 600
enable_gpu = true

[condenser]
type = "noop"
```

**注意**: `max_iterations` 在 CLI 启动时传 `--max-iterations 100` 覆盖配置文件中的 30。

### 2.6 OpenHands 单次运行的完整生命周期（以 pyeit 为例）

以下展示一次完整的 baseline 运行从启动到结束的全过程：

**Step 1: 启动命令**
```bash
# run_baseline.py 内部实际执行的命令：
/data/yjh/conda_envs/openhands/bin/python3 /home/yjh/OpenHands/run_evolution_task.py \
  --prompt-file /home/yjh/Evolution_reproduce/data/agent_prompts_v2/pyeit_prompt.txt \
  --workspace /data/yjh/openhands_workspace/tier1_v2_pyeit_20260319_141215 \
  --session-name tier1_v2_pyeit_20260319_141215 \
  --max-iterations 100 \
  --config /home/yjh/OpenHands/config.toml \
  --output-file /home/yjh/Evolution_reproduce/data/reproduction_results_v2/pyeit_result.json
```

**Step 2: run_evolution_task.py 内部流程**
```
1. kill_action_servers()  — 清理旧进程
2. 创建 OpenHands AgentController
3. AgentController 启动 LocalRuntime:
   ├─ 启动 action_execution_server.py (FastAPI/Uvicorn, 端口 30000-39999)
   ├─ 等待 server 就绪 (HTTP health check)
   └─ 建立 HTTP 连接
4. 注入 prompt → Agent 开始工作
5. Agent 循环: 思考 → 行动(bash/IPython) → 观察结果 → 再思考
6. Agent 调用 finish() 或达到 max_iterations
7. 收集结果: 检查 workspace 中的 results.json
8. 保存 trajectory 和 result JSON
9. kill_action_servers()  — 清理
```

**Step 3: Agent 实际行为观察（pyeit 示例，43 events）**
```
Event 1-3:   读取论文内容，制定复现计划（列出步骤清单）
Event 4-8:   创建 toy test — 最小 FEM 网格验证
Event 9-15:  实现 Protocol（激励/测量模式）
Event 16-22: 实现 FEM Forward Solver（刚度矩阵、Poisson 方程）
Event 23-30: 实现 JAC 逆问题求解器（Tikhonov 正则化）
Event 31-38: 全尺寸运行（530 nodes, 16 electrodes）
Event 39-42: 保存结果到 results.json，验证 sanity check
Event 43:    调用 finish()
```

**Step 4: 产出文件（在 workspace 目录中）**
```
/data/yjh/openhands_workspace/tier1_v2_pyeit_20260319_141215/
├── results.json          # 复现结果（metrics, status, files_produced）
├── 3D_eit.png           # 3D 重建可视化图
├── reproduce_eit.py     # Agent 生成的复现代码
└── (其他中间文件)
```

**Step 5: results.json 示例内容**
```json
{
  "paper_title": "pyEIT: 3D EIT Reconstruction using JAC",
  "reproduction_status": "success",
  "metrics": {
    "mesh_nodes": 530,
    "mesh_elements": 2399,
    "electrodes": 16,
    "measurements": 192,
    "anomaly_detected": true,
    "method": "JAC with Kotre regularization"
  },
  "files_produced": ["3D_eit.png", "results.json"],
  "notes": "Successfully reproduced 3D EIT mesh generation and JAC reconstruction"
}
```

### 2.7 快速启动单篇论文的命令

```bash
# 方法1: 从已有 markdown 启动
cd /home/yjh/Evolution_reproduce
python code/baseline/run_baseline.py \
  --markdown data/paper_markdowns_v2/pyeit_full.md \
  --paper-id pyeit_fullpaper \
  --max-iterations 100

# 方法2: 从 arxiv ID 启动（自动下载+OCR）
python code/baseline/run_baseline.py --arxiv-id 2301.10137

# 方法3: 批量启动某个 Tier
python code/baseline/run_baseline.py \
  --registry data/ReproduceBench/paper_registry_v2.json \
  --tier 1 --stagger 120

# 检查状态
python code/baseline/run_baseline.py --status
```

---

## 三、关键文件清单

### 3.1 核心框架代码

| 文件（绝对路径） | 功能 | 是否修改过 |
|-----------------|------|-----------|
| `/home/yjh/Evolution_reproduce/code/baseline/run_baseline.py` | B2 基线框架主脚本（单篇/批量/状态监控） | ✅ 自建 |
| `/home/yjh/Evolution_reproduce/code/utils/arxiv_to_markdown.py` | arxiv ID → PDF 下载 → PaddleOCR → Markdown | ✅ 自建 |
| `/home/yjh/Evolution_reproduce/code/utils/sandbox_cleanup.sh` | 手动沙箱清理工具（5步清理流程） | ✅ 自建 |
| `/home/yjh/OpenHands/run_evolution_task.py` | OpenHands 任务启动器（**已修改** `kill_action_servers()`） | ⚠️ 已修改 |
| `/home/yjh/OpenHands/config.toml` | OpenHands 全局配置 | ⚠️ 已修改 |

### 3.2 数据文件

| 文件/目录（绝对路径） | 内容 |
|---------------------|------|
| `/home/yjh/Evolution_reproduce/data/ReproduceBench/paper_registry_v2.json` | 15篇论文注册表（Tier 1-3，含 markdown 路径） |
| `/home/yjh/Evolution_reproduce/data/paper_markdowns_v2/` | 所有15篇论文的 Markdown（task 版 + full 版） |
| `/home/yjh/Evolution_reproduce/data/agent_prompts_v2/` | 已生成的 Agent Prompt（pyeit, pat, insar, bpm, diff） |
| `/home/yjh/Evolution_reproduce/data/reproduction_results_v2/` | OpenHands 运行结果 JSON |
| `/data/yjh/openhands_results_v2/trajectories/` | Agent 执行轨迹（用于 Phase 2 经验提取） |
| `/data/yjh/openhands_workspace/` | OpenHands 工作空间（含 agent 生成的代码和结果文件） |

### 3.3 日志

| 文件（绝对路径） | 内容 |
|-----------------|------|
| `/home/yjh/Evolution_reproduce/logs/sandbox_stdout/pyeit.log` | pyeit 运行日志 |
| `/home/yjh/Evolution_reproduce/logs/sandbox_stdout/pat.log` | pat 运行日志 |
| `/home/yjh/Evolution_reproduce/logs/sandbox_stdout/insar.log` | insar 运行日志 |
| `/home/yjh/Evolution_reproduce/logs/sandbox_stdout/bpm.log` | bpm 运行日志 |
| `/home/yjh/Evolution_reproduce/logs/sandbox_stdout/diff.log` | diff 运行日志（Round 4，当前活跃） |

### 3.4 Phase 2 相关代码（已创建骨架，尚未使用）

| 文件（绝对路径） | 功能 |
|-----------------|------|
| `/home/yjh/Evolution_reproduce/code/experience_db/experience_db.py` | 经验数据库 |
| `/home/yjh/Evolution_reproduce/code/experience_db/trajectory_parser.py` | 轨迹解析器 |
| `/home/yjh/Evolution_reproduce/code/experience_db/seed_from_trajectories.py` | 从轨迹中提取种子经验 |
| `/home/yjh/Evolution_reproduce/code/evaluation/mas_calculator.py` | MAS 分数计算器 |
| `/home/yjh/Evolution_reproduce/code/evaluation/llm_judge.py` | LLM 评判器 |
| `/home/yjh/Evolution_reproduce/code/evaluation/evaluate_run.py` | 运行评估器 |
| `/home/yjh/Evolution_reproduce/code/agent/planner.py` | 经验增强规划器 |

---

## 四、实验结果与稳定性

### 4.1 Tier 1 复现结果汇总

| 论文 | Agent 状态 | 迭代数 | 耗时 | results.json | 质量评估 |
|------|-----------|--------|------|-------------|---------|
| **pyeit** | ✅ FINISHED | ~43 events | 1128s | ✅ 有 | **高** — 3D EIT mesh, JAC 重建, 异常检测 |
| **pat** | ✅ FINISHED | ~31 events | 1058s | ✅ 有 | **高** — 反投影, 带通滤波, 光谱解混 |
| **insar** | ✅ FINISHED | ~42 events | 1044s | ✅ 有 | **高** — 相位解缠, toy-first, 4个结果文件 |
| **bpm** | ⚠️ ERROR | ~47 events | 1620s | ✅ 有 | **中** — BPM 重建完整运行, 实验后沙箱崩溃 |
| **diff** | 🔄 RUNNING | — | 56min+ | — | Round 4, PID 1294007, 沙箱稳定无崩溃 |

**成功率**: 4/5 = 80%（有 results.json）| 干净完成: 3/5 = 60%

### 4.2 沙箱崩溃根因分析

**问题现象:**
- diff 论文前3轮均失败，报 `ConnectError: [Errno 111] Connection refused`
- 命令执行出现 30s 超时

**根因:**
- **~53+ 孤儿 python3.12 进程**（jupyter kernel、tmux server、file viewer 等）来自之前被 kill 的 `action_execution_server` 父进程
- 这些孤儿进程持续占用 TCP 端口 30000-39999
- 新启动的 OpenHands 运行时找不到可用端口，或连接到错误的旧 server

**原始 `kill_action_servers()` 的缺陷:**
- 只用 `pkill -f action_execution_server` 杀名为 `action_execution_server` 的进程
- **不杀子进程**（jupyter、tmux 等），导致孤儿进程积累

**修复方案（已应用到 `/home/yjh/OpenHands/run_evolution_task.py`）:**

```python
def kill_action_servers(wait=3):
    """4步综合清理"""
    # Step 1: 使用 PGID 杀 action_execution_server 整个进程树
    # Step 2: 通过 ss 命令杀 30000-39999 端口上的孤儿 python3.12 监听器
    # Step 3: 通过 lsof 备份清理（捕获 ss 遗漏的进程）
    # Step 4: 清理过时的 tmux session
```

**验证结果:**
- 清理前: 53+ 孤儿进程在 30000-39999 端口
- 清理后: 仅 6 个无关系统监听器
- diff Round 4 成功启动，持续运行 56+ 分钟无崩溃

### 4.3 手动清理命令

如果遇到沙箱问题，使用以下命令：

```bash
# 方法1：运行清理脚本
bash /home/yjh/Evolution_reproduce/code/utils/sandbox_cleanup.sh

# 方法2：手动清理
# 查看端口占用
ss -tlnp | grep -E ':3[0-9]{4}\b'
# 杀掉所有占用 30000-39999 端口的进程
lsof -i :30000-39999 -t | xargs kill -9
# 杀掉所有 action_execution_server
pkill -9 -f action_execution_server
# 杀掉所有 run_evolution_task
pkill -9 -f run_evolution_task
```

---

## 五、下一步计划

### 🔴 5.0 最高优先级：修复任务难度问题

**这是 Phase 1 最关键的未完成工作。** 当前结果不可靠，因为使用了 `_task.md`（代码脚本）而非 `_full.md`（真正论文）。

**具体执行步骤:**

1. **修改 `run_baseline.py`** — 将 `launch_from_registry()` 中的 markdown 优先级从 `_task.md` 改为 `_full.md`：
   ```python
   # 修改前（当前代码）:
   md_path = md_task if md_task and Path(md_task).exists() else md_full
   
   # 修改后（正确做法）:
   md_path = md_full if md_full and Path(md_full).exists() else md_task
   ```

2. **用 `_full.md` 重新跑 Tier 1 全部 5 篇论文**
   ```bash
   # 清理旧进程
   bash /home/yjh/Evolution_reproduce/code/utils/sandbox_cleanup.sh
   
   # 逐篇用 _full.md 启动（不用 registry，直接指定 markdown）
   cd /home/yjh/Evolution_reproduce
   for paper in pyeit pat insar bpm diff; do
     python code/baseline/run_baseline.py \
       --markdown "data/paper_markdowns_v2/${paper}_full.md" \
       --paper-id "${paper}_v3_full" \
       --max-iterations 100
     # 等待完成后再跑下一篇
     echo "等待 ${paper} 完成..."
     wait
   done
   ```

3. **对比分析两组结果**
   - `_task.md` 结果（v2）: 保留在 `data/reproduction_results_v2/`
   - `_full.md` 结果（v3）: 保存到 `data/reproduction_results_v3/`
   - 对比成功率、结果质量、耗时差异 — 这才是有意义的基线数据
   - 预期: 使用 `_full.md` 后成功率应显著下降（可能 20-40%），这才能体现经验增强的价值

4. **建立双条件评估体系**
   - **easy mode** (`_task.md`): 用于调试框架、验证流程正确性
   - **hard mode** (`_full.md`): 用于正式基线数据、论文报告
   - 后续所有正式实验均使用 hard mode

### 5.1 其他 Phase 1 收尾

1. **等待 diff Round 4 完成**（可能已完成或即将完成）
   - 检查命令: `ps -p 1294007 -o pid,etime,rss --no-headers`
   - 完成后检查: `cat /home/yjh/Evolution_reproduce/data/reproduction_results_v2/diff_result.json | python3 -m json.tool`

2. **如果 diff 成功** → 记录 v2 (easy mode) 完整结果，然后开始 v3 (hard mode) 重测
3. **如果 diff 再次失败** → 直接进入 v3 重测，不再纠结 v2 的 diff

### 5.2 Phase 2 入口任务：经验提取

**前置条件**: v3 (hard mode) 的 Tier 1 结果已出。Phase 2 应基于 `_full.md` 的运行数据。

Phase 2 的目标是从 Tier 1 的轨迹（包括成功和失败）中提取**可复用的复现经验**，构建经验数据库。

**具体步骤:**

1. **收集轨迹数据**
   ```bash
   # 检查轨迹文件
   ls -la /data/yjh/openhands_results_v2/trajectories/
   ```

2. **解析轨迹，提取经验模式**
   - 使用 `code/experience_db/trajectory_parser.py` 解析 agent 的行动序列
   - 识别: 成功模式（什么策略有效）、失败模式（什么导致失败）、工具使用模式
   - **重点关注 `_full.md` 运行中的失败案例** — 这才是 Failure-Driven Learning 的核心输入

3. **构建经验数据库**
   - 使用 `code/experience_db/experience_db.py`
   - 种子经验包括: 环境设置技巧、调试策略、数据生成方法、结果验证方法
   - 核心设计原则（来自 reproduce_readme.md）：**只记录失败中获得的经验**（Failure-Driven Extraction）

4. **评估 Tier 1 结果质量**
   - 使用 `code/evaluation/evaluate_run.py` 计算每篇论文的 MAS 分数
   - MAS = Methodology Adherence Score（方法论遵循度）
   - 对比 easy mode vs hard mode 的 MAS 差异

### 5.3 建议的第一条命令（给下一个 Agent）

```bash
# 首先检查 diff 是否完成
ps -p 1294007 -o pid,etime,rss --no-headers 2>&1 && echo "STILL RUNNING" || echo "COMPLETED"

# 如果已完成，查看结果
cat /home/yjh/Evolution_reproduce/data/reproduction_results_v2/diff_result.json | python3 -m json.tool

# 查看所有 Tier 1 结果
for p in pyeit pat insar bpm diff; do
  if [ -f "/home/yjh/Evolution_reproduce/data/reproduction_results_v2/${p}_result.json" ]; then
    echo "$p: $(python3 -c "import json; d=json.load(open('/home/yjh/Evolution_reproduce/data/reproduction_results_v2/${p}_result.json')); print(f\"{d.get('agent_state','?')} results={d.get('has_results_json','?')} elapsed={d.get('elapsed_seconds',0):.0f}s\")" 2>/dev/null)"
  else
    echo "$p: 无结果文件"
  fi
done

# 检查轨迹文件（为 Phase 2 做准备）
ls -la /data/yjh/openhands_results_v2/trajectories/ 2>&1
```

### 5.4 关键注意事项

1. **不要同时运行多个 OpenHands 任务** — 端口冲突风险。每次只运行一个。
2. **每次启动前运行清理** — `bash /home/yjh/Evolution_reproduce/code/utils/sandbox_cleanup.sh`
3. **LLM API 限流** — 使用 stagger（60s 间隔）进行批量启动
4. **config.toml 中的 max_iterations=30 会被 CLI --max-iterations 100 覆盖** — 实际运行使用 100 次迭代
5. **工作空间在 `/data/yjh/openhands_workspace/`** — 不在项目目录下，注意查看正确路径
6. **轨迹保存在 `/data/yjh/openhands_results_v2/trajectories/`** — Phase 2 经验提取的输入数据

---

## 附录：快速状态检查脚本

```bash
#!/bin/bash
# 一键检查所有状态
echo "=== Tier 1 Results ==="
for p in pyeit pat insar bpm diff; do
  if [ -f "/home/yjh/Evolution_reproduce/data/reproduction_results_v2/${p}_result.json" ]; then
    echo "$p: $(python3 -c "
import json
d=json.load(open('/home/yjh/Evolution_reproduce/data/reproduction_results_v2/${p}_result.json'))
print(f\"{d.get('agent_state','?')} | results.json={d.get('has_results_json','?')} | {d.get('elapsed_seconds',0):.0f}s\")
" 2>/dev/null)"
  else
    echo "$p: 无结果文件"
  fi
done

echo ""
echo "=== Running Processes ==="
pgrep -a -f "run_evolution_task" 2>/dev/null || echo "无运行中的任务"

echo ""
echo "=== Port Usage (30000-39999) ==="
ss -tlnp 2>/dev/null | grep -E ':3[0-9]{4}\b' | head -5 || echo "无端口占用"

echo ""
echo "=== Workspace Files ==="
for ws in /data/yjh/openhands_workspace/tier1_v2_*; do
  if [ -d "$ws" ]; then
    has_results=$([ -f "$ws/results.json" ] && echo "✅" || echo "❌")
    echo "  $(basename $ws): results.json=$has_results"
  fi
done
```
