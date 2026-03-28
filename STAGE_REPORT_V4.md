# Evolution-Reproduce: V4 经验增强测试报告 (修订版)

**报告日期:** 2026-03-28 02:30 (CST)  
**阶段:** Phase 2 Step 2 — V4 经验增强复现 (Experience-Enhanced Reproduction)  
**LLM:** Claude 4.6 Opus via ai-gateway (`openai/global.anthropic.claude-opus-4-6-v1`)  
**Agent:** OpenHands CodeActAgent (local runtime, max 100 iterations)  
**经验来源:** V3 轨迹提取 + 手工策划的元经验

---

## 一、V4 实验设计

### 1.1 目标
对 V3 中失败的 2 篇论文 (BPM, Diff) 进行经验增强重跑，验证经验注入是否能提升复现成功率。

### 1.2 经验注入方法
- **经验数据库:** 16 条经验 (9 条 V2 遗留 + 1 条 V3 BPM 轨迹提取 + 6 条手工策划元经验)
- **注入方式:** 在 Agent prompt 中追加 `[RELEVANT EXPERIENCE FROM PRIOR TASKS]` 段落
- **匹配策略:** 两阶段检索 — Stage 1: `aliyun/text-embedding-v4` 余弦相似度 → Stage 2: `GPT-5-mini` LLM 重排序
- **BPM 注入经验:** 1 条负面经验（V3 BPM 因 64³ vs 256³ 导致 SNR=-24dB）
- **Diff 注入经验:** 1 条正面经验（可微分光学 3 阶段策略 + 代码提示）

### 1.3 V3 → V4 变更
| 改进项 | V3 | V4 |
|--------|----|----|
| LLM 模型 | `cds/Claude-4.6-opus` (不稳定) | `global.anthropic.claude-opus-4-6-v1` (稳定) |
| 经验注入 | 无 | ✅ 基于经验数据库的 prompt 增强 |
| Max iterations | 30 | 100 |
| Prompt 规则 | 7 条 | 9 条 (新增 RULE 8 分辨率匹配, RULE 9 避免 IPython) |

---

## 二、V4 结果总览

| 论文 | V3 状态 | V4 Agent 状态 | V4 耗时 | results.json | V4 复现状态 | 改善 |
|------|---------|--------------|---------|-------------|------------|------|
| **bpm** | ❌ ERROR (工具循环) | ❌ ERROR (AttributeError) | 1013s (~17min) | ❌ | ❌ 失败 | ⚠️ 部分改善 |
| **diff** | ❌ ERROR (API故障) | ✅ FINISHED | 532s (~9min) | ✅ | ✅ **成功** | 🎉 **突破** |

**V4 新增成功: 1/2 (diff)**  
**总体成功率: V3 3/5 → V4 4/5 (80%)**

---

## 三、🔬 经验注入效果的诚实评估

> **核心问题：经验注入到底起了什么作用？V4 的改善是因为经验，还是因为其他变量？**

### 3.1 变量混淆分析

V3 → V4 同时改变了 **4 个变量**，无法归因：

| 变量 | V3 | V4 | 对结果的影响 |
|------|----|----|------------|
| ① LLM 模型端点 | `cds/Claude-4.6-opus` (频繁宕机) | `global.anthropic.claude-opus-4-6-v1` (稳定) | **关键** — V3 diff 直接因 API 故障失败 |
| ② Max iterations | 30 | 100 | **重要** — 更多迭代空间 |
| ③ Prompt 规则 | 7 条 | 9 条 (新增分辨率匹配+避免IPython) | **中等** — 直接编码了 V3 教训 |
| ④ 经验注入 | 无 | 有 | **不确定** — 见下文分析 |

### 3.2 Diff 成功的归因分析

**V3 Diff 失败的真实原因：** `BadRequestError: cds/Claude-4.6-opus` API 不可用。V3 Diff 的 45 个事件中，最后 5 个全是 `Missing required parameters for execute_bash`，这是 API 返回错误后 Agent 进入的降级模式。**V3 Diff 从未真正开始算法实现。**

**V4 Diff 成功的归因：**
- **主因 (>80%):** API 稳定性修复 — 换了可用的模型端点
- **辅因 (<20%):** 经验注入提供了 3 阶段策略框架

**证据 — Agent 是否参考了经验？**
- ✅ Agent 第一个 think（事件 4）中提到了 "Snell's law" 和 "least_squares"，与经验中的关键词一致
- ❌ 但 Agent 的实现策略（直接写一个大文件 `diff_deflectometry.py`）与经验建议的 3 阶段渐进策略不同
- ❌ Agent 没有使用经验建议的 autograd/JAX，而是直接用 scipy.optimize.least_squares
- **结论：** 经验可能提供了方向性提示，但 Agent 主要依靠自身对论文的理解

