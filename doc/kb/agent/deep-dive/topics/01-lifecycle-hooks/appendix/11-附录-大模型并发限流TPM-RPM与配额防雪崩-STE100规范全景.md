# 深度解构：大模型并发限流 TPM / RPM 与配额防雪崩全景

> **文档定位**：L2 受控宿主运行时（Harness）高可用与流量工程核心附录——系统剖析大模型服务质量保障体系（TPM、RPM、TPD、Usage Tiers），还原真实电商黑五 100 并发工单击穿 450k TPM 引发 429 级联雪崩的惨烈现场，给出基于 Redis 令牌桶削峰平谷、优先级配额开槽与 Java 21 生产落地代码。  
> **所属专题**：[01-lifecycle-hooks 专题目录](../00-专题总揽与实战索引.md)  
> **孪生姊妹篇**：[11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md](./11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md)（商业计费篇）  
> **关联底层文档**：  
> * [11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md](../11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md)（算力预算预占与 Egress 限流）  
> * [09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md](../09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md)（前置剪枝降低 TPM 压力）  
> * [01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../../../../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md)（售后争议调解退赔母案）

---

## 第一章：ASD-STE100 国际技术标准规范（Technical Specification）

> 本章遵循 **ASD-STE100（简明英语标准，Simplified Technical English）** 国际规范编写。  
> 规范要求：句子长度严格控制在 20 词以内，每句仅表达单一技术指令或判定，动词采用主动语态，严禁使用模棱两可与情绪化词汇。

### 1. PURPOSE AND DEFINITION (目的与定义)
* Model providers enforce strict rate limits on API requests.
* Tokens Per Minute (TPM) limits total token throughput.
* Requests Per Minute (RPM) limits total request count.
* Exceeding these limits causes HTTP 429 errors.
* The Harness must control traffic flow to prevent cascading failures.

### 2. SYSTEM INVARIANTS (系统不变量)
* **Rule 1**: Outgoing traffic must not exceed eighty percent of the provider tier TPM limit.
* **Rule 2**: The rate limiter must check both RPM and TPM before model invocation.
* **Rule 3**: High-priority transactions must use dedicated quota pools.
* **Rule 4**: Failed requests must use exponential backoff with random jitter.

### 3. PROCEDURE (标准执行程序)
* **Step 1**: Calculate the required tokens for the outbound request in Hook 3.
* **Step 2**: Acquire tokens from the distributed token bucket in Redis.
* **Step 3**: Queue the request if the current token bucket is empty.
* **Step 4**: Transmit the request to the model provider when tokens become available.
* **Step 5**: Catch HTTP 429 status codes and apply jittered backoff immediately.
* **Step 6**: Release reserved tokens if the network request fails prematurely.

### 4. WARNINGS AND PROHIBITIONS (警告与操作禁忌)
* **WARNING**: Do not assume large account balances remove rate limits.
* **PROHIBITION**: Do not retry failed requests immediately without backoff delay.
* **PROHIBITION**: Do not share default rate limit pools between batch and real-time tasks.
* **PROHIBITION**: Do not bypass the Harness rate limiter under burst traffic conditions.

---

## 第二章：TPM、RPM、TPD 与 Usage Tier 梯级配额全景解构

在企业级大模型应用中，很多技术负责人常问一个非常朴素的问题：
> **“我们公司明明在大模型云账户里充值了 10 万美元，余额充沛得可以用一年，为什么高峰期系统突然全线报错报死，疯狂弹出 `HTTP 429 Too Many Requests`？”**

答案就在于：**“账户余额（Money）” 解决的是“计费”问题，而 “TPM / RPM（Rate Limits）” 解决的是云厂商基础设施的“防被打崩（Stability）”问题**。

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              大模型云厂商的双重控制阀门                                 │
│                                                                                        │
│     【资金计费阀门 (Billing)】                          【流量配额阀门 (Rate Limits)】    │
│      • 账户充值余额 (Balance)                          • 每分钟请求数 (RPM)              │
│      • 决定能买多少 Tokens (P&L 损益)                   • 每分钟 Token 量 (TPM)           │
│      • 余额不足 ──► 报 402 Payment Required             • 瞬间超频 ──► 报 429 RateLimit   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 核心定义与工业界本质差异

* **RPM (Requests Per Minute，每分钟请求数)**：
  * **含义**：60 秒内允许发起的最大 HTTP API 往返请求次数（无论单次请求是发了 1 个字还是 10 万字）；
  * **物理实质**：保护云厂商网关的 **TCP / HTTP/2 连接池与反向代理并发数**。
