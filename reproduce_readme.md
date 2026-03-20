# Research Plan: Project Evolution–Reproduce
**—— An Autonomous Paper Reproduction System with Failure-Driven Learning and Evolutionary Experience Memory**

---

## 一、 问题定义与研究动机 (Problem Definition & Motivation)

### 1.1 问题陈述 (Problem Statement)

**核心问题**：给定一篇学术论文 $P$（来自任意学科领域，唯一要求是其实验部分基于 Python 实现；以 PDF 形式提供，不附带任何官方代码），能否构建一个自主 Agent 系统 $\mathcal{A}$，使其在一个隔离的计算沙盒环境 $\mathcal{E}$ 中，**从零开始自主完成论文的代码复现**？

具体而言，Agent 需要自主完成但不限于以下能力：

1. **论文理解**：从非结构化论文中理解研究方法、实验设计与关键细节
2. **环境配置**：自动安装依赖、下载数据、配置运行环境
3. **代码实现**：从零编写完整的实验代码
4. **迭代调试**：通过观察运行时报错与实验结果，反复修正代码直至可正常运行
5. **指标对齐**：最终评估复现指标与原论文报告指标之间的差距

> **重要声明**：本项目面向的论文**不局限于机器学习或深度学习领域**。任何基于 Python 实现实验的学术论文——包括但不限于计算物理、计算化学、生物信息学、信号处理、数值优化、科学计算、统计分析等——均在本系统的适用范围内。不同领域的论文在实验结构、评估方式、代码组织上差异巨大，因此**系统不预设任何固定的复现流程或结构化抽取模板**，而是由 Agent 根据论文内容自主规划复现策略。

**形式化目标**：

$$\min_{\theta_\mathcal{A}} \mathbb{E}_{P \sim \mathcal{D}_{\text{papers}}} \left[ \Delta(P, \mathcal{A}_\theta) \right] + \lambda \cdot \text{Cost}(\mathcal{A}_\theta, P)$$

其中 $\Delta$ 是复现指标与原论文指标的归一化偏差，$\text{Cost}$ 包括 LLM API 调用次数、沙盒计算时长、迭代轮数，$\lambda$ 是成本权衡系数。

### 1.2 研究动机 (Motivation)

**现实痛点**：

- **代码不可得**：大量学术论文不开源代码，或代码质量低、无法运行。即使在 CS 领域，提供可运行代码的比例也不高，其他学科（物理、化学、生物等）的情况更差。
- **复现成本极高**：一个有经验的研究员复现一篇中等复杂度论文通常需要 1-4 周，涉及大量调试和隐性知识（trick）的猜测。
- **隐性知识壁垒**：论文中大量关键细节被省略——不同领域有不同的"潜规则"，这些"论文中没写但对复现至关重要"的知识构成了巨大壁垒。
- **跨领域更为严峻**：不同领域的论文在方法描述风格、实验组织方式、评估标准等方面差异巨大，无法用统一的模板来处理。

**学术机会**：

- **对于 Agent 研究**：论文复现是目前已知的、对 LLM Agent 而言最具挑战性的长程任务之一，远超 SWE-bench 的单 bug 修复。它要求 Agent 具备跨阶段规划、长期记忆、从失败中学习的能力。
- **对于经验学习**：该场景天然产生大量 trial-and-error 数据，是验证 "experience-driven long-horizon agent" 范式的理想试验场。
- **对于跨领域泛化**：由于涉及多个学科领域，可以验证经验库的跨领域迁移能力。

### 1.3 核心假设 (Research Hypotheses)

> **H1 (Failure-Driven Learning Hypothesis)**：通过只记录 Agent 经历多次失败后才解决的困难问题（而非一次性成功的简单问题），可以构建一个高信噪比的经验库，显著提升后续任务的首次成功率。
>
> **H2 (Anti-Pollution Retrieval Hypothesis)**：使用两阶段检索（向量召回 + LLM Reranker）并采用严格的"宁缺毋滥"注入策略，比直接注入 Top-K 经验能减少 LLM 的幻觉率和错误率。
>
> **H3 (Evolutionary Fusion Hypothesis)**：通过 Propose-and-Verify 的竞争式融合机制，经验库的平均质量（以泛化性和成功率衡量）会随任务数量的增加而单调提升。

---

## 二、 相关工作与定位 (Related Work & Positioning)

### 2.1 LLM-Based Coding Agents

| 系统 | 核心能力 | 局限性 | 与本项目的关系 |
|------|---------|--------|--------------|
| **OpenHands (fka OpenDevin)** | 提供沙盒执行环境、终端/浏览器交互、multi-agent 框架 | 本身不具备经验积累能力，每次任务从零开始 | **作为本系统的底层执行载体（已部署）** |
| **SWE-Agent** | 针对 GitHub Issue 的代码修复 Agent | 仅处理单文件 bug 修复，不涉及从零构建 | 任务粒度完全不同 |
| **AIDE (AI-Driven Exploration)** | 针对 ML 实验的自动化搜索，tree-structured exploration | 侧重超参数搜索与实验设计，不处理从零复现 | 可借鉴其树形搜索策略 |
| **MLAgentBench** | ML 任务的 benchmark，评估 Agent 在 Kaggle 式任务上的表现 | 提供 starter code，非从零开始；不涉及论文理解 | 可作为部分评估基准 |
| **AutoCodeRover** | 基于代码搜索的 bug 定位与修复 | 针对已有代码库的维护，非从零构建 | 其 spectrum-based 定位思路可借鉴 |

### 2.2 Experience/Skill Library for Agents

| 系统 | 经验机制 | 局限性 |
|------|---------|--------|
| **Voyager (MineCraft Agent)** | Skill Library：成功执行的代码片段存入向量库，后续检索复用 | 记录所有成功经验（含大量 trivial 经验），信噪比低；无融合与淘汰机制 |
| **ExpeL (Experience Learning)** | 从 trajectory 中提取自然语言 insights | 仅用于简单推理任务（ALFWorld, WebShop），未验证于长程编码任务 |
| **Reflexion** | 自我反思 + verbal reinforcement | 反思结果仅用于单次任务的 retry，不跨任务持久化 |
| **LATS (Language Agent Tree Search)** | 将 MCTS 引入 Agent 决策 | 搜索在单任务内进行，不涉及跨任务经验迁移 |
| **AgentTrek** | 从 web tutorial 中自动生成 agent trajectory 数据用于训练 | 依赖外部知识源（教程），非从自身失败中学习 |

**本项目的差异化定位**：

1. **Failure-Only Recording**：与 Voyager 的"全记录"策略相反，我们仅记录困难问题的解决方案，大幅提升信噪比
2. **Cross-Task Experience Transfer with Anti-Pollution**：与 Reflexion 的"单任务反思"不同，经验跨任务持久化，但通过 LLM Reranker 严格防止污染
3. **Evolutionary Competition**：与所有现有系统的"只增不减"知识库不同，引入达尔文式竞争淘汰，使经验库质量持续提升
4. **Multi-Domain Long-Horizon Task**：在跨领域的从零论文复现场景中验证，而非局限于单一领域或简单任务

### 2.3 Paper Reproduction & Understanding

- **PaperMage / Nougat / Grobid**：PDF 论文的结构化解析工具
- **PaddleOCR (PPStructureV3)**：本项目实际采用的 PDF→Markdown 解析方案（详见第四节）
- **Papers with Code**：提供论文-代码-数据集的关联，可用于构建评估基准
- **ML Reproducibility Challenge**：学术界已有的人工复现挑战赛，可为我们提供"人类复现成功率"的基线

---

## 三、 核心设计哲学 (Design Principles)

### Principle 1: 失败驱动学习 (Failure-Driven Extraction)

**核心论断**：基础大模型（GPT-4o / Claude 4 Sonnet / Claude 4 Opus）已掌握标准知识（如编写常见的 Python 程序、配置标准依赖等）。**记录这些一次性成功的经验只会稀释经验库的信噪比**。

**触发条件**：仅当 Agent 在某个子任务上经历 $\geq k$ 次失败尝试后才解决时（$k$ 为可调超参，建议初始值 $k=3$），才触发经验提取。

**理论依据**：这与认知科学中的 "desirable difficulty" 理论一致——人类也主要从困难的、需要挣扎才解决的问题中形成持久记忆。

### Principle 2: 无固定流程，Agent 自主规划 (No Fixed Pipeline, Agent-Driven Planning)

**核心论断**：由于本项目面向的论文来自各个学科领域，不同论文之间的实验结构差异巨大，**不存在一个通用的、固定的复现流程**（如原方案中 S0→S1→S2→…→S5 的线性阶段划分）。

- 一篇计算物理论文的复现可能主要是数值求解器的实现 + 参数调优
- 一篇生物信息学论文可能涉及数据预处理管线 + 统计分析
- 一篇深度学习论文则可能需要模型搭建 + 训练 + 评估

**替代方案**：Agent 在阅读论文后**自主规划**复现步骤。随着经验库的积累，Agent 也可以参考同类论文的历史复现经验来制定更合理的策略。换言之，**合适的流程本身也是可以从 experience 中学习和演化的**。

### Principle 3: 无固定抽取模板 (No Fixed Extraction Schema)

**核心论断**：同理，由于领域多样性，**不存在一个统一的结构化信息抽取模板**（如原方案中固定的 `⟨Architecture, Loss, Dataset, Hyperparams, Training Protocol, Evaluation Metrics⟩` 六元组）。

- 对于 ML 论文，提取模型架构和训练超参数是关键
- 对于计算物理论文，提取物理方程、边界条件和数值方法是关键
- 对于统计分析论文，提取数据来源、统计模型和假设检验方法是关键

**替代方案**：Agent 根据论文内容自行判断需要关注和提取的关键信息。经验库同样可以帮助 Agent 学习"对于某类论文，通常需要关注哪些关键信息"。

### Principle 4: 全自动无标分类 (Zero Hand-crafted Taxonomy)

**放弃人工定义的 Tag 系统**。原因：

- 人工标签体系在经验库规模 < 100 时可能有效，但随着领域扩展，标签维护成本指数增长
- 标签边界模糊（一个关于"数值精度导致结果不稳定"的经验，应该归类为"数值方法"、"精度问题"还是"调试技巧"？）

**替代方案**：依赖高维稠密向量检索（Dense Retrieval）+ 动态 LLM 重排序（Reranking），让检索过程自适应地找到语义匹配的经验。

### Principle 5: 非破坏性保守融合 (Non-Destructive Conservative Fusion)

**绝不强制合并相似经验**。原因：

- 看似相似的两条经验可能在微妙的上下文条件下有不同的最优解
- 强行合并可能丢失关键的条件信息

