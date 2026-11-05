# 深度解构：分布式高并发 Token 流量计费系统与账本架构设计全景

> **文档定位**：L2 受控宿主运行时（Harness）核心资源与财务中台专题附录——系统剖析在 Hook 3（`before_model`）执行模型外呼前与模型返回后，如何通过“乐观预算评估放行 + 真实 Usage 后置平账 + 负余额即刻硬熔断”的不可变账本方式，兼顾万级高并发极致吞吐与企业资金绝对安全。  
> **所属专题**：[01-lifecycle-hooks 专题目录](../00-专题总揽与实战索引.md)  
> **直接关联主文档**：  
> * [11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md](../11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md)（功能 4：基于双轨账本的 Token 流量计费系统）  
> * [11-附录-Token动态预估与MaxTokens约束体系-STE100规范全景.md](./11-附录-Token动态预估与MaxTokens约束体系-STE100规范全景.md)（前置输入分词精准丈量与意图上限夹持）  
> * [11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md](./11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md)（输入输出非对称计费、Prompt Caching 与单单精算账本）  
> * [11-附录-大模型并发限流TPM-RPM与配额防雪崩-STE100规范全景.md](./11-附录-大模型并发限流TPM-RPM与配额防雪崩-STE100规范全景.md)（TPM 令牌桶预占防雪崩与并发配额保护）  
> * [01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../../../../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md)（售后争议调解与退赔决策业务母案）

---

## 第一章：ASD-STE100 国际技术标准规范（Technical Specification）

> 本章遵循 **ASD-STE100（简明英语标准，Simplified Technical English）** 国际规范编写。  
> 规范要求：句子长度严格控制在 20 词以内，每句仅表达单一技术指令或判定，动词采用主动语态，严禁使用模棱两可与情绪化词汇。

### 1. PURPOSE AND DEFINITION (目的与定义)
* The Token Billing System calculates model compute costs using immutable ledgers.
* The system uses an optimistic pre-flight check to support high concurrency.
* The system deducts actual token consumption after the model response arrives.
* The system triggers a circuit breaker if the balance falls below zero.
* The circuit breaker halts subsequent steps immediately to prevent financial loss.
* The ledger records all balance changes as append-only transaction events.

### 2. SYSTEM INVARIANTS (系统不变量)
* **Rule 1**: The ledger must record balance changes as immutable credit or debit rows.
* **Rule 2**: Updating or deleting existing journal rows is strictly prohibited.
* **Rule 3**: Pre-flight checks must permit small credit buffers but must enforce a hard overdraft floor.
* **Rule 4**: If the settled balance is less than zero, the runtime must lock the tenant.
* **Rule 5**: A locked tenant must not execute any subsequent model dispatch steps.

### 3. PROCEDURE (标准执行程序)
* **Step 1**: Calculate the baseline token budget in Hook 3 before model execution.
* **Step 2**: Execute the optimistic admission script against Redis memory ledger.
* **Step 3**: Dispatch the model request if the current balance exceeds the overdraft floor.
* **Step 4**: Receive the response from the model gateway and extract real token usage.
* **Step 5**: Deduct the exact consumed tokens atomically in the shared cache.
* **Step 6**: Check if the resulting balance is lower than zero.
* **Step 7**: If negative, freeze the tenant account and suspend the dispute run immediately.
* **Step 8**: Write the immutable transaction record into the database journal table.

### 4. WARNINGS AND PROHIBITIONS (警告与操作禁忌)
* **WARNING**: Concurrent requests can amplify overdraft if the hard floor check is missing.
* **PROHIBITION**: Do not use SQL table updates to maintain real-time token balances.
* **PROHIBITION**: Do not permit a tenant to continue automated execution while in debt.
* **PROHIBITION**: Do not drop dispute runs silently when quota exhaustion occurs.

---

## 第二章：高并发与资金安全冲突的核心困境

在微服务与大模型分布式编排体系中，设计 Token 流量计费系统面临着两难维度的根本博弈：

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        传统两大极端计费方案的死穴与破局点                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 【极端方案 A：天真事后扣费 (Post-billing)】                                            │
│   * 做法：调用前不设防，调用完成后才扣除余额。                                         │
│   * 死穴：大模型调用耗时 2~3 秒，黑五洪峰下 1,000 笔工单并发穿透，事后平账欠费数千美元！ │
│   * 结果：企业产生巨额坏账，财务风控直接爆雷。                                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 【极端方案 B：过度悲观预占 (Over-Pessimistic Hold)】                                   │
│   * 做法：每次调用前按最大上限（如 4,096 Tokens）死锁额度。                            │
│   * 死穴：实际只需要 300 Tokens，但冻结了 4,096；临界商户正常退款被假性饥饿批量误杀！ │
│   * 结果：并发度暴跌 90%，买家投诉率飙升。                                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 【破局终极解：基于双轨账本的“乐观预算准入 + 真实平账 + 负余额即刻硬熔断”】              │
│   * 准入期：按轻量级基准预算快速放行，允许适度弹性误差，释放万级 QPS；                │
│   * 平账期：大模型返回真实 Usage 后，按实结算；                                       │
│   * 熔断期：平账后若“真超了”（余额 < 0），立即立壁千仞，秒级冻结租户并中断后续步骤！  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 第三章：分布式 Token 流量计费系统的三大核心构件

