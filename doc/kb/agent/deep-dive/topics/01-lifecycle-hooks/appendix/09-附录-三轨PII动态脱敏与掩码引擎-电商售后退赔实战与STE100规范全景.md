# 深度解构附录：三轨 PII 动态脱敏与掩码引擎——电商售后退赔实战与 STE100 规范全景

> **知识库归属**：企业级 Agent 架构 L2 层（受控宿主运行时 Harness）专题矩阵  
> **文档定位**：Hook 2 `before_context` 功能三“三轨高性能 PII 动态脱敏与掩码引擎”深度算法与工程落地附录——全面剖析 PII 与 PCI-DSS 数据合规红线、动态脱敏（DDM）与掩码引擎内核机制，深挖 Regex+Luhn、Aho-Corasick、Local NER 三轨数学与算法原理，结合跨境电商“售后争议调解与退赔决策 Agent”真实母案步进拆解端到端脱敏流，并在文末提供基于 **ASD-STE100** 国际标准的工程规范。  
> **工程基线**：**Java 21（LTS）**（全面采用 `record`、并发结构化任务范围 `StructuredTaskScope`、不可变集合与区间仲裁算法）。  
> **编写标准**：涵盖 **ASD-STE100（Simplified Technical English）** 国际规范标准章节（受控词汇、句长 $\le 20$ 词、主动语态、单句单动作指令）。  
> **关联主文档**：[09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md](../09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md#3-功能三三轨高性能-pii-动态脱敏与掩码引擎multi-track-pii-tokenization-engine)  
> **业务母案实战**：[01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../../../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md)（售后争议调解与退赔决策 Agent）  
> **所属专题**：[00-专题总揽与实战索引.md](../00-专题总揽与实战索引.md)  
> **理论图谱穿透**：[01-分布式系统架构体系全景知识图谱-v1.0.md](../../../../../distributed-systems/01-分布式系统架构体系全景知识图谱-v1.0.md#四-穿透实战ai-agent-harness-在本知识图谱中的落地点映射)

---

## 零、 痛点场景：跨境退赔 Agent 触碰的数据泄漏“雷区”

在跨国电商售后退赔调解场景中，买家提交的客诉工单往往混杂着高度敏感的个人信息与金融数据。例如，一位法国巴黎买家在为 $180 瑕疵手表申请 $50 仅退款时，随手在工单留言附带了其私人信用卡卡号、住址、私人电话甚至银行转账明细。

如果 Agent Harness 在调用大模型前**缺乏前置动态掩码装甲**，原始文本将直接明文发送给云端大模型 API（如 OpenAI、Anthropic）：

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    数据明文裸奔传输的灭顶之灾                                            │
│                                                                                                        │
│  [买家工单原始文本]                                                                                      │
│  "我是 Jean-Luc Moreau，手表有划痕。请赔付到我的 Visa 卡 4532-0150-0000-0008，住址: 14 Rue de Rivoli... "   │
│                                              │                                                         │
│                                              ▼ (无脱敏防护)                                            │
│                     ┌────────────────────────────────────────────────┐                                 │
│                     │       公网明文调用云端 LLM API (OpenAI 等)       │                                 │
│                     └────────────────────────┬───────────────────────┘                                 │
│                                              │                                                         │
│         ┌────────────────────────────────────┴────────────────────────────────────┐                    │
│         ▼                                                                         ▼                    │
│  ▌引爆 PCI-DSS 极刑违规：                                                  ▌引爆 GDPR 顶格天价罚单：            │
│    • 云端模型非金融合规认证存储端                                             • PII 未经授权出境至境外第三方服务器│
│    • 卡组织 (Visa/Mastercard) 吊销商户跨国收单资格                           • 欧盟数据监管局开出年营收 4% 罚单  │
│    • 独立站全线停摆，资金池被物理冻结                                         • 严重损害跨国品牌商誉与消费者信任  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

为了彻底解决这一致命风险，必须在 L2 Harness 的 `before_context` 门禁中建立**“三轨高性能 PII 动态脱敏与掩码引擎”**。

---

## 一、 概念底座：PII、PCI-DSS、动态脱敏与掩码引擎

### 1. PII（Personally Identifiable Information，个人身份信息）
* **法律定义**：指任何能够单独或与其他信息结合后，**直接或间接唯一识别特定自然人**的数据。
* **分级保护范畴**：
  * **直接标识符（Direct PII）**：身份证号、护照号、全名（Full Name）、手机号、私人电子邮箱；
  * **间接/准标识符（Quasi PII）**：送货门牌地址、邮政编码、出生日期、IP 地址、设备指纹。
* **法律管辖**：欧盟 **GDPR**、美国加州 **CCPA**、中国《个人信息保护法（PIPL）》。

### 2. PCI-DSS（Payment Card Industry Data Security Standard，支付卡行业安全标准）
* **行业定义**：由 Visa、MasterCard、American Express 等全球六大国际卡组织联合制定的**金融支付卡数据安全全球强制性规范**。
* **核心保护目标**：
  * **PAN（Primary Account Number）**：15 位或 16 位的信用卡/借记卡主账号；
  * **SAD（Sensitive Authentication Data）**：卡背 CVV/CVC 码、PIN 码、磁条/芯片等效数据。
* **红线要求**：
  * **SAD 严禁以任何形式被存储或传输**；
  * **PAN 严禁明文发送给任何未通过 PCI-DSS 认证的第三方系统**（云端大模型 API 均未获得 PCI-DSS 认证，一旦卡号明文外发，卡组织可直接吊销商户收单牌照）。

### 3. 动态脱敏（Dynamic Data Masking, DDM）与静态脱敏的本质区别
* **静态脱敏（Static Data Masking）**：离线落盘脱敏。在数据库备份或测试环境初始化时，将真实数据一次性覆盖替换（如 `张三` 改为 `张*`），原数据被物理破坏。
* **动态脱敏（Dynamic Data Masking）**：**在线内存拦截（In-flight Masking）**。
  * 数据库中保留合法业务真实数据；
  * 数据在流经 Harness 内存并组装给大模型的前一毫秒，由控制环截断并动态替换为结构化代币（Token Placeholder，如 `{{CREDIT_CARD_1}}`）；
  * 模型处理完毕后，再在受控的安全宿主环境内部按需反向还原（De-tokenization）。**敏感明文全生命周期绝不出内网！**

### 4. 掩码引擎（Tokenization / Masking Engine）
掩码引擎是 Agent Harness 的“信息防辐射滤镜”。其核心职能是：
1. **精准识别**：从混杂各异的自由文本中无遗漏捕获敏感实体；
2. **结构化代币化**：生成带有类型语义的代号（如 `{{BUYER_NAME_1}}`），保持自然语言语义连贯，确保大模型理解上下文意图；
3. **加盐可逆绑定**：在单次运行的私有堆内存中建立映射，执行结束物理清空。

---

## 二、 三轨引擎底层数学与算法工作原理

面对生产环境中**强规则数字**、**海量专有词典**与**弱模式口语化表达**共存的复杂现状，Cogniva Harness 采用了三轨并行分工与区间仲裁架构：

```
                ┌────────────────────────────────────────────────────────┐
                │          待组装原始输入 (买家工单、聊天、OCR 文本)         │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           Hook 2 三轨并行流水线 (Parallel Tri-Track)                            │
│                                                                                                 │
│  ▌第一轨：正则 + Luhn 校验和 (Regex + Luhn)                                                      │
│    • 目标：强格式规则数据 (信用卡卡号、国际电话、标准邮箱)                                      │
│    • 机制：正则粗筛 ➔ Luhn 数学校验 ➔ 100% 精准识别真卡号 (剔除订单号/长流水号)                 │
│                                                                                                 │
│  ▌第二轨：Aho-Corasick 多模式自动机 (AC Automaton)                                              │
│    • 目标：海量专有词典 (全球 10,000+ 地名、物流海外仓代号、核心供应商代码)                      │
│    • 机制：Trie 字典树 + 失败指针 (Fail Pointer)，仅需单次扫描 O(N) 命中全量静态敏感词          │
│                                                                                                 │
│  ▌第三轨：轻量级本地 NER 模型 (Local Compact NER)                                               │
│    • 目标：非结构化开放集弱模式 (非标准自然人英文姓名、口语化街道地址、自报称谓)                │
│    • 机制：本地 ONNX Runtime 极速轻量命名实体识别，不依赖外网 API，杜绝未脱敏数据外流           │
└───────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │      跨轨重叠区间仲裁器 (Interval Conflict Arbiter)       │
                │        规则优先 ➔ 长度优先 ➔ 词典优先 ➔ 模型兜底         │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │  生成安全上下文 (SanitizedContext) + 临时加盐保险库     │
                │  "买家 {{BUYER_NAME_1}} 的信用卡 {{CREDIT_CARD_1}}..." │
                └────────────────────────────────────────────────────────┘
```

---

### 1. 第一轨：正则与数学校验和引擎（Regex + Luhn Checksum）

#### 业务痛点：长数字“误杀”危机
电商系统中充斥着长纯数字字符串：16 位订单号（如 `2026110389271104`）、物流运单条码、产品 EAN-13 码。如果单纯使用正则表达式 `\b\d{16}\b` 进行无差别匹配替换，**会导致正常的业务订单号被当作信用卡全量误杀**，使大模型彻底丧失决策基础。

#### 破局关键：ISO/IEC 7812 与 Luhn（模 10）数学校验算法
全球所有主流金融卡（Visa、MasterCard、American Express 等）的卡号最后一位均为**数学校验位（Checksum Digit）**，完全遵循 Luhn 算法。

##### Luhn 算法数学公式与执行推导步骤：
设卡号数字序列从左至右为 $d_1, d_2, \dots, d_n$（$n$ 通常为 16），从右向左进行逆向加权：

1. **反向索引**：以最右侧校验位 $d_n$ 为第 1 位（奇数位）；
2. **偶数位倍增**：对所有偶数位数字 $d_{n-1}, d_{n-3}, \dots$ 乘以 2：
   $$f(x) = \begin{cases} 2x, & \text{若 } 2x \le 9 \\ 2x - 9, & \text{若 } 2x > 9 \end{cases}$$
3. **奇数位保持**：奇数位数字保持不变；
4. **全量求和**：计算所有位调整后的总累加和：
   $$S = \sum_{k=1}^{n} g(d_k)$$
5. **模 10 判定准则**：
   $$S \equiv 0 \pmod{10}$$
   **只有当 $S \pmod{10} == 0$ 时，该 16 位数字才是真正的金融支付卡号**；普通的业务订单号通过 Luhn 校验的概率不足 $10\%$，从而实现超过 $90\%$ 的误杀过滤。

---

### 2. 第二轨：Aho-Corasick 高性能多模式自动机（AC Automaton）

#### 业务痛点：多模式串暴跌陷阱
跨境电商业务需要保护成千上万个专有名词：全球 10,000+ 敏感地名、3,000 家核心供应商代码（如 `SUPPLIER-SHENZHEN-09`）、500 个欧洲海外仓编码（如 `WH-FR-PARIS-NORD-03`）。
若采用传统单模式正则或 `string.contains()` 进行循环匹配，时间复杂度高达：
$$\mathcal{O}(M \times \sum |P_i|)$$
（$M$ 为输入文本长度，$P_i$ 为各模式串长度）。一次请求需耗费数百毫秒，导致控制环吞吐量急剧恶化。

#### 算法内核：Trie 树 + 失败指针（Fail Pointer）
Aho-Corasick 算法将所有敏感词在预加载阶段构建成一棵 **Trie 字典树**，并在节点之间预先计算**失败转移指针（Failure Transition）**与**输出链（Output Pointer）**。

* **时间复杂度**：
  $$\mathcal{O}(N + Z)$$
  （$N$ 为输入文本长度，$Z$ 为命中的敏感词总数）。**无论词典中包含 1 万个词还是 10 万个词，扫描耗时完全与词典规模解耦**；
* **无回溯跳转**：扫描过程中输入指针永不后退。一旦在某个分支匹配失败，自动机沿着 `Fail Pointer` 瞬间滑向具有最长公共前后缀的等价状态，在 $1 \sim 2$ 毫秒内完成全量文本词典检测。

---

### 3. 第三轨：轻量级本地 NER 模型引擎（Local Compact NER）

#### 业务痛点：非结构化开放集弱模式
* 买家口语化留言：“*Hi, this is Jean-Luc Moreau, I live at 14 Rue de Rivoli near the Louvre...*”
* 人名与详细门牌地址具有无限拼写可能，既无法用正则穷举，也无法放入静态词典。

#### 架构红线与破局方案
* **绝对禁令**：**严禁将未脱敏文本发给外部云端 LLM 进行脱敏识别！** 这本身就属于违法的数据跨境出境。
* **本地化推演**：在 L2 Harness 进程容器内，利用 **ONNX Runtime** 加载本地紧凑型命名实体识别模型（如 INT8 量化微调版 `mDeBERTa-v3-NER`）：
  * **零网络开销**：推演在 Worker 本地 CPU/内存中闭环，数据物理不出机房；
  * **极限低延迟**：量化模型推理耗时压缩在 $5 \sim 15\text{ms}$ 以内；
  * **精准标注**：对人名（`B-PER`, `I-PER`）与街道地址（`B-LOC`, `I-LOC`）提供概率评分。

---

## 三、 跨国电商退赔母案：三轨端到端步进实战

为了让您直观理解三轨如何在毫秒级协同作业，我们以**“售后争议调解与退赔决策 Agent”**处理法国巴黎手表客诉母案为例，进行**全流程七步数据流穿透拆解**：

---

### 【业务母案全景背景】
* **买家画像**：法国巴黎买家 `Jean-Luc Moreau`；
* **争议标的**：售价 **$180** 的钛合金运动手表（Titanium Sport Watch）；
* **客诉事实**：表盘有细微划痕，买家要求仅退款 **$50**，否则发起拒付（Chargeback）；
* **关联上下游元数据**：工单中混入了买家留言、内部海外仓条码以及供应商代码。

---

### Step 1: 原始输入上下文注入（Raw Context Inflow）

买家在售后前端提交留言，CRM 售后工单系统将上下文推入 Kafka，Worker 拾取并组装出如下原始文本片段：

> **[原始工单输入文本]**：  
> *"Customer Jean-Luc Moreau (Phone: +33-6-12345678, Address: 14 Rue de Rivoli, Paris 75001) reported scratches on order 2026110398471201. Buyer demanded $50 refund to Visa card 4532015000000008, or threatened chargeback. Warehouse lot: WH-FR-PARIS-NORD-03, Supplier: SUPPLIER-SZ-WATCH-09."*

---

### Step 2: 第一轨（Regex + Luhn Checksum）处理细节

第一轨启动，扫描文本中所有符合长数字、电话与邮箱规则的候选字串：

```
候选数字 1: 2026110398471201 (16 位订单号)
候选数字 2: 4532015000000008 (16 位银行卡号)
候选字串 3: +33-6-12345678    (国际 E.164 电话号码)
```

1. **针对候选数字 1（`2026110398471201`）执行 Luhn 校验**：
   * 逆序：`1, 0, 2, 1, 7, 4, 8, 9, 3, 0, 1, 1, 6, 2, 0, 2`
   * 偶数位翻倍求和：
     * $d_2(0) \times 2 = 0$
     * $d_4(1) \times 2 = 2$
     * $d_6(4) \times 2 = 8$
     * $d_8(9) \times 2 = 18 \rightarrow 1+8=9$
     * $d_{10}(0) \times 2 = 0$
     * $d_{12}(1) \times 2 = 2$
     * $d_{14}(2) \times 2 = 4$
     * $d_{16}(2) \times 2 = 4$
   * 全量累加和 $S = 43$；
   * 计算 $43 \pmod{10} = 3 \neq 0$ ❌ **Luhn 校验失败！**
   * **决策判定**：**此为普通业务订单号，绝非信用卡，坚决不脱敏！保留明文供模型比对订单**。
2. **针对候选数字 2（`4532015000000008`）执行 Luhn 校验**：
   * 逆序：`8, 0, 0, 0, 0, 0, 0, 0, 5, 1, 0, 2, 3, 5, 4`
   * 偶数位翻倍求和计算得：总和 $S = 40$；
   * 计算 $40 \pmod{10} = 0$ ✔️ **Luhn 校验成功！**
   * **决策判定**：**此为真实 Visa 信用卡卡号！锁定区间 `[195, 211]`，打标 `CREDIT_CARD`**。
3. **针对国际电话（`+33-6-12345678`）**：
   * 命中 E.164 正则规则，锁定区间 `[35, 50]`，打标 `PHONE_NUMBER`。

---

### Step 3: 第二轨（Aho-Corasick 多模式自动机）处理细节

第二轨启动，加载预热好的全球静态敏感字典 Trie 树，单次流式扫描文本：

1. **匹配敏感仓储代码**：
   * 命中词典词条：`WH-FR-PARIS-NORD-03`；
   * 锁定区间 `[254, 274]`，打标 `LOGISTICS_WH`。
2. **匹配保密供应商代码**：
   * 命中词典词条：`SUPPLIER-SZ-WATCH-09`；
   * 锁定区间 `[286, 307]`，打标 `SUPPLIER_CODE`。

---

### Step 4: 第三轨（Local Compact NER 模型）处理细节

第三轨启动，本地 ONNX Runtime 驱动量化 NER 模型进行实体边界推断：

1. **人名实体识别（PER）**：
   * 词元序列：`Jean` (B-PER), `-` (I-PER), `Luc` (I-PER), `Moreau` (I-PER)；
   * 综合置信度：$0.982$；
   * 锁定区间 `[10, 25]`（`Jean-Luc Moreau`），打标 `BUYER_NAME`。
2. **街道与住址实体识别（LOC）**：
   * 词元序列：`14` (B-LOC), `Rue` (I-LOC), `de` (I-LOC), `Rivoli` (I-LOC), `,` (I-LOC), `Paris` (I-LOC), `75001` (I-LOC)；
   * 综合置信度：$0.965$；
   * 锁定区间 `[61, 91]`（`14 Rue de Rivoli, Paris 75001`），打标 `SHIPPING_ADDRESS`。

---

### Step 5: 跨轨重叠区间仲裁器（Interval Conflict Arbiter）消除冲突

仲裁器收集三轨产出的全部区间候选：

| 匹配项 | 来源轨 | 区间范围 | 打标类型 | 仲裁判定 |
| :--- | :--- | :--- | :--- | :--- |
| `Jean-Luc Moreau` | 轨三 (NER) | `[10, 25]` | `BUYER_NAME` | ✔️ 无冲突，采纳 |
| `+33-6-12345678` | 轨一 (Regex) | `[35, 50]` | `PHONE_NUMBER` | ✔️ 无冲突，采纳 |
| `14 Rue de Rivoli, Paris 75001` | 轨三 (NER) | `[61, 91]` | `SHIPPING_ADDRESS` | ✔️ 无冲突，采纳 |
| `2026110398471201` | 轨一 (Regex+Luhn) | `[114, 130]` | 无 (Luhn失败) | ❌ 剔除，不予脱敏 |
| `4532015000000008` | 轨一 (Regex+Luhn) | `[195, 211]` | `CREDIT_CARD` | ✔️ 强规则通过，采纳 |
| `WH-FR-PARIS-NORD-03` | 轨二 (AC自动机) | `[254, 274]` | `LOGISTICS_WH` | ✔️ 词典精确命中，采纳 |
| `SUPPLIER-SZ-WATCH-09` | 轨二 (AC自动机) | `[286, 307]` | `SUPPLIER_CODE` | ✔️ 词典精确命中，采纳 |

---

### Step 6: 占位符替换与私有加盐保险库注册

引擎根据仲裁结果，生成结构化代币，并向单次 Run 私有堆内存中的 `EphemeralPiiVault` 进行动态注册：

#### 临时内存保险库注册明细（Worker 私有堆内存）：
```json
{
  "{{BUYER_NAME_1}}": "Jean-Luc Moreau",
  "{{PHONE_NUMBER_1}}": "+33-6-12345678",
  "{{SHIPPING_ADDRESS_1}}": "14 Rue de Rivoli, Paris 75001",
  "{{CREDIT_CARD_1}}": "4532015000000008",
  "{{LOGISTICS_WH_1}}": "WH-FR-PARIS-NORD-03",
  "{{SUPPLIER_CODE_1}}": "SUPPLIER-SZ-WATCH-09"
}
```

---

### Step 7: 生成安全脱敏上下文（SanitizedContext）

最终输送给云端大模型 API 的安全文本如下：

> **[模型最终看到的无害上下文]**：  
> *"Customer **{{BUYER_NAME_1}}** (Phone: **{{PHONE_NUMBER_1}}**, Address: **{{SHIPPING_ADDRESS_1}}**) reported scratches on order **2026110398471201**. Buyer demanded $50 refund to Visa card **{{CREDIT_CARD_1}}**, or threatened chargeback. Warehouse lot: **{{LOGISTICS_WH_1}}**, Supplier: **{{SUPPLIER_CODE_1}}**."*

#### 关键战果：
1. **0 真实 PII / 支付数据出境**：大模型 API 完全不知道买家真实姓名、银行卡号与法国住址；
2. **0 误杀业务订单号**：`2026110398471201` 完好无损保留，大模型能精准调用后台 ERP 工具查询该订单的物流轨迹与妥投证明；
3. **闭环可逆还原**：大模型做出决策 *“同意退款 $50 至 {{CREDIT_CARD_1}}”*，Harness 在本地工具调用时利用 `EphemeralPiiVault` 将真实卡号调出执行退款，且内存随当前 Run 完结自动 GC 零化！

---

## 四、 生产级 Java 21 落地架构实现

以下是在 Harness `before_context` 中运行的工业级 Java 21 三轨脱敏引擎与冲突仲裁完整工程实现：

```java
package com.cogniva.agent.harness.security;

import java.util.*;
import java.util.concurrent.*;
import java.util.regex.*;

/**
 * Hook 2: 三轨高性能 PII 动态脱敏与掩码引擎 (Java 21 LTS 规范)
 */
public final class TriTrackPiiTokenizationEngine {

    // 匹配 13~19 位连续数字 (候选信用卡号)
    private static final Pattern CARD_PATTERN = Pattern.compile("\\b\\d{13,19}\\b");
    // 匹配 E.164 国际电话号码
    private static final Pattern PHONE_PATTERN = Pattern.compile("\\+\\d{1,3}-\\d{1,4}-\\d{6,10}");

    /**
     * 不可变区间记录
     */
    public record MatchInterval(int start, int end, String tokenType, String rawValue) {
        public int length() {
            return end - start;
        }
    }

    /**
     * 第一轨：正则 + Luhn 模 10 校验和算法
     */
    public List<MatchInterval> scanTrackOneRegexAndLuhn(String text) {
        List<MatchInterval> matches = new ArrayList<>();

        // 1. 扫描银行卡候选
        Matcher cardMatcher = CARD_PATTERN.matcher(text);
        while (cardMatcher.find()) {
            String candidate = cardMatcher.group();
            if (isValidLuhn(candidate)) {
                matches.add(new MatchInterval(cardMatcher.start(), cardMatcher.end(), "CREDIT_CARD", candidate));
            }
        }

        // 2. 扫描国际电话
        Matcher phoneMatcher = PHONE_PATTERN.matcher(text);
        while (phoneMatcher.find()) {
            matches.add(new MatchInterval(phoneMatcher.start(), phoneMatcher.end(), "PHONE_NUMBER", phoneMatcher.group()));
        }

        return Collections.unmodifiableList(matches);
    }

    /**
     * 严格 Luhn 模 10 算法实现
     */
    public static boolean isValidLuhn(String cardNumber) {
        int sum = 0;
        boolean alternate = false;
        for (int i = cardNumber.length() - 1; i >= 0; i--) {
            int digit = Character.digit(cardNumber.charAt(i), 10);
            if (digit < 0) return false;

            if (alternate) {
                digit *= 2;
                if (digit > 9) {
                    digit = (digit % 10) + 1; // 等价于 digit -= 9
                }
            }
            sum += digit;
            alternate = !alternate;
        }
        return (sum % 10 == 0);
    }

    /**
     * 跨轨区间冲突仲裁器 (按起始位置升序，重叠时长度优先、规则优先)
     */
    public List<MatchInterval> arbitrateConflicts(List<MatchInterval> allMatches) {
        List<MatchInterval> sorted = new ArrayList<>(allMatches);
        // 仲裁规则：起始位置升序；重叠时优先保留长度较长区间；再者优先保留信用卡
        sorted.sort(Comparator.comparingInt(MatchInterval::start)
                .thenComparing((a, b) -> Integer.compare(b.length(), a.length()))
                .thenComparing(a -> "CREDIT_CARD".equals(a.tokenType()) ? -1 : 1));

        List<MatchInterval> resolved = new ArrayList<>();
        int lastEnd = -1;

        for (MatchInterval current : sorted) {
            if (current.start() >= lastEnd) {
                resolved.add(current);
                lastEnd = current.end();
            }
        }
        return Collections.unmodifiableList(resolved);
    }

    /**
     * 生产级三轨并发执行并构建安全上下文与临时保险库
     */
    public SanitizationOutput executeTriTrack(String rawInput, String runId, String salt) {
        List<MatchInterval> aggregatedMatches = new CopyOnWriteArrayList<>();

        // 采用 Java 21 结构化并发 (Structured Concurrency) 并行运行三轨
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var sub1 = scope.fork(() -> scanTrackOneRegexAndLuhn(rawInput));
            var sub2 = scope.fork(() -> scanTrackTwoAhoCorasick(rawInput));
            var sub3 = scope.fork(() -> scanTrackThreeLocalNer(rawInput));

            scope.join();
            scope.throwIfFailed();

            aggregatedMatches.addAll(sub1.get());
            aggregatedMatches.addAll(sub2.get());
            aggregatedMatches.addAll(sub3.get());
        } catch (Exception e) {
            throw new SecurityException("Tri-track PII scanning execution failed", e);
        }

        // 冲突区间仲裁
        List<MatchInterval> winningIntervals = arbitrateConflicts(aggregatedMatches);

        // 组装脱敏文本与私有加盐保险库
        StringBuilder sanitizedBuffer = new StringBuilder();
        int cursor = 0;
        Map<String, String> vaultMap = new HashMap<>();

        int cardCount = 1, phoneCount = 1, nameCount = 1, addrCount = 1, whCount = 1, supCount = 1;

        for (MatchInterval interval : winningIntervals) {
            sanitizedBuffer.append(rawInput, cursor, interval.start());

            String placeholder = switch (interval.tokenType()) {
                case "CREDIT_CARD"      -> "{{CREDIT_CARD_" + (cardCount++) + "}}";
                case "PHONE_NUMBER"     -> "{{PHONE_NUMBER_" + (phoneCount++) + "}}";
                case "BUYER_NAME"       -> "{{BUYER_NAME_" + (nameCount++) + "}}";
                case "SHIPPING_ADDRESS" -> "{{SHIPPING_ADDRESS_" + (addrCount++) + "}}";
                case "LOGISTICS_WH"     -> "{{LOGISTICS_WH_" + (whCount++) + "}}";
                case "SUPPLIER_CODE"    -> "{{SUPPLIER_CODE_" + (supCount++) + "}}";
                default                 -> "{{SENSITIVE_DATA}}";
            };

            sanitizedBuffer.append(placeholder);
            vaultMap.put(placeholder, interval.rawValue());
            cursor = interval.end();
        }
        sanitizedBuffer.append(rawInput.substring(cursor));

        return new SanitizationOutput(
                sanitizedBuffer.toString(),
                new EphemeralPiiVault(runId, salt, vaultMap)
        );
    }

    // 模拟第二轨与第三轨实现
    private List<MatchInterval> scanTrackTwoAhoCorasick(String text) {
        List<MatchInterval> list = new ArrayList<>();
        int whIdx = text.indexOf("WH-FR-PARIS-NORD-03");
        if (whIdx >= 0) {
            list.add(new MatchInterval(whIdx, whIdx + "WH-FR-PARIS-NORD-03".length(), "LOGISTICS_WH", "WH-FR-PARIS-NORD-03"));
        }
        int supIdx = text.indexOf("SUPPLIER-SZ-WATCH-09");
        if (supIdx >= 0) {
            list.add(new MatchInterval(supIdx, supIdx + "SUPPLIER-SZ-WATCH-09".length(), "SUPPLIER_CODE", "SUPPLIER-SZ-WATCH-09"));
        }
        return list;
    }

    private List<MatchInterval> scanTrackThreeLocalNer(String text) {
        List<MatchInterval> list = new ArrayList<>();
        int nameIdx = text.indexOf("Jean-Luc Moreau");
        if (nameIdx >= 0) {
            list.add(new MatchInterval(nameIdx, nameIdx + "Jean-Luc Moreau".length(), "BUYER_NAME", "Jean-Luc Moreau"));
        }
        int addrIdx = text.indexOf("14 Rue de Rivoli, Paris 75001");
        if (addrIdx >= 0) {
            list.add(new MatchInterval(addrIdx, addrIdx + "14 Rue de Rivoli, Paris 75001".length(), "SHIPPING_ADDRESS", "14 Rue de Rivoli, Paris 75001"));
        }
        return list;
    }

    public record SanitizationOutput(String sanitizedText, EphemeralPiiVault ephemeralVault) {}

    public static final class EphemeralPiiVault {
        private final String runId;
        private final String salt;
        private final Map<String, String> internalMap;

        public EphemeralPiiVault(String runId, String salt, Map<String, String> map) {
            this.runId = runId;
            this.salt = salt;
            this.internalMap = Map.copyOf(map);
        }

        public Optional<String> deTokenize(String token) {
            return Optional.ofNullable(internalMap.get(token));
        }
    }
}
```

---

## 五、 基于 ASD-STE100 规范的工程技术标准

本章节遵循国际航空与工业标准 **ASD-STE100（Simplified Technical English）** 编写。旨在通过严格受控词汇、短句结构（$\le 20$ 词）与主动语态，消除跨国开发与合规团队的技术理解歧义。

### SECTION 1: PURPOSE AND DEFINITIONS / 目的与术语定义

#### STE English:
1. This section gives mandatory rules for PII tokenization and masking in Hook 2.
2. **PII**: Personally Identifiable Information that identifies a living person.
3. **PCI-DSS**: Security standards for credit card data and payment transactions.
4. **Tokenization**: The replacement of sensitive data with non-sensitive placeholder tokens.
5. **Luhn Algorithm**: A formula that checks the checksum digit of a credit card number.
6. **Aho-Corasick Automaton**: A state machine that finds many dictionary words in one scan.
7. **Local NER**: A machine learning model that finds names and addresses inside the worker.

#### 标准中文对照：
1. 本章节给出 Hook 2 中 PII 代币化与掩码处理的强制性规则。
2. **PII**：能够识别特定自然人的个人身份信息。
3. **PCI-DSS**：关于信用卡数据与支付交易的安全标准。
4. **代币化（Tokenization）**：使用非敏感占位代号替换敏感数据的处理过程。
5. **Luhn 算法**：检验信用卡卡号校验和位数的数学公式。
6. **Aho-Corasick 自动机**：在单次扫描中匹配多个字典关键词的状态机。
7. **本地 NER**：在 Worker 内部识别姓名与地址的机器学习模型。

---

### SECTION 2: OPERATIONAL RULES AND TECHNICAL INVARIANTS / 操作规程与不可变技术约束

#### STE English:
1. The engine must scan all context text before it calls the model.
2. Track 1 must run the Luhn algorithm on all 16-digit number candidates.
3. Do not mask 16-digit numbers if the Luhn checksum is not correct.
4. Track 2 must scan the static sensitive dictionary with the Aho-Corasick algorithm.
5. Track 3 must use a local NER model to find person names and street addresses.
6. Do not send unmasked text to remote AI models to find PII.
7. The arbiter must give top priority to valid credit card numbers.
8. The engine must replace sensitive data with structured tokens like `{{CREDIT_CARD_1}}`.
9. The engine must store raw sensitive values in the ephemeral vault only.
10. The harness must delete the ephemeral vault after the run completes.
11. Do not save the raw values of the ephemeral vault to the database.

#### 标准中文对照：
1. 引擎在调用模型之前，必须先扫描全部上下文文本。
2. 第一轨必须对所有 16 位候选数字运行 Luhn 算法。
3. 若 Luhn 校验和不正确，严禁掩码该 16 位数字。
4. 第二轨必须使用 Aho-Corasick 算法扫描静态敏感词典。
5. 第三轨必须使用本地 NER 模型识别人名与街道地址。
6. 严禁向远程 AI 模型发送未掩码文本以识别 PII。
7. 仲裁器必须对合法的信用卡卡号赋予最高优先级。
8. 引擎必须使用如 `{{CREDIT_CARD_1}}` 等结构化代币替换敏感数据。
9. 引擎必须且仅能将敏感原始明文存放在临时保险库中。
10. Harness 必须在本次任务运行结束后删除临时保险库。
11. 严禁将临时保险库中的原始明文持久化保存至数据库。

---

### SECTION 3: FAILURE CONDITIONS AND CORRECTIVE ACTIONS / 故障条件与修正动作

#### STE English:
1. **Condition A: Luhn Verification Library Crashes**:
   * Cause: Bad numeric input string or integer overflow.
   * Action: The harness isolates the candidate token.
   * Action: The harness tags the token as sensitive by default.
   * Action: The system issues an alert and continues safely.
2. **Condition B: Overlapping Matches Between Track 1 and Track 3**:
   * Cause: NER model tags a credit card number as an address code.
   * Action: The arbiter accepts the Track 1 credit card match.
   * Action: The arbiter cancels the Track 3 address match for that range.
3. **Condition C: Local NER Engine Runs Out of Memory**:
   * Cause: The model worker process has insufficient heap RAM.
   * Action: The engine falls back to Track 1 regex and Track 2 dictionary.
   * Action: The harness flags the run for strict human supervision.

#### 标准中文对照：
1. **故障条件 A：Luhn 校验库崩溃**：
   * 触发起因：非法数字输入字符串或整型溢出。
   * 修正动作：Harness 隔离该候选代币。
   * 修正动作：Harness 默认将该代币标为敏感数据进行兜底掩码。
   * 修正动作：系统发出告警并保持安全继续运行。
2. **故障条件 B：第一轨与第三轨匹配区间重叠**：
   * 触发起因：NER 模型将信用卡卡号误标为地址编码的一部分。
   * 修正动作：仲裁器采纳第一轨的信用卡匹配判定。
   * 修正动作：仲裁器取消该区间内第三轨的地址匹配。
3. **故障条件 C：本地 NER 引擎内存耗尽（OOM）**：
   * 触发起因：模型 Worker 进程堆内存不足。
   * 修正动作：引擎优雅降级至第一轨正则与第二轨静态词典。
   * 修正动作：Harness 将本次运行打上标记，转入严格的人工监督复核。

---

## 六、 全链路知识库双向链接

* ⬅️ **回溯 Hook 2 主文档**：[09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md](../09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md#3-功能三三轨高性能-pii-动态脱敏与掩码引擎multi-track-pii-tokenization-engine)（查看功能三整体架构与脱敏代号规范）
* 📂 **穿透关联专属附录**：
  * [09-附录-配置元数据水化与物理Prompt模具架构设计与Java落地全景.md](./09-附录-配置元数据水化与物理Prompt模具架构设计与Java落地全景.md)
  * [09-附录-数据合规与隐私安全防御门禁-电商售后退赔实战与STE100规范全景.md](./09-附录-数据合规与隐私安全防御门禁-电商售后退赔实战与STE100规范全景.md)
  * [09-附录-GDPR长臂管辖与拒绝权转人工机制-STE100规范全景.md](./09-附录-GDPR长臂管辖与拒绝权转人工机制-STE100规范全景.md)
* 🛡️ **穿透 L6/L2 纵深防御解析**：[06-L6-AIG规则扫描与L2-Harness提权防御-纵深防御深度解析.md](../06-L6-AIG规则扫描与L2-Harness提权防御-纵深防御深度解析.md)
* 💼 **穿透电商售后退赔真实业务实战**：[01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../../../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md)

---
*本文档为 Cogniva 架构体系深度解构专题篇，由企业级 Agent 架构基础设施、金融安全与全球数据合规团队联合维护。*