* **TPM (Tokens Per Minute，每分钟 Token 吞吐量)**：
  * **含义**：60 秒滑动窗口内允许处理的 **总 Token 数量（包含请求输入 Tokens + 预留输出 Tokens）**；
  * **物理实质**：保护云厂商物理机房内 **GPU 显存占用与 Tensor Core 算力饱和度**。
* **TPD / RPD (Tokens / Requests Per Day，每日配额总量)**：
  * **含义**：单日内累计消耗的 Token 或请求总上限；
  * **物理实质**：企业级账户的“保险丝”，防止由于 Agent 内部死循环或脚本失控导致企业一夜破产。

### 2.2 充值消费与层级绑定（Usage Tiers 梯级对照表）

以 OpenAI GPT-4o 的官方配额阶梯为例，展示云厂商如何将企业分流（不同层级的水龙头差异高达数百倍）：

| 账号等级 (Usage Tier) | 升级门槛 (充值/消费) | TPM 配额限制 (GPT-4o) | RPM 配额限制 | 典型企业承受力 |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1 (个人体验)** | 首次充值 **$5 美元** | **30,000 TPM** | 500 RPM | **极易猝死**：单笔长上下文工单（25k tokens）直接占满配额 |
| **Tier 2 (小微团队)** | 累计消费 **$50 美元** 且满 7 天 | **450,000 TPM** | 5,000 RPM | **无法抗峰**：并发 8 笔真实售后工单即刻打穿熔断 |
| **Tier 3 (企业起步)** | 累计消费 **$100 美元** 且满 7 天 | **800,000 TPM** | 5,000 RPM | 中小电商日常平稳运行，但大促峰值面临 429 风险 |
| **Tier 4 (生产主力)** | 累计消费 **$250 美元** 且满 14 天 | **2,000,000 TPM** | 10,000 RPM | 绝大多数企业级生产系统的推荐最低准入门槛 |
| **Tier 5 (集团独角兽)**| 累计消费 **$1,000 美元** 且满 30 天 | **10,000,000+ TPM** | 10,000 RPM | 支撑跨国大型电商全平台并发客服与智能仲裁 |

---

## 第三章：黑五 100 并发售后退赔工单瞬时击穿实录（车祸现场）

以我们的统一业务母案——**“跨境电商售后争议调解与退赔决策 AI Agent”** 为例，模拟黑五大促（Black Friday）当晚 20:00 的高并发真实车祸：

```
                                 黑五 20:00:00 瞬间涌入 100 笔售后工单
                                                   │
                                                   ▼
                     ┌───────────────────────────────────────────────────────────┐
                     │  微服务无节制并发派发: 100 个 Worker 并发调用 GPT-4o / Claude  │
                     └─────────────────────────────┬─────────────────────────────┘
                                                   │
                          单笔工单平均上下文 8,000 Tokens (含质检图片与规则模具)
                                                   │
                                                   ▼
                          瞬时 Token 需求: 100 × 8,000 = 800,000 Tokens/分
                                                   │
         ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
         ▼ (若企业处于 Tier 2: 450,000 TPM 上限)                                               ▼ (若客户端盲目重试)
【瞬间击穿 TPM 水龙头!】                                                              【引发惊群效应与雪崩!】
云端网关抛出 HTTP 429 RateLimitError                                                  未做退避的客户端同时发起重试
超过 50% 的工单退款流程当场阻塞卡死                                                  二次冲击将云网关封锁窗口延长至数分钟
```

### 3.1 真实数据测算与击穿机理
* **工单特征**：法国巴黎买家 Alice 购买 $180 智能手表表盘划痕争议理赔工单 `ORD-20261104-8839`，单笔工单经历 Step 2 事实核验与 Step 3 运费仲裁时，上下文累积达到 **8,000 Tokens**；
* **瞬时并发暴击**：
  * 100 笔工单在 10 秒内由上游 MQ 消费触发；
  * **RPM 维度**：$100 \text{ Requests} / \text{minute} \ll 5,000 \text{ RPM}$（RPM 负载仅 2%，完全正常）；
  * **TPM 维度**：云厂商在收到请求时，采用**滑动时间窗口瞬时预占**（Prompt Tokens + `max_tokens` 预留输出）：
    $$\text{Instantaneous TPM Demand} = 100 \times 8,000 \text{ Tokens} = \mathbf{800,000 \text{ Tokens / 分钟}}$$
* **惨烈恶果**：
  * 若当前企业账号处于 **Tier 2（450,000 TPM）**：前 56 笔工单被成功接收，第 57 笔开始，云厂商网关直接丢弃请求并返回 `HTTP 429 Too Many Requests: Rate limit reached for model in organization`；
  * **级联雪崩**：上游业务微服务捕获到 429 报错，未经退避直接重试（Retry Loop），使后续正常买家的请求同样被堵死在 429 队列中，长达 20 分钟内全站退赔决策完全失灵。