### 3.3 BPM 失败的归因分析

**V4 BPM 注入的经验：**
```
Experience #1 ⚠️ KNOWN FAILURE
  WARNING: Use grid resolution matching the paper (256x256x128 at 144nm voxels).
  Low resolution (64x64x32 at 576nm) causes severe aliasing.
```

**Agent 是否参考了经验？**
- ✅ **明确参考！** Agent 第一个 think（事件 4）中写道：
  > "Resolution considerations (from experience): The experience warns that low resolution causes severe aliasing. The paper uses 256×256×128 at 144nm voxels. I need to match this."
- ✅ Agent 的复现计划（事件 8）明确使用了 256×256×128 网格
- ❌ **但 Agent 仍然先做了 toy test（64×64×32）**，然后在 toy test 阶段就卡住了（SNR=-19dB）
- ❌ Agent 从未到达全尺寸实验阶段就因 AttributeError 崩溃

**结论：** 经验对 BPM 的影响是 **正面但不足的**。Agent 正确接收了分辨率警告，但：
1. BPM 的核心困难不是分辨率，而是优化算法的收敛性
2. 经验没有提供关于 BPM 优化策略的具体指导（步长选择、TV 正则化参数等）
3. OpenHands 的 AttributeError 是框架 bug，与经验无关

### 3.4 经验匹配策略的问题

当前匹配策略存在根本性缺陷：

| 问题 | 描述 | 严重性 |
|------|------|--------|
| **数据泄露** | 经验直接来自同一篇论文的历史运行，不是跨论文迁移 | 🔴 致命 |
| **变量混淆** | V3→V4 同时改了 4 个变量，无法归因 | 🔴 致命 |
| **经验质量低** | 16 条经验中，9 条是 V2 遗留（与当前任务无关），6 条是手工策划 | 🟡 严重 |
| **匹配粒度粗** | 用论文摘要做 embedding 匹配，无法区分"算法类型相似"vs"领域相似" | 🟡 严重 |
| **无对照实验** | 没有"V4 无经验但修复 API"的对照组 | 🔴 致命 |

### 3.5 诚实结论

> **V4 的成功率提升（60%→80%）主要归因于 API 稳定性修复和 max_iterations 增加，而非经验注入。**
> 
> 经验注入对 BPM Agent 有可观察的正面影响（Agent 明确引用了分辨率警告），但不足以解决核心问题。
> 对 Diff 的影响无法与 API 修复分离。
> 
> **当前的经验框架不具备科学有效性，需要重新设计。**

---

## 四、逐篇详细分析

### 4.1 Diff ✅ — 可微分折射偏折术 (首次成功)

**论文:** "Towards self-calibrated lens metrology by differentiable refractive deflectometry"

| 指标 | V4 值 | 论文参考 | 匹配 |
|------|-------|---------|------|
| c1 误差 (theta-only) | 22.3% | 大误差 (未自校准) | ✅ |
| c2 误差 (theta-only) | 7.2% | 大误差 | ✅ |
| c1 误差 (联合优化) | **0.47%** | 接近零 | ✅ |
| c2 误差 (联合优化) | **0.17%** | 接近零 | ✅ |
| 代价函数比 (theta/joint) | **201x** | >1个数量级 | ✅ |
| RMS 交点误差比 | **14.4x** | 显著改善 | ✅ |

**Agent 行为分析 (43 events, 532s):**
- 事件 4: 分析论文，制定 10 步计划
- 事件 14-15: 写 `diff_deflectometry.py` (heredoc 失败)
- 事件 20-21: 改用 str_replace_editor 创建文件
- 事件 22-23: 首次运行成功，得到 203.7x 代价比
- 事件 26-35: 迭代改进（修复 φ_z 退化、提高分辨率）
- 事件 36-37: 最终运行，201x 代价比
- 事件 42: 完成

**产出文件:** `diff_deflectometry.py` (17KB), `results.json`

### 4.2 BPM ❌ — 光学层析 (仍然失败，但有改善)

| 指标 | V3 值 | V4 值 | 论文参考 |
|------|-------|-------|---------|
| Agent 事件数 | 158 (大量错误循环) | 57 (更有效) | — |
| 梯度验证 | 未验证 | ✅ 相对误差 1e-7~1e-9 | — |
| 重建 SNR | -24.14 dB | ~-19 dB | 22.74 dB |
| 失败原因 | execute_ipython_cell 死循环 | AttributeError + 空think循环 | — |

**Agent 行为分析 (57 events, 1013s):**
- 事件 4: 分析论文 + **明确引用经验中的分辨率警告**
- 事件 8: 制定 7 步计划，目标 256³ 网格
- 事件 14-23: 实现 BPM 前向模型 + toy test
- 事件 26-29: 梯度验证 ✅ (1e-7~1e-9)
- 事件 34-37: 重建测试 → SNR=-19dB，卡住
- 事件 38-53: 空 think 循环 → AttributeError