**替代方案**：融合产物作为新的"假设"参与竞争，原始经验保留，由实际任务表现决定去留。

### Principle 6: 严格防污染检索 (Strict Anti-Pollution Retrieval)

**核心论断**：**宁可不给提示，也绝不给错误提示**。

**理论依据**：已有研究表明（Shi et al., 2023, "Large Language Models Can Be Easily Distracted by Irrelevant Context"），在 LLM 的上下文中注入无关信息会显著降低其推理准确率。对于代码生成任务，错误的经验提示可能引导 Agent 走向完全错误的实现路径，其破坏性远大于不提供任何提示。

---

## 四、 系统架构设计 (System Architecture)

### 4.1 整体架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Project Evolution–Reproduce                   │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Paper    │───>│  Agent       │───>│  Adaptive Task        │  │
│  │  Parser   │    │  Planner     │    │  Controller           │  │
│  │(PaddleOCR)│    │  (自主规划)   │    │  (动态编排)            │  │
│  └──────────┘    └──────────────┘    └───────┬───────────────┘  │
│                                              │                   │
│                     ┌────────────────────────┼──────────┐        │
│                     │      Iterative Loop     │          │        │
│                     ▼                        ▼          ▼        │
│              ┌─────────────┐  ┌──────────┐  ┌────────────┐      │
│              │  Experience  │  │ OpenHands │  │ Evaluation │      │
│              │  Retrieval   │─>│ CodeAct   │─>│ Judge      │      │
│              │  (2-Stage)   │  │  Agent    │  │ (动态指标)  │      │
│              └──────┬──────┘  └─────┬────┘  └─────┬──────┘      │
│                     │               │              │              │
│                     ▼               ▼              ▼              │
│              ┌──────────────────────────────────────────┐        │
│              │         Experience Memory System          │        │
│              │  ┌────────┐ ┌──────────┐ ┌───────────┐  │        │
│              │  │VectorDB│ │Score Mgr │ │Fusion Eng │  │        │
│              │  └────────┘ └──────────┘ └───────────┘  │        │
│              └──────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 论文解析管线 (Paper Parsing Pipeline)

#### 4.2.1 PDF → Markdown：基于 PaddleOCR PPStructureV3

本项目采用 **PaddleOCR PPStructureV3** 作为 PDF 到 Markdown 的转换工具。该方案已部署在独立的 Conda 环境 `paddle_env` 中。

**调用方式**：

```bash
# 通过独立的 paddle_env 环境调用 OCR 工具
/home/yjh/.conda/envs/paddle_env/bin/python run_ocr_tool.py \
    --pdf <论文PDF路径> \
    --output_dir <输出目录>
```

**核心实现**（`run_ocr_tool.py`）：

```python
from paddleocr import PPStructureV3

pipeline = PPStructureV3()
output = pipeline.predict(input=pdf_path)

# 拼接所有页面的 Markdown 文本
markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)

# 同时保存 Markdown 中引用的图片
for item in markdown_images:
    for path, image in item.items():
        image.save(output_path / path)
```

**选择 PaddleOCR 的理由**：
- 对公式、表格、图片的识别质量优秀，适合学术论文
- 支持端到端 PDF → Markdown 转换，保留文档结构
- 开源且可本地部署，无 API 成本

**输出产物**：高质量的 Markdown 文件 + 论文中图片的本地副本，供 Agent 后续阅读和理解。

#### 4.2.2 Agent 自主理解论文（无固定抽取模板）

**与原方案的关键区别**：我们**不使用固定的结构化抽取模板**。原方案定义了一个六元组 `⟨Architecture, Loss, Dataset, Hyperparams, Training Protocol, Evaluation Metrics⟩`，这仅适用于 ML/DL 论文。

**本方案的做法**：将 Markdown 格式的论文全文（或关键章节）直接提供给 Agent，由 Agent 自主完成以下任务：

1. **理解论文核心方法**：Agent 阅读论文后，用自己的理解总结实验方法
2. **识别复现所需的关键信息**：Agent 自行判断哪些信息是复现必需的（这因领域而异）
3. **标注缺失信息**：Agent 识别论文中未明确说明但对复现至关重要的细节
4. **制定复现计划**：Agent 自主规划复现步骤（无预设流程）

随着经验库的积累，Agent 在步骤 2-4 中可以参考历史经验来优化自己的策略。例如，经验库中可能积累了"复现计算物理论文时，通常需要特别关注边界条件的处理"这类元级经验。

#### 4.2.3 动态生成复现计划 (Dynamic Scaffolding: Checklist / DAG)

**核心思想**：虽然我们不预设死板的六元组或固定流程（见 Principle 2 & 3），但 Agent 在阅读完论文后，**必须先输出一个结构化的复现计划**，然后再开始编码。这个计划是 Agent 根据论文内容**动态生成**的（而非系统预设的），形式为 **Checklist** 或 **DAG（有向无环图）**。

**为什么需要 Dynamic Scaffolding？**

1. **降低迷失概率**：论文复现是长程任务（20-30+ 步迭代），Agent 极易在中途"忘记"原本的目标或跳过关键步骤。一个显式的 Checklist 提供了持续的导航锚点。
2. **天然的 Episode 切分边界**：Checklist 的每个节点对应一个独立子任务，为 Trajectory 的 Episode 分段（4.4.4 Step 2）提供了完美的、语义清晰的边界——无需完全依赖启发式规则。
3. **进度可观测**：系统可以随时检查 Checklist 的完成状态，判断 Agent 的进度是否正常（如是否在某个节点卡住过久）。
4. **经验库协同**：Checklist 生成时可以检索经验库中的"元经验"（同类论文的推荐复现策略），使计划更加合理。

**实现方式**：在 System Prompt 中强制要求 Agent 在开始编码前输出结构化计划：

```
MANDATORY FIRST STEP: After reading the paper, you MUST output a structured 
reproduction plan BEFORE writing any code. The plan should be a Checklist 
(or DAG if steps have complex dependencies) with the following format:

## Reproduction Plan
- [ ] Node 1: [Description of subtask, e.g., "Set up environment and install dependencies"]
  - Dependencies: none
  - Expected output: "All imports succeed without errors"
- [ ] Node 2: [Description of subtask, e.g., "Implement data loading and preprocessing"]
  - Dependencies: Node 1
  - Expected output: "Data loaded, shape (N, D) printed, sample visualized"
- [ ] Node 3: ...
  ...

Rules for the plan:
- Each node must have a clear, VERIFIABLE expected output (not vague goals)
- Mark dependencies between nodes explicitly
- The plan should cover: environment setup → data preparation → core method 
  implementation → training/execution → evaluation → metric comparison
  (but adapt to the specific paper — not all papers need all of these)
- You may revise the plan as you learn more during implementation

For EVERY subsequent action you take, you MUST indicate which Checklist 
node you are currently working on, using the format: [Working on: Node X]
```

**节点粒度指南**：
- 每个节点应对应 **3-8 步** OpenHands 操作（太细则 Checklist 臃肿，太粗则失去导航价值）
- 典型的论文复现 Checklist 包含 **5-12 个节点**
- 允许 Agent 在执行过程中动态修改计划（添加/删除/拆分节点），但必须显式声明修改

**与 Episode 分段的协同**：
- Checklist 节点切换自动成为 Episode 分段的**强信号**（优先级高于启发式规则）
- 当 Agent 声明 `[Working on: Node X]` 时，系统自动标记一个 Episode 边界
- 每个 Node 的完成/失败状态直接映射到经验提取的触发条件

### 4.3 OpenHands 执行环境（已部署）

#### 4.3.1 部署配置

OpenHands 已在本地完成部署（路径：`/home/yjh/OpenHands`），采用以下配置：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Runtime | `docker` / `conda-isolated` | **每任务独立隔离环境**（见 4.3.3） |
| Agent | `CodeActAgent` | 交替执行代码和自然语言推理 |
| LLM | `openai/cds/Claude-4.6-opus` | 通过 OpenAI 兼容网关调用 Claude 4.6 |
| Max Iterations | `30`（可调） | 每个任务的最大迭代次数 |
| Workspace | `/data/yjh/openhands_workspace` | 工作目录 |
| Trajectory 保存 | `/data/yjh/openhands_results_v2/trajectories` | 完整记录 Agent 操作轨迹 |
| GPU | 启用 (`enable_gpu = true`) | 沙盒内可访问 GPU |
| Browser | 禁用 | 论文复现任务不需要浏览器 |
| Jupyter | 启用 | 支持交互式代码执行 |
| Editor | 启用 | 支持代码编辑 |
| Sandbox Timeout | 600s | 单次执行超时 |

#### 4.3.2 GPU 资源约束

**本项目的 GPU 资源限制为单卡**。这一约束是合理的，因为：

- 我们默认所选论文的实验**不需要大量算力**即可复现
- 大部分学术论文（尤其是非 DL 领域）的实验本身就在单卡甚至 CPU 上完成
- 对于确实需要多卡的论文（如大规模分布式训练），不在本项目的初期范围内

这也意味着在论文选择时，需要筛选出**单卡可复现**的论文作为 benchmark。

#### 4.3.3 强制任务隔离 (Mandatory Per-Task Sandbox Isolation)

**核心原则**：每一个复现任务**必须**在独立的、隔离的执行环境中运行。任务之间**绝不共享** Python 环境、系统级依赖或工作目录状态。

**为什么必须隔离？**

1. **依赖冲突**：不同论文可能需要互相冲突的依赖版本（如论文 A 需要 `torch==1.13` + `numpy<1.24`，论文 B 需要 `torch==2.1` + `numpy>=1.26`）。共享环境会导致隐蔽的版本冲突 bug，极难调试。
2. **状态泄露**：前一个任务遗留的文件（中间产物、缓存、配置文件）可能干扰后续任务。例如，前一个任务创建的 `config.yaml` 可能被后续 Agent 误读。
3. **可复现性**：隔离环境确保每个任务从**干净状态**开始，使实验结果可复现。如果任务共享环境，则结果可能依赖于任务执行顺序——这是科学实验的大忌。
4. **失败隔离**：一个任务中 Agent 的"破坏性操作"（如 `pip uninstall numpy`、误删系统文件）不会影响其他任务。

**两种隔离方案**：

| 方案 | 实现方式 | 优势 | 劣势 | 适用场景 |
|------|---------|------|------|---------|
| **方案 A: Docker Container** | 每个任务启动一个独立的 Docker 容器，基于预构建的基础镜像 | 完全隔离（文件系统 + 网络 + 进程）；可精确快照和回滚；安全性高 | 启动开销较大（~5-15s）；需要 Docker 守护进程；GPU 透传需配置 `nvidia-docker` | 生产环境、需要严格隔离的场景 |
| **方案 B: 独立 Conda Env** | 每个任务创建一个独立的 Conda 环境（`conda create -n task_xxx python=3.10`），任务结束后销毁 | 启动快（~3-5s）；GPU 天然可用；无需额外基础设施 | 仅隔离 Python 依赖，不隔离文件系统和系统级包；隔离度不如 Docker | 开发调试阶段、资源受限的场景 |