---

## 第四章：Harness 微内核企业级防 429 削峰平谷架构

为了保证在突发并发下系统 SLA 稳定，受控宿主运行时（Harness）坚决不在业务层裸调大模型 API，而是在 **Hook 3（`before_model`）** 构建高可用流量工程护盾：

```
                      [上游突发 100 笔并发请求]
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 【Hook 3: before_model 分布式流量工程护盾】                             │
│                                                                        │
│ 1. 业务配额分层隔离开槽 (Quota Siloing)                                 │
│    ├── 核心交易与 VIP 退赔池: 独享 70% TPM 配额 (优先放行)               │
│    └── 公开普通售后沙箱池: 限制在 30% TPM 配额 (排队平滑)                │
│                                                                        │
│ 2. Redis 高精度分布式令牌桶 (Distributed Token Bucket)                  │
│    ├── 恒定速率向桶内注水 (按 80% 安全水位: 360,000 Tokens/分)          │
│    └── 请求按预估 Tokens 领令牌; 令牌不足则挂起入队, 绝不超额发出       │
│                                                                        │
│ 3. 抖动指数退避调度器 (Full Jitter Exponential Backoff)                │
│    └── 遭遇偶尔 429 时: Sleep = Uniform(0, min(Backoff_Cap, Base * 2^attempt))│
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │ (平滑削峰后，有序下发)
                                  ▼
                   [大模型云厂商 API: 0 次 429 拦截]
```

### 4.1 核心防护机制一：Redis 分布式令牌桶算法（Token Bucket）
* **算法原语**：
  * 在 Redis 中维护一个以**Token 数量（而非请求次数）**为单位的令牌桶；
  * 令牌产生速率：严格锚定企业账号当前 Tier 值的 **80% 安全水位**（如 Tier 2 的 450k TPM，令牌产生速率设定为每秒注入 $450,000 \times 0.80 / 60 = 6,000$ Tokens）；
  * 任何请求在 Hook 3 出网前，必须先原子预扣对应体积的令牌；
  * 若令牌不足，Worker 线程就地挂起等待或将任务排入延迟消息队列（削峰平谷），**从根本上不给外部云网关抛出 429 的机会**。

### 4.2 核心防护机制二：业务优先级隔离开槽（Quota Siloing）
* 坚决杜绝“全平台业务共享一个默认 API Key”；
* **开槽隔离**：
  * **黄金级（Gold Pool）**：分配给购物车结账、大促核销、高信用买家退款，独享 70% 的 TPM 配额，提供确定性零延迟；
  * **普通级（Silver Pool）**：分配给日常低危售后争议仲裁，共享 25% 配额；
  * **沙箱级（Bronze Sandbox）**：分配给新用户、风控嫌疑用户或离线对账，限制在 5% 配额，发生拥堵时就地异步排队，物理隔离故障。

### 4.3 核心防护机制三：带抖动的全指数退避（Full Jitter Exponential Backoff）
* 当瞬时偶发依然触发 429 时，严禁采用固定间隔重试（如 `sleep(1000)`，会导致所有人同时重试制造惊群重叠）；
* **工业级公式**：
  $$\text{Sleep Time} = \text{Random}(0, \min(T_{max}, T_{base} \times 2^{\text{attempt}}))$$
* 通过加入随机扰动（Jitter），将并发请求在时域上均匀打散，使外部网关平滑愈合。

---

## 第五章：Java 21 生产级分布式 TPM 令牌桶限流器 (`DistributedTokenBucketRateLimiter.java`)

以下为在微内核 Hook 3 阶段拦截流量的工业级 Redis Lua 令牌桶限流实现：

