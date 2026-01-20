# 智能体评测（Agent Evaluation）

本页面介绍如何在 SciEvalKit 中运行一次完整的智能体（Agent）评测流程，涵盖环境准备、配置文件编写、评测执行以及评测结果与轨迹的解读。

## 如何运行一次智能体评测（How to Run an Agent Evaluation）

智能体评测的目标是：在给定评测数据集（Benchmark）上，自动化地运行智能体推理过程，并对其输出进行统一打分与统计分析。整个流程由配置文件驱动，可复现、可扩展。



### 1. 环境变量配置

智能体评测通常涉及两类模型调用：

- **智能体（Agent）**：负责执行推理与决策流程  
- **评测模型（Judge）**：负责对智能体最终输出进行自动化评分  

SciEvalKit 采用 OpenAI-compatible API 进行模型调用，请在运行评测前配置以下环境变量。

#### 1.1 智能体

`Agent` 用于执行智能体推理逻辑，默认从环境变量中读取模型 API 配置：

```bash
export OPENAI_API_KEY=your_api_key
export OPENAI_BASE_URL=your_api_base_url
```

其中：

- `OPENAI_API_KEY`：模型服务的访问密钥  
- `OPENAI_BASE_URL`：模型服务的 API 地址

---

#### 1.2 评测模型（Judge）

如果数据集在评测阶段调用评测模型（Judge）对智能体输出进行评分，默认同样使用 OpenAI-compatible 接口：

```bash
export OPENAI_API_KEY=your_api_key
export OPENAI_API_BASE=your_api_base_url
```

说明：

- 若未显式区分 `OPENAI_API_BASE` 与 `OPENAI_BASE_URL`，两者也可使用同一地址  
- 若需要为 Agent 与 Judge 分别指定不同的 API Key / Base，可单独设置  

---

### 2. 编写评测配置文件（JSON）

智能体评测完全由配置文件驱动。用户可在任意位置新建一个 JSON 配置文件，例如 `agent_eval_config.json`。

#### 2.1 示例

```json
{
  "agent": {
    "class": "SmolAgentsAgent",
    "model_version": "o3",
    "api_key": "sk-12345",
    "api_base": "https://api.openai.com/v1/"
  },
  "data": {
    "BrowseCompZH": {
      "class": "BrowseCompZH",
      "dataset": "BrowseCompZH"
    }
  }
}

```

---

#### 2.2 Agent 配置说明

`agent` 字段用于指定评测中使用的智能体：

- `class`：智能体类名  
- `model_version`：智能体中调用模型名称

如需为智能体单独指定 API Key 或 Base，可在该字段下补充对应参数。

---

#### 2.3 Data（Benchmark）配置说明

`data` 字段用于指定评测数据集及其评测参数：

- `dataset` 的 key 即为数据集名称（dataset_name）
---

### 3. 运行智能体评测

完成环境配置与配置文件编写后，即可通过命令行运行评测。

#### 3.1 基本命令

```bash
python agent_runner.py \
  --config agent_eval_config.json \
  --work-dir ./outputs \
  --mode all \
  --api-nproc 4
```

---

#### 3.2 关键参数说明

- `--config`：评测配置文件路径  
- `--work-dir`：评测输出目录  
- `--mode`：评测模式  
  - `all`：先运行智能体推理，再进行评测打分  
  - `infer`：仅运行智能体推理，保存轨迹，不进行打分  
  - `eval`：仅进行评测（需已有轨迹文件）  
- `--api-nproc`：并发请求数，用于并行处理多个样本  

---

#### 3.3 复用与断点续跑

- `--reuse`：开启结果复用  
  - 优先读取已有的轨迹（traj）与评测结果  
  - 适用于中断后继续运行或重复评测分析  

---

### 4. 评测流程与结果数据记录

#### 4.1 评测执行流程概览

智能体评测的入口为 `agent_runner.py`，核心流程如下：

```
run_agent_eval_from_config
  → run_agent_eval
    → _run_one_sample（逐样本执行）
```

系统会对数据集中所有样本依次执行智能体推理与评测逻辑。

---

#### 4.2 评测结果存储结构

所有评测结果由 `TrajectoryStore` 统一管理，目录结构如下：

```text
{work_dir}/agent_eval/
  └── {dataset_name}/
      └── {agent.name}/
          └── {agent.model_version}/
              └── {eval_id}/
```

其中：

- `eval_id` 格式为：`T{yyyyMMdd}_G{gitsha8}`  
- 用于标识一次唯一评测运行

---

#### 4.3 单样本与汇总文件