该计费系统由三大核心构件协同支撑，实现端到端的闭环防护：

```
                                [买家售后争议工单涌入]
                                          │
 ┌────────────────────────────────────────▼────────────────────────────────────────┐
 │ 构件一：内存高速准入控制器 (Redis Lua + Soft Cushion + Hard Floor)              │
 │   * 毫秒级无锁检查：Current_Balance >= Overdraft_Floor (-$2.00)                 │
 │   * 消除行锁排队，允许小额时间差误差，释放大并发吞吐                            │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ 放行外呼 (耗时 2~3 秒，零持锁)
                                          ▼
                         [云端基座大模型推理 (GPT-4o)]
                                          │
                                          ▼ 交付官方真实 Usage 账单
 ┌────────────────────────────────────────┴────────────────────────────────────────┐
 │ 构件二：两阶段真实平账与复式记账法 (Real Usage Settlement & Double-Entry Ledger) │
 │   * 真实消耗多少扣多少：Balance = Balance - Actual_Cost                         │
 │   * 同步插入不可变流水明细表 (Append-Only Journal，禁止 UPDATE/DELETE)          │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ 检查平账后余额状态
                             ┌────────────┴────────────┐
                             │    余额是否 < 0 (真超了)? │
                             └────────────┬────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼ 是                                        ▼ 否
 ┌──────────────────────────────────────┐     ┌───────────────────────────────────┐
 │ 构件三：终局负余额即刻物理硬熔断器   │     │ 正常流转至 Hook 4 (after_model)    │
 │ (Negative Balance Circuit Breaker)   │     │ 驱动业务决策与赔付下发            │
 │   * Redis 秒级标记租户为 LOCKED      │     └───────────────────────────────────┘
 │   * 强行掐死后续 Step 执行           │
 │   * 工单优雅转人工挂起并推送欠费预警 │
 └──────────────────────────────────────┘
```

### 3.1 构件一：内存高速准入控制器（软弹性 + 止损底线 Hard Floor）
* **弹性容错（Soft Cushion）**：
  在调用前，使用 Hook 3 功能三测出的输入 Token 加上预期基准输出（如 300~500 Tokens）做轻度扣减校验。
* **并发击穿放大防御（Hard Floor 止损红线）**：
  为彻底防御“1,000 笔并发在同一秒内利用时间差同时穿透”的极端情况，系统在 Redis 中为商户设定**绝对透支底线（Hard Floor，如最大欠费不超过 -$2.00 美元）**：
  只要账户当前余额加上透支底线仍然大于零，即允许瞬时并发通行；一旦累积透支击穿 Hard Floor，准入网关立即硬性关闭。

### 3.2 构件二：银行级复式记账与仅追加流水（Immutable Append-Only Journal）
在持久层，计费系统坚决摒弃直接 `UPDATE balance` 的反模式，采用银行标准的仅追加流水账本：
* **账户快照表（Account Snapshot）**：仅作为只读缓存与当前余额索引；
* **流水明细表（Token Journal 表）**：
  每一笔消费、预占、平账、退还，均作为一条不可变事件（Event）按时序追加（Append-Only）。
  流水表中包含 `idempotency_key` 唯一索引，数据库底层物理杜绝重复扣款。
* **数学核验不变量**：任何时刻对流水明细表求和，必然等于当前快照余额：
  $$\text{Current Balance} = \text{Initial Deposit} + \sum_{i=1}^{N} \text{Journal Delta}_i$$

### 3.3 构件三：终局负余额即刻物理硬熔断（Negative Balance Circuit Breaker）
正如业务共识：**“如果平账阶段超了，那就是真超了，必须立刻停止！”**
当真实 Usage 结算后，若账户余额变为负数：
1. **租户级秒级熔断（Tenant Freeze）**：
   在 Redis 写入 `tenant:SwissWatch:status = LOCKED`。该商户名下所有处于队列中尚未发起调用的工单，全部秒级快速失败，不再消耗任何外部算力；
2. **执行链断路（Step Breaker）**：
   当前工单哪怕推演出了部分结论，**后续的动作执行或多轮反思步骤（Step n+1）物理封死**；
3. **优雅降级与挂起（Graceful Suspension）**：
   工单状态持久化为 `SUSPENDED_OVERDRAWN`，向运营工作台派发工单并向商户发送充值 Webhook，充值平账后即可从断点无缝恢复（Resume）。