```java
package com.cogniva.agent.harness.ratelimit;

import java.time.Instant;
import java.util.Collections;
import java.util.Objects;

/**
 * Hook 3 分布式 TPM (Tokens Per Minute) 令牌桶限流器
 * 拦截超频请求，防止大模型供应商返回 HTTP 429
 */
public final class DistributedTokenBucketRateLimiter {

    // Redis Lua 脚本: 原子计算令牌填充与消耗
    private static final String TOKEN_BUCKET_LUA_SCRIPT = """
        local bucket_key = KEYS[1]
        local tokens_requested = tonumber(ARGV[1])
        local max_capacity = tonumber(ARGV[2])
        local refill_rate_per_sec = tonumber(ARGV[3])
        local now_sec = tonumber(ARGV[4])

        local data = redis.call('HMGET', bucket_key, 'tokens', 'last_updated')
        local current_tokens = tonumber(data[1])
        local last_updated = tonumber(data[2])

        if current_tokens == nil then
            current_tokens = max_capacity
            last_updated = now_sec
        else
            local elapsed_sec = math.max(0, now_sec - last_updated)
            current_tokens = math.min(max_capacity, current_tokens + (elapsed_sec * refill_rate_per_sec))
            last_updated = now_sec
        end

        if current_tokens >= tokens_requested then
            current_tokens = current_tokens - tokens_requested
            redis.call('HMSET', bucket_key, 'tokens', current_tokens, 'last_updated', last_updated)
            redis.call('EXPIRE', bucket_key, 120) -- 自动回收
            return 1 -- 准入成功
        else
            redis.call('HMSET', bucket_key, 'tokens', current_tokens, 'last_updated', last_updated)
            return 0 -- 令牌不足，限流拦截
        end
        """;

    private final RedisClient redisClient;
    private final String bucketKey;
    private final long maxCapacityTokens;      // 桶容量 (通常设定为 80% Tier TPM)
    private final double refillTokensPerSec;   // 令牌每秒注入速率

    public DistributedTokenBucketRateLimiter(
            RedisClient redisClient, 
            String poolName, 
            long tierTpmLimit) {
        this.redisClient = Objects.requireNonNull(redisClient);
        this.bucketKey = "harness:ratelimit:tpm:" + poolName;
        // 安全策略: 仅使用 80% 配额作为硬顶格，预留 20% 防突刺
        this.maxCapacityTokens = (long) (tierTpmLimit * 0.80);
        this.refillTokensPerSec = (double) this.maxCapacityTokens / 60.0;
    }

    /**
     * 在 Hook 3 发起调用前申请 Token 额度
     */
    public boolean tryAcquire(int requiredTokens) {
        long currentSec = Instant.now().getEpochSecond();
        
        Long result = redisClient.eval(
            TOKEN_BUCKET_LUA_SCRIPT,
            Collections.singletonList(bucketKey),
            String.valueOf(requiredTokens),
            String.valueOf(maxCapacityTokens),
            String.valueOf(refillTokensPerSec),
            String.valueOf(currentSec)
        );

        return result != null && result == 1L;
    }

    // 辅助接口定义
    public interface RedisClient {
        Long eval(String script, java.util.List<String> keys, String... args);
    }
}
```

---

## 第六章：高频面试与架构评审答辩话术

### Q: “大模型接口报 429 时，为什么不能简单地用 Spring Retry 重试 3 次？”
> **实战回答口径**：  
> “在处理大模型 429 报错时，如果采用传统的固定间隔重试（如 Spring Retry 默认重试 3 次），在生产环境中相当于**自杀式放大故障**：  
> 1. **加剧惊群效应（Thundering Herd）**：大模型 429 的本质是云厂商的 TPM 滑动窗口被占满。如果 100 个并发请求在同一秒失败，并在 1 秒后同时重试，会在时域上形成更密集的波峰，导致云厂商网关继续抛出 429，甚至直接触发 IP 封锁；  
> 2. **正确的工程解法有两手**：  
>    * **事前预防（Hook 3）**：在本地 Harness 落地 **Redis 分布式令牌桶**，将外发流量物理平滑在 Tier 额度的 80% 以内，绝不让超频流量漏到公网；  
>    * **事后补偿（Backoff with Jitter）**：必须使用**带随机抖动的指数退避（Full Jitter Backoff）**，将重试时间打散在 $[0, 2^n]$ 随机区间内，配合线程挂起与背压削峰，确保系统平滑自愈。”

---

## 第七章：全链路知识库穿透与双向链接

* ⬅️ **穿透姊妹篇（商业计费与成本精算）**：[11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md](./11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md)
* ➡️ **穿透 Hook 3 模型前门禁**：[11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md](../11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md)
* ⬅️ **穿透 Hook 2 上下文剪枝门禁**：[09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md](../09-Hook2-before_context-隐私脱敏与上下文剪枝落地实战.md)
* 🛡️ **穿透 DoW 恶意算力耗尽防御**：[11-附录-恶意算力耗尽攻击DoW与微内核防御体系-STE100规范全景.md](./11-附录-恶意算力耗尽攻击DoW与微内核防御体系-STE100规范全景.md)
* 💼 **穿透电商售后退赔真实业务母案**：[01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../../../../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md)
* 📑 **返回专题总揽与实战索引**：[00-专题总揽与实战索引.md](../00-专题总揽与实战索引.md)

---
*本文档为 Cogniva 架构体系深度解构专题篇，由企业级 Agent 架构基础设施、流量工程与可靠性稳定性保障团队联合维护。*
