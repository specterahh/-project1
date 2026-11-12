# 云栖移动使用手册

电信数据库智能问答系统。库名 `telecom_ops`，业务是浙江省 11 个地市的移动客户、套餐、号卡、话单、账单和投诉。用自然语言提问，页面生成一条 SQL，查本地库，并把结果和数据来源摊开。

## 1. 页面使用

打开「电信数据库智能问答系统」。

1. 在左边输入问题，或点下面四个例子之一。
2. 点「生成 SQL」。按钮变成「生成中」时不要连点。
3. 右边出现实际执行的 SQL 和结果表。
4. 右下角写明数据来源、统计方式、筛选条件、排序方式。
5. 左下角留下这一次的记录。

没有结果时，右边写「没有符合条件的记录」。超过 200 行只显示前 200 行，并注明截断。失败时右边写原因，记录标成红色「失败」。

## 2. 问答记录

记录记在这台浏览器里，刷新还在。最多留 12 条。没有账号。

- 点整行：回看那一次的问题、SQL、结果和溯源，不再调用模型。
- 重新查询：用当时那条 SQL 再查一次库。库如果换过，数字会跟着变。不重新生成 SQL。
- 删除：只删这条记录，不删库里的客户、账单或话单。

## 3. 数据溯源怎么读

每次成功都有四行。

| 行 | 含义 |
|---|---|
| 数据来源 | 固定是 `telecom_ops.db`，后面是这句 SQL 用到的那一张表 |
| 统计方式 | 计数、求和、平均、最大、最小、分组。都没有时写「逐行列出，未做聚合」 |
| 筛选条件 | SQL 里 `WHERE` 的原文。没有筛选就写「未筛选」 |
| 排序方式 | `ORDER BY` 的原文。有 `LIMIT` 会写成「只要前 N 条」 |

## 4. 能问什么，不能问什么

能问一张表里的事，也能问这张表自己和自己的关系，例如推荐人、父子投诉。

不能做这些。页面会拒绝，不会去改库：

- 把客户和账单、订购和套餐这类两张不同的表连在一起
- `WITH`、窗口函数
- 插入、修改、删除

在网指 `status = '在网'`，不是「销户时间为空」。停机、欠费停机的人销户时间也是空的。

时间都是文本，形如 `2024-08-31 14:55:06`。问某个月，对应的是 `YYYY-MM`。

## 5. 本地文件以及相关修改