**单样本文件：**

- `sample_{idx}_traj.json`  
  - 智能体推理轨迹（成功状态、最终答案、推理步骤）
- `sample_{idx}_eval.json`  
  - 评测结果（样本索引、最终答案、评分、元数据）

**汇总文件：**

- `{agent.name}_{dataset_name}.json`  
  - 所有样本的预测结果
- `summary.json`  
  - 各评分指标的均值与统计结果

---

通过上述流程，用户可以在 SciEvalKit 中完成一次标准化、可复现的智能体评测实验，并基于轨迹与评测结果进一步开展分析或方法对比。

---

## 接口与轨迹存储（Interfaces & Trajectory Storage）

SciEvalKit 的智能体评测模块通过一组统一的接口定义与标准化的轨迹存储结构，从而支持可复现评测、过程分析与方法扩展。本节重点介绍评测流程中涉及的核心接口、数据结构以及轨迹落盘约定。

---

### 1. 核心接口与数据结构（`scieval/agents/base.py`）

#### 1.1 EvalSample：评测样本的统一输入载体

`EvalSample` 是智能体评测中单个样本的统一输入表示，用于承载智能体推理所需的全部信息，并作为 `Agent.run()` 方法的参数输入。

其主要字段包括：

- `prompt`：文本输入，通常为字符串或格式化后的提示文本  
- `images`：图像输入，可为本地路径、URL 或 data URI  
- `files`：附加文件路径列表，用于工具调用或外部信息读取  
- `metadata`：任意键值形式的元数据，用于存储样本标识、来源或难度等信息  

`EvalSample` 的设计目标在于统一多模态输入接口，并与具体 Agent 实现解耦，使其能够在不同评测任务之间复用。

---

#### 1.2 AgentBase：智能体接口抽象

`AgentBase` 是所有智能体的抽象基类，仅约定最小必要接口：

```python
run(self, sample: EvalSample) -> EvalResult
```

其中：

- `sample`：当前评测样本（`EvalSample`）
- 返回值由具体 Agent 实现决定，通常为 `EvalResult`

---

### 2. 推理轨迹与评测记录结构（`records.py`）

为支持智能体推理过程的可解释性与后续分析，SciEvalKit 对推理轨迹与评测结果进行了结构化建模，并明确区分二者的职责。

---

#### 2.1 ToolCalling：工具调用记录

`ToolCalling` 用于记录一次完整的工具调用过程，主要字段包括：

- `tool_name`：工具名称  
- `tool_input`：工具调用时的输入参数  
- `tool_output`：工具返回结果  

该结构用于精确还原智能体在推理过程中何时、以何种方式调用了外部工具。

---

#### 2.2 StepResult：单步推理与对话记录

`StepResult` 表示智能体推理过程中的一个步骤，通常对应一次模型响应或行动，其字段包括：

- `role`：当前步骤的角色标识（如 system / user / assistant / tool）  
- `content`：多模态内容数组，可包含文本或图像等信息  
- `tool_calling`：本步骤中发生的工具调用列表（可为空）  

多个 `StepResult` 按时间顺序组合，构成完整的智能体推理轨迹。

---

#### 2.3 EvalResult：单样本推理结果

`EvalResult` 用于表示智能体在单个样本上的完整推理结果，是推理阶段的核心输出结构，其主要字段包括：

- `success`：是否成功完成任务  
- `final_answer`：智能体给出的最终答案  
- `steps`：推理轨迹（`List[StepResult]`）  

`EvalResult` 会被直接用于轨迹存储，并作为后续评测阶段的重要输入。

---

#### 2.4 EvalRecord：单样本评测结果

`EvalRecord` 用于表示评测阶段生成的单样本结果记录，其关注点在于最终输出与评分信息，主要字段包括：

- `index`：样本索引  
- `final_answer`：用于评分的最终答案  
- `score`：评测得分（可为标量或结构化指标）  
- `metadata`：评测阶段附加的元数据信息  

`EvalRecord` 主要用于评测结果落盘与统计分析，不包含推理过程细节。

---

### 3. TrajectoryStore：轨迹与评测结果存储

`TrajectoryStore` 是统一的轨迹与评测结果读写管理器，负责将智能体推理过程与评测结果进行序列化并写入磁盘。

---

#### 3.1 文件存储约定

对于每个样本索引 `idx`，`TrajectoryStore` 约定生成以下两个文件：

- `sample_{idx}_traj.json`  
  - 存储智能体推理轨迹，由 `EvalResult` 序列化生成  