---

## 五、V2 → V3 → V4 完整对比

| 论文 | V2 (代码脚本) | V3 (完整论文) | V4 (经验增强) | 趋势 |
|------|-------------|-------------|-------------|------|
| **pyeit** | ✅ | ✅ | (未重跑) | 稳定成功 |
| **pat** | ✅ | ✅ | (未重跑) | 稳定成功 |
| **insar** | ✅ | ✅ | (未重跑) | 稳定成功 |
| **bpm** | ❌ ConnectError | ❌ 工具循环 | ❌ AttributeError | 逐步改善但未成功 |
| **diff** | ❌ ConnectError | ❌ API故障 | ✅ **成功** | 🎉 突破 (但归因不清) |
| **成功率** | **3/5 (60%)** | **3/5 (60%)** | **4/5 (80%)** | 📈 +20% (混淆变量) |

---

## 六、框架重新设计方案

### 6.1 核心问题诊断

当前框架的根本问题是 **无法证明经验的因果效应**：

1. **无对照组:** 没有"修复 API + 无经验"的 baseline
2. **数据泄露:** 经验来自同一篇论文的历史运行
3. **样本量太小:** 只有 2 篇论文的 V4 数据
4. **变量混淆:** 同时改了 API、iterations、prompt 规则、经验

### 6.2 重新设计：Train/Test Split + 严格对照

#### 6.2.1 数据划分

**15 篇论文分为 Training Set (10篇) 和 Test Set (5篇)：**

| 集合 | 论文 | Tier | 领域 | 理由 |
|------|------|------|------|------|
| **Train** | pyeit | 1 | biomedical_imaging | 已成功，提供正面经验 |
| **Train** | pat | 1 | biomedical_imaging | 已成功，提供正面经验 |
| **Train** | insar | 1 | remote_sensing | 已成功，高质量复现 |
| **Train** | bpm | 1 | computational_optics | 已失败，提供负面经验 |
| **Train** | diff | 1 | computational_optics | V4 已成功，提供正面经验 |
| **Train** | oopao | 2 | adaptive_optics | 自适应光学模拟 |
| **Train** | lenstronomy | 2 | astrophysics | 引力透镜建模 |
| **Train** | pnp_cassi | 2 | computational_imaging | 编码孔径光谱成像 |
| **Train** | dpi | 3 | scientific_computing | 可微分逆问题 |
| **Train** | ptyrad | 3 | computational_imaging | 叠层成像自动微分 |
| **Test** | fpm_inr | 2 | computational_imaging | 傅里叶叠层+隐式神经表示 |
| **Test** | lensless | 2 | computational_imaging | 无透镜成像 ADMM |
| **Test** | lfm | 2 | computational_imaging | 光场显微镜 |
| **Test** | sparse_sim | 3 | computational_imaging | 稀疏结构照明 |
| **Test** | flfm | 3 | computational_imaging | 傅里叶光场显微镜 |

**划分原则：**
- Training 包含所有 Tier 1（已有运行数据）+ 部分 Tier 2/3
- Test 选择与 Training 有领域重叠但不完全相同的论文
- Test 论文从未被运行过，确保零数据泄露
- 每个集合覆盖多个 Tier 和领域

#### 6.2.2 严格对照实验设计

```
Phase A: Training Set 运行 (10 篇)
  ├── A1: Baseline 运行 (无经验, 固定 API + iterations)
  │     → 已有 Tier 1 的 V3 数据 (pyeit/pat/insar/bpm/diff)
  │     → 需新跑 Tier 2/3 的 5 篇 (oopao/lenstronomy/pnp_cassi/dpi/ptyrad)
  ├── A2: 从 A1 轨迹提取经验 → Experience DB (新 schema)
  └── A3: 经验增强重跑 Training Set 中的失败论文 (验证经验有效性)
  
Phase B: Test Set 严格评估 (5 篇)
  ├── B1: Baseline 运行 (无经验, 同一 API + iterations)  ← 对照组
  ├── B2: 经验增强运行 (有经验, 同一 API + iterations)  ← 实验组
  └── B3: 对比 B1 vs B2 → 经验的因果效应
```

**关键约束：**
- B1 和 B2 使用 **完全相同的** API 端点、max_iterations、prompt 规则
- B1 和 B2 的 **唯一区别** 是是否注入经验
- 经验 **只来自 Training Set**，不来自 Test Set 自身
- 每篇论文运行 **至少 2 次** 以评估方差

#### 6.2.3 经验提取策略改进