**当前推荐策略**：**方案 B（独立 Conda Env）作为默认方案**，方案 A（Docker）作为可选升级路径。理由：
- 当前部署环境已有完善的 Conda 基础设施
- 论文复现任务的主要冲突来源是 Python 依赖版本，Conda 隔离已足够覆盖 > 90% 的场景
- 文件系统隔离通过为每个任务分配独立的工作目录（`/data/yjh/openhands_workspace/task_{id}/`）来实现

**Conda 隔离的具体实现**：

```python
# 任务开始前：创建隔离环境
def setup_task_sandbox(task_id: str, python_version: str = "3.10"):
    env_name = f"task_{task_id}"
    workspace = f"/data/yjh/openhands_workspace/task_{task_id}"
    
    # 1. 创建独立 Conda 环境
    subprocess.run([
        "conda", "create", "-n", env_name, 
        f"python={python_version}", "-y", "--quiet"
    ], check=True)
    
    # 2. 创建独立工作目录
    os.makedirs(workspace, exist_ok=True)
    
    # 3. 返回环境配置
    return {
        "conda_env": env_name,
        "workspace": workspace,
        "python_bin": f"/home/yjh/.conda/envs/{env_name}/bin/python"
    }

# 任务结束后：清理隔离环境
def teardown_task_sandbox(task_id: str):
    env_name = f"task_{task_id}"
    workspace = f"/data/yjh/openhands_workspace/task_{task_id}"
    
    # 1. 删除 Conda 环境
    subprocess.run(["conda", "env", "remove", "-n", env_name, "-y"], check=True)
    
    # 2. 归档工作目录（保留产物用于经验提取，但不影响后续任务）
    shutil.move(workspace, f"/data/yjh/openhands_archive/task_{task_id}")
```

### 4.4 经验触发与提取机制 (Experience Trigger & Extraction)

#### 4.4.1 三种探索结局与记录策略

| 结局类型 | 定义 | 是否触发经验提取 |
|---------|------|----------------|
| **A: 挣扎后成功** | Agent 经历 $\geq k$ 次失败后最终解决问题 | ✅ 触发（核心场景） |
| **B: 一次性成功** | Agent 首次尝试或少于 $k$ 次失败就解决 | ❌ 不触发（LLM 基础能力已覆盖） |
| **C: 彻底失败** | Agent 耗尽迭代次数仍未解决 | ✅ 触发，记录为 `[Negative Constraint]` |

##### Trivial Failure SKIP Rule（瞬时错误/低级失误过滤）

并非所有失败都值得记录。以下"低级失误"类失败即使满足 $\geq k$ 次的触发条件，也应被**跳过**（SKIP）：

- **拼写错误**（typo）导致的反复失败
- **简单语法错误**（missing colon, unmatched parenthesis）
- **文件路径不存在**（Agent 忘记先创建目录）

这些情况由 LLM 在经验提取阶段判断（见 4.4.4 Step 4 的 SKIP 机制）。

##### Silent Bug Detection（静默错误检测）

**核心洞察**：传统的"Agent 遇到报错 → 调试"循环只能捕获**显式错误**（Exception）。但论文复现中，更危险的是**静默错误**——代码顺利运行，但产出的结果是错误的（如 Loss 不收敛、Accuracy 为随机水平、数值结果偏差数个数量级）。

| Symptom 类型 | 检测方式 | 示例 |
|-------------|---------|------|
| **Exception Symptom** (传统) | 程序抛出 Error/Traceback | `RuntimeError`, `ValueError`, etc. |
| **Metric Anomaly Symptom** (新增) | 代码无报错但输出指标与论文报告值差异超过阈值 | Loss 不收敛（100 epochs 后仍 > 10.0）；Accuracy 为 0% 或接近随机 |
| **Output Shape/Type Anomaly** (新增) | 输出数据的形状、类型或数量级与预期不符 | 预期输出 shape (N, 3) 实际得到 (N, 1)；预期浮点数得到全零 |
| **NaN/Inf Symptom** (新增) | 计算过程中出现 NaN 或 Inf | `Loss: nan`；梯度爆炸 |

**检测机制**：在 System Prompt 中明确要求 Agent 在每步执行后进行 **Sanity Check**：

```
CRITICAL RULE: After every code execution, you MUST perform a sanity check:
- If the code ran without errors, check whether the output values are 
  reasonable (correct magnitude, no NaN/Inf, expected shape).
- If a metric (loss, accuracy, error, etc.) deviates from the paper's 
  reported value by more than an order of magnitude, treat this as a 
  SILENT BUG and investigate the root cause before proceeding.
- A "successful run" with nonsensical output is NOT success — it is a 
  silent failure that requires debugging.
```

**经验提取触发**：当 Agent 发现并修复了一个 Silent Bug 后（经历 $\geq k$ 次调试迭代），系统同样触发经验提取。此时 `condition.error_or_symptom` 字段记录的不是 Exception，而是 Metric Anomaly 的描述。例如：

```json
{
  "condition": {
    "error_or_symptom": "Code runs without errors but loss does not converge after 100 epochs (stays > 10.0 while paper reports final loss ~0.01)",
    "task_context": "Training a neural PDE solver for Burgers equation"
  },
  "action": {
    "solution": "Input data was not normalized; the PDE solution values ranged [0, 1000] but the network expected [-1, 1]. Added min-max normalization before training."
  }
}
```

#### 4.4.2 经验数据结构 (Experience Schema)

```json
{
  "id": "exp_20250315_001",
  "type": "positive | negative",
  "domain_hint": "computational_physics | bioinformatics | deep_learning | ...",
  "condition": {
    "error_or_symptom": "RuntimeError: singular matrix encountered in np.linalg.solve",
    "task_context": "Implementing a finite element solver for 2D heat equation",
    "environment": "Python 3.10, NumPy 1.24, SciPy 1.11",
    "failed_attempts_summary": [
      "Tried direct inversion → singular matrix",
      "Tried adding small epsilon to diagonal → results diverged"
    ]
  },
  "action": {
    "solution": "Use scipy.sparse.linalg.spsolve with sparse CSR matrix instead of dense solver; add Dirichlet BC before assembly to avoid singularity",
    "code_implement": "... ",
    "verification": "Solver converges, L2 error < 1e-6 vs analytical solution"
  },
  "rationale": "Dense solver fails because the stiffness matrix is singular without proper boundary conditions; sparse solver with pre-applied BCs avoids the issue and is also more memory efficient",
  "metadata": {
    "source_paper": "arxiv:2401.xxxxx",
    "creation_time": "2025-03-15T10:30:00Z",
    "score": 5.0,
    "call_count": 0,
    "success_count": 0,
    "last_used": null,
    "lineage": null
  }
}
```

**设计要点**：

1. **`domain_hint` 字段**：由 Agent 自动标注的领域提示（非严格分类），辅助检索时的相关性判断
2. **`rationale` 字段不注入上下文**：仅在经验生成时用于质量检查、在融合时用于理解，检索注入时只使用 `condition` 和 `action`
3. **`failed_attempts_summary`**：记录失败尝试的摘要，供未来 Agent 避免重走老路
4. **`lineage`**：记录该经验是否由融合产生（指向父经验 ID），用于追溯和审计
5. **无 `stage` 字段**：由于不存在固定阶段划分，改为依赖语义检索匹配

#### Schema 设计中的关键取舍与开放问题 (Design Tradeoffs & Open Questions)

经验 Schema 的设计远非 trivial，其中涉及多个需要反复权衡的维度。以下逐一讨论我们面临的关键抉择，以及当前的倾向性判断（部分问题可能需要通过实验才能最终定论）：

**取舍 1：经验粒度——原子问题-解决方案 vs 工作流模式**

| 粒度层次 | 示例 | 优势 | 劣势 |
|---------|------|------|------|
| **原子级 (Atomic)** | "遇到 `CUDA OOM` → 减小 batch size 或用 gradient checkpointing" | 检索精准度高；context 占用小；复用性强 | 丢失了问题出现的宏观上下文；无法表达"先做 A 再做 B"的时序依赖 |
| **工作流级 (Workflow)** | "复现 FEM 论文的完整流程：先定义 mesh → 组装刚度矩阵 → 施加边界条件 → 求解 → 后处理" | 保留了步骤间的因果与时序关系；对新手 Agent 更有指导性 | 检索匹配困难（query 通常是单个错误，而非完整流程）；context 占用大；跨领域迁移性差 |
| **中间级 (Episode)** | "在组装刚度矩阵阶段，如果遇到奇异矩阵 → 检查是否遗漏了边界条件的施加" | 平衡了精准度和上下文信息 | 需要合理的分段策略（见 4.4.4 节） |

**当前倾向**：以**原子级**为主体，辅以少量**工作流级**的"元经验"（meta-experience）。元经验不直接解决具体错误，而是描述"复现某类论文的推荐策略"，在任务初期由 Agent 主动检索参考。原子级经验则在遇到具体问题时被动触发。两者分别服务于 Agent 的"规划"和"执行"阶段。

**取舍 2：代码表示——完整 `code_implement` vs 自然语言描述 vs 混合方案**

| 表示方式 | 优势 | 劣势 |
|---------|------|------|
| **完整 `code_implement`** | 精确无歧义；Agent 可直接复用 | Token 占用大（一个 diff 可能 200+ tokens）；与具体代码结构强耦合，跨项目迁移性差；容易过拟合到特定上下文 |
| **纯自然语言 `solution`** | 紧凑（通常 50-100 tokens）；抽象程度高，迁移性强 | 可能遗漏关键实现细节；LLM 需要"翻译"回代码，增加出错概率 |
| **混合方案：自然语言 + 关键代码片段** | 兼顾紧凑性和精确性 | 需要判断哪些代码值得保留（这本身就需要 LLM 的判断） |

**当前倾向**：采用**混合方案**。`action.solution` 字段用自然语言描述解决策略（必选），`action.code_implement` 字段保留关键代码变更（可选，仅当代码变更的核心逻辑在 5 行以内时才记录完整 diff；否则记录伪代码或关键 API 调用）。这样做的理由是：

- 检索注入时优先使用 `solution`（自然语言），保持 context 紧凑
- 当 Agent 明确需要代码参考时，再展开 `code_implement`
- 限制 diff 长度也是一种隐式的"信息量筛选"——如果一个修复需要大量代码变更，说明它可能过于特定，不适合作为可迁移的经验