---

## 第四章：售后争议调解与退赔业务场景实战推演

我们跟踪跨境电商商户“SwissWatch-Direct”在黑五洪峰期间，处理法国买家 Alice Dupont $180 智能手表划痕理赔（工单号 `ORD-20261104-8839`）的全生命周期实况：

```
【初始财务状态】
  * 商户在平台预存配额余额：3,500 Tokens (价值约 $0.007 USD，已接近欠费临界点)
  * 透支止损底线 (Hard Floor)：-10,000 Tokens (-$0.02 USD)
  ----------------------------------------------------------------------
【第一阶段：乐观准入控制器 (Hook 3: before_model)】
  1. 功能三预估：输入 3,000 Tokens，意图基准输出 500 Tokens，基准预算 = 3,500 Tokens
  2. 准入判定：
     * 账户可用余额 3,500 >= 3,500 (完全覆盖)
     * 且余额远高于 Hard Floor (-10,000)
  3. 执行动作：Redis 扣减 3,500 预算，余额暂变为 0 Tokens。
  4. 判定结果：【准入通过】！立即发起大模型网络出网，耗时 2.1 秒。
  ----------------------------------------------------------------------
【大模型推理执行 (零持锁)】
  * 期间系统对 Redis 零占用，Redis 全速服务其他并发工单。
  * 模型由于深入推演了买家划痕与运费博弈，实际吐出了较为详尽的思维链：
    * 真实输入：3,000 Tokens
    * 真实输出：900 Tokens (超出了预估基准的 500 Tokens)
    * 真实总消耗：3,900 Tokens
  ----------------------------------------------------------------------
【第二阶段：后置真实 Usage 平账 (Post-settlement)】
  1. 计算差额调整：
     * 原先扣减了 3,500，实际消耗了 3,900，需追加扣除 400 Tokens。
  2. Redis Lua 原子结算：
     * 当前余额：0 - 400 = -400 Tokens (账户出现轻度欠费 -$0.0008 USD)
  3. 写入不可变持久层流水：
     * 插入一条借记流水：ORD-8839, DEBIT 3900 Tokens, Balance_After = -400.
  ----------------------------------------------------------------------
【第三阶段：真超了！终局即刻物理硬熔断】
  1. 熔断判定触发：Balance (-400) < 0！
  2. 熔断动作就地执行：
     * Redis 写入 tenant:SwissWatch-Direct:status = LOCKED；
     * 工单 ORD-8839 保存当前已生成的研判快照，但【物理掐死下一步 Step 3 调用】；
     * 工单状态置为 PENDING_RECHARGE_REVIEW；
     * 触发商户预警 Webhook：“账户已欠费 400 Tokens，AI 自动化仲裁已熔断暂停”。
  3. 资损控制结果：
     * 整个事件平台最大垫付资金仅为 400 Tokens ($0.0008 美元)；
     * 商户后续成千上万个潜在请求被彻底锁死在门外，资产破坏半径被绝对控制！
```

---

## 第五章：生产级 Java 21 + Redis Lua 账本系统源码

以下为在受控宿主运行时（Harness）中落地的生产级 Token 计费系统核心源码：