当前问题：经验太粗糙（"用高分辨率"），缺乏可操作性。

**改进方向：**

| 维度 | 当前 | 改进 |
|------|------|------|
| **粒度** | 论文级别 ("BPM 要用高分辨率") | 算法级别 ("迭代重建需要验证梯度+调步长") |
| **结构** | condition + action 二元组 | condition + diagnosis + action + verification 四元组 |
| **来源** | 手工策划 + 粗糙轨迹解析 | 结构化轨迹分析 (成功步骤序列 + 失败恢复模式) |
| **匹配** | 论文摘要 embedding (粗粒度) | 算法标签 + 数学方法 + 编程模式 多维匹配 |
| **验证** | 无 | 经验注入后 Agent 是否实际采纳 (adoption rate) |

**新的经验 Schema：**
```json
{
  "id": "exp_xxx",
  "type": "positive|negative",
  "level": "algorithm|implementation|debugging",
  "tags": ["fft", "optimization", "inverse_problem", "snell_law"],
  "condition": {
    "algorithm_type": "iterative_reconstruction",
    "math_methods": ["gradient_descent", "TV_regularization"],
    "common_pitfall": "resolution_aliasing"
  },
  "action": {
    "strategy": "...",
    "code_pattern": "...",
    "verification_method": "..."
  },
  "evidence": {
    "source_paper": "bpm",
    "source_version": "v3",
    "adoption_rate": null,
    "effectiveness": "negative"
  }
}
```

#### 6.2.4 经验匹配策略改进

当前：用论文摘要做 embedding 匹配 → 粒度太粗，且容易匹配到"领域相似但方法不同"的经验。

**改进：多维度匹配**

```
Score = w1 * tag_overlap           # 算法/方法标签精确匹配
      + w2 * embedding_similarity  # 语义相似度 (保留作为补充)
      + w3 * failure_pattern_match # 失败模式匹配 (如果当前任务有类似风险)
```

其中 `tag_overlap` 基于预定义的标签集合做精确匹配（如 `["fft", "inverse_problem"]`），比纯 embedding 更可靠。

---

## 七、成本估算

| 论文 | 事件数 | 耗时 | 估算 tokens | 估算成本 |
|------|--------|------|------------|---------|
| BPM (V4, 失败) | 57 | 1013s | ~1.5M | ~$30 |
| Diff (V4, 成功) | 43 | 532s | ~1.2M | ~$24 |
| **V4 总计** | **100** | **1545s** | **~2.7M** | **~$54** |

---

## 八、下一步计划 (修订版)

### Phase A: Training Set 运行 + 经验提取 (2-3 天)

| 步骤 | 任务 | 预计耗时 |
|------|------|---------|
| A1a | 对 5 篇新 Training 论文 (oopao, lenstronomy, pnp_cassi, dpi, ptyrad) 运行 baseline | 5-8h |
| A1b | 收集 A1a 结果 + 已有 Tier 1 V3 结果 | 1h |
| A2 | 从全部 10 篇 Training 轨迹提取结构化经验 (新 schema) | 2-3h |
| A3 | 经验增强重跑 Training 失败论文 (验证) | 3-5h |

### Phase B: Test Set 严格评估 (1-2 天)

| 步骤 | 任务 | 预计耗时 |
|------|------|---------|
| B1 | 对 5 篇 Test 论文运行 baseline (无经验, 对照组) | 5-8h |
| B2 | 对 5 篇 Test 论文运行经验增强 (实验组) | 5-8h |
| B3 | 对比分析 B1 vs B2，计算经验因果效应 | 2h |

### Phase C: 报告 + 论文 (1 天)

| 步骤 | 任务 |
|------|------|
| C1 | MAS 评分 + LLM Judge 评估 |
| C2 | 统计分析 + 可视化 |
| C3 | 最终报告 |

---

## 九、结论 (修订版)

### 确认的事实
1. **V4 Diff 首次成功复现**，质量高（201x 代价改善，所有声明验证通过）
2. **V4 BPM 有改善**（梯度验证通过，更少事件），但仍失败
3. **经验对 BPM Agent 有可观察影响**（Agent 明确引用了分辨率警告）

### 需要修正的结论
1. ~~"经验增强有效"~~ → **无法确认**，因变量混淆
2. ~~"成功率从 60% 提升到 80%"~~ → **80% 是真实的，但归因不清**
3. ~~"经验 + API 稳定性的协同效应"~~ → **API 稳定性是主因，经验效应待验证**

### 下一步的核心目标
**设计严格的 Train/Test 对照实验，在从未见过的 Test Set 上验证经验的因果效应。**

---

*本报告经过对 V4 轨迹的逐事件分析后修订，力求诚实反映实验结果。*  
*框架重新设计方案待实施。*