**取舍 3：Context Window 预算——经验条目的尺寸控制**

经验注入是与 Agent 的主 prompt 竞争 context window 的。在 Claude 4.6 Opus 的 200K context 下，理论上空间充裕，但实际上论文 Markdown 本身就可能占 30K-80K tokens，加上代码、执行输出等，留给经验注入的空间有限。

**预算约束设计**：
- 单条经验注入的 token 上限：**500 tokens**（包含 condition + action，不含 rationale）
- 单次检索注入的总 token 上限：**1500 tokens**（即最多注入 3 条简洁经验，或 1-2 条详细经验）
- 如果经验本身超出 500 tokens，触发**自动摘要**：LLM 将其压缩为 500 tokens 以内的精华版本

**关键观察**：这一约束反过来也指导了经验的写入质量——如果一条经验无法在 500 tokens 内清晰描述 condition 和 action，说明它可能需要被分拆为多条更原子化的经验。

**取舍 4：领域通用性 vs 领域特异性**

一个关于 "NumPy 广播规则导致 shape mismatch" 的经验，在 ML、科学计算、信号处理等多个领域都可能有用。但一个关于 "分子动力学中 Lennard-Jones 势的截断半径选择" 的经验，仅在特定领域有价值。

| 经验类型 | 跨领域迁移性 | 经验库中的期望占比 | 策略 |
|---------|-------------|-----------------|------|
| **工具/环境类**（pip 安装问题、版本兼容、CUDA 配置等） | 极高 | ~30% | 无需 `domain_hint` 过滤 |
| **通用编程类**（数据结构、算法 bug、数值精度等） | 高 | ~40% | `domain_hint` 作为弱信号 |
| **领域特定类**（特定物理方程、特定 ML 架构 trick 等） | 低 | ~30% | `domain_hint` 作为强过滤信号 |

**设计决策**：`domain_hint` 在检索时不作为硬过滤条件（避免遗漏跨领域可用的经验），而是作为 Reranker 的参考信号之一。Reranker 可以自主判断一条"标注为 ML"的经验是否对当前的科学计算任务同样适用。

**取舍 5：环境版本信息的时效性**

`condition.environment` 字段记录了 "Python 3.10, NumPy 1.24" 等版本信息。但随着时间推移，这些版本会过时。一条在 "NumPy 1.24" 上有效的经验，在 "NumPy 2.0" 上可能因 API 变更而失效。

**问题**：是否需要经验的"版本保鲜"机制？

**当前策略**（保守）：
- `environment` 字段照常记录，供 Reranker 参考
- Reranker 在判断时会检查版本兼容性（判断标准第 3 条已包含此项）
- **不主动更新**旧经验的版本信息——如果旧经验因版本不匹配被反复判定为 `IRRELEVANT`，其 score 自然衰减直至淘汰
- 如果同一问题在新版本下有新解法，会被作为新经验录入，与旧经验形成自然竞争

**未来改进方向**：可考虑定期对 Silver 层经验做"版本兼容性审计"，自动检测其引用的 API 是否在当前主流版本中仍然有效。

**取舍 6：是否记录 Agent 的"推理链"（Chain of Thought）**

Agent 在解决问题时的推理过程（"我看到这个错误，猜测原因可能是 X，先尝试 Y..."）包含丰富的元认知信息。是否应该作为经验的一部分记录？

| 选项 | 优势 | 劣势 |
|------|------|------|
| **记录完整 CoT** | 帮助未来 Agent 理解"为什么这个解法有效" | Token 占用巨大（通常 1000+ tokens）；含大量噪音（犹豫、错误推理、回溯） |
| **不记录 CoT** | 经验精简；检索匹配更纯粹 | 失去了"思路"信息，只有"答案" |
| **记录 CoT 摘要** | 保留关键推理步骤，过滤噪音 | 摘要质量依赖 LLM |

**当前倾向**：CoT 的精华已被 `rationale` 字段承载（记录"为什么这个方案有效"的核心理由），无需额外存储完整 CoT。完整 CoT 保存在原始 Trajectory 文件中，仅在需要时回溯。

#### 4.4.3 提取质量控制 (Extraction Quality Gate)

经验提取不是自动存入，而是经过一个**质量验证步骤**：

1. **自动提取**：LLM 从 Agent 的完整 trajectory 中提取候选经验
2. **自洽性检查**：另一个 LLM 调用验证 `condition → action` 的逻辑是否自洽
3. **去重检查**：与经验库中已有条目做向量相似度检查，如果相似度 > 0.95，标记为潜在重复，交由融合模块处理
4. **最小信息量检查**：如果 `action` 过于通用（如 "检查代码"、"重新运行"），拒绝录入

#### 4.4.4 从 Trajectory 到 Experience 的提取管线 (Trajectory-to-Experience Extraction Pipeline)

经验提取的质量**根本性地取决于输入 trajectory 的质量**。OpenHands 记录的原始 trajectory 通常是一个冗长、含噪的 JSON 序列（一次论文复现任务可能包含 20-30 个迭代步骤，每步包含 Agent 的思考、代码编写、执行输出等），直接将其交给 LLM 提取经验，面临以下困难：

- **长度问题**：原始 trajectory 可能超过 50K tokens，超出单次 LLM 调用的有效处理范围
- **噪音问题**：大量"尝试 → 失败 → 换个方向再试"的来回反复，干扰 LLM 对核心问题-解决方案的识别
- **边界问题**：多个子任务交织在一起，难以判断某段 trajectory 属于哪个问题的解决过程

因此，我们需要一个**结构化的预处理管线**，将原始 trajectory 转化为干净、可提取的形式。

##### Step 1: Trajectory 结构化解析 (Structural Parsing)

OpenHands 的 trajectory 以 JSON 格式存储在 `/data/yjh/openhands_results_v2/trajectories` 中。每个 trajectory 包含一系列 `(observation, action)` 对。首先进行结构化解析：

```python
# 每个 trajectory 步骤被解析为标准化的 Step 对象
@dataclass
class TrajectoryStep:
    step_id: int
    action_type: str          # "code_execute" | "file_edit" | "terminal_cmd" | "think"
    action_content: str       # Agent 执行的具体内容
    observation: str          # 执行结果（stdout/stderr/file content）
    has_error: bool           # 该步骤是否产生了错误
    error_type: str | None    # 错误分类（ImportError, RuntimeError, ValueError, ...）
    timestamp: float
```

**关键处理**：对 `observation` 进行截断和清洗——移除冗余的 stack trace 重复帧、过长的数据输出（如打印了整个数据集）、ANSI 转义序列等。保留**最后 20 行**的错误输出，通常足以定位问题。

##### Step 2: 语义分段——识别 Episode 边界 (Episode Segmentation)

一个完整的 trajectory 包含多个"子任务"的解决过程。我们需要将其分割为独立的 **Episode**（情节），每个 Episode 对应一个独立的问题-解决尝试。

**分段策略：基于"意图转变"的启发式规则**

| 分段信号 | 检测方法 | 示例 |
|---------|---------|------|
| **Agent 明确声明新目标** | 正则匹配 Agent 思考内容中的目标切换关键词 | "Now let me move on to...", "Next, I need to..." |
| **错误类型突变** | 连续两步的 `error_type` 完全不同且不是同一 call stack | 从 `ImportError` 跳到 `ValueError` |
| **文件操作对象变化** | 连续步骤编辑/创建的文件发生变化 | 从编辑 `model.py` 转到编辑 `data_loader.py` |
| **长时间的 "think" 行动** | Agent 发出不含代码的纯推理步骤 | 重新审视问题、规划下一阶段 |

**混合分段方法**：

1. **规则初筛**：基于上述启发式规则进行初步分段
2. **LLM 精调**（可选，对于复杂 trajectory）：将规则分段结果交给 LLM 验证和修正边界

```
Below is the operation log of an AI Agent, which has been preliminarily
segmented into several Episodes.
Please verify whether the segmentation is reasonable:
- Does each Episode correspond to an independent subtask?
- Are there any steps that should not be separated but were incorrectly split?
- Are there multiple problems mixed within the same Episode?

Please output the corrected Episode boundaries.
```

##### Step 3: Episode 去噪——提取核心叙事 (Episode Denoising)

单个 Episode 内部仍可能包含大量噪音。一个典型的"挣扎后成功"的 Episode 可能如下：

```
尝试1: 用方法A → 报错X
尝试2: 还是用方法A，微调参数 → 还是报错X        ← 冗余
尝试3: 换方法B → 报错Y（新错误，有进展）
尝试4: 在方法B基础上修bug → 报错Y的变种        ← 冗余
尝试5: 完全换思路，用方法C → 成功                ← 核心转折
```

**去噪规则**：

| 噪音模式 | 检测方法 | 处理方式 |
|---------|---------|---------|
| **重复失败**（相同错误、微小变化） | 相邻步骤的 `error_type` 相同且 `action_content` 的编辑距离 < 20% | 仅保留首次和末次尝试，中间步骤压缩为 "尝试了 N 次类似方案，均失败" |
| **探索性死胡同**（尝试后完全回退） | Agent 先修改文件，后来又 revert 或删除该修改 | 压缩为 "尝试了方法 X 但效果不好，已回退" |
| **冗长输出**（打印大量数据/日志） | `observation` 长度 > 2000 字符 | 截断至最后 500 字符 + 前 200 字符（保留开头和结尾） |
| **环境探索**（ls、cat、pip list 等信息收集操作） | `action_type` 为信息查询类 | 合并为 "Agent 检查了环境/文件状态" |

**去噪后的 Episode 应满足**：
- 总长度 < 3000 tokens
- 清晰的三段结构：**问题描述** → **失败尝试概要** → **最终解决方案**

##### Step 4: LLM 驱动的经验提取 (LLM-Driven Experience Extraction)

将去噪后的 Episode 交给 LLM，按照 Experience Schema（见 4.4.2）提取结构化经验。

**提取 Prompt 设计**：

```
你是一个经验提取专家。以下是一个 AI 编程 Agent 在复现论文过程中
解决某个具体问题的操作记录（已去噪）。

请从中提取一条结构化经验，格式如下：

【Episode 记录】
{denoised_episode}

【论文信息】
{paper_title, paper_domain}

请提取：
1. condition.error_or_symptom: 核心错误或症状的一句话描述
2. condition.task_context: Agent 当时在做什么（一句话）
3. condition.environment: 涉及的关键库和版本
4. condition.failed_attempts_summary: 失败尝试的列表（每条一句话）
5. action.solution: 最终解决方案（2-3句话，侧重"做了什么"而非"为什么"）
6. action.code_implement: 关键代码（如果核心变更在5行以内则给出；否则给出伪代码）
7. action.verification: 如何验证解决方案有效
8. rationale: 为什么这个方案有效（1-2句话，解释根本原因）
9. domain_hint: 最匹配的领域标签

【质量要求】
- condition 和 action 必须足够具体，能让另一个不了解上下文的 Agent 理解并应用
- 如果你认为这个 Episode 不包含值得记录的经验（例如问题太 trivial，
  或解决方案过于特定无法迁移），请输出 SKIP 并说明理由
- solution 中不要包含论文特定的变量名或文件名，使用通用描述
```