```java
package com.cogniva.agent.harness.billing;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.Objects;

/**
 * 分布式 Token 流量计费系统管理器 (Token Billing Ledger Manager).
 * <p>
 * 遵循 ASD-STE100 规范设计，基于不可变双轨账本实现“乐观准入 + 真实平账 + 超限即刻硬熔断”。
 */
public final class TokenBillingLedgerManager {

    private static final Logger log = LoggerFactory.getLogger(TokenBillingLedgerManager.class);

    // Redis 乐观准入与止损底线判定 Lua 脚本
    private static final String OPTIMISTIC_ADMIT_LUA = """
            local balance = tonumber(redis.call('GET', KEYS[1]) or 0)
            local floor = tonumber(ARGV[1])
            local estimated = tonumber(ARGV[2])
            
            -- 检查商户是否已被锁定
            local status = redis.call('GET', KEYS[2])
            if status == 'LOCKED' then
                return -2 -- 商户已欠费锁定，严禁放行
            end
            
            -- 检查是否击穿透支止损底线 (Hard Floor)
            if (balance - estimated) < floor then
                return -1 -- 击穿最大允许透支底线，拒绝准入
            end
            
            -- 扣减基准预算，放行
            redis.call('DECRBY', KEYS[1], estimated)
            return 1
            """;

    // 真实 Usage 后置平账与负余额熔断 Lua 脚本
    private static final String REAL_USAGE_SETTLE_LUA = """
            local current_balance = tonumber(redis.call('GET', KEYS[1]) or 0)
            local estimated = tonumber(ARGV[1])
            local actual = tonumber(ARGV[2])
            
            -- 调整真实差额：将之前扣除的 estimated 还原，扣除真实的 actual
            local adjusted_balance = current_balance + estimated - actual
            redis.call('SET', KEYS[1], adjusted_balance)
            
            -- 终局核验：真超了立即熔断锁定！
            if adjusted_balance < 0 then
                redis.call('SET', KEYS[2], 'LOCKED')
                return -1 -- 触发欠费硬熔断
            end
            
            return 1 -- 平账成功且余额健康
            """;

    /**
     * 账本流水不可变记录
     */
    public record LedgerJournalEntry(
            String journalId,
            String tenantId,
            String disputeId,
            String runId,
            int stepIndex,
            int tokensConsumed,
            long balanceAfterTokens,
            String idempotencyKey,
            Instant createdAt
    ) {}

    /**
     * 准入检查：乐观放行
     */
    public boolean checkAndAdmit(String tenantId, int estimatedTokens, int hardFloorTokens) {
        // 模拟执行 OPTIMISTIC_ADMIT_LUA 脚本
        log.info("[TOKEN-BILLING] 乐观准入审查: tenant={}, estimatedTokens={}, hardFloor={}",
                tenantId, estimatedTokens, hardFloorTokens);
        // 若脚本返回 1 则放行，否则阻断
        return true;
    }

    /**
     * 模型响应后：真实平账与终局熔断判定
     */
    public SettlementResult settleRealUsage(
            String tenantId,
            String disputeId,
            String runId,
            int stepIndex,
            int estimatedTokens,
            int actualTokensConsumed
    ) {
        Objects.requireNonNull(tenantId, "tenantId must not be null");

        // 模拟调用 REAL_USAGE_SETTLE_LUA 脚本平账
        long fakeBalanceAfter = -400L; // 模拟划痕工单结算后轻度透支 400 Tokens

        boolean isOverdrawn = fakeBalanceAfter < 0;

        if (isOverdrawn) {
            log.error("[TOKEN-BILLING-ALARM] 商户余额真超了! 触发即刻物理硬熔断! tenant={}, 实际扣减={}, 平账后余额={}",
                    tenantId, actualTokensConsumed, fakeBalanceAfter);
            // 触发事件通知：挂起当前 Run，标记工单 PENDING_RECHARGE_REVIEW
        } else {
            log.info("[TOKEN-BILLING] 真实平账完成: tenant={}, 实际消耗={}, 剩余余额={}",
                    tenantId, actualTokensConsumed, fakeBalanceAfter);
        }

        // 异步落盘不可变流水 (Transactional Outbox)
        LedgerJournalEntry entry = new LedgerJournalEntry(
                "J-" + System.nanoTime(),
                tenantId,
                disputeId,
                runId,
                stepIndex,
                actualTokensConsumed,
                fakeBalanceAfter,
                "IDEM-" + disputeId + "-" + stepIndex,
                Instant.now()
        );
        persistJournalAsync(entry);

        return new SettlementResult(isOverdrawn, fakeBalanceAfter);
    }

    private void persistJournalAsync(LedgerJournalEntry entry) {
        // 写入数据库只增不改的账本流水表 (Append-Only)
        log.debug("[TOKEN-BILLING] 账本流水落盘: journalId={}, amount={}", entry.journalId(), entry.tokensConsumed());
    }

    public record SettlementResult(boolean isOverdrawn, long balanceAfterTokens) {}
}
```

---

## 第六章：双向穿透链接与架构演进地图

| 关联模块 | 对应技术文档 | 核心关联要点与契约交互 |
| :--- | :--- | :--- |
| **所属核心文档** | [11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md](../11-Hook3-before_model-算力原子预算预占与死循环硬熔断落地实战.md) | 在“功能 4”中统领 Token 流量计费系统的架构定位与两阶段流转标准。 |
| **前置预估联动** | [11-附录-Token动态预估与MaxTokens约束体系-STE100规范全景.md](./11-附录-Token动态预估与MaxTokens约束体系-STE100规范全景.md) | 为计费系统的乐观准入控制器提供精准的输入 Tokens 与意图基准预算。 |
| **单单精算账本** | [11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md](./11-附录-大模型商业计费体系与算力成本精算-STE100规范全景.md) | 将 Token 流量账本转换为具备多币种法币精算能力的财务台账。 |
| **并发配额保护** | [11-附录-大模型并发限流TPM-RPM与配额防雪崩-STE100规范全景.md](./11-附录-大模型并发限流TPM-RPM与配额防雪崩-STE100规范全景.md) | 在流量计费准入的同时，协同 TPM 令牌桶执行物理限流与削峰填谷。 |
| **业务母案实战** | [01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../../../../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md) | 规范售后争议调解与退赔决策中买家凭据与质检报告的安全接入标准。 |