实习目录示例：`C:\Users\spect\Desktop\Folder\实习project1\`。

| 文件 | 干什么 |
|---|---|
| `generate_sample.py` | 每张表 100 行，只写库，用来核对 |
| `generate_data.py` | 每张表默认 1 万行，同时写库和 Excel |
| `sql_problems.py` | 100 道固定题。初级 20，中级 40，高级 40 |
| `telecom_ops.db` | 六个表都在这一个文件里 |
| `telecom_ops.xlsx` | 同一个库，一个表一个 sheet，sheet 名就是表名 |
| `readme.md` | 本手册 |

环境：Windows，Python 3.11 及以上，DB Browser for SQLite，Excel 或 WPS。虚拟环境解释器：

```powershell
.\.venv\Scripts\python.exe -m pip install openpyxl
```

生成或覆盖库之前，先关掉 DB Browser 和 Excel，否则文件被锁住。

100 行核对：

```powershell
.\.venv\Scripts\python.exe .\generate_sample.py
```

1 万行和 Excel：

```powershell
.\.venv\Scripts\python.exe .\generate_data.py
```

改行数（1 到 20 万）：

```powershell
.\.venv\Scripts\python.exe .\generate_data.py --rows 20000
```

20 万行的 Excel 会很大，不建议第一次就用。

检查 100 道题都能在当前库上跑出结果：

```powershell
.\.venv\Scripts\python.exe .\sql_problems.py
```

通过时打印 `100 题都能跑出结果`。
sheet 顺序是 `customers`、`plans`、`subscriptions`、`usage_records`、`bills`、`tickets`。

## 6. 数据是怎么来的

表格数据右XAI生成：

1. 定 6 张表，每张至少 15 列，带主键、外键和索引。
2. 用 DB Browser 核对空库。
3. `generate_sample.py` 写 100 行，核对关联没有断。
4. `generate_data.py` 覆盖成每张表 1 万行，并导出 Excel。
5. `sql_problems.py` 写 100 道单表题，并在这 1 万行上跑通。
6. 问答页面接同一个库。

生成规则：先有客户和套餐，订购引用它们，话单、账单、投诉再往下挂。时间用 `datetime` 生成，存成 `strftime` 字符串。业务时间从 2020-01-01 到 2025-11-30。种子默认 42，同一参数再跑，数据相同。故意留空值、重复号码、负话费、账算不平，引用不断。

## 7. 六张表


时间列格式 `YYYY-MM-DD HH:MM:SS`。按年取前 4 位，按月取前 7 位。

### customers 客户

`referrer_customer_id` 指向另一个客户，这是推荐关系。

customer_id 主键。customer_no 唯一。full_name，id_card_no，gender，birth_date，phone_no，email，city_code，city_name，district_name，address，customer_level，status，referrer_customer_id，register_time，cancel_time，credit_score，profile_json，is_test_user，updated_at。

等级：普通、银卡、金卡、钻石。状态：在网、停机、销户、欠费停机。地市是杭州到丽水共 11 个。

索引：手机号，地市加状态，等级加入网时间，推荐人。

### plans 套餐

plan_id 主键。plan_code 唯一。plan_name，plan_type，monthly_fee，voice_minutes，data_mb，sms_count，overage_voice_fee，overage_data_fee，contract_months，effective_from，effective_to，status，target_segment，region_limit，benefit_json，offline_reason，created_at。

类型：语音、流量、融合、宽带、物联网。状态：在售、停售。客群：大众、校园、政企、老人。`region_limit` 为空表示全省。

### subscriptions 订购

一张号卡一条。约一成客户有两张卡，约一成客户没有订购。

subscription_id 主键。customer_id、plan_id 外键。msisdn，iccid，imsi，start_time，end_time，contract_end_time，channel_code，agent_id，city_code，city_name，monthly_fee_snapshot，discount_rate，status，auto_renew，promo_code，extra_json，created_at，updated_at。

状态：生效、预约生效、停机、已退订。渠道：营业厅、APP、网厅、代理商、客服。唯一约束是客户、套餐、生效时间三者合在一起。

### usage_records 话单

usage_id 主键。subscription_id、customer_id 外键，并且客户和号码都跟这张订购一致。caller_msisdn，usage_time，usage_month，usage_type，direction，peer_number，duration_sec，data_kb，sms_cnt，charge_amount，is_roaming，roam_city，cell_id，network_type，rating_status，raw_json，created_at。

类型：语音、流量、短信、增值。`usage_month` 等于使用时间的前 7 位。负话费在 `charge_amount`。

### bills 账单

每张订购一张，账期是订购生效的那个月。

bill_id 主键。bill_no 唯一。customer_id、subscription_id 外键。bill_month，plan_fee，voice_fee，data_fee，sms_fee，value_added_fee，discount_amount，adjust_amount，total_amount，paid_amount，unpaid_amount，bill_status，issue_time，due_time，pay_time，pay_channel，invoice_no，city_code，remark，fee_detail_json。

状态：未出账、已出账、部分支付、已结清、坏账。同一客户、同一订购、同一账期只有一张。约 1% 的总额和分项对不上，少量已付大于总额，少量未付为负。

### tickets 投诉

ticket_id 主键。ticket_no 唯一。customer_id 外键。subscription_id 若有值，必须是这个客户的卡。parent_ticket_id 指向本表里编号更小的父单。related_bill_id 指向账单。category，sub_category，priority，status，channel，title，description，city_code，city_name，created_time，first_response_time，closed_time，sla_hours，is_escalated，satisfaction_score，handler_id，tags_json。

大类：费用、网络、业务办理、服务态度。优先级：低、中、高、紧急。状态：新建、处理中、待回访、已关闭、已撤销。渠道：10086、APP、营业厅、工信部转办。满意度正常是 1 到 5，另有 0 和 9。

### 只用于核对的跨表语句

100 道题和问答页面都不允许跨表。下面这句只用来在 DB Browser 里看关联有没有断：

```sql
SELECT c.full_name, s.msisdn, p.plan_name, b.bill_month, b.total_amount
FROM subscriptions AS s
JOIN customers AS c ON c.customer_id = s.customer_id
JOIN plans AS p ON p.plan_id = s.plan_id
JOIN bills AS b ON b.subscription_id = s.subscription_id
LIMIT 10;
```

## 8. 100 道固定题

在 `sql_problems.py` 的 `sql_problems` 里，分「初级」「中级」「高级」。每级的 `id` 从 1 另起。每题有问题原文和对应 SQL。

| 难度 | 数量 | 在考什么 |
|---|---|---|
| 初级 | 20 | 条件、计数、排序、只要前几条、空值 |
| 中级 | 40 | 分组、分组后再筛、分档、按月汇总、金额对平 |
| 高级 | 40 | 自连接、子查询、同组平均、父子投诉 |

题面不出现「查询」二字。初级第 1 题是「杭州现在还在网的人有多少」。

页面上的自由提问不限于这 100 句，但生成出来的 SQL 遵守同一套限制。

## 9. 已知限制

- 填了身份证的记录是 20 位，真实身份证是 18 位。
- 姓名和性别分开随机，所以可能出现男性叫「李艳」。
- 出生日期可以早于 2020。入网、话单、账单、投诉的时间都在 2020-01-01 到 2025-11-30。
- 问答记录只在当前浏览器里，换浏览器或清站点数据就没了。
- 模型偶尔会把条件写宽。看右边的 SQL 和溯源，不对就改问法再生成一次。


该readme由XAI润色