**关键设计决策**：

1. **`SKIP` 机制**：即使 Episode 满足了失败次数的硬触发条件（$\geq k$ 次失败），LLM 仍可判断其不值得记录。这是一个**软过滤层**，弥补硬规则的不足。例如，Agent 因为拼写错误反复失败 3 次，虽然满足 $k=3$ 的触发条件，但 LLM 会判断这不是一条有价值的经验。

2. **通用化要求**：Prompt 明确要求 LLM 将解决方案从具体论文的上下文中"解耦"出来——使用通用描述而非论文特定的变量名/文件名。这是保障经验**跨任务迁移性**的关键。

3. **单 Episode 单经验**：每个 Episode 最多提取一条经验。如果一个 Episode 中包含多个独立的问题-解决对，应在 Step 2 中被分为多个 Episode。

##### Step 5: 提取后验证与入库 (Post-Extraction Validation)

LLM 提取的候选经验还需经过 4.4.3 中描述的质量门控：

```
Episode 原始日志
      │
      ▼
[Step 1] 结构化解析 → TrajectoryStep 序列
      │
      ▼
[Step 2] Episode 分段 → 独立 Episode 列表
      │
      ▼
[Step 3] Episode 去噪 → 精简 Episode（< 3000 tokens）
      │
      ▼
[Step 4] LLM 提取 → 候选 Experience（或 SKIP）
      │
      ▼
[Step 5] 质量门控
      ├── 自洽性检查 ✓
      ├── 去重检查 ✓（相似度 < 0.95）
      ├── 最小信息量检查 ✓
      │
      ▼
  写入 Experience DB
```

##### 关于 Trajectory 构造的工程优化

**问题**：OpenHands 默认的 `max_iterations = 30`，对于复杂论文可能不够，但盲目增大迭代次数会导致 trajectory 过长（100+ 步），极大增加噪音和处理成本。

**优化策略**：

1. **分阶段执行**：将长任务拆分为多个独立的 OpenHands session（如 "环境配置"、"核心代码实现"、"调试运行"），每个 session 产生独立的、更短的 trajectory。系统在 session 之间保存工作目录状态。

2. **Agent 自主 checkpoint**：在 System Prompt 中引导 Agent 定期输出结构化的 checkpoint 信息（当前进度、已完成的步骤、遇到的问题），这些 checkpoint 自然成为 Episode 的分段标记。

3. **增量式 trajectory 写入**：不等整个任务结束才处理 trajectory，而是在 Agent 每解决一个子问题时就实时判断是否满足经验提取条件。这避免了"一次性处理超长 trajectory"的问题，也使经验能在同一个任务的后续步骤中就被利用。

### 4.5 探索感知的两阶段检索 (Exploration-Aware Two-Stage Retrieval)

**核心思想：早期放宽，晚期收紧（Early Relaxation, Late Strictness）**

Agent 在处理一个复现任务时，存在一个从"探索"到"利用"的自然过渡。在任务的不同阶段，经验检索应采取不同的策略：

| 任务阶段 | Retrieval 策略 | 理由 |
|---------|---------------|------|
| **Early Stage**（前 1/3 迭代） | **放宽 Reranker 标准**：接受 `PARTIAL` 经验；注入更多候选（Top-3~5）；降低相似度阈值 | 任务初期 Agent 对问题理解不深，宽泛的经验提示有助于**发散探索**，避免过早陷入局部最优 |
| **Mid Stage**（中 1/3 迭代） | **标准模式**：正常的 Two-Stage 检索 | 平衡探索与利用 |
| **Late Stage**（后 1/3 迭代） | **严格过滤**：仅接受 `RELEVANT` 经验；最多注入 1 条；提高相似度阈值 | 任务后期 Agent 已对问题有较深理解，此时不相关的经验噪音危害更大；需要**精确制导** |

**直觉解释**：这类似于强化学习中的 $\epsilon$-greedy 策略——探索率随训练推进而衰减。在 Agent 的单次任务生命周期内，检索策略从"广撒网"逐渐收敛到"精准匹配"。

**实现方式**：通过 `exploration_ratio = (max_iterations - current_iteration) / max_iterations` 动态调整以下参数：
- Reranker 的接受阈值（early: `PARTIAL` 也接受 → late: 仅 `RELEVANT`）
- 注入经验的最大条数（early: 3~5 条 → late: 0~1 条）
- 向量检索的相似度下限（early: 0.7 → late: 0.9）

#### 4.5.1 Stage 1: 语义召回 (Dense Retrieval)

**查询构造**：

```python
query = f"""
[Error/Symptom]: {error_traceback_or_symptom}
[Task Context]: {what_agent_is_trying_to_do}
[Domain]: {domain_hint}
[Recent Code]: {last_modified_code_snippet}  # 限制在 500 tokens 以内
[Failed Attempts]: {list_of_what_was_tried}
"""
```

**检索策略**：

- 使用 Embedding 模型（推荐：`text-embedding-3-large` 或开源 `bge-large-en-v1.5`）编码 query
- 在 VectorDB 中检索 Top-$K_1$ 候选（$K_1 = 10$）
- **负经验（Negative Constraint）也参与检索**，且在 Reranker 阶段被特殊处理

#### 4.5.2 Stage 2: LLM Reranker (Precision Filter)

**设计目标**：从 $K_1 = 10$ 个候选中精确筛选出 0-2 条直接适用的经验。

**Reranker Prompt 设计**（关键，需严格控制）：

```
你是一个经验相关性判断专家。以下是一个 AI 编程 Agent 当前遇到的问题，
以及从经验库中检索到的若干候选经验。

【当前问题描述】
{query}

【候选经验列表】
{experiences_with_ids}

请逐条判断每个经验是否 **直接适用于** 当前问题。
判断标准（必须同时满足）：
1. 该经验的 Condition 与当前问题的 **根本原因** 相同（而非仅表面症状相似）
2. 该经验的 Action 可以 **直接应用或稍作改动即可应用** 于当前场景
3. 该经验与当前的 **技术栈版本、运行环境** 不存在冲突

对于每条经验，输出：
- RELEVANT: 直接适用，应注入
- PARTIAL: 有一定参考价值但不完全匹配，可作为灵感
- IRRELEVANT: 不适用，不应注入

如果所有经验都不直接适用，请输出 NONE。
宁可输出 NONE 也不要勉强注入不确定的经验。
```

**注入策略**：

- `RELEVANT`：完整注入 `condition` + `action`（不含 `rationale`）
- `PARTIAL`：仅注入 `action` 作为 "可能有参考价值的提示"，并加上 disclaimer
- `IRRELEVANT` / `NONE`：不注入任何内容
- **Negative Constraint injection is special**: Injected as "WARNING: The following approach has been verified as ineffective", guiding the Agent to avoid known dead ends

#### 4.5.4 Experience Gap Marking (经验缺口标记机制)

**Problem**: When the Reranker returns `NONE` (no relevant experiences found), this is a valuable signal — it indicates that the experience library has a **coverage gap** for this type of problem. If we ignore this signal, the system may repeatedly fail to provide help for similar future problems.

**Mechanism**: When retrieval returns `NONE`, the system records an **Experience Gap Marker**:

```json
{
  "type": "gap_marker",
  "query_snapshot": {
    "error_or_symptom": "...",
    "task_context": "...",
    "domain_hint": "..."
  },
  "task_id": "task_xxx",
  "iteration": 15,
  "timestamp": "2025-03-15T10:30:00Z",
  "resolved": false
}
```

**Post-Task Processing**: After the task completes, the system reviews all gap markers for that task:

| Scenario | Action |
|----------|--------|
| Gap marker's problem was **eventually solved** (after $\geq k$ failures) | Normal experience extraction applies — the resulting experience naturally fills the gap |
| Gap marker's problem was **eventually solved easily** (< $k$ failures) | The problem was within LLM's base capability; no experience needed — **remove gap marker** |
| Gap marker's problem was **never solved** (task failed) | Record as `[Negative Constraint]` with high priority; flag this problem category for manual review or targeted experience seeding |

**Why this is better than always forcing experience generation**:
- Not every `NONE` result means we need a new experience — sometimes the LLM handles it fine without help
- The gap marker only triggers experience generation when the gap actually caused difficulty (failure-driven, consistent with Principle 1)
- Gap markers that accumulate across multiple tasks for the same problem category signal **systematic coverage holes**, which can inform targeted experience seeding or even manual experience authoring

**Periodic Gap Analysis**: Every $N = 20$ tasks, the system runs a gap analysis:
1. Cluster all unresolved gap markers by semantic similarity
2. Identify the top-5 most frequent gap clusters
3. These represent the highest-priority areas where the experience library needs expansion
4. Output a structured report for human review (optional)

#### 4.5.5 Cost Control (成本控制)

**问题**：每次 Agent 遇到错误都调用 Reranker 的 LLM，成本会很高。

**解决方案**：分级触发

| 触发条件 | 检索策略 | 成本 |
|---------|---------|------|
| 首次遇到某类错误 | Stage 1 only（纯向量检索），如果相似度 > 0.9 直接注入 | 极低 |
| 同类错误第 2 次出现 | Stage 1 + Stage 2（加入 Reranker） | 中等 |
| 同类错误第 3+ 次出现 | Stage 1 + Stage 2 + 扩大召回范围至 $K_1 = 20$ | 较高 |
| Agent 主动请求 | 全量检索 | 最高 |

### 4.6 信用分配与分数机制 (Credit Assignment & Scoring)

#### 4.6.1 核心挑战

不能因为复现一篇极其困难的论文失败，就惩罚过程中被调用的经验。需要解耦**任务固有难度**和**经验质量**。

#### 4.6.2 难度评估 (Task Difficulty Estimation)

在每个任务开始前，由 LLM Judge 基于以下特征估计任务难度 $d \in [1.0, 5.0]$：

- **方法复杂度**：标准算法 (1.0) vs 高度定制化实现 (5.0)
- **数据可得性**：公开数据集 (1.0) vs 私有数据需模拟 (4.0)
- **关键信息完整度**：论文中有完整实验细节 (1.0) vs 大量关键细节未报告 (4.0)
- **计算规模**：轻量实验 (1.0) vs 需要大量计算资源 (5.0)
- **复现先例**：已有多个成功复现 (1.0) vs 无人成功复现过 (5.0)
- **领域专业性**：通用 Python 编程 (1.0) vs 需要深厚领域知识 (5.0)

