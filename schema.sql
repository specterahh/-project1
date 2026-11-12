-- telecom_ops / 云栖移动运营库
-- 只有表结构，没有业务数据。
-- 时间列都是 TEXT，格式 YYYY-MM-DD HH:MM:SS，由 datetime 生成后再 strftime。
-- 外键是逻辑约束。造「引用不存在」这类脏数据前，先 PRAGMA foreign_keys=OFF。

PRAGMA foreign_keys = ON;

CREATE TABLE customers (
  customer_id          INTEGER PRIMARY KEY,
  customer_no          TEXT    NOT NULL UNIQUE,
  full_name            TEXT    NOT NULL,
  id_card_no           TEXT,
  gender               TEXT    NOT NULL,
  birth_date           TEXT,
  phone_no             TEXT    NOT NULL,
  email                TEXT,
  city_code            TEXT    NOT NULL,
  city_name            TEXT    NOT NULL,
  district_name        TEXT,
  address              TEXT,
  customer_level       TEXT    NOT NULL,
  status               TEXT    NOT NULL,
  referrer_customer_id INTEGER,
  register_time        TEXT    NOT NULL,
  cancel_time          TEXT,
  credit_score         INTEGER,
  profile_json         TEXT,
  is_test_user         INTEGER NOT NULL DEFAULT 0,
  updated_at           TEXT    NOT NULL,
  FOREIGN KEY (referrer_customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX idx_customers_phone    ON customers(phone_no);
CREATE INDEX idx_customers_city     ON customers(city_code, status);
CREATE INDEX idx_customers_level    ON customers(customer_level, register_time);
CREATE INDEX idx_customers_referrer ON customers(referrer_customer_id);

CREATE TABLE plans (
  plan_id            INTEGER PRIMARY KEY,
  plan_code          TEXT    NOT NULL UNIQUE,
  plan_name          TEXT    NOT NULL,
  plan_type          TEXT    NOT NULL,
  monthly_fee        REAL    NOT NULL,
  voice_minutes      INTEGER NOT NULL,
  data_mb            INTEGER NOT NULL,
  sms_count          INTEGER NOT NULL,
  overage_voice_fee  REAL    NOT NULL,
  overage_data_fee   REAL    NOT NULL,
  contract_months    INTEGER NOT NULL,
  effective_from     TEXT    NOT NULL,
  effective_to       TEXT,
  status             TEXT    NOT NULL,
  target_segment     TEXT    NOT NULL,
  region_limit       TEXT,
  benefit_json       TEXT,
  offline_reason     TEXT,
  created_at         TEXT    NOT NULL
);

CREATE INDEX idx_plans_type    ON plans(plan_type, status);
CREATE INDEX idx_plans_fee     ON plans(monthly_fee);
CREATE INDEX idx_plans_segment ON plans(target_segment, region_limit);

CREATE TABLE subscriptions (
  subscription_id      INTEGER PRIMARY KEY,
  customer_id          INTEGER NOT NULL,
  plan_id              INTEGER NOT NULL,
  msisdn               TEXT    NOT NULL,
  iccid                TEXT,
  imsi                 TEXT,
  start_time           TEXT    NOT NULL,
  end_time             TEXT,
  contract_end_time    TEXT,
  channel_code         TEXT    NOT NULL,
  agent_id             TEXT,
  city_code            TEXT    NOT NULL,
  city_name            TEXT    NOT NULL,
  monthly_fee_snapshot REAL    NOT NULL,
  discount_rate        REAL,
  status               TEXT    NOT NULL,
  auto_renew           INTEGER NOT NULL DEFAULT 1,
  promo_code           TEXT,
  extra_json           TEXT,
  created_at           TEXT    NOT NULL,
  updated_at           TEXT    NOT NULL,
  UNIQUE (customer_id, plan_id, start_time),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (plan_id)     REFERENCES plans(plan_id)
);

CREATE INDEX idx_sub_customer ON subscriptions(customer_id, status);
CREATE INDEX idx_sub_plan     ON subscriptions(plan_id);
CREATE INDEX idx_sub_msisdn   ON subscriptions(msisdn);
CREATE INDEX idx_sub_city     ON subscriptions(city_code, start_time);

CREATE TABLE usage_records (
  usage_id        INTEGER PRIMARY KEY,
  subscription_id INTEGER NOT NULL,
  customer_id     INTEGER NOT NULL,
  caller_msisdn   TEXT    NOT NULL,
  usage_time      TEXT    NOT NULL,
  usage_month     TEXT    NOT NULL,
  usage_type      TEXT    NOT NULL,
  direction       TEXT    NOT NULL,
  peer_number     TEXT,
  duration_sec    INTEGER,
  data_kb         INTEGER,
  sms_cnt         INTEGER,
  charge_amount   REAL,
  is_roaming      INTEGER NOT NULL DEFAULT 0,
  roam_city       TEXT,
  cell_id         TEXT,
  network_type    TEXT    NOT NULL,
  rating_status   TEXT    NOT NULL,
  raw_json        TEXT,
  created_at      TEXT    NOT NULL,
  FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
  FOREIGN KEY (customer_id)     REFERENCES customers(customer_id)
);

CREATE INDEX idx_usage_month    ON usage_records(usage_month, usage_type);
CREATE INDEX idx_usage_time     ON usage_records(usage_time);
CREATE INDEX idx_usage_customer ON usage_records(customer_id, usage_month);
CREATE INDEX idx_usage_caller   ON usage_records(caller_msisdn);
CREATE INDEX idx_usage_peer     ON usage_records(peer_number);
CREATE INDEX idx_usage_sub      ON usage_records(subscription_id, usage_time);

CREATE TABLE bills (
  bill_id          INTEGER PRIMARY KEY,
  bill_no          TEXT    NOT NULL UNIQUE,
  customer_id      INTEGER NOT NULL,
  subscription_id  INTEGER NOT NULL,
  bill_month       TEXT    NOT NULL,
  plan_fee         REAL    NOT NULL,
  voice_fee        REAL    NOT NULL,
  data_fee         REAL    NOT NULL,
  sms_fee          REAL    NOT NULL,
  value_added_fee  REAL    NOT NULL,
  discount_amount  REAL    NOT NULL,
  adjust_amount    REAL    NOT NULL,
  total_amount     REAL    NOT NULL,
  paid_amount      REAL    NOT NULL,
  unpaid_amount    REAL    NOT NULL,
  bill_status      TEXT    NOT NULL,
  issue_time       TEXT    NOT NULL,
  due_time         TEXT    NOT NULL,
  pay_time         TEXT,
  pay_channel      TEXT,
  invoice_no       TEXT,
  city_code        TEXT    NOT NULL,
  remark           TEXT,
  fee_detail_json  TEXT,
  UNIQUE (customer_id, subscription_id, bill_month),
  FOREIGN KEY (customer_id)     REFERENCES customers(customer_id),
  FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

CREATE INDEX idx_bills_month  ON bills(bill_month, bill_status);
CREATE INDEX idx_bills_city   ON bills(city_code, bill_month);
CREATE INDEX idx_bills_unpaid ON bills(unpaid_amount, due_time);
CREATE INDEX idx_bills_sub    ON bills(subscription_id);

CREATE TABLE tickets (
  ticket_id            INTEGER PRIMARY KEY,
  ticket_no            TEXT    NOT NULL UNIQUE,
  customer_id          INTEGER NOT NULL,
  subscription_id      INTEGER,
  parent_ticket_id     INTEGER,
  related_bill_id      INTEGER,
  category             TEXT    NOT NULL,
  sub_category         TEXT    NOT NULL,
  priority             TEXT    NOT NULL,
  status               TEXT    NOT NULL,
  channel              TEXT    NOT NULL,
  title                TEXT    NOT NULL,
  description          TEXT,
  city_code            TEXT    NOT NULL,
  city_name            TEXT    NOT NULL,
  created_time         TEXT    NOT NULL,
  first_response_time  TEXT,
  closed_time          TEXT,
  sla_hours            INTEGER NOT NULL,
  is_escalated         INTEGER NOT NULL DEFAULT 0,
  satisfaction_score   INTEGER,
  handler_id           TEXT,
  tags_json            TEXT,
  FOREIGN KEY (customer_id)      REFERENCES customers(customer_id),
  FOREIGN KEY (subscription_id)  REFERENCES subscriptions(subscription_id),
  FOREIGN KEY (parent_ticket_id) REFERENCES tickets(ticket_id),
  FOREIGN KEY (related_bill_id)  REFERENCES bills(bill_id)
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id, status);
CREATE INDEX idx_tickets_parent   ON tickets(parent_ticket_id);
CREATE INDEX idx_tickets_created  ON tickets(created_time);
CREATE INDEX idx_tickets_cat      ON tickets(category, sub_category, priority);
CREATE INDEX idx_tickets_city     ON tickets(city_code, created_time);
