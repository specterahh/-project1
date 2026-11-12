"""云栖移动 telecom_ops 放量数据。

在脚本所在目录生成：
  telecom_ops.db     SQLite 库
  telecom_ops.xlsx   一个工作簿，每张表一个 sheet

用法（先关掉 DB Browser 里打开的同名库）：
  python generate_data.py
  python generate_data.py --rows 10000
  python generate_data.py --rows 200000

默认每个表 10000 行。时间用 datetime 生成，再用 strftime 存成字符串。
业务时间落在 2020-01-01 到 2025-11-30。出生日期按真实年龄，可以早于 2020。
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

START = datetime(2020, 1, 1, 0, 0, 0)
END = datetime(2025, 11, 30, 23, 59, 59)

CITIES = [
    ("330100", "杭州"), ("330200", "宁波"), ("330300", "温州"),
    ("330400", "嘉兴"), ("330500", "湖州"), ("330600", "绍兴"),
    ("330700", "金华"), ("330800", "衢州"), ("330900", "舟山"),
    ("331000", "台州"), ("331100", "丽水"),
]
DISTRICTS = {
    "杭州": ["西湖区", "滨江区", "余杭区", "萧山区"],
    "宁波": ["海曙区", "鄞州区", "江北区"],
    "温州": ["鹿城区", "瓯海区", "龙湾区"],
    "嘉兴": ["南湖区", "秀洲区"],
    "湖州": ["吴兴区", "南浔区"],
    "绍兴": ["越城区", "柯桥区"],
    "金华": ["婺城区", "金东区"],
    "衢州": ["柯城区", "衢江区"],
    "舟山": ["定海区", "普陀区"],
    "台州": ["椒江区", "临海市"],
    "丽水": ["莲都区", "缙云县"],
}
SURNAMES = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕张孔曹严华金魏陶姜")
GIVEN = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀英", "浩", "婷"]
LEVELS = ["普通", "银卡", "金卡", "钻石"]
CUST_STATUS = ["在网", "停机", "销户", "欠费停机"]
PLAN_TYPES = ["语音", "流量", "融合", "宽带", "物联网"]
SEGMENTS = ["大众", "校园", "政企", "老人"]
STEMS = {
    "语音": ["飞享", "孝心卡", "畅聊"],
    "流量": ["畅享", "校园卡", "日租卡"],
    "融合": ["全家享", "5G畅享", "政企通"],
    "宽带": ["宽带融合", "千兆融合", "家庭宽带"],
    "物联网": ["物联网专网", "行业卡", "连接卡"],
}
EDITIONS = ["标准版", "升级版", "青春版"]
CHANNELS = ["营业厅", "APP", "网厅", "代理商", "客服"]
SUB_STATUS = ["生效", "预约生效", "停机", "已退订"]
USAGE_TYPES = ["语音", "流量", "短信", "增值"]
DIRECTIONS = {"语音": ["主叫", "被叫"], "流量": ["上行", "下行"], "短信": ["上行", "下行"], "增值": ["上行", "下行"]}
NETWORKS = ["2G", "4G", "5G", "WIFI"]
RATING = ["已批价", "未批价", "批价失败"]
BILL_STATUS = ["未出账", "已出账", "部分支付", "已结清", "坏账"]
PAY_CHANNELS = ["微信", "支付宝", "银行卡", "现金", "托收"]
TICKET_CATS = {
    "费用": ["多扣费", "不明扣费", "发票"],
    "网络": ["无信号", "网速慢", "断线"],
    "业务办理": ["无法办理", "办理错误", "携号转网"],
    "服务态度": ["推诿", "等待过长", "解释不清"],
}
PRIORITIES = ["低", "中", "高", "紧急"]
TICKET_STATUS = ["新建", "处理中", "待回访", "已关闭", "已撤销"]
TICKET_CHANNELS = ["10086", "APP", "营业厅", "工信部转办"]
FEES = [8, 19, 29, 39, 59, 79, 99, 129, 169, 199, 299, 399]

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  customer_no TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  id_card_no TEXT,
  gender TEXT NOT NULL,
  birth_date TEXT,
  phone_no TEXT NOT NULL,
  email TEXT,
  city_code TEXT NOT NULL,
  city_name TEXT NOT NULL,
  district_name TEXT,
  address TEXT,
  customer_level TEXT NOT NULL,
  status TEXT NOT NULL,
  referrer_customer_id INTEGER,
  register_time TEXT NOT NULL,
  cancel_time TEXT,
  credit_score INTEGER,
  profile_json TEXT,
  is_test_user INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (referrer_customer_id) REFERENCES customers(customer_id)
);
CREATE INDEX idx_customers_phone ON customers(phone_no);
CREATE INDEX idx_customers_city ON customers(city_code, status);
CREATE INDEX idx_customers_level ON customers(customer_level, register_time);
CREATE INDEX idx_customers_referrer ON customers(referrer_customer_id);

CREATE TABLE plans (
  plan_id INTEGER PRIMARY KEY,
  plan_code TEXT NOT NULL UNIQUE,
  plan_name TEXT NOT NULL,
  plan_type TEXT NOT NULL,
  monthly_fee REAL NOT NULL,
  voice_minutes INTEGER NOT NULL,
  data_mb INTEGER NOT NULL,
  sms_count INTEGER NOT NULL,
  overage_voice_fee REAL NOT NULL,
  overage_data_fee REAL NOT NULL,
  contract_months INTEGER NOT NULL,
  effective_from TEXT NOT NULL,
  effective_to TEXT,
  status TEXT NOT NULL,
  target_segment TEXT NOT NULL,
  region_limit TEXT,
  benefit_json TEXT,
  offline_reason TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_plans_type ON plans(plan_type, status);
CREATE INDEX idx_plans_fee ON plans(monthly_fee);
CREATE INDEX idx_plans_segment ON plans(target_segment, region_limit);

CREATE TABLE subscriptions (
  subscription_id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  plan_id INTEGER NOT NULL,
  msisdn TEXT NOT NULL,
  iccid TEXT,
  imsi TEXT,
  start_time TEXT NOT NULL,
  end_time TEXT,
  contract_end_time TEXT,
  channel_code TEXT NOT NULL,
  agent_id TEXT,
  city_code TEXT NOT NULL,
  city_name TEXT NOT NULL,
  monthly_fee_snapshot REAL NOT NULL,
  discount_rate REAL,
  status TEXT NOT NULL,
  auto_renew INTEGER NOT NULL DEFAULT 1,
  promo_code TEXT,
  extra_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (customer_id, plan_id, start_time),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
);
CREATE INDEX idx_sub_customer ON subscriptions(customer_id, status);
CREATE INDEX idx_sub_plan ON subscriptions(plan_id);
CREATE INDEX idx_sub_msisdn ON subscriptions(msisdn);
CREATE INDEX idx_sub_city ON subscriptions(city_code, start_time);

CREATE TABLE usage_records (
  usage_id INTEGER PRIMARY KEY,
  subscription_id INTEGER NOT NULL,
  customer_id INTEGER NOT NULL,
  caller_msisdn TEXT NOT NULL,
  usage_time TEXT NOT NULL,
  usage_month TEXT NOT NULL,
  usage_type TEXT NOT NULL,
  direction TEXT NOT NULL,
  peer_number TEXT,
  duration_sec INTEGER,
  data_kb INTEGER,
  sms_cnt INTEGER,
  charge_amount REAL,
  is_roaming INTEGER NOT NULL DEFAULT 0,
  roam_city TEXT,
  cell_id TEXT,
  network_type TEXT NOT NULL,
  rating_status TEXT NOT NULL,
  raw_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE INDEX idx_usage_month ON usage_records(usage_month, usage_type);
CREATE INDEX idx_usage_time ON usage_records(usage_time);
CREATE INDEX idx_usage_customer ON usage_records(customer_id, usage_month);
CREATE INDEX idx_usage_caller ON usage_records(caller_msisdn);
CREATE INDEX idx_usage_peer ON usage_records(peer_number);
CREATE INDEX idx_usage_sub ON usage_records(subscription_id, usage_time);

CREATE TABLE bills (
  bill_id INTEGER PRIMARY KEY,
  bill_no TEXT NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL,
  subscription_id INTEGER NOT NULL,
  bill_month TEXT NOT NULL,
  plan_fee REAL NOT NULL,
  voice_fee REAL NOT NULL,
  data_fee REAL NOT NULL,
  sms_fee REAL NOT NULL,
  value_added_fee REAL NOT NULL,
  discount_amount REAL NOT NULL,
  adjust_amount REAL NOT NULL,
  total_amount REAL NOT NULL,
  paid_amount REAL NOT NULL,
  unpaid_amount REAL NOT NULL,
  bill_status TEXT NOT NULL,
  issue_time TEXT NOT NULL,
  due_time TEXT NOT NULL,
  pay_time TEXT,
  pay_channel TEXT,
  invoice_no TEXT,
  city_code TEXT NOT NULL,
  remark TEXT,
  fee_detail_json TEXT,
  UNIQUE (customer_id, subscription_id, bill_month),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);
CREATE INDEX idx_bills_month ON bills(bill_month, bill_status);
CREATE INDEX idx_bills_city ON bills(city_code, bill_month);
CREATE INDEX idx_bills_unpaid ON bills(unpaid_amount, due_time);
CREATE INDEX idx_bills_sub ON bills(subscription_id);

CREATE TABLE tickets (
  ticket_id INTEGER PRIMARY KEY,
  ticket_no TEXT NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL,
  subscription_id INTEGER,
  parent_ticket_id INTEGER,
  related_bill_id INTEGER,
  category TEXT NOT NULL,
  sub_category TEXT NOT NULL,
  priority TEXT NOT NULL,
  status TEXT NOT NULL,
  channel TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  city_code TEXT NOT NULL,
  city_name TEXT NOT NULL,
  created_time TEXT NOT NULL,
  first_response_time TEXT,
  closed_time TEXT,
  sla_hours INTEGER NOT NULL,
  is_escalated INTEGER NOT NULL DEFAULT 0,
  satisfaction_score INTEGER,
  handler_id TEXT,
  tags_json TEXT,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
  FOREIGN KEY (parent_ticket_id) REFERENCES tickets(ticket_id),
  FOREIGN KEY (related_bill_id) REFERENCES bills(bill_id)
);
CREATE INDEX idx_tickets_customer ON tickets(customer_id, status);
CREATE INDEX idx_tickets_parent ON tickets(parent_ticket_id);
CREATE INDEX idx_tickets_created ON tickets(created_time);
CREATE INDEX idx_tickets_cat ON tickets(category, sub_category, priority);
CREATE INDEX idx_tickets_city ON tickets(city_code, created_time);
"""

