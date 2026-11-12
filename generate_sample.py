"""每张表 100 行样本。关联不断，时间用 datetime 生成再 strftime。"""

import json
import random
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
N = 100
START = datetime(2020, 1, 1, 0, 0, 0)
END = datetime(2025, 11, 30, 23, 59, 59)
ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schema.sql"
OUT = ROOT / "telecom_ops.db"

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


def stamp(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def day(dt):
    return dt.strftime("%Y-%m-%d")


def month(dt):
    return dt.strftime("%Y-%m")


def rand_dt(rng, start, end):
    if end <= start:
        return start
    seconds = rng.randint(0, int((end - start).total_seconds()))
    return start + timedelta(seconds=seconds)


def phone(rng):
    prefix = rng.choice(["130", "131", "135", "136", "137", "138", "139", "150", "151", "158", "159", "186", "187", "188", "198"])
    return prefix + "".join(str(rng.randint(0, 9)) for _ in range(8))


def id_card(rng, birth):
    area = rng.choice(CITIES)[0] + f"{rng.randint(0, 99):02d}"
    birth_s = birth.strftime("%Y%m%d") if birth else f"{rng.randint(1970, 2002)}{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}"
    seq = f"{rng.randint(0, 999):03d}"
    body = area + birth_s + seq
    return body + rng.choice("0123456789X")


def main():
    rng = random.Random(SEED)
    tmp = Path("/tmp/telecom_ops.db")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA.read_text())
    con.execute("PRAGMA foreign_keys = ON")

    customers = []
    phones = []
    cards = []
    for i in range(1, N + 1):
        city_code, city_name = CITIES[(i - 1) % len(CITIES)]
        birth = None if i % 17 == 0 else datetime(rng.randint(1960, 2004), rng.randint(1, 12), rng.randint(1, 28))
        status = rng.choices(CUST_STATUS, weights=[70, 10, 12, 8])[0]
        register = rand_dt(rng, START, END - timedelta(days=30))
        cancel = None
        if status == "销户":
            cancel = rand_dt(rng, register, END)
        level = rng.choices(LEVELS, weights=[55, 25, 15, 5])[0]
        p = phone(rng)
        card = None if i % 11 == 0 else id_card(rng, birth)
        email = None if i % 7 == 0 else f"user{i:03d}@example.com"
        score = rng.randint(320, 860)
        if i in (5, 6):
            score = -rng.randint(1, 40)
        elif i in (7, 8):
            score = rng.randint(1001, 1500)
        elif i % 19 == 0:
            score = None
        referrer = None if i <= 15 else rng.randint(1, i - 1)
        if i % 13 == 0:
            profile = "{bad-json"
        else:
            profile = json.dumps(
                {"terminal": rng.choice(["4G", "5G"]), "elder_plan_interest": level == "老人" or rng.random() < 0.1, "tags": [rng.choice(["视频", "游戏", "上网课", "商务"])]},
                ensure_ascii=False,
            )
        row = (
            i, f"YQ{register.year}{i:06d}", rng.choice(SURNAMES) + rng.choice(GIVEN),
            card, rng.choices(["男", "女", "未知"], weights=[48, 48, 4])[0],
            day(birth) if birth else None, p, email, city_code, city_name,
            rng.choice(DISTRICTS[city_name]), f"{city_name}{rng.choice(DISTRICTS[city_name])}示例路{rng.randint(1, 200)}号",
            level, status, referrer, stamp(register), stamp(cancel) if cancel else None,
            score, profile, 1 if i in (99, 100) else 0, stamp(rand_dt(rng, register, END)),
        )
        customers.append(row)
        phones.append(p)
        cards.append(card)
    # 重复手机号、重复证件
    customers[97] = customers[97][:6] + (phones[0],) + customers[97][7:]
    customers[98] = customers[98][:6] + (phones[1],) + customers[98][7:]
    customers[99] = customers[99][:6] + (phones[2],) + customers[99][7:]
    if cards[3]:
        customers[96] = customers[96][:3] + (cards[3],) + customers[96][4:]
    # 两名销户客户没有退网时间
    closed = [c for c in customers if c[13] == "销户"]
    for c in closed[:2]:
        idx = c[0] - 1
        customers[idx] = customers[idx][:16] + (None,) + customers[idx][17:]
    con.executemany(
        """INSERT INTO customers (
            customer_id, customer_no, full_name, id_card_no, gender, birth_date, phone_no, email,
            city_code, city_name, district_name, address, customer_level, status, referrer_customer_id,
            register_time, cancel_time, credit_score, profile_json, is_test_user, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        customers,
    )

    plans = []
    for i in range(1, N + 1):
        ptype = PLAN_TYPES[(i - 1) % len(PLAN_TYPES)]
        segment = SEGMENTS[(i * 3) % len(SEGMENTS)]
        fee = FEES[(i - 1) % len(FEES)]
        opened = rand_dt(rng, START, datetime(2024, 6, 1))
        status = "停售" if i % 6 == 0 else "在售"
        closed_at = rand_dt(rng, opened, END) if status == "停售" else None
        if i in (12, 18) and closed_at and closed_at > opened:
            closed_at = opened - timedelta(days=10)
        region = None if i % 4 != 0 else CITIES[i % len(CITIES)][0]
        benefit = "{bad" if i % 29 == 0 else json.dumps(
            {"sub_cards": rng.randint(0, 3), "broadband_mbps": rng.choice([0, 100, 300, 500, 1000]), "member": rng.choice(["无", "视频会员", "音乐会员"])},
            ensure_ascii=False,
        )
        plans.append((
            i, f"P{ptype[:1]}{i:04d}", f"{segment}{ptype}{fee}元套餐{i}", ptype, float(fee),
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
    con.executemany(
        """INSERT INTO plans (
            plan_id, plan_code, plan_name, plan_type, monthly_fee, voice_minutes, data_mb, sms_count,
            overage_voice_fee, overage_data_fee, contract_months, effective_from, effective_to, status,
            target_segment, region_limit, benefit_json, offline_reason, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        plans,
    )

    # 70 个客户 1 张卡，15 个客户 2 张卡，共 100 条订购
    pairs = [(i, 1) for i in range(1, 71)] + [(i, k) for i in range(71, 86) for k in (1, 2)]
    subscriptions = []
    for sid, (cid, nth) in enumerate(pairs, start=1):
        cust = customers[cid - 1]
        plan = plans[(sid * 3 + nth) % N]
        register = datetime.strptime(cust[15], "%Y-%m-%d %H:%M:%S")
        plan_from = datetime.strptime(plan[11], "%Y-%m-%d %H:%M:%S")
        begin = max(register, plan_from, START)
        if begin >= END:
            begin = START
        start_time = rand_dt(rng, begin, END - timedelta(days=1))
        status = rng.choices(SUB_STATUS, weights=[60, 8, 12, 20])[0]
        end_time = None
        if status == "已退订":
            end_time = rand_dt(rng, start_time, END)
        if sid in (3, 4) :
            end_time = start_time - timedelta(days=3)
            status = "已退订"
        contract_months = plan[10]
        contract_end = start_time + timedelta(days=30 * contract_months) if contract_months else None
        channel = rng.choice(CHANNELS)
        agent = None if channel in ("APP", "网厅") and rng.random() < 0.8 else f"AG{rng.randint(1000, 9999)}"
        rate = round(rng.choice([1, 0.95, 0.9, 0.8, 0.7]), 2)
        if sid in (5, 6):
            rate = None
        elif sid == 7:
            rate = 1.4
        elif sid == 8:
            rate = -0.2
        msisdn = cust[6] if nth == 1 else phone(rng)
        extra = "{bad" if sid % 31 == 0 else json.dumps({"nth_card": nth, "device_contract": rng.random() < 0.3}, ensure_ascii=False)
        subscriptions.append((
            sid, cid, plan[0], msisdn, "8986" + f"{rng.randint(0, 10**15 - 1):015d}",
            "460" + f"{rng.randint(0, 10**12 - 1):012d}",
            stamp(start_time), stamp(end_time) if end_time else None,
            stamp(contract_end) if contract_end else None,
            channel, agent, cust[8], cust[9], float(plan[4]), rate, status,
            0 if status == "已退订" else 1, None if rng.random() < 0.7 else f"PROMO{rng.randint(10, 99)}",
            extra, stamp(start_time), stamp(rand_dt(rng, start_time, END)),
        ))
    con.executemany(
        """INSERT INTO subscriptions (
            subscription_id, customer_id, plan_id, msisdn, iccid, imsi, start_time, end_time,
            contract_end_time, channel_code, agent_id, city_code, city_name, monthly_fee_snapshot,
            discount_rate, status, auto_renew, promo_code, extra_json, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        subscriptions,
    )

    usages = []
    for uid in range(1, N + 1):
        sub = subscriptions[(uid * 5) % N]
        start_time = datetime.strptime(sub[6], "%Y-%m-%d %H:%M:%S")
        end_limit = datetime.strptime(sub[7], "%Y-%m-%d %H:%M:%S") if sub[7] and sub[7] > sub[6] else END
        when = rand_dt(rng, max(start_time, START), min(end_limit, END))
        utype = USAGE_TYPES[(uid - 1) % len(USAGE_TYPES)]
        direction = rng.choice(DIRECTIONS[utype])
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
        if uid in (1, 2, 3):
            charge = round(-rng.random() * 5, 2)
            rating = "已批价"
        roaming = 1 if uid % 9 == 0 else 0
        peer = None if utype == "流量" and uid % 2 == 0 else phones[(uid + 3) % N]
        raw = "not-json" if uid % 23 == 0 else json.dumps({"cell_hint": f"HZ-{uid % 50:02d}", "seq": uid}, ensure_ascii=False)
        usages.append((
            uid, sub[0], sub[1], sub[3], stamp(when), month(when), utype, direction, peer,
            duration, data_kb, sms_cnt, charge, roaming,
            rng.choice(["上海", "南京", "北京"]) if roaming else None,
            f"CELL{rng.randint(10000, 99999)}", rng.choices(NETWORKS, weights=[5, 25, 60, 10])[0],
            rating, raw, stamp(min(END, when + timedelta(minutes=rng.randint(1, 120)))),
        ))
    con.executemany(
        """INSERT INTO usage_records (
            usage_id, subscription_id, customer_id, caller_msisdn, usage_time, usage_month,
            usage_type, direction, peer_number, duration_sec, data_kb, sms_cnt, charge_amount,
            is_roaming, roam_city, cell_id, network_type, rating_status, raw_json, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        usages,
    )

    bills = []
    for bid in range(1, N + 1):
        sub = subscriptions[bid - 1]
        start_time = datetime.strptime(sub[6], "%Y-%m-%d %H:%M:%S")
        bill_month_dt = datetime(start_time.year, start_time.month, 1)
        if bill_month_dt < START:
            bill_month_dt = START
        issue = min(END, bill_month_dt + timedelta(days=rng.randint(1, 5), hours=8))
        due = min(END, issue + timedelta(days=15))
        plan_fee = round(sub[13], 2)
        voice_fee = round(rng.random() * 20, 2)
        data_fee = round(rng.random() * 30, 2)
        sms_fee = round(rng.random() * 5, 2)
        value_added = round(rng.choice([0, 0, 5, 6, 10, 15]), 2)
        discount = round(rng.choice([0, 0, 5, 10, 20]), 2)
        adjust = round(rng.choice([0, 0, 0, -5, -10, 3]), 2)
        total = round(plan_fee + voice_fee + data_fee + sms_fee + value_added - discount + adjust, 2)
        if bid in (9, 10, 11, 12):
            total = round(total + rng.choice([-15, 8, 21, -3]), 2)
        status = rng.choices(BILL_STATUS, weights=[5, 15, 15, 60, 5])[0]
        if status == "已结清":
            paid = total
        elif status == "部分支付":
            paid = round(total * rng.uniform(0.2, 0.8), 2) if total > 0 else 0
        elif status == "坏账":
            paid = 0
        else:
            paid = 0
        if bid == 13:
            paid = round(total + 12, 2)
        unpaid = round(total - paid, 2)
        if bid in (14, 15):
            unpaid = round(unpaid + 7, 2)
        pay_time = None
        pay_channel = None
        if status in ("已结清", "部分支付") and not (status == "已结清" and bid in (16, 17)):
            pay_time = stamp(rand_dt(rng, issue, END))
            pay_channel = rng.choice(PAY_CHANNELS)
        detail = "[1,2," if bid % 27 == 0 else json.dumps({"idd": 0, "ringtone": value_added}, ensure_ascii=False)
        remark = None if rng.random() < 0.8 else rng.choice(["客户来电核对", "调账", "投诉后退费"])
        bills.append((
            bid, f"B{bill_month_dt.strftime('%Y%m')}{bid:06d}", sub[1], sub[0], month(bill_month_dt),
            plan_fee, voice_fee, data_fee, sms_fee, value_added, discount, adjust, total, round(paid, 2), unpaid,
            status, stamp(issue), stamp(due), pay_time, pay_channel,
            None if rng.random() < 0.6 else f"INV{bid:08d}", sub[11], remark, detail,
        ))
    con.executemany(
        """INSERT INTO bills (
            bill_id, bill_no, customer_id, subscription_id, bill_month, plan_fee, voice_fee, data_fee,
            sms_fee, value_added_fee, discount_amount, adjust_amount, total_amount, paid_amount,
            unpaid_amount, bill_status, issue_time, due_time, pay_time, pay_channel, invoice_no,
            city_code, remark, fee_detail_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        bills,
    )

    bill_by_sub = {b[3]: b[0] for b in bills}
    subs_by_customer = {}
    for s in subscriptions:
        subs_by_customer.setdefault(s[1], []).append(s[0])
    tickets = []
    for tid in range(1, N + 1):
        cid = rng.randint(1, N)
        cust = customers[cid - 1]
        sub_id = None
        if cid in subs_by_customer and rng.random() < 0.75:
            sub_id = rng.choice(subs_by_customer[cid])
        related = bill_by_sub.get(sub_id) if sub_id and rng.random() < 0.5 else None
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
        if status == "已关闭" and tid in (20, 21):
            closed = None
        score = None if status != "已关闭" or rng.random() < 0.2 else rng.randint(1, 5)
        if tid in (22, 23):
            score = 0
        elif tid in (24, 25):
            score = 9
        tags = "not-json" if tid % 28 == 0 else json.dumps(rng.sample(["重复投诉", "携号转网", "老人", "升级"], rng.randint(0, 2)), ensure_ascii=False)
        parent = None
        tickets.append((
            tid, f"T{created.strftime('%Y%m%d')}{tid:05d}", cid, sub_id, parent, related,
            cat, subcat, rng.choices(PRIORITIES, weights=[30, 40, 20, 10])[0], status,
            rng.choice(TICKET_CHANNELS), f"{subcat}问题{tid}", f"客户反映{city_name if False else cust[9]}{subcat}",
            cust[8], cust[9], stamp(created), stamp(first) if first else None, stamp(closed) if closed else None,
            sla, 1 if tid % 8 == 0 else 0, score, f"HK{rng.randint(100, 999)}", tags,
        ))
    con.executemany(
        """INSERT INTO tickets (
            ticket_id, ticket_no, customer_id, subscription_id, parent_ticket_id, related_bill_id,
            category, sub_category, priority, status, channel, title, description, city_code, city_name,
            created_time, first_response_time, closed_time, sla_hours, is_escalated, satisfaction_score,
            handler_id, tags_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        tickets,
    )
    # 约 20 张子单指向更早的工单
    for tid in range(21, 41):
        con.execute("UPDATE tickets SET parent_ticket_id = ? WHERE ticket_id = ?", (tid - 20, tid))

    con.commit()
    fk = list(con.execute("PRAGMA foreign_key_check"))
    if fk:
        raise SystemExit(f"foreign key check failed: {fk[:10]}")
    counts = {
        name: con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in ("customers", "plans", "subscriptions", "usage_records", "bills", "tickets")
    }
    mismatch = con.execute(
        """SELECT
            (SELECT COUNT(*) FROM usage_records u JOIN subscriptions s ON u.subscription_id = s.subscription_id WHERE u.customer_id != s.customer_id),
            (SELECT COUNT(*) FROM bills b JOIN subscriptions s ON b.subscription_id = s.subscription_id WHERE b.customer_id != s.customer_id),
            (SELECT COUNT(*) FROM usage_records WHERE substr(usage_time, 1, 7) != usage_month),
            (SELECT COUNT(*) FROM tickets t JOIN subscriptions s ON t.subscription_id = s.subscription_id WHERE t.customer_id != s.customer_id)
        """
    ).fetchone()
    if counts != {k: N for k in counts} or any(mismatch):
        raise SystemExit(f"bad sample counts={counts} mismatch={mismatch}")
    con.close()
    shutil.copy(tmp, OUT)
    print("wrote", OUT, counts)


if __name__ == "__main__":
    main()