##### 幻觉风险与缓解 (Hallucination Risk & Mitigation)

**已知问题**：LLM 对论文难度的估计可能存在显著偏差（幻觉），尤其是：
- LLM 可能**高估**自己熟悉的领域（如 ML）的难度，因为它"知道这些问题的复杂性"
- LLM 可能**低估**不熟悉的领域（如计算物理、生物信息学）的难度，因为它"不知道自己不知道什么"
- 部分评估维度（如"复现先例"）需要 LLM 具备事实性知识，而这恰恰是幻觉的高发区

**缓解策略**：

1. **多维度独立评估 + 聚合**：要求 LLM 对上述 6 个维度分别打分（而非给出一个综合分数），然后取加权平均。这比直接要求一个综合判断更可靠，因为每个维度的判断更局部、更可验证。

2. **事后校准 (Post-hoc Calibration)**：在积累了足够多的任务数据后（~30 篇论文），对比 LLM 预估难度 $d_{\text{pred}}$ 与实际难度 $d_{\text{actual}}$（由 Agent 实际消耗的迭代次数反推），拟合一个校准函数 $d_{\text{calibrated}} = f(d_{\text{pred}})$。后续任务使用校准后的难度值。

3. **容错设计**：难度评估仅用于**调节信用分配的幅度**（见 4.6.3），而非用于二元决策（如"是否尝试这篇论文"）。因此，即使难度估计有 ±1.0 的偏差，对系统整体行为的影响也是渐进的而非灾难性的。在最坏情况下，一条优秀经验因为难度被低估而少获得一些奖励分，但不会被错误淘汰。

4. **人工 Ground Truth 锚点**：在 ReproduceBench 构建阶段，为每篇论文人工标注难度 ground truth（由领域专家评估）。这既用于校准 LLM Judge，也用于在消融实验中对比"LLM 估计难度 vs 人工标注难度"对信用分配的影响。

#### 4.6.3 分数更新公式 (Score Update Formula)

设经验 $e$ 在难度为 $d$ 的任务中被调用，结果为 $o \in \{\text{success}, \text{partial}, \text{failure}\}$：

$$\text{Score}(e) \leftarrow \text{Score}(e) + \alpha \cdot R(o, d)$$

其中奖励函数 $R$ 定义为：

| 结果 $o$ | 奖励 $R(o, d)$ | 直觉解释 |
|---------|-----------------|---------|
| `success` | $+\beta_1 \cdot d$ | 在越难的任务中成功，奖励越大 |
| `partial` | $+\beta_2 \cdot d$ | 虽未完全解决但推进了进展 |
| `failure` | $-\gamma / d$ | 在越简单的任务中失败，惩罚越大 |

建议初始超参：$\alpha = 0.3$，$\beta_1 = 2.0$，$\beta_2 = 0.5$，$\gamma = 3.0$。

#### 4.6.4 成功/失败的判定 (Outcome Determination)

经验被调用后，如何判断它是否"帮助"了当前子任务？这是信用分配中**最关键也最容易出错**的环节——一个看似简单的问题实际上充满了边界情况。

##### 基本判定规则

| 结果 | 判定条件 | 标签 |
|------|---------|------|
| **直接成功** | 经验注入后，Agent 在接下来的 $W=2$ 步内解决了该子问题，**且输出结果通过合理性验证**（见下方"成功的度量验证"） | `success` |
| **向前推进** | 经验注入后，Agent 的错误**类型发生了变化**（从 Error A → Error B），表明原问题已解决但暴露了新问题 | `partial` |
| **无效** | 经验注入后 $W$ 步内，Agent 仍然遇到**相同类型**的错误 | `failure` |
| **回归有害** | 经验注入后出现了**之前没有过**的新错误，且该错误可追溯到经验建议的修改 | `failure` (加重惩罚) |

##### "向前推进" vs "回归错误" 的区分

这是判定中最困难的部分。考虑以下场景：

> 经验建议 Agent 将 `np.linalg.solve` 改为 `scipy.sparse.linalg.spsolve`。修改后：
> - 情况 A：`LinAlgError: singular matrix` 消失了，但出现 `ValueError: dimension mismatch` → 这是**向前推进**（原问题已解决，新问题是下一步的自然障碍）
> - 情况 B：`LinAlgError: singular matrix` 消失了，但出现 `ImportError: scipy.sparse not found` → 这是**回归错误**（经验建议引入了环境不支持的依赖）

**区分逻辑（基于规则，无需 LLM）**：

1. **Error Fingerprint Matching**: 对每个错误提取指纹 `(error_type, error_message_hash, source_file, line_number)`。注入前后对比指纹。
2. **Causal Tracing**: 如果新错误出现在**经验建议修改的代码行或其直接调用链**上，则判定为回归；如果出现在**后续逻辑步骤**中，则判定为向前推进。
3. **Rollback Test** (optional, high cost): 系统自动回退经验建议的修改，检查新错误是否消失。如果消失，确认为回归。

##### 成功的度量验证 (Metric-Based Success Validation)

**核心原则**：仅仅"不再报那个具体的 Error"**不能**直接记为 `success`。只有当后续的执行结果（数值输出、Loss、指标等）**符合预期**时，才结算为真正的 `success`。

**理由**：消除一个 Error 只是必要条件而非充分条件。Agent 可能通过不正确的方式"修复"了错误（如 catch 并 suppress 异常、hardcode 返回值），导致代码表面上不再报错但实际行为完全错误。

**验证层次**（按优先级递减）：

| 验证层次 | 条件 | 判定 |
|---------|------|------|
| **L1: 指标对齐** | 输出指标与论文报告值的偏差 < 1 个数量级 | `success` |
| **L2: 合理性检查** | 无法对比论文值，但输出值在合理范围内（无 NaN/Inf、shape 正确、数量级合理） | `success` (provisional) |
| **L3: 仅错误消除** | Error 消失但无法验证输出合理性（如中间步骤无数值输出） | `partial`（而非 `success`） |
| **L4: 静默退化** | Error 消失但输出明显异常（全零、NaN、随机噪声等） | `failure`（静默 bug，见 4.4.1 Silent Bug Detection） |

**实现方式**：在 $W=2$ 步窗口结束时，系统自动检查最后一步的 `observation`：
1. 如果包含数值输出 → 与论文已知值（若有）对比，执行 L1 验证
2. 如果包含数值输出但无论文对照 → 执行 L2 合理性检查（无 NaN/Inf、shape 匹配、数量级合理）
3. 如果无数值输出 → 降级为 `partial`，仅记录"错误消除"

##### 观察窗口 $W$ 的选择

$W = 2$ 是一个保守选择。理由：
- $W = 1$：过于严格，Agent 可能需要一步来"消化"经验建议（如安装额外依赖后才能生效）
- $W = 3+$：过于宽松，中间可能掺入 Agent 自身的探索行为，难以归因到经验

### 4.7 进化与融合机制 (Evolutionary Fusion: Propose-and-Verify)

#### 4.7.1 触发条件

**不是持续运行的后台任务**，而是在满足以下条件时触发：

1. 经验库规模超过阈值 $N_{\min} = 100$
2. 两条经验的向量相似度 > $\tau_{\text{fuse}} = 0.85$
3. 两条经验的 `score` 都 > 最低存活线（避免融合两条低质量经验）

#### 4.7.2 融合流程

```
发现相似经验对 (A, B)
        │
        ▼
LLM 分析 A 和 B 的 condition/action/rationale
        │
        ├── 判定：A 和 B 是同一问题的不同解法 → 不融合，保留竞争
        │
        ├── 判定：A 和 B 是同一问题的互补方面 → 生成融合经验 C
        │
        └── 判定：A 和 B 看似相似但根本原因不同 → 不融合，标记为"表面相似"
```

**融合经验 C 的属性**：
- `status`：**`[Hypothesis]`**（而非正常经验）。融合经验 C **不应直接赋予平均分或被视为已验证经验**。它的初始标签为 `[Hypothesis]`，表示这是一条由 LLM 推理生成的、**尚未经过实战验证的候选经验**。
- `score`：设为新创建经验的初始分数（`5.0`），**而非** $\frac{\text{Score}(A) + \text{Score}(B)}{2}$。理由：父经验 A、B 的高分是它们各自经过实战检验的结果，融合产物 C 并未经历任何实战，不应"继承"这些分数。
- `lineage`：`[A.id, B.id]`（可追溯）
- `call_count` / `success_count`：初始化为 0（需要从头证明自己）

**[Hypothesis] → 正式经验的晋升机制**：
1. **检索可见**：`[Hypothesis]` 经验正常参与检索和 Reranker 筛选（与正常经验无差别）
2. **晋升条件**：当 C 在某个**真实任务**中被检索到、被 Agent 采纳、并且该子任务**执行成功**后，C 正式晋升为正常经验（`status` 从 `[Hypothesis]` 变为 `[Verified]`），此后按正常的 Score 更新规则计算分数
3. **淘汰加速**：如果 C 在连续 $N_{\text{hypothesis}} = 10$ 个任务中**从未被检索命中**，或被检索到但连续 3 次执行失败，则直接删除（比 Bronze 层的淘汰更激进）
4. **原始经验保护**：父经验 A 和 B **始终保留**，不因 C 的创建而受到任何影响。只有当 C 晋升为 `[Verified]` 且 Score 超过 A 或 B 时，A/B 才进入正常的竞争淘汰流程

**理由**：未经实战验证的 LLM 融合产物就是潜在的"毒药"——LLM 可能在融合过程中引入幻觉、丢失关键条件信息、或产生看似合理但实际无效的"缝合怪"解决方案。`[Hypothesis]` 标签确保这些风险被显式管理。

#### 4.7.3 淘汰机制：分层保留 (Tiered Retention)

将经验按 `score` 和 `call_count` 分为三个层级：

| 层级 | 条件 | 淘汰策略 |
|------|------|---------|
| **Gold** | `score > 8.0` 且 `success_count >= 5` | **永不淘汰**。经过充分验证的高质量经验 |
| **Silver** | `score > 3.0` | 温和 Decay：每 30 天未使用 score 衰减 5%。降至 3.0 以下则降级 |
| **Bronze** | `score <= 3.0` | 激进 Decay：每 15 天未使用 score 衰减 15%。降至 0 以下则删除 |

**关键设计**：Gold 层的"永不淘汰"保护了那些"低频但极高价值"的经验——例如某个只在处理特定库版本兼容性问题时才需要的经验，虽然不常被调用，但一旦调用就极其有效。

---