TABLES = ["customers", "plans", "subscriptions", "usage_records", "bills", "tickets"]


def stamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def day(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def month(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def rand_dt(rng: random.Random, start: datetime, end: datetime) -> datetime:
    if end <= start:
        return start
    return start + timedelta(seconds=rng.randint(0, int((end - start).total_seconds())))


def phone(rng: random.Random) -> str:
    prefix = rng.choice(["130", "131", "135", "136", "137", "138", "139", "150", "151", "158", "159", "186", "187", "188", "198"])
    return prefix + "".join(str(rng.randint(0, 9)) for _ in range(8))


def id_card(rng: random.Random, birth: datetime | None) -> str:
    area = rng.choice(CITIES)[0] + f"{rng.randint(0, 99):02d}"
    if birth is None:
        birth_s = f"{rng.randint(1970, 2002)}{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}"
    else:
        birth_s = birth.strftime("%Y%m%d")
    return area + birth_s + f"{rng.randint(0, 999):03d}" + rng.choice("0123456789X")


def digits(rng: random.Random, width: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(width))


def log(message: str) -> None:
    print(message, flush=True)


def insert_many(con: sqlite3.Connection, sql: str, rows: list[tuple], batch: int = 5000) -> None:
    for offset in range(0, len(rows), batch):
        con.executemany(sql, rows[offset : offset + batch])
    con.commit()


def build_customers(rng: random.Random, n: int) -> tuple[list[tuple], list[dict]]:
    rows = []
    phones = [phone(rng) for _ in range(n)]
    dup_n = min(n // 2, max(3, n // 300)) if n >= 6 else 0
    for i in range(dup_n):
        phones[n - 1 - i] = phones[i]
    cards: list[str | None] = []
    slim = []
    closed_without_cancel = 0
    cancel_budget = max(2, n // 500)
    for i in range(1, n + 1):
        city_code, city_name = CITIES[(i - 1) % len(CITIES)]
        district = rng.choice(DISTRICTS[city_name])
        birth = None if i % 17 == 0 else datetime(rng.randint(1960, 2004), rng.randint(1, 12), rng.randint(1, 28))
        status = rng.choices(CUST_STATUS, weights=[70, 10, 12, 8])[0]
        register = rand_dt(rng, START, END - timedelta(days=30))
        cancel = None
        if status == "销户":
            if closed_without_cancel < cancel_budget:
                closed_without_cancel += 1
            else:
                cancel = rand_dt(rng, register, END)
        level = rng.choices(LEVELS, weights=[55, 25, 15, 5])[0]
        card = None if i % 11 == 0 else id_card(rng, birth)
        cards.append(card)
        email = None if i % 7 == 0 else f"user{i:07d}@example.com"
        if i % 400 == 0:
            score = -rng.randint(1, 40)
        elif i % 450 == 0:
            score = rng.randint(1001, 1500)
        elif i % 19 == 0:
            score = None
        else:
            score = rng.randint(320, 860)
        referrer = None if i <= max(15, n // 20) else rng.randint(1, i - 1)
        if i % 89 == 0:
            profile = "{bad-json"
        else:
            profile = json.dumps(
                {"terminal": rng.choice(["4G", "5G"]), "elder_plan_interest": level == "老人", "tags": [rng.choice(["视频", "游戏", "上网课", "商务"])]},
                ensure_ascii=False,
            )
        rows.append((
            i, f"YQ{register.year}{i:08d}", rng.choice(SURNAMES) + rng.choice(GIVEN),
            card, rng.choices(["男", "女", "未知"], weights=[48, 48, 4])[0],
            day(birth) if birth else None, phones[i - 1], email, city_code, city_name, district,
            f"{city_name}{district}示例路{rng.randint(1, 200)}号",
            level, status, referrer, stamp(register), stamp(cancel) if cancel else None,
            score, profile, 1 if i % 500 == 0 else 0, stamp(rand_dt(rng, register, END)),
        ))
        slim.append({"id": i, "phone": phones[i - 1], "city_code": city_code, "city_name": city_name, "register": register})
    if n > 4 and cards[3]:
        rows[n // 2] = rows[n // 2][:3] + (cards[3],) + rows[n // 2][4:]
    return rows, slim


def build_plans(rng: random.Random, n: int) -> tuple[list[tuple], list[dict]]:
    rows = []
    slim = []
    for i in range(1, n + 1):
        ptype = PLAN_TYPES[(i - 1) % len(PLAN_TYPES)]
        segment = SEGMENTS[(i * 3) % len(SEGMENTS)]
        fee = FEES[(i - 1) % len(FEES)]
        stem = STEMS[ptype][(i // len(PLAN_TYPES)) % len(STEMS[ptype])]
        edition = EDITIONS[i % len(EDITIONS)]
        city_code, city_name = CITIES[i % len(CITIES)]
        region = None if i % 4 != 0 else city_code
        place = "全省" if region is None else city_name
        opened = rand_dt(rng, START, datetime(2024, 6, 1))
        status = "停售" if i % 6 == 0 else "在售"
        closed_at = None
        if status == "停售":
            closed_at = rand_dt(rng, opened, END)
            if i % 333 == 0 and opened - timedelta(days=10) >= START:
                closed_at = opened - timedelta(days=10)
        benefit = "{bad" if i % 97 == 0 else json.dumps(
            {"sub_cards": rng.randint(0, 3), "broadband_mbps": rng.choice([0, 100, 300, 500, 1000]), "member": rng.choice(["无", "视频会员", "音乐会员"])},
            ensure_ascii=False,
        )
        rows.append((
            i, f"P{i:06d}", f"{place}{stem}{fee}元{edition}", ptype, float(fee),
            0 if ptype == "流量" else rng.choice([100, 200, 500, 1000, 2000]),
            0 if ptype == "语音" else rng.choice([1024, 5120, 10240, 30720, 61440]),
            rng.choice([0, 50, 100, 200]),
            round(rng.choice([0.1, 0.15, 0.19, 0.25]), 2),
            round(rng.choice([0.01, 0.03, 0.05, 0.1]), 2),
            rng.choice([0, 6, 12, 24, 36]),
            stamp(opened), stamp(closed_at) if closed_at else None, status, segment, region, benefit,
            None if status == "在售" else rng.choice(["资费调整", "合约到期", "替换新产品"]),
            stamp(opened),
        ))
        slim.append({"id": i, "fee": float(fee), "months": rows[-1][10], "opened": opened})
    return rows, slim


def build_subscriptions(rng: random.Random, n: int, customers: list[dict], plans: list[dict]) -> tuple[list[tuple], list[dict]]:
    n_double = n // 10
    n_single = n - 2 * n_double
    pairs = [(cid, 1) for cid in range(1, n_single + 1)]
    for cid in range(n_single + 1, n_single + n_double + 1):
        pairs.append((cid, 1))
        pairs.append((cid, 2))
    rows = []
    slim = []
    for sid, (cid, nth) in enumerate(pairs, start=1):
        cust = customers[cid - 1]
        plan = plans[((cid - 1 + (nth - 1) * 7919) % n)]
        begin = max(cust["register"], plan["opened"], START)
        if begin >= END - timedelta(days=1):
            begin = START
        start_time = rand_dt(rng, begin, END - timedelta(days=1))
        if nth == 2:
            start_time = min(END - timedelta(hours=1), start_time + timedelta(days=30))
        status = rng.choices(SUB_STATUS, weights=[60, 8, 12, 20])[0]
        end_time = None
        if status == "已退订":
            end_time = rand_dt(rng, start_time, END)
        if sid % 333 == 0 and start_time - timedelta(days=3) >= START:
            end_time = start_time - timedelta(days=3)
            status = "已退订"
        contract_end = None
        if plan["months"]:
            contract_end = min(END, start_time + timedelta(days=30 * plan["months"]))
        channel = rng.choice(CHANNELS)
        agent = None if channel in ("APP", "网厅") and rng.random() < 0.8 else f"AG{rng.randint(1000, 9999)}"
        if sid % 271 == 0:
            rate = None
        elif sid % 277 == 0:
            rate = 1.4
        elif sid % 281 == 0:
            rate = -0.2
        else:
            rate = round(rng.choice([1, 0.95, 0.9, 0.8, 0.7]), 2)
        msisdn = cust["phone"] if nth == 1 else phone(rng)
        extra = "{bad" if sid % 311 == 0 else json.dumps({"nth_card": nth, "device_contract": nth == 2 and rng.random() < 0.3}, ensure_ascii=False)
        rows.append((
            sid, cid, plan["id"], msisdn, "8986" + digits(rng, 15), "460" + digits(rng, 12),
            stamp(start_time), stamp(end_time) if end_time else None,
            stamp(contract_end) if contract_end else None,
            channel, agent, cust["city_code"], cust["city_name"], plan["fee"], rate, status,
            0 if status == "已退订" else 1,
            None if rng.random() < 0.7 else f"PROMO{rng.randint(10, 99)}",
            extra, stamp(start_time), stamp(rand_dt(rng, start_time, END)),
        ))
        slim.append({
            "id": sid, "customer_id": cid, "msisdn": msisdn, "start": start_time,
            "end": end_time, "fee": plan["fee"], "city_code": cust["city_code"],
        })
    return rows, slim


def build_usage(rng: random.Random, n: int, subs: list[dict], msisdns: list[str]) -> list[tuple]:
    rows = []
    for uid in range(1, n + 1):
        sub = subs[rng.randrange(n)]
        end_limit = sub["end"] if sub["end"] and sub["end"] > sub["start"] else END
        when = rand_dt(rng, max(sub["start"], START), min(end_limit, END))
        utype = USAGE_TYPES[(uid - 1) % len(USAGE_TYPES)]
        rating = rng.choices(RATING, weights=[80, 12, 8])[0]
        duration = data_kb = sms_cnt = None
        if utype == "语音":
            duration = rng.randint(5, 1800)
        elif utype == "流量":
            data_kb = rng.randint(20, 2_000_000)
        elif utype == "短信":
            sms_cnt = rng.randint(1, 5)
        else:
            duration = rng.randint(0, 60)
        charge = None if rating != "已批价" else round(rng.random() * 8, 2)
        if uid % 211 == 0:
            charge = round(-rng.random() * 5, 2)
            rating = "已批价"
        roaming = 1 if uid % 9 == 0 else 0
        peer = None if utype == "流量" and uid % 2 == 0 else msisdns[uid % len(msisdns)]
        raw = "not-json" if uid % 223 == 0 else json.dumps({"cell_hint": f"HZ-{uid % 80:02d}", "seq": uid}, ensure_ascii=False)
        rows.append((
            uid, sub["id"], sub["customer_id"], sub["msisdn"], stamp(when), month(when), utype,
            rng.choice(DIRECTIONS[utype]), peer, duration, data_kb, sms_cnt, charge, roaming,
            rng.choice(["上海", "南京", "北京"]) if roaming else None,
            f"CELL{rng.randint(10000, 99999)}", rng.choices(NETWORKS, weights=[5, 25, 60, 10])[0],
            rating, raw, stamp(min(END, when + timedelta(minutes=rng.randint(1, 120)))),
        ))
    return rows


def build_bills(rng: random.Random, n: int, subs: list[dict]) -> list[tuple]:
    rows = []
    for bid in range(1, n + 1):
        sub = subs[bid - 1]
        bill_month_dt = datetime(sub["start"].year, sub["start"].month, 1)
        issue = min(END, max(bill_month_dt, START) + timedelta(days=rng.randint(0, 5), hours=8))
        due = min(END, issue + timedelta(days=15))
        if due < issue:
            due = issue
        plan_fee = round(sub["fee"], 2)
        voice_fee = round(rng.random() * 20, 2)
        data_fee = round(rng.random() * 30, 2)
        sms_fee = round(rng.random() * 5, 2)
        value_added = round(rng.choice([0, 0, 5, 6, 10, 15]), 2)
        discount = round(rng.choice([0, 0, 5, 10, 20]), 2)
        adjust = round(rng.choice([0, 0, 0, -5, -10, 3]), 2)
        total = round(plan_fee + voice_fee + data_fee + sms_fee + value_added - discount + adjust, 2)
        if bid % 97 == 0:
            total = round(total + rng.choice([-15, 8, 21, -3]), 2)
        status = rng.choices(BILL_STATUS, weights=[5, 15, 15, 60, 5])[0]
        if status == "已结清":
            paid = total
        elif status == "部分支付":
            paid = round(total * rng.uniform(0.2, 0.8), 2) if total > 0 else 0.0
        else:
            paid = 0.0
        if bid % 257 == 0:
            paid = round(total + 12, 2)
        unpaid = round(total - paid, 2)
        if bid % 263 == 0:
            unpaid = round(unpaid + 7, 2)
        pay_time = None
        pay_channel = None
        settled_without_pay = status == "已结清" and bid % 251 == 0
        if status in ("已结清", "部分支付") and not settled_without_pay:
            pay_time = stamp(rand_dt(rng, issue, END))
            pay_channel = rng.choice(PAY_CHANNELS)
        detail = "[1,2," if bid % 227 == 0 else json.dumps({"idd": 0, "ringtone": value_added}, ensure_ascii=False)
        remark = None if rng.random() < 0.85 else rng.choice(["客户来电核对", "调账", "投诉后退费"])
        rows.append((
            bid, f"B{bill_month_dt.strftime('%Y%m')}{bid:08d}", sub["customer_id"], sub["id"], month(bill_month_dt),
            plan_fee, voice_fee, data_fee, sms_fee, value_added, discount, adjust, total, round(paid, 2), unpaid,
            status, stamp(issue), stamp(due), pay_time, pay_channel,
            None if rng.random() < 0.6 else f"INV{bid:08d}", sub["city_code"], remark, detail,
        ))
    return rows


def build_tickets(rng: random.Random, n: int, customers: list[dict], subs_by_customer: dict[int, list[int]], bill_by_sub: dict[int, int]) -> list[tuple]:
    rows = []
    for tid in range(1, n + 1):
        parent = None
        if tid > n // 10 and rng.random() < 0.22:
            parent = rng.randint(1, tid - 1)
            cid = rows[parent - 1][2]
            sub_id = None
            related = None
        else:
            cid = rng.randint(1, n)
            sub_id = None
            if cid in subs_by_customer and rng.random() < 0.75:
                sub_id = rng.choice(subs_by_customer[cid])
            related = bill_by_sub.get(sub_id) if sub_id and rng.random() < 0.5 else None
        cust = customers[cid - 1]
        cat = rng.choice(list(TICKET_CATS))
        subcat = rng.choice(TICKET_CATS[cat])
        status = rng.choices(TICKET_STATUS, weights=[10, 20, 10, 50, 10])[0]
        created = rand_dt(rng, START, END - timedelta(days=1))
        sla = rng.choice([4, 8, 24, 48, 72])
        first = None if status == "新建" and rng.random() < 0.7 else min(END, created + timedelta(hours=rng.randint(1, sla)))
        closed = None
        if status in ("已关闭", "已撤销"):
            base = first or created
            closed = min(END, base + timedelta(hours=rng.randint(1, 96)))
        if status == "已关闭" and tid % 229 == 0:
            closed = None
        if tid % 180 == 0:
            score = 0 if tid % 360 == 0 else 9
        elif status != "已关闭" or rng.random() < 0.2:
            score = None
        else:
            score = rng.randint(1, 5)
        tags = "not-json" if tid % 233 == 0 else json.dumps(rng.sample(["重复投诉", "携号转网", "老人", "升级"], rng.randint(0, 2)), ensure_ascii=False)
        rows.append((
            tid, f"T{created.strftime('%Y%m%d')}{tid:07d}", cid, sub_id, parent, related,
            cat, subcat, rng.choices(PRIORITIES, weights=[30, 40, 20, 10])[0], status,
            rng.choice(TICKET_CHANNELS), f"{subcat}问题{tid}", f"客户反映{cust['city_name']}{subcat}",
            cust["city_code"], cust["city_name"], stamp(created), stamp(first) if first else None,
            stamp(closed) if closed else None, sla, 1 if tid % 8 == 0 else 0, score,
            f"HK{rng.randint(100, 999)}", tags,
        ))
    return rows


def export_excel(con: sqlite3.Connection, path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError:
        sys.exit("缺少 openpyxl。先执行：pip install openpyxl")
    book = Workbook(write_only=True)
    for name in TABLES:
        sheet = book.create_sheet(name)
        cursor = con.execute(f"SELECT * FROM {name}")
        sheet.append([item[0] for item in cursor.description])
        while True:
            chunk = cursor.fetchmany(5000)
            if not chunk:
                break
            for row in chunk:
                sheet.append(list(row))
        log(f"  已写入 sheet {name}")
    book.save(path)


def verify(con: sqlite3.Connection, n: int) -> None:
    bad_fk = con.execute("PRAGMA foreign_key_check").fetchall()
    if bad_fk:
        raise SystemExit(f"外键检查失败：{bad_fk[:5]}")
    for name in TABLES:
        count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        if count != n:
            raise SystemExit(f"{name} 行数是 {count}，不是 {n}")
    mismatch = con.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM usage_records u JOIN subscriptions s ON u.subscription_id = s.subscription_id WHERE u.customer_id != s.customer_id),
          (SELECT COUNT(*) FROM bills b JOIN subscriptions s ON b.subscription_id = s.subscription_id WHERE b.customer_id != s.customer_id),
          (SELECT COUNT(*) FROM usage_records WHERE substr(usage_time, 1, 7) != usage_month),
          (SELECT COUNT(*) FROM tickets t JOIN subscriptions s ON t.subscription_id = s.subscription_id WHERE t.customer_id != s.customer_id)
        """
    ).fetchone()
    if any(mismatch):
        raise SystemExit(f"关联或月份不一致：{mismatch}")
    too_early = con.execute(
        """
        SELECT COUNT(*) FROM (
          SELECT register_time AS t FROM customers
          UNION ALL SELECT cancel_time FROM customers WHERE cancel_time IS NOT NULL
          UNION ALL SELECT usage_time FROM usage_records
          UNION ALL SELECT issue_time FROM bills
          UNION ALL SELECT created_time FROM tickets
        ) WHERE t < '2020-01-01' OR t >= '2025-12-01'
        """
    ).fetchone()[0]
    if too_early:
        raise SystemExit(f"有 {too_early} 个业务时间不在 2020-01 到 2025-11")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="生成 telecom_ops 的 SQLite 和 Excel")
    parser.add_argument("--rows", type=int, default=10000, help="每张表的行数，默认 10000，最大 200000")
    parser.add_argument("--seed", type=int, default=42, help="随机种子，默认 42")
    parser.add_argument("--outdir", type=Path, default=None, help="输出目录，默认脚本所在目录")
    args = parser.parse_args()
    if not 1 <= args.rows <= 200_000:
        sys.exit("--rows 需要在 1 到 200000 之间")

    outdir = (args.outdir or Path(__file__).resolve().parent).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    db_path = outdir / "telecom_ops.db"
    xlsx_path = outdir / "telecom_ops.xlsx"
    try:
        if db_path.exists():
            db_path.unlink()
        if xlsx_path.exists():
            xlsx_path.unlink()
    except PermissionError:
        sys.exit("文件被占用。请先关闭 DB Browser 和 Excel 里打开的 telecom_ops.db / telecom_ops.xlsx，再运行。")

    rng = random.Random(args.seed)
    n = args.rows
    log(f"每张表 {n} 行，输出到 {outdir}")

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = MEMORY")
    con.execute("PRAGMA synchronous = OFF")
    con.executescript(SCHEMA_SQL)

    log("[1/6] 客户")
    customers, cust_slim = build_customers(rng, n)
    insert_many(con, """INSERT INTO customers (
        customer_id, customer_no, full_name, id_card_no, gender, birth_date, phone_no, email,
        city_code, city_name, district_name, address, customer_level, status, referrer_customer_id,
        register_time, cancel_time, credit_score, profile_json, is_test_user, updated_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", customers)
    del customers

    log("[2/6] 套餐")
    plans, plan_slim = build_plans(rng, n)
    insert_many(con, """INSERT INTO plans (
        plan_id, plan_code, plan_name, plan_type, monthly_fee, voice_minutes, data_mb, sms_count,
        overage_voice_fee, overage_data_fee, contract_months, effective_from, effective_to, status,
        target_segment, region_limit, benefit_json, offline_reason, created_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", plans)
    del plans

    log("[3/6] 订购")
    subs, sub_slim = build_subscriptions(rng, n, cust_slim, plan_slim)
    insert_many(con, """INSERT INTO subscriptions (
        subscription_id, customer_id, plan_id, msisdn, iccid, imsi, start_time, end_time,
        contract_end_time, channel_code, agent_id, city_code, city_name, monthly_fee_snapshot,
        discount_rate, status, auto_renew, promo_code, extra_json, created_at, updated_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", subs)
    del subs
    msisdns = [item["msisdn"] for item in sub_slim]
    subs_by_customer: dict[int, list[int]] = {}
    for item in sub_slim:
        subs_by_customer.setdefault(item["customer_id"], []).append(item["id"])

    log("[4/6] 话单")
    usage = build_usage(rng, n, sub_slim, msisdns)
    insert_many(con, """INSERT INTO usage_records (
        usage_id, subscription_id, customer_id, caller_msisdn, usage_time, usage_month,
        usage_type, direction, peer_number, duration_sec, data_kb, sms_cnt, charge_amount,
        is_roaming, roam_city, cell_id, network_type, rating_status, raw_json, created_at
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", usage)
    del usage

    log("[5/6] 账单")
    bills = build_bills(rng, n, sub_slim)
    insert_many(con, """INSERT INTO bills (
        bill_id, bill_no, customer_id, subscription_id, bill_month, plan_fee, voice_fee, data_fee,
        sms_fee, value_added_fee, discount_amount, adjust_amount, total_amount, paid_amount,
        unpaid_amount, bill_status, issue_time, due_time, pay_time, pay_channel, invoice_no,
        city_code, remark, fee_detail_json
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", bills)
    bill_by_sub = {row[3]: row[0] for row in bills}
    del bills

    log("[6/6] 投诉")
    tickets = build_tickets(rng, n, cust_slim, subs_by_customer, bill_by_sub)
    insert_many(con, """INSERT INTO tickets (
        ticket_id, ticket_no, customer_id, subscription_id, parent_ticket_id, related_bill_id,
        category, sub_category, priority, status, channel, title, description, city_code, city_name,
        created_time, first_response_time, closed_time, sla_hours, is_escalated, satisfaction_score,
        handler_id, tags_json
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", tickets)
    del tickets

    log("检查关联")
    verify(con, n)
    log("导出 Excel")
    export_excel(con, xlsx_path)
    con.close()
    log(f"完成：{db_path}")
    log(f"完成：{xlsx_path}")


if __name__ == "__main__":
    main()