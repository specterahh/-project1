# 100 道单表题。只能 SELECT，不用窗口函数，不用 WITH。自连接可以，跨表不能。
# 初级 20，中级 40，高级 40。题面不出现「查询」二字。
# 对着 telecom_ops.db 检查：python sql_problems.py

sql_problems = {
    "初级": [
        {
            "id": 1,
            "problem": "杭州现在还在网的人有多少",
            "sql": """
SELECT COUNT(*) AS "在网人数"
FROM customers AS c
WHERE c.city_name = '杭州' AND c.status = '在网'
""",
        },
        {
            "id": 2,
            "problem": "信用分过了800的，按分数从高到低先看20个",
            "sql": """
SELECT c.full_name AS "姓名", c.phone_no AS "手机号", c.credit_score AS "信用分"
FROM customers AS c
WHERE c.credit_score > 800
ORDER BY c.credit_score DESC
LIMIT 20
""",
        },
        {
            "id": 3,
            "problem": "邮箱空着的客户，把编号和手机号列出来",
            "sql": """
SELECT c.customer_no AS "客户编号", c.full_name AS "姓名", c.phone_no AS "手机号"
FROM customers AS c
WHERE c.email IS NULL
""",
        },
        {
            "id": 4,
            "problem": "钻石客户都在哪些城市",
            "sql": """
SELECT c.full_name AS "姓名", c.phone_no AS "手机号", c.city_name AS "地市"
FROM customers AS c
WHERE c.customer_level = '钻石'
""",
        },
        {
            "id": 5,
            "problem": "测试号有哪些，看姓名和状态",
            "sql": """
SELECT c.full_name AS "姓名", c.phone_no AS "手机号", c.status AS "状态"
FROM customers AS c
WHERE c.is_test_user = 1
""",
        },
        {
            "id": 6,
            "problem": "还在卖、月租不到50的套餐，便宜的排前面",
            "sql": """
SELECT p.plan_name AS "套餐", p.monthly_fee AS "月租", p.plan_type AS "类型"
FROM plans AS p
WHERE p.status = '在售' AND p.monthly_fee < 50
ORDER BY p.monthly_fee
""",
        },
        {
            "id": 7,
            "problem": "流量类套餐一共多少个",
            "sql": """
SELECT COUNT(*) AS "流量套餐数"
FROM plans AS p
WHERE p.plan_type = '流量'
""",
        },
        {
            "id": 8,
            "problem": "套餐名里带校园的，把编码和月租列出来",
            "sql": """
SELECT p.plan_code AS "编码", p.plan_name AS "套餐", p.monthly_fee AS "月租"
FROM plans AS p
WHERE p.plan_name LIKE '%校园%'
""",
        },
        {
            "id": 9,
            "problem": "已经退订的号卡，号码和退订时间",
            "sql": """
SELECT s.msisdn AS "号码", s.end_time AS "退订时间", s.city_name AS "地市"
FROM subscriptions AS s
WHERE s.status = '已退订'
ORDER BY s.end_time
""",
        },
        {
            "id": 10,
            "problem": "宁波用APP办的卡有多少张",
            "sql": """
SELECT COUNT(*) AS "办卡数"
FROM subscriptions AS s
WHERE s.city_name = '宁波' AND s.channel_code = 'APP'
""",
        },
        {
            "id": 11,
            "problem": "折扣低于8折的订购，折扣低的排前面",
            "sql": """
SELECT s.subscription_id AS "订购号", s.msisdn AS "号码", s.discount_rate AS "折扣"
FROM subscriptions AS s
WHERE s.discount_rate < 0.8
ORDER BY s.discount_rate
""",
        },
        {
            "id": 12,
            "problem": "语音通话超过20分钟的话单，先看最长的15条",
            "sql": """
SELECT u.caller_msisdn AS "号码", u.usage_time AS "时间", u.duration_sec AS "秒数"
FROM usage_records AS u
WHERE u.usage_type = '语音' AND u.duration_sec >= 1200
ORDER BY u.duration_sec DESC
LIMIT 15
""",
        },
        {
            "id": 13,
            "problem": "漫游话单一共多少条",
            "sql": """
SELECT COUNT(*) AS "漫游条数"
FROM usage_records AS u
WHERE u.is_roaming = 1
""",
        },
        {
            "id": 14,
            "problem": "话费记成负数的话单",
            "sql": """
SELECT u.usage_id AS "话单号", u.caller_msisdn AS "号码", u.usage_time AS "时间", u.charge_amount AS "话费"
FROM usage_records AS u
WHERE u.charge_amount < 0
""",
        },
        {
            "id": 15,
            "problem": "还没结清、未付超过100的账单，欠得多的排前面",
            "sql": """
SELECT b.bill_no AS "账单号", b.bill_month AS "账期", b.unpaid_amount AS "未付", b.bill_status AS "状态"
FROM bills AS b
WHERE b.unpaid_amount > 100 AND b.bill_status <> '已结清'
ORDER BY b.unpaid_amount DESC
""",
        },
        {
            "id": 16,
            "problem": "2025年10月的账单有几张",
            "sql": """
SELECT COUNT(*) AS "账单数"
FROM bills AS b
WHERE b.bill_month = '2025-10'
""",
        },
        {
            "id": 17,
            "problem": "坏账按未付从大到小列出来",
            "sql": """
SELECT b.bill_no AS "账单号", b.bill_month AS "账期", b.total_amount AS "总额", b.unpaid_amount AS "未付"
FROM bills AS b
WHERE b.bill_status = '坏账'
ORDER BY b.unpaid_amount DESC
""",
        },
        {
            "id": 18,
            "problem": "紧急、还没关闭也没撤销的投诉",
            "sql": """
SELECT t.ticket_no AS "单号", t.title AS "标题", t.status AS "状态", t.created_time AS "建单时间"
FROM tickets AS t
WHERE t.priority = '紧急' AND t.status NOT IN ('已关闭', '已撤销')
ORDER BY t.created_time
""",
        },
        {
            "id": 19,
            "problem": "工信部转办的单子有多少",
            "sql": """
SELECT COUNT(*) AS "转办数"
FROM tickets AS t
WHERE t.channel = '工信部转办'
""",
        },
        {
            "id": 20,
            "problem": "满意度打了1分的投诉，看单号和地市",
            "sql": """
SELECT t.ticket_no AS "单号", t.category AS "类别", t.city_name AS "地市", t.satisfaction_score AS "评分"
FROM tickets AS t
WHERE t.satisfaction_score = 1
""",
        },
    ],
    "中级": [
        {
            "id": 1,
            "problem": "各地市现在在网的人数，人多的排前面",
            "sql": """
SELECT c.city_name AS "地市", COUNT(*) AS "在网人数"
FROM customers AS c
WHERE c.status = '在网'
GROUP BY c.city_name
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 2,
            "problem": "每个等级的平均信用分，没填分的别算进去",
            "sql": """
SELECT c.customer_level AS "等级", ROUND(AVG(c.credit_score), 1) AS "平均信用分", COUNT(c.credit_score) AS "有分数的人数"
FROM customers AS c
WHERE c.credit_score IS NOT NULL
GROUP BY c.customer_level
""",
        },
        {
            "id": 3,
            "problem": "2023年每个月新入网多少人",
            "sql": """
SELECT substr(c.register_time, 1, 7) AS "入网月份", COUNT(*) AS "人数"
FROM customers AS c
WHERE c.register_time >= '2023-01-01' AND c.register_time < '2024-01-01'
GROUP BY substr(c.register_time, 1, 7)
ORDER BY substr(c.register_time, 1, 7)
""",
        },
        {
            "id": 4,
            "problem": "哪些手机号被登记了不止一次",
            "sql": """
SELECT c.phone_no AS "手机号", COUNT(*) AS "次数"
FROM customers AS c
GROUP BY c.phone_no
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 5,
            "problem": "按信用分把人分成无分、负分、偏低、中等、良好、超范围，各有多少",
            "sql": """
SELECT
  CASE
    WHEN c.credit_score IS NULL THEN '无分'
    WHEN c.credit_score < 0 THEN '负分'
    WHEN c.credit_score < 500 THEN '偏低'
    WHEN c.credit_score < 700 THEN '中等'
    WHEN c.credit_score <= 1000 THEN '良好'
    ELSE '超范围'
  END AS "分档",
  COUNT(*) AS "人数"
FROM customers AS c
GROUP BY "分档"
ORDER BY "人数" DESC
""",
        },
        {
            "id": 6,
            "problem": "每种状态超过500人的，把人数列出来",
            "sql": """
SELECT c.status AS "状态", COUNT(*) AS "人数"
FROM customers AS c
GROUP BY c.status
HAVING COUNT(*) > 500
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 7,
            "problem": "手机号前三位都有哪些号段",
            "sql": """
SELECT DISTINCT substr(c.phone_no, 1, 3) AS "号段"
FROM customers AS c
ORDER BY "号段"
""",
        },
        {
            "id": 8,
            "problem": "在售套餐按类型看平均月租",
            "sql": """
SELECT p.plan_type AS "类型", ROUND(AVG(p.monthly_fee), 2) AS "平均月租", COUNT(*) AS "个数"
FROM plans AS p
WHERE p.status = '在售'
GROUP BY p.plan_type
ORDER BY AVG(p.monthly_fee) DESC
""",
        },
        {
            "id": 9,
            "problem": "月租在50到150之间、已经停售的套餐",
            "sql": """
SELECT p.plan_name AS "套餐", p.monthly_fee AS "月租", p.effective_to AS "停售时间"
FROM plans AS p
WHERE p.status = '停售' AND p.monthly_fee BETWEEN 50 AND 150
ORDER BY p.monthly_fee
""",
        },
        {
            "id": 10,
            "problem": "大众、校园、政企、老人各有多少套餐",
            "sql": """
SELECT p.target_segment AS "客群", COUNT(*) AS "套餐数"
FROM plans AS p
GROUP BY p.target_segment
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 11,
            "problem": "合约超过12个月、语音超过500分钟的套餐",
            "sql": """
SELECT p.plan_name AS "套餐", p.contract_months AS "合约月数", p.voice_minutes AS "语音分钟"
FROM plans AS p
WHERE p.contract_months > 12 AND p.voice_minutes > 500
""",
        },
        {
            "id": 12,
            "problem": "每种类型最贵的月租是多少",
            "sql": """
SELECT p.plan_type AS "类型", MAX(p.monthly_fee) AS "最高月租", MIN(p.monthly_fee) AS "最低月租"
FROM plans AS p
GROUP BY p.plan_type
""",
        },
        {
            "id": 13,
            "problem": "全省能办和限制了地市的套餐各有多少",
            "sql": """
SELECT
  CASE WHEN p.region_limit IS NULL THEN '全省' ELSE '限地市' END AS "范围",
  COUNT(*) AS "套餐数"
FROM plans AS p
GROUP BY "范围"
""",
        },
        {
            "id": 14,
            "problem": "限了地市的套餐，每个地市编码有几个",
            "sql": """
SELECT p.region_limit AS "地市编码", COUNT(*) AS "套餐数"
FROM plans AS p
WHERE p.region_limit IS NOT NULL
GROUP BY p.region_limit
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 15,
            "problem": "各地市现在生效中的卡有多少张",
            "sql": """
SELECT s.city_name AS "地市", COUNT(*) AS "生效卡数"
FROM subscriptions AS s
WHERE s.status = '生效'
GROUP BY s.city_name
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 16,
            "problem": "折扣是空的、大于1的、或者是负数的订购",
            "sql": """
SELECT s.subscription_id AS "订购号", s.msisdn AS "号码", s.discount_rate AS "折扣"
FROM subscriptions AS s
WHERE s.discount_rate IS NULL OR s.discount_rate > 1 OR s.discount_rate < 0
""",
        },
        {
            "id": 17,
            "problem": "每个渠道的平均月租快照",
            "sql": """
SELECT s.channel_code AS "渠道", ROUND(AVG(s.monthly_fee_snapshot), 2) AS "平均月租", COUNT(*) AS "卡数"
FROM subscriptions AS s
GROUP BY s.channel_code
ORDER BY AVG(s.monthly_fee_snapshot) DESC
""",
        },
        {
            "id": 18,
            "problem": "同一个客户办了不止一张卡的",
            "sql": """
SELECT s.customer_id AS "客户号", COUNT(*) AS "卡数"
FROM subscriptions AS s
GROUP BY s.customer_id
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 19,
            "problem": "2024年每个月新生效多少张卡",
            "sql": """
SELECT substr(s.start_time, 1, 7) AS "生效月份", COUNT(*) AS "卡数"
FROM subscriptions AS s
WHERE s.start_time >= '2024-01-01' AND s.start_time < '2025-01-01'
GROUP BY substr(s.start_time, 1, 7)
ORDER BY substr(s.start_time, 1, 7)
""",
        },
        {
            "id": 20,
            "problem": "关掉了自动续费的卡，按状态数一下",
            "sql": """
SELECT s.status AS "状态", COUNT(*) AS "卡数"
FROM subscriptions AS s
WHERE s.auto_renew = 0
GROUP BY s.status
""",
        },
        {
            "id": 21,
            "problem": "退订时间比生效时间还早的号卡",
            "sql": """
SELECT s.subscription_id AS "订购号", s.msisdn AS "号码", s.start_time AS "生效", s.end_time AS "结束"
FROM subscriptions AS s
WHERE s.end_time IS NOT NULL AND s.end_time < s.start_time
""",
        },
        {
            "id": 22,
            "problem": "每个月、每种类型的话单各有多少条",
            "sql": """
SELECT u.usage_month AS "月份", u.usage_type AS "类型", COUNT(*) AS "条数"
FROM usage_records AS u
GROUP BY u.usage_month, u.usage_type
ORDER BY u.usage_month, u.usage_type
""",
        },
        {
            "id": 23,
            "problem": "已经批完价的话单，按类型看平均话费",
            "sql": """
SELECT u.usage_type AS "类型", ROUND(AVG(u.charge_amount), 2) AS "平均话费", COUNT(*) AS "条数"
FROM usage_records AS u
WHERE u.rating_status = '已批价' AND u.charge_amount IS NOT NULL
GROUP BY u.usage_type
""",
        },
        {
            "id": 24,
            "problem": "每种网络的流量一共多少KB，只算流量话单",
            "sql": """
SELECT u.network_type AS "网络", SUM(u.data_kb) AS "流量KB", COUNT(*) AS "条数"
FROM usage_records AS u
WHERE u.usage_type = '流量'
GROUP BY u.network_type
ORDER BY SUM(u.data_kb) DESC
""",
        },
        {
            "id": 25,
            "problem": "语音主叫总时长最长的10个号码",
            "sql": """
SELECT u.caller_msisdn AS "号码", SUM(u.duration_sec) AS "总秒数", COUNT(*) AS "次数"
FROM usage_records AS u
WHERE u.usage_type = '语音' AND u.direction = '主叫' AND u.duration_sec IS NOT NULL
GROUP BY u.caller_msisdn
ORDER BY SUM(u.duration_sec) DESC
LIMIT 10
""",
        },
        {
            "id": 26,
            "problem": "漫游到上海、南京、北京各有多少条",
            "sql": """
SELECT u.roam_city AS "漫游地", COUNT(*) AS "条数"
FROM usage_records AS u
WHERE u.is_roaming = 1
GROUP BY u.roam_city
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 27,
            "problem": "没批上价或者批价失败的，按月数一下",
            "sql": """
SELECT u.usage_month AS "月份", u.rating_status AS "批价状态", COUNT(*) AS "条数"
FROM usage_records AS u
WHERE u.rating_status IN ('未批价', '批价失败')
GROUP BY u.usage_month, u.rating_status
ORDER BY u.usage_month
""",
        },
        {
            "id": 28,
            "problem": "5G语音里，单次超过10分钟的有多少条",
            "sql": """
SELECT COUNT(*) AS "条数"
FROM usage_records AS u
WHERE u.network_type = '5G' AND u.usage_type = '语音' AND u.duration_sec > 600
""",
        },
        {
            "id": 29,
            "problem": "每个账期的未付合计，未付多的月份排前面",
            "sql": """
SELECT b.bill_month AS "账期", ROUND(SUM(b.unpaid_amount), 2) AS "未付合计", COUNT(*) AS "张数"
FROM bills AS b
GROUP BY b.bill_month
ORDER BY SUM(b.unpaid_amount) DESC
""",
        },
        {
            "id": 30,
            "problem": "总额和分项加出来对不上的账单",
            "sql": """
SELECT b.bill_no AS "账单号", b.total_amount AS "总额",
       ROUND(b.plan_fee + b.voice_fee + b.data_fee + b.sms_fee + b.value_added_fee - b.discount_amount + b.adjust_amount, 2) AS "分项合计"
FROM bills AS b
WHERE ABS(b.total_amount - (b.plan_fee + b.voice_fee + b.data_fee + b.sms_fee + b.value_added_fee - b.discount_amount + b.adjust_amount)) > 0.02
""",
        },
        {
            "id": 31,
            "problem": "各地市坏账有几笔",
            "sql": """
SELECT b.city_code AS "地市编码", COUNT(*) AS "坏账笔数", ROUND(SUM(b.unpaid_amount), 2) AS "未付合计"
FROM bills AS b
WHERE b.bill_status = '坏账'
GROUP BY b.city_code
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 32,
            "problem": "账单按已结清、有欠费、未付为负分成三类，各多少张",
            "sql": """
SELECT
  CASE
    WHEN b.unpaid_amount < 0 THEN '未付为负'
    WHEN b.unpaid_amount = 0 THEN '没有未付'
    ELSE '还有欠费'
  END AS "欠费情况",
  COUNT(*) AS "张数"
FROM bills AS b
GROUP BY "欠费情况"
""",
        },
        {
            "id": 33,
            "problem": "每个账期的结清率，用已结清张数除以总张数",
            "sql": """
SELECT b.bill_month AS "账期",
       SUM(CASE WHEN b.bill_status = '已结清' THEN 1 ELSE 0 END) AS "已结清张数",
       COUNT(*) AS "总张数",
       ROUND(1.0 * SUM(CASE WHEN b.bill_status = '已结清' THEN 1 ELSE 0 END) / COUNT(*), 3) AS "结清率"
FROM bills AS b
GROUP BY b.bill_month
ORDER BY b.bill_month
""",
        },
        {
            "id": 34,
            "problem": "已付比总额还多的账单",
            "sql": """
SELECT b.bill_no AS "账单号", b.total_amount AS "总额", b.paid_amount AS "已付", b.unpaid_amount AS "未付", b.bill_status AS "状态"
FROM bills AS b
WHERE b.paid_amount > b.total_amount
""",
        },
        {
            "id": 35,
            "problem": "投诉按大类数一下，哪类最多",
            "sql": """
SELECT t.category AS "类别", COUNT(*) AS "单量"
FROM tickets AS t
GROUP BY t.category
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 36,
            "problem": "升级过的单子，按优先级各有多少",
            "sql": """
SELECT t.priority AS "优先级", COUNT(*) AS "单量"
FROM tickets AS t
WHERE t.is_escalated = 1
GROUP BY t.priority
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 37,
            "problem": "各地市的紧急单有多少",
            "sql": """
SELECT t.city_name AS "地市", COUNT(*) AS "紧急单量"
FROM tickets AS t
WHERE t.priority = '紧急'
GROUP BY t.city_name
HAVING COUNT(*) > 0
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 38,
            "problem": "每类投诉的平均满意度，没打分的不算",
            "sql": """
SELECT t.category AS "类别", ROUND(AVG(t.satisfaction_score), 2) AS "平均分", COUNT(t.satisfaction_score) AS "有分数的单量"
FROM tickets AS t
WHERE t.satisfaction_score IS NOT NULL
GROUP BY t.category
""",
        },
        {
            "id": 39,
            "problem": "每个渠道里，各种状态的单子各有多少",
            "sql": """
SELECT t.channel AS "渠道", t.status AS "状态", COUNT(*) AS "单量"
FROM tickets AS t
GROUP BY t.channel, t.status
ORDER BY t.channel, COUNT(*) DESC
""",
        },
        {
            "id": 40,
            "problem": "状态写着已关闭，关闭时间却是空的",
            "sql": """
SELECT t.ticket_no AS "单号", t.city_name AS "地市", t.created_time AS "建单时间"
FROM tickets AS t
WHERE t.status = '已关闭' AND t.closed_time IS NULL
""",
        },
    ],
    "高级": [
        {
            "id": 1,
            "problem": "客户和推荐人不在同一个城市的，看双方姓名和城市",
            "sql": """
SELECT c.full_name AS "客户", c.city_name AS "客户城市", r.full_name AS "推荐人", r.city_name AS "推荐人城市"
FROM customers AS c
JOIN customers AS r ON c.referrer_customer_id = r.customer_id
WHERE c.city_name <> r.city_name
LIMIT 50
""",
        },
        {
            "id": 2,
            "problem": "推荐超过5个人的推荐人，按人数从多到少",
            "sql": """
SELECT r.full_name AS "推荐人", r.city_name AS "城市", COUNT(*) AS "推荐人数"
FROM customers AS c
JOIN customers AS r ON c.referrer_customer_id = r.customer_id
GROUP BY r.customer_id, r.full_name, r.city_name
HAVING COUNT(*) > 5
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 3,
            "problem": "信用分比同城平均分还高的人，先看前30个",
            "sql": """
SELECT c.full_name AS "姓名", c.city_name AS "地市", c.credit_score AS "信用分"
FROM customers AS c
WHERE c.credit_score > (
  SELECT AVG(c2.credit_score)
  FROM customers AS c2
  WHERE c2.city_name = c.city_name AND c2.credit_score IS NOT NULL
)
ORDER BY c.credit_score DESC
LIMIT 30
""",
        },
        {
            "id": 4,
            "problem": "在网、但是从来没有推荐过别人的客户，看前30个",
            "sql": """
SELECT c.customer_no AS "客户编号", c.full_name AS "姓名", c.city_name AS "地市"
FROM customers AS c
WHERE c.status = '在网'
  AND NOT EXISTS (
    SELECT 1 FROM customers AS o WHERE o.referrer_customer_id = c.customer_id
  )
LIMIT 30
""",
        },
        {
            "id": 5,
            "problem": "推荐人自己已经销户，被推荐的人还在网",
            "sql": """
SELECT c.full_name AS "客户", c.status AS "客户状态", r.full_name AS "推荐人", r.status AS "推荐人状态"
FROM customers AS c
JOIN customers AS r ON c.referrer_customer_id = r.customer_id
WHERE c.status = '在网' AND r.status = '销户'
""",
        },
        {
            "id": 6,
            "problem": "同一个推荐人下面，等级比推荐人更高的客户",
            "sql": """
SELECT c.full_name AS "客户", c.customer_level AS "客户等级", r.full_name AS "推荐人", r.customer_level AS "推荐人等级"
FROM customers AS c
JOIN customers AS r ON c.referrer_customer_id = r.customer_id
WHERE (c.customer_level = '钻石' AND r.customer_level <> '钻石')
   OR (c.customer_level = '金卡' AND r.customer_level IN ('银卡', '普通'))
   OR (c.customer_level = '银卡' AND r.customer_level = '普通')
LIMIT 50
""",
        },
        {
            "id": 7,
            "problem": "每个地市入网最早的那个人",
            "sql": """
SELECT c.city_name AS "地市", c.full_name AS "姓名", c.register_time AS "入网时间"
FROM customers AS c
WHERE c.register_time = (
  SELECT MIN(c2.register_time)
  FROM customers AS c2
  WHERE c2.city_name = c.city_name
)
""",
        },
        {
            "id": 8,
            "problem": "手机号重复、而且至少有一个是销户状态的号码",
            "sql": """
SELECT c.phone_no AS "手机号", COUNT(*) AS "人数",
       SUM(CASE WHEN c.status = '销户' THEN 1 ELSE 0 END) AS "其中销户"
FROM customers AS c
GROUP BY c.phone_no
HAVING COUNT(*) > 1 AND SUM(CASE WHEN c.status = '销户' THEN 1 ELSE 0 END) > 0
""",
        },
        {
            "id": 9,
            "problem": "月租高于同类型平均月租的套餐，贵的排前面，看前20个",
            "sql": """
SELECT p.plan_name AS "套餐", p.plan_type AS "类型", p.monthly_fee AS "月租"
FROM plans AS p
WHERE p.monthly_fee > (
  SELECT AVG(p2.monthly_fee) FROM plans AS p2 WHERE p2.plan_type = p.plan_type
)
ORDER BY p.monthly_fee DESC
LIMIT 20
""",
        },
        {
            "id": 10,
            "problem": "停售时间比上架时间还早的套餐",
            "sql": """
SELECT p.plan_code AS "编码", p.plan_name AS "套餐", p.effective_from AS "上架", p.effective_to AS "停售"
FROM plans AS p
WHERE p.effective_to IS NOT NULL AND p.effective_to < p.effective_from
""",
        },
        {
            "id": 11,
            "problem": "同类型里语音分钟不是最多、但月租却是最贵的套餐",
            "sql": """
SELECT p.plan_name AS "套餐", p.plan_type AS "类型", p.monthly_fee AS "月租", p.voice_minutes AS "语音分钟"
FROM plans AS p
WHERE p.monthly_fee = (
    SELECT MAX(p2.monthly_fee) FROM plans AS p2 WHERE p2.plan_type = p.plan_type
  )
  AND p.voice_minutes < (
    SELECT MAX(p3.voice_minutes) FROM plans AS p3 WHERE p3.plan_type = p.plan_type
  )
""",
        },
        {
            "id": 12,
            "problem": "在售套餐均价比该客群全部套餐均价还高的客群",
            "sql": """
SELECT p.target_segment AS "客群",
       ROUND(AVG(CASE WHEN p.status = '在售' THEN p.monthly_fee END), 2) AS "在售均价",
       ROUND(AVG(p.monthly_fee), 2) AS "全部均价"
FROM plans AS p
GROUP BY p.target_segment
HAVING AVG(CASE WHEN p.status = '在售' THEN p.monthly_fee END) > AVG(p.monthly_fee)
""",
        },
        {
            "id": 13,
            "problem": "流量额度低于同类型平均、月租却高于同类型平均的套餐",
            "sql": """
SELECT p.plan_name AS "套餐", p.data_mb AS "流量MB", p.monthly_fee AS "月租"
FROM plans AS p
WHERE p.plan_type = '流量'
  AND p.data_mb < (SELECT AVG(p2.data_mb) FROM plans AS p2 WHERE p2.plan_type = '流量')
  AND p.monthly_fee > (SELECT AVG(p3.monthly_fee) FROM plans AS p3 WHERE p3.plan_type = '流量')
""",
        },
        {
            "id": 14,
            "problem": "月租一样、类型不一样的两款套餐，凑成一对看前30对",
            "sql": """
SELECT a.plan_name AS "套餐A", a.plan_type AS "类型A", b.plan_name AS "套餐B", b.plan_type AS "类型B", a.monthly_fee AS "月租"
FROM plans AS a
JOIN plans AS b ON a.monthly_fee = b.monthly_fee AND a.plan_id < b.plan_id
WHERE a.plan_type <> b.plan_type
LIMIT 30
""",
        },
        {
            "id": 15,
            "problem": "月租快照比所在渠道平均月租高出一倍以上的号卡",
            "sql": """
SELECT s.msisdn AS "号码", s.channel_code AS "渠道", s.monthly_fee_snapshot AS "月租快照"
FROM subscriptions AS s
WHERE s.monthly_fee_snapshot > 2 * (
  SELECT AVG(s2.monthly_fee_snapshot)
  FROM subscriptions AS s2
  WHERE s2.channel_code = s.channel_code
)
""",
        },
        {
            "id": 16,
            "problem": "每个地市生效卡的平均月租，高于全省生效卡平均月租的地市",
            "sql": """
SELECT s.city_name AS "地市", ROUND(AVG(s.monthly_fee_snapshot), 2) AS "当地均价"
FROM subscriptions AS s
WHERE s.status = '生效'
GROUP BY s.city_name
HAVING AVG(s.monthly_fee_snapshot) > (
  SELECT AVG(s2.monthly_fee_snapshot) FROM subscriptions AS s2 WHERE s2.status = '生效'
)
ORDER BY AVG(s.monthly_fee_snapshot) DESC
""",
        },
        {
            "id": 17,
            "problem": "状态还写着预约生效，生效时间却已经早于2025年的号卡",
            "sql": """
SELECT s.subscription_id AS "订购号", s.msisdn AS "号码", s.status AS "状态", s.start_time AS "生效时间"
FROM subscriptions AS s
WHERE s.status = '预约生效' AND s.start_time < '2025-01-01'
ORDER BY s.start_time
""",
        },
        {
            "id": 18,
            "problem": "折扣比本地平均折扣还低的号卡，低的排前面，看前30张",
            "sql": """
SELECT s.msisdn AS "号码", s.city_name AS "地市", s.discount_rate AS "折扣"
FROM subscriptions AS s
WHERE s.discount_rate IS NOT NULL
  AND s.discount_rate < (
    SELECT AVG(s2.discount_rate)
    FROM subscriptions AS s2
    WHERE s2.city_name = s.city_name AND s2.discount_rate IS NOT NULL
  )
ORDER BY s.discount_rate
LIMIT 30
""",
        },
        {
            "id": 19,
            "problem": "同一个客户名下，既有生效卡又有已退订卡",
            "sql": """
SELECT s.customer_id AS "客户号",
       SUM(CASE WHEN s.status = '生效' THEN 1 ELSE 0 END) AS "生效",
       SUM(CASE WHEN s.status = '已退订' THEN 1 ELSE 0 END) AS "已退订"
FROM subscriptions AS s
GROUP BY s.customer_id
HAVING SUM(CASE WHEN s.status = '生效' THEN 1 ELSE 0 END) > 0
   AND SUM(CASE WHEN s.status = '已退订' THEN 1 ELSE 0 END) > 0
""",
        },
        {
            "id": 20,
            "problem": "APP或网厅办的卡里，没填办理工号的",
            "sql": """
SELECT s.subscription_id AS "订购号", s.msisdn AS "号码", s.channel_code AS "渠道", s.city_name AS "地市"
FROM subscriptions AS s
WHERE s.channel_code IN ('APP', '网厅') AND s.agent_id IS NULL
""",
        },
        {
            "id": 21,
            "problem": "语音主叫总时长超过全体号码平均时长两倍的号码",
            "sql": """
SELECT u.caller_msisdn AS "号码", SUM(u.duration_sec) AS "总秒数"
FROM usage_records AS u
WHERE u.usage_type = '语音' AND u.direction = '主叫' AND u.duration_sec IS NOT NULL
GROUP BY u.caller_msisdn
HAVING SUM(u.duration_sec) > 2 * (
  SELECT AVG(x.total_sec) FROM (
    SELECT SUM(u2.duration_sec) AS total_sec
    FROM usage_records AS u2
    WHERE u2.usage_type = '语音' AND u2.direction = '主叫' AND u2.duration_sec IS NOT NULL
    GROUP BY u2.caller_msisdn
  ) AS x
)
ORDER BY SUM(u.duration_sec) DESC
""",
        },
        {
            "id": 22,
            "problem": "对端号码也在这批话单里当过主叫的语音单，看前30条",
            "sql": """
SELECT u.usage_id AS "话单号", u.caller_msisdn AS "主叫", u.peer_number AS "对端", u.usage_time AS "时间"
FROM usage_records AS u
WHERE u.usage_type = '语音'
  AND u.peer_number IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM usage_records AS o
    WHERE o.caller_msisdn = u.peer_number AND o.usage_id <> u.usage_id
  )
LIMIT 30
""",
        },
        {
            "id": 23,
            "problem": "同一个号码、同一个月，既有语音又有流量的月份",
            "sql": """
SELECT u.caller_msisdn AS "号码", u.usage_month AS "月份",
       SUM(CASE WHEN u.usage_type = '语音' THEN 1 ELSE 0 END) AS "语音条数",
       SUM(CASE WHEN u.usage_type = '流量' THEN 1 ELSE 0 END) AS "流量条数"
FROM usage_records AS u
GROUP BY u.caller_msisdn, u.usage_month
HAVING SUM(CASE WHEN u.usage_type = '语音' THEN 1 ELSE 0 END) > 0
   AND SUM(CASE WHEN u.usage_type = '流量' THEN 1 ELSE 0 END) > 0
""",
        },
        {
            "id": 24,
            "problem": "单月话费合计高于该号码全部月份平均话费的那些月份",
            "sql": """
SELECT m.号码, m.月份, m.月话费
FROM (
  SELECT u.caller_msisdn AS "号码", u.usage_month AS "月份", ROUND(SUM(u.charge_amount), 2) AS "月话费"
  FROM usage_records AS u
  WHERE u.charge_amount IS NOT NULL
  GROUP BY u.caller_msisdn, u.usage_month
) AS m
WHERE m.月话费 > (
  SELECT AVG(m2.月话费) FROM (
    SELECT u2.caller_msisdn AS "号码", u2.usage_month AS "月份", SUM(u2.charge_amount) AS "月话费"
    FROM usage_records AS u2
    WHERE u2.charge_amount IS NOT NULL
    GROUP BY u2.caller_msisdn, u2.usage_month
  ) AS m2
  WHERE m2.号码 = m.号码
)
ORDER BY m.月话费 DESC
LIMIT 30
""",
        },
        {
            "id": 25,
            "problem": "漫游话单里，话费高于非漫游已批价平均话费的",
            "sql": """
SELECT u.usage_id AS "话单号", u.caller_msisdn AS "号码", u.roam_city AS "漫游地", u.charge_amount AS "话费"
FROM usage_records AS u
WHERE u.is_roaming = 1
  AND u.charge_amount > (
    SELECT AVG(u2.charge_amount)
    FROM usage_records AS u2
    WHERE u2.is_roaming = 0 AND u2.rating_status = '已批价' AND u2.charge_amount IS NOT NULL
  )
ORDER BY u.charge_amount DESC
LIMIT 30
""",
        },
        {
            "id": 26,
            "problem": "短信一次发了4条以上的短信话单",
            "sql": """
SELECT u.usage_id AS "话单号", u.caller_msisdn AS "号码", u.usage_time AS "时间", u.sms_cnt AS "条数"
FROM usage_records AS u
WHERE u.usage_type = '短信' AND u.sms_cnt >= 4
""",
        },
        {
            "id": 27,
            "problem": "话单超过两条、而且不止一种类型的号码",
            "sql": """
SELECT u.caller_msisdn AS "号码", COUNT(*) AS "条数", COUNT(DISTINCT u.usage_type) AS "类型数"
FROM usage_records AS u
GROUP BY u.caller_msisdn
HAVING COUNT(*) > 2 AND COUNT(DISTINCT u.usage_type) > 1
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 28,
            "problem": "哪类网络、哪个月的流量合计，高于所有网络月份的平均流量",
            "sql": """
SELECT g.网络, g.月份, g.流量KB
FROM (
  SELECT u.network_type AS "网络", u.usage_month AS "月份", SUM(u.data_kb) AS "流量KB"
  FROM usage_records AS u
  WHERE u.usage_type = '流量'
  GROUP BY u.network_type, u.usage_month
) AS g
WHERE g.流量KB > (
  SELECT AVG(x.kb) FROM (
    SELECT SUM(u2.data_kb) AS kb
    FROM usage_records AS u2
    WHERE u2.usage_type = '流量'
    GROUP BY u2.network_type, u2.usage_month
  ) AS x
)
ORDER BY g.流量KB DESC
""",
        },
        {
            "id": 29,
            "problem": "未付高于同账期平均未付的账单，看前30张",
            "sql": """
SELECT b.bill_no AS "账单号", b.bill_month AS "账期", b.unpaid_amount AS "未付"
FROM bills AS b
WHERE b.unpaid_amount > (
  SELECT AVG(b2.unpaid_amount) FROM bills AS b2 WHERE b2.bill_month = b.bill_month
)
ORDER BY b.unpaid_amount DESC
LIMIT 30
""",
        },
        {
            "id": 30,
            "problem": "已结清但付款时间是空的，或者未出账却已经有付款时间的",
            "sql": """
SELECT b.bill_no AS "账单号", b.bill_status AS "状态", b.pay_time AS "付款时间", b.paid_amount AS "已付"
FROM bills AS b
WHERE (b.bill_status = '已结清' AND b.pay_time IS NULL)
   OR (b.bill_status = '未出账' AND b.pay_time IS NOT NULL)
""",
        },
        {
            "id": 31,
            "problem": "每个地市未付合计高于全部地市平均未付合计的地市",
            "sql": """
SELECT g.地市编码, g.未付合计
FROM (
  SELECT b.city_code AS "地市编码", ROUND(SUM(b.unpaid_amount), 2) AS "未付合计"
  FROM bills AS b
  GROUP BY b.city_code
) AS g
WHERE g.未付合计 > (
  SELECT AVG(x.未付合计) FROM (
    SELECT SUM(b2.unpaid_amount) AS "未付合计"
    FROM bills AS b2
    GROUP BY b2.city_code
  ) AS x
)
ORDER BY g.未付合计 DESC
""",
        },
        {
            "id": 32,
            "problem": "调账金额不是0、而且总额仍然对不上分项的账单",
            "sql": """
SELECT b.bill_no AS "账单号", b.adjust_amount AS "调账", b.total_amount AS "总额"
FROM bills AS b
WHERE b.adjust_amount <> 0
  AND ABS(b.total_amount - (b.plan_fee + b.voice_fee + b.data_fee + b.sms_fee + b.value_added_fee - b.discount_amount + b.adjust_amount)) > 0.02
""",
        },
        {
            "id": 33,
            "problem": "同一个客户、同一个账期有不止一张账单的",
            "sql": """
SELECT b.customer_id AS "客户号", b.bill_month AS "账期", COUNT(*) AS "张数", ROUND(SUM(b.total_amount), 2) AS "总额合计"
FROM bills AS b
GROUP BY b.customer_id, b.bill_month
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 34,
            "problem": "未付金额和「总额减已付」对不上的账单",
            "sql": """
SELECT b.bill_no AS "账单号", b.total_amount AS "总额", b.paid_amount AS "已付", b.unpaid_amount AS "未付"
FROM bills AS b
WHERE ABS(b.unpaid_amount - (b.total_amount - b.paid_amount)) > 0.02
""",
        },
        {
            "id": 35,
            "problem": "子单和父单不是同一类的投诉",
            "sql": """
SELECT t.ticket_no AS "子单", t.category AS "子单类别", p.ticket_no AS "父单", p.category AS "父单类别"
FROM tickets AS t
JOIN tickets AS p ON t.parent_ticket_id = p.ticket_id
WHERE t.category <> p.category
LIMIT 40
""",
        },
        {
            "id": 36,
            "problem": "自己下面还有子单的父单，看子单有几张",
            "sql": """
SELECT p.ticket_no AS "父单", p.status AS "父单状态", COUNT(*) AS "子单数"
FROM tickets AS t
JOIN tickets AS p ON t.parent_ticket_id = p.ticket_id
GROUP BY p.ticket_id, p.ticket_no, p.status
ORDER BY COUNT(*) DESC
""",
        },
        {
            "id": 37,
            "problem": "子单已经关闭、父单还在处理中",
            "sql": """
SELECT t.ticket_no AS "子单", t.closed_time AS "子单关闭时间", p.ticket_no AS "父单", p.status AS "父单状态"
FROM tickets AS t
JOIN tickets AS p ON t.parent_ticket_id = p.ticket_id
WHERE t.status = '已关闭' AND p.status = '处理中'
""",
        },
        {
            "id": 38,
            "problem": "每个地市单量最多的投诉类别",
            "sql": """
SELECT t.city_name AS "地市", t.category AS "类别", COUNT(*) AS "单量"
FROM tickets AS t
GROUP BY t.city_name, t.category
HAVING COUNT(*) = (
  SELECT MAX(cnt) FROM (
    SELECT COUNT(*) AS cnt
    FROM tickets AS t2
    WHERE t2.city_name = t.city_name
    GROUP BY t2.category
  )
)
ORDER BY t.city_name
""",
        },
        {
            "id": 39,
            "problem": "满意度低于同类别平均分、而且还升级过的单子",
            "sql": """
SELECT t.ticket_no AS "单号", t.category AS "类别", t.satisfaction_score AS "评分"
FROM tickets AS t
WHERE t.is_escalated = 1
  AND t.satisfaction_score IS NOT NULL
  AND t.satisfaction_score < (
    SELECT AVG(t2.satisfaction_score)
    FROM tickets AS t2
    WHERE t2.category = t.category AND t2.satisfaction_score IS NOT NULL
  )
""",
        },
        {
            "id": 40,
            "problem": "已经关闭、而且关闭时间比建单晚了3天以上的单子",
            "sql": """
SELECT t.ticket_no AS "单号", t.city_name AS "地市", t.created_time AS "建单", t.closed_time AS "关闭", t.sla_hours AS "时限小时"
FROM tickets AS t
WHERE t.status = '已关闭'
  AND t.closed_time IS NOT NULL
  AND t.closed_time > datetime(t.created_time, '+3 day')
""",
        },
    ],
}


def _check_rules():
    assert set(sql_problems) == {"初级", "中级", "高级"}
    assert [len(sql_problems[k]) for k in ("初级", "中级", "高级")] == [20, 40, 40]
    for level, items in sql_problems.items():
        ids = [item["id"] for item in items]
        assert ids == list(range(1, len(items) + 1)), (level, ids[:5])
        for item in items:
            problem = item["problem"]
            sql = item["sql"].strip()
            assert "查询" not in problem, problem
            assert sql.upper().startswith("SELECT"), item["id"]
            upper = sql.upper()
            assert " WITH " not in f" {upper} "
            for ban in (" OVER ", " ROW_NUMBER", " RANK(", " LAG(", " LEAD(", "WITH "):
                assert ban not in upper, (level, item["id"], ban)


def check_against_db(db_path: str) -> None:
    import sqlite3

    _check_rules()
    con = sqlite3.connect(db_path)
    bad = []
    for level, items in sql_problems.items():
        for item in items:
            sql = item["sql"].strip().rstrip(";")
            try:
                rows = con.execute(sql).fetchall()
            except sqlite3.Error as exc:
                bad.append((level, item["id"], str(exc)))
                continue
            if len(rows) == 0:
                bad.append((level, item["id"], "0 rows"))
    con.close()
    if bad:
        for item in bad:
            print("FAIL", *item)
        raise SystemExit(f"{len(bad)} 题没通过")
    print("100 题都能跑出结果")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    _check_rules()
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "telecom_ops.db"
    if not db.exists():
        print("规则检查通过。旁边没有 telecom_ops.db，跳过实跑。")
    else:
        check_against_db(str(db))