## 五、 Prompt 工程与 Agent 交互设计 (Prompt Engineering)

### 5.1 System Prompt 核心结构

```
You are a professional academic paper reproduction Agent. Your goal is to
write and debug Python code from scratch based on the given paper content,
until you reproduce experimental results consistent with the original paper.

[Paper Content]: {paper_markdown}
[Working Directory]: {workspace_path}

{optional_experience_injection}

Follow this workflow:
1. Carefully read the paper and understand the core method and experimental design
2. Output a structured Reproduction Plan (Checklist/DAG) — see Section 4.2.3
3. Implement the code step by step, running verification after each step
4. When encountering issues, analyze the root cause and fix them
5. Finally, run the complete experiment and compare metrics against those reported in the paper

ITERATION EFFICIENCY — MANDATORY TOY-FIRST PRINCIPLE:
During the coding and debugging phase, YOU MUST create a MINIMAL TOY DATASET 
or use extremely small parameters (e.g., 1 epoch, 10 samples, coarse grid) 
to quickly verify the correctness of the code execution. ONLY when the toy 
experiment runs perfectly and the logic is verified, are you allowed to run 
the full-scale experiment. This rule applies to ALL phases:
- Data loading: first test with 10 samples, not the full dataset
- Model training: first run 1-2 epochs with tiny batch size
- Numerical simulation: first run on a coarse 10x10 grid, not 1000x1000
- Statistical analysis: first test on synthetic data with known ground truth
Rationale: A full-scale run that fails after 30 minutes wastes an entire 
iteration. A toy run that fails in 5 seconds gives you the same diagnostic 
information at 1/360th the cost.

SANITY CHECK AFTER EVERY EXECUTION — see Section 4.4.1 (Silent Bug Detection)
```

### 5.2 日志与 Trajectory 收集

所有 Agent 的操作（代码编写、命令执行、输出观察、推理过程）都被完整记录为 **Trajectory**（保存至 `/data/yjh/openhands_results_v2/trajectories`），用于：

1. **经验提取**（见 4.4 节）
2. **事后分析与论文撰写**（成功/失败案例分析）
3. **训练数据构建**（长远目标：用 trajectory 微调开源 LLM）

---

## 六、 评估框架 (Evaluation Framework)

### 6.1 Benchmark 构建: ReproduceBench

#### 6.1.1 数据集构建

从以下来源收集论文，构建 **ReproduceBench**。论文来源**跨越多个学科领域**：

| Tier | 论文特征 | 数量 | 示例领域 |
|------|---------|------|----------|
| **Tier 1: Easy** | 经典算法、小规模实验、有多个成功复现 | 20 篇 | 统计方法、经典ML、简单数值模拟 |
| **Tier 2: Medium** | 中等复杂度、标准数据集、有部分复现 | 20 篇 | 深度学习、计算物理、信号处理 |
| **Tier 3: Hard** | 复杂实现/流程、少有复现 | 10 篇 | 复杂优化算法、多物理场耦合、新型架构 |

**论文选择标准**：
- 论文有明确的定量指标（可以是 Accuracy、RMSE、PSNR、相对误差、统计显著性等，不限于 ML 指标）
- 实验部分基于 Python 实现（或可以用 Python 合理复现）
- **单卡 GPU（或纯 CPU）可复现**——不需要大量算力
- 论文本身不提供官方代码（或我们故意不使用）
- 有至少一个第三方成功复现的记录（作为 ground truth 验证）

#### 6.1.2 多维度评估体系 (Multi-Dimensional Evaluation)

仅依赖最终数值指标（如 Accuracy）来评价复现质量是**远远不够的**。一个"跑出了正确数字但代码完全不对"的情况（例如 hardcode 了结果）不应被视为成功复现。参考 PaperCoder (Paper2Code, 2025) 的评估框架设计，我们采用**多层次、多维度**的评估体系：

##### 层次一：执行层评估 (Execution-Level Evaluation)

| 指标 | 定义 | 衡量的能力 |
|------|------|---------|
| **Task Completion Rate (TCR)** | Agent 成功完成复现任务（代码可运行并产出结果）的比例 | 系统的基础编码与调试能力 |
| **Metric Alignment Score (MAS)** | 指标类型感知的对齐分数（见下方详细定义），截断到 $[0, 1]$ | 复现精度 |
| **Full Reproduction Rate (FRR)** | MAS > 0.95 的论文比例 | 端到端成功率 |
| **Attempt Efficiency (AE)** | 达到成功所需的平均迭代次数 | 经验库的加速效果 |
| **Cost Efficiency (CE)** | 每篇论文消耗的 LLM API tokens + 计算时长 | 实用性 |

**MAS 的指标类型感知定义 (Metric-Type-Aware MAS)**：

不同论文使用不同类型的指标，其性质差异显著。有的指标越大越好（如 Accuracy），有的越小越好（如 RMSE），且不同指标对偏差的敏感度也不同（Accuracy 差 1% 可能就是 SOTA 与非 SOTA 的区别；RMSE 差 0.01 可能无关紧要）。因此**不能使用统一的简单公式**。

MAS 的计算根据指标类型分类处理：

| 指标类型 | 方向 | MAS 公式 | 示例指标 |
|---------|------|---------|---------|
| **Higher-is-Better (↑)** | 越大越好 | $\text{MAS} = \min\left(\frac{v_{\text{repr}}}{v_{\text{paper}}}, 1.0\right)$ | Accuracy, F1, AUC, PSNR, R² |
| **Lower-is-Better (↓)** | 越小越好 | $\text{MAS} = \min\left(\frac{v_{\text{paper}}}{v_{\text{repr}}}, 1.0\right)$ | RMSE, MAE, FID, Perplexity, Loss |
| **Target-Value (⊙)** | 越接近目标值越好 | $\text{MAS} = 1 - \frac{|v_{\text{repr}} - v_{\text{paper}}|}{\max(|v_{\text{paper}}|, \epsilon)}$，截断到 $[0,1]$ | 特定物理常数、标定值 |

**关键设计要点**：
1. **方向信息必须标注**：在 ReproduceBench 的元数据中，每个指标必须标注其方向（↑/↓/⊙），由人工在 benchmark 构建阶段完成
2. **多指标聚合**：当论文报告多个指标时，取各指标 MAS 的**加权平均**，权重由该指标在论文中的重要性决定（主指标权重高，辅助指标权重低），权重在 benchmark 元数据中预定义
3. **量纲安全**：对于 Higher-is-Better 和 Lower-is-Better 类型，采用比值而非差值，天然处理了量纲问题
4. **上界封顶**：MAS 最大值为 1.0——超越论文报告值不额外奖励（避免鼓励 Agent 通过 overfitting 或错误实现获得"更好"的数字）
5. **$\epsilon$ 保护**：Target-Value 类型中 $\epsilon = 10^{-8}$，防止论文报告值为 0 时的除零错误

##### 层次二：代码忠实度评估 (Code Faithfulness Evaluation)

**为什么需要这一层？** 指标对齐不代表实现正确。Agent 可能通过"巧合"获得接近的数字，但实际实现与论文方法完全偏离。参考 PaperCoder 的做法，我们引入 LLM Judge 对代码本身的忠实度进行评估。

**评估方式**：分为 Reference-Based（有 ground truth 代码时）和 Reference-Free（仅有论文时）两种模式。

**Reference-Based 评估**（当有 ground truth 代码库时）：
- LLM Judge 对比生成的代码与参考实现，从论文中提取关键实现组件列表
- 逐一检查每个组件是否被正确实现
- 对缺失或错误的组件标注严重程度（high / medium / low）
- 输出总体正确性评分（1-5 分）

**Reference-Free 评估**（仅有论文时）：
- LLM Judge 仅基于论文内容推断应有的关键实现组件
- 检查生成的代码是否涵盖了这些组件
- 评估实现是否忠实于论文描述的方法

**关键实现组件的划分**（由 LLM Judge 从论文中自动提取，按三个维度）：

| 维度 | 描述 | 示例 |
|------|------|------|
| **Data Processing** | 数据获取、预处理、增强、划分 | 数据标准化方式、训练/测试划分比例、特征工程 |
| **Method** | 核心算法/模型的实现 | 算法主逻辑、关键公式的代码实现、特殊模块 |
| **Evaluation** | 评估流程与指标计算 | 评估指标的正确计算、评估协议（k-fold等） |

对每个组件，判定为：**○（完全满足）**、**△（部分满足）**、**×（未满足）**。

##### 层次三：经验库进化评估 (Experience Library Evolution Metrics)

| 指标 | 定义 | 衡量的能力 |
|------|------|---------|
| **Experience Library Growth (ELG)** | 经验库中 Gold tier 经验的比例随时间的变化 | 经验库质量的进化趋势 |
| **Experience Hit Rate (EHR)** | 经验被检索并判定为 RELEVANT 的比例 | 经验库与实际需求的匹配度 |
| **Experience Acceleration Factor (EAF)** | 有经验 vs 无经验时，相同任务的迭代次数比 | 经验库带来的直接加速 |
| **Cross-Domain Transfer Rate (CDTR)** | 在领域 A 积累的经验在领域 B 被成功使用的比例 | 跨领域泛化能力 |

##### 层次四：人类对齐评估 (Human Alignment Evaluation)

在条件允许时，参考 PaperCoder 的人类评估协议：
- 邀请论文作者（或领域专家）对生成的代码进行排名
- 评估者定义该论文的关键实现标准，然后检查代码是否满足
- 回答关键问题："使用这个生成的代码库，是否比从零开始复现更容易？"

> **注意**：人类评估成本高昂，仅在最终评估阶段对少量关键论文（~10 篇）执行，不作为日常开发迭代的评估手段。

#### 6.1.3 Baselines

| Baseline | 描述 |
|---------|------|
| **B1: Vanilla LLM** | 直接给 LLM 论文全文，让它一次性输出完整代码（无迭代、无经验） |
| **B2: OpenHands-CodeAct (No Experience)** | 使用 OpenHands CodeActAgent 但不带经验库（消融实验核心 baseline） |
| **B3: OpenHands + Voyager-Style Skill Library** | 使用 Voyager 式的"全记录"经验库（验证 H1: failure-only 是否优于 all-recording） |
| **B4: OpenHands + Reflexion** | 使用 Reflexion 式的单任务自反思（验证 H2: 跨任务经验是否优于单任务反思） |
| **B5: Human Expert** | 招募有经验的研究员手动复现同一组论文（作为人类上界参考） |

#### 6.1.4 消融实验 (Ablation Studies)

| 消融 | 移除的组件 | 验证的假设 |
|------|---------|---------|
| **A1** | 移除 Stage 2 Reranker，直接注入 Top-3 | H2: Anti-pollution 的价值 |
| **A2** | 记录所有经验（含一次性成功） | H1: Failure-only 的价值 |
| **A3** | 移除难度加权，使用简单成功率 | 信用分配机制的价值 |
| **A4** | 移除融合机制 | H3: 进化融合的价值 |
| **A5** | 移除 Negative Constraint 记录 | 死胡同记录的价值 |

### 6.2 统计严谨性

- 每个实验配置重复 **3 次**（不同随机种子），报告均值和标准差
- 使用 **配对 t 检验** 或 **Wilcoxon 符号秩检验** 验证改进的统计显著性
- 报告 **置信区间** 而非仅报告点估计

---

## 七、 执行路线图 (Execution Roadmap)

### Phase 0: 文献调研与 Benchmark 构建 (Month 1)

| 任务 | 交付物 |
|------|--------|
| 调研 OpenHands / SWE-Agent / AIDE / Voyager / ExpeL 等系统 | Related Work Survey |
| 收集 50 篇候选论文（跨领域），按 Tier 分类 | ReproduceBench v0.1 |
| 为每篇论文获取 Ground Truth 指标 | Benchmark Metadata |
| 定义评估指标与消融实验计划 | Evaluation Protocol 文档 |

### Phase 1: 基础设施构建 (Month 2)

| 任务 | 交付物 | 验证标准 |
|------|--------|---------|
| 基于已部署的 OpenHands，定制论文复现 Prompt | 可运行的 Agent 框架 | Agent 能在沙盒中执行代码并获取输出 |
| 集成 PaddleOCR 论文解析管线 | Paper Parser 模块 | 对 10 篇测试论文，Markdown 输出质量合格 |
| 实现 Experience DB (ChromaDB/Qdrant + SQLite) | DB 模块 + CRUD API | 可存储/检索/更新经验 |
| 实现 Trajectory Logger 与经验提取管线 | 日志 + 提取模块 | 完整记录 Agent 操作并能自动提取经验 |

### Phase 2: 冷启动与经验积累 (Month 3)

| 任务 | 交付物 | 验证标准 |
|------|--------|---------|
| 在 20 篇 Tier 1 论文上运行 Agent (No Experience) | Baseline B2 结果 | 收集 TCR, MAS, FRR 指标 |
| 验证经验提取质量 | 初始经验库 (预计 30-80 条) | 人工审查 20 条经验的质量，合格率 > 70% |
| 调试 Failure-Driven Trigger 的阈值 $k$ | 最优 $k$ 值 | 对比 $k=2, 3, 5$ 的经验质量 |
| 实现并验证 Two-Stage Retrieval | 检索模块 | 在已知的 condition-action 对上，检索准确率 > 80% |

### Phase 3: 经验驱动复现与消融实验 (Month 4-5)

| 任务 | 交付物 | 验证标准 |
|------|--------|---------|
| 在全部 50 篇论文上运行完整系统 | 主实验结果 | FRR 显著优于 B2 (p < 0.05) |
| 运行 Baselines B1, B3, B4 | Baseline 对比结果 | 确认各 baseline 的合理性 |
| 运行消融实验 A1-A5 | 消融结果表 | 每个消融都有统计显著的影响 |
| 分析 Reranker 的拦截率和准确率 | Reranker 分析报告 | 拦截率 > 30%，拦截准确率 > 85% |

### Phase 4: 融合机制与规模化 (Month 6)

| 任务 | 交付物 | 验证标准 |
|------|--------|---------|
| 实现 Propose-and-Verify 融合模块 | 融合引擎 | 融合经验的平均 Score > 父经验平均 Score |
| 在更多论文上持续运行（扩展至 100 篇） | 长期进化数据 | ELG 指标持续上升 |
| 分析"何时系统比从零开始快" | 盈亏平衡分析 | 确定经验库规模的"拐点" |

### Phase 5: 论文撰写与开源 (Month 7-8)

| 任务 | 交付物 |
|------|--------|
| 撰写论文（目标: ICLR / NeurIPS / ICML） | 论文初稿 |
| 整理代码，开源 ReproduceBench + 系统代码 | GitHub Repo |
| 制作 Demo 视频 | 演示材料 |

---

## 八、 风险分析与缓解 (Risk Analysis & Mitigation)

| 风险 | 严重性 | 可能性 | 缓解策略 |
|------|--------|--------|---------|
| **R1: LLM 幻觉导致实现严重偏离** | 高 | 高 | 在每步实现后加入运行验证，通过实际输出而非 LLM 自信度来判断正确性 |
| **R2: 经验库被低质量经验污染** | 高 | 中 | 提取质量门控 (4.4.3) + 严格的 Reranker 过滤 |
| **R3: 单卡 GPU 资源不足** | 中 | 低 | 论文选择时已筛选单卡可复现的论文；极少数需要更多资源的作为 stretch goal |
| **R4: 论文中关键信息缺失导致无法复现** | 高 | 高 | Agent 识别缺失信息并尝试多种合理默认值；经验库积累领域惯例 |
| **R5: API 成本过高** | 中 | 中 | 分级检索策略 (4.5.3)；批量实验使用较便宜的模型做初筛 |
| **R6: 跨领域论文的评估标准不统一** | 中 | 高 | 各领域使用该领域标准的评估指标；MAS 公式适用于所有定量指标 |
| **R7: Negative Experience 误导 Agent** | 中 | 低 | Negative Experience 仅作为"警告"注入，不作为硬约束 |
| **R8: 融合产生的经验质量退化** | 低 | 中 | 融合经验 Score 从保守值开始，需自证其用 |

---

## 九、 学术贡献与投稿策略 (Academic Contributions & Publication Strategy)

### 9.1 核心学术贡献

1. **Failure-Driven Experience Learning 范式**：提出并验证了"仅从困难失败中学习"在长程编码任务中的有效性，与认知科学理论形成交叉
2. **Anti-Pollution Retrieval 机制**：设计并验证了两阶段检索 + LLM Reranker 在经验注入场景下防止上下文污染的有效性
3. **Evolutionary Experience Fusion**：提出 Propose-and-Verify 竞争式融合机制，首次在 Agent 经验库中引入达尔文式自然选择
4. **ReproduceBench**：贡献一个跨领域、可标准化评估论文复现能力的 Benchmark，填补社区空白
5. **Agent 自主规划范式**：展示在没有预设流程的情况下，Agent 可以结合经验自主学习出合适的复现策略

### 9.2 投稿目标

| 优先级 | 目标会议 | Track | 匹配理由 |
|--------|---------|-------|---------|
| 1 | **ICLR 2026** | Main | Agent + Learning from Experience，ICLR 近年强调 agent learning |
| 2 | **NeurIPS 2026** | Datasets & Benchmarks | ReproduceBench 本身可独立投稿 |
| 3 | **ICSE 2026** | SE for AI | 从软件工程角度切入自动代码生成与调试 |
| 4 | **COLM 2026** | Main | 语言模型的能力边界探索 |

### 9.3 论文写作框架

**Title 候选**：
- "Evolution-Reproduce: Learning from Failure for Autonomous Paper Reproduction"
- "Experience-Driven Agents: Failure as the Teacher in Long-Horizon Code Generation"

**Story Line**：
1. 论文复现是 AI Agent 面临的最具挑战性的长程任务之一，且跨越多个学科领域
2. 现有 Agent 每次从零开始，无法从历史经验中学习
3. 我们提出 Failure-Driven Experience Learning + Anti-Pollution Retrieval + Evolutionary Fusion
4. Agent 无需预设固定流程，自主规划复现策略，并从经验中学习改进
5. 在跨领域 ReproduceBench 上的实验表明，经验库使 Agent 的复现成功率提升 X%，效率提升 Y%
6. 消融实验验证了每个组件的独立贡献

---

## 十、 长期愿景与扩展 (Long-Term Vision)

### 10.1 近期扩展 (6-12 个月)

- **多 Agent 协作**：将论文复现分解为 Parser Agent、Coder Agent、Debugger Agent、Evaluator Agent 的协作
- **开源模型替代**：用积累的 trajectory 数据微调开源 LLM（如 DeepSeek-Coder），降低对商用 API 的依赖
- **交互式模式**：当 Agent 遇到无法自主解决的问题时，生成结构化的"求助请求"，发送给人类专家

### 10.2 远期愿景 (1-3 年)

- **科研 Agent 生态**：从"复现论文"扩展到"改进论文"——Agent 不仅复现，还能提出改进假设并实验验证
- **跨领域经验迁移**：验证某一领域积累的调试经验能否帮助其他领域的复现（跨域泛化）
- **持续学习的 Agent 网络**：多个 Agent 实例共享经验库，形成"集体智慧"

---

## 十一、 资源需求 (Resource Requirements)

| 资源 | 数量 | 用途 | 备注 |
|------|------|------|------|
| GPU | **单卡**（已有） | 论文复现的沙盒执行 | 默认所选论文不需要大量算力 |
| LLM API | Claude 4.6 Opus（已配置） | Agent 推理 + Reranker + 经验提取 | 通过 `ai-gateway-internal.dp.tech` 网关调用 |
| PaddleOCR | `paddle_env` 环境（已部署） | PDF → Markdown 转换 | /home/yjh/new_flow/ocr.sh|
| OpenHands | 本地部署（已完成） | Agent 执行框架 | /home/yjh/OpenHands  |
| VectorDB | 1 实例 | 经验库存储与检索 | 自部署 ChromaDB/Qdrant，免费 |

---

## 十二、 总结 (Summary)

本研究计划提出 **Evolution-Reproduce**，一个基于失败驱动学习与进化记忆的自主论文复现系统。与原方案及现有系统相比，其核心特点在于：

1. **跨领域适用**：面向所有基于 Python 实现实验的学术论文，不局限于 ML/DL 领域
2. **无固定流程**：不预设 S0→S5 的线性阶段，Agent 自主规划复现策略，流程本身也可从经验中学习演化
3. **无固定抽取模板**：不使用固定的结构化信息抽取六元组，Agent 根据论文内容自行判断关键信息
4. **只从失败中学习**（Failure-Driven），避免经验库被 trivial 知识淹没
5. **严格防止经验污染**（Anti-Pollution Retrieval），宁缺毋滥
6. **达尔文式经验进化**（Evolutionary Fusion），让经验库质量持续自主提升

**基础设施已就绪**：PaddleOCR（PDF→Markdown）和 OpenHands（Agent 执行环境）均已部署完毕，GPU 资源为单卡，默认所选论文的复现不要求大量算力。

通过构建跨领域的 **ReproduceBench** 并设计严格的消融实验，我们将科学地验证每个设计决策的独立价值。项目时间跨度为 8 个月，预计产出 1-2 篇顶会论文和一个开源 Benchmark。