- `sample_{idx}_eval.json`  
  - 存储评测结果，由 `EvalRecord` 序列化生成  

该约定保证了推理过程与评测结果在存储层面的明确分离，便于单样本级别的调试、复现与复用。

---

#### 3.2 轨迹与评测结果写入接口

- `save_traj(result: EvalResult)`  
  - 接收 `EvalResult` 对象  
  - 自动序列化其中的 `steps` 字段并写入轨迹文件  

- `save_eval(record: EvalRecord | Any)`  
  - 接收 `EvalRecord` 或任意支持 `to_dict()` 方法的对象  
  - 用于评测结果的统一落盘  

通过 `TrajectoryStore` 的统一管理，评测流程可以在 `infer`、`eval` 与 `reuse` 等不同运行模式之间灵活切换，而无需重复执行智能体推理。

---

### 4. 设计原则

上述接口与轨迹存储设计目标为：

- 智能体推理过程与评测逻辑的解耦  
- 推理轨迹的可解释、可回放与可分析  
- 评测结果的标准化存储与统计支持  

这些设计为后续的 Agent 扩展、Benchmark 构建以及评测分析工具提供了稳定而清晰的基础。

---

## 如何新增一个评测 Benchmark（Dataset）

在 SciEvalKit 的智能体评测框架中，新增一个评测 Benchmark 的核心思想是：**新增一个 Dataset 类，并在配置文件中引用该数据集**。评测流程本身无需修改。

---

### 1. 新增 Dataset 类

请在 `scieval/dataset/` 目录下新增你的 Dataset 实现。一个支持智能体评测的 Dataset 通常需要实现以下方法：

- `load_data()`  
  用于加载原始数据，并构造内部样本列表。

- `build_agent_sample()`（`build_prompt()`为模型评测）  
  用于将单条原始数据转换为智能体可直接消费的输入样本：
  - 对于 Agent 评测，返回 `EvalSample`
  - 对于模型评测，返回模型输入所需的 prompt

- `score_agent_sample()`  
  用于定义智能体评测阶段的评分逻辑，根据智能体输出结果生成评分信息。

完成 Dataset 类实现后，需要确保该类能够被 `build_dataset` 正确构建。

---

### 2. Dataset 注册

为了让评测框架能够加载新增的数据集，需要在以下位置完成注册或导出：

- 在 `scieval/dataset/__init__.py` 中显式导出 Dataset 类  
- 或在 `build_dataset` 所在模块中注册对应的 Dataset 映射关系  

只要 `build_dataset(dataset_name)` 能够返回对应的数据集实例，即可被评测流程使用。

---

### 4. 模型评测与 Agent 评测的共存支持

同一个 Dataset 可以同时支持模型评测与智能体评测，两种路径互不冲突：

- **模型评测路径**  
  - `build_prompt()`：构造模型输入  
  - `evaluate()`：对模型输出进行打分与结果汇总  

- **智能体评测路径**  
  - `build_agent_sample()`：构造智能体输入样本（`EvalSample`）  
  - `score_agent_sample()`：对智能体输出进行评分  

通过这种设计，同一数据集可以被复用于不同评测范式，避免重复实现。

---

## 如何新增一个 Agent

新增 Agent 的流程相对直接，核心是：**实现一个继承自 `AgentBase` 的智能体类，并让评测运行器能够识别该类**。

---

### 1. 实现 Agent 类

请在 `scieval/agents/` 目录下新增一个 Agent 类，并继承自 `AgentBase`。一个最小可用的 Agent 实现需要包含：

- `name`：智能体名称（字符串）
- `run(self, sample: EvalSample) -> EvalResult`：智能体推理入口方法

在 `run()` 方法中，Agent 需要根据输入的 `EvalSample` 执行推理逻辑，并返回 `EvalResult`，至少包含：

- `success`：是否成功完成任务  
- `final_answer`：智能体的最终输出  

如有需要，也可以在返回结果中补充 `steps` 字段，用于记录完整推理轨迹。

---

### 3. 在配置文件中指定 Agent

完成 Agent 实现与注册后，可在配置文件中通过 `agent` 字段指定使用的智能体：

```json
{
  "agent": {
    "class": "YourAgentClass",
    "model_version": "your-model"
  },
  "data": {
    "YourDataset": {
        "class": "YourDatasetClass",
        "dataset": "YourDataset"
    }
  }
}
```

其中：

- `class`：Agent 类名  
- `model_version`：智能体中调用的模型名称

通过上述步骤，即可将新的 Agent 接入 SciEvalKit 的智能体评测流程中。