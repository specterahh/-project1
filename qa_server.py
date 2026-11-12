"""本地打开「电信数据库智能问答系统」。

把本文件和 telecom_ops.db 放在同一个文件夹，然后：

    .\\.venv\\Scripts\\python.exe .\\qa_server.py

浏览器会自己打开。只监听本机，密钥不会写进数据库。
国内网络请选 DeepSeek。Grok 的接口在内地通常连不上。
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "telecom_ops.db"
PORT = 8765
QUERY_TIMEOUT_SECONDS = 3.0

SCHEMA = """
customers(customer_id, customer_no, full_name, id_card_no, gender, birth_date, phone_no, email, city_code, city_name, district_name, address, customer_level, status, referrer_customer_id, register_time, cancel_time, credit_score, profile_json, is_test_user, updated_at)
plans(plan_id, plan_code, plan_name, plan_type, monthly_fee, voice_minutes, data_mb, sms_count, overage_voice_fee, overage_data_fee, contract_months, effective_from, effective_to, status, target_segment, region_limit, benefit_json, offline_reason, created_at)
subscriptions(subscription_id, customer_id, plan_id, msisdn, iccid, imsi, start_time, end_time, contract_end_time, channel_code, agent_id, city_code, city_name, monthly_fee_snapshot, discount_rate, status, auto_renew, promo_code, extra_json, created_at, updated_at)
usage_records(usage_id, subscription_id, customer_id, caller_msisdn, usage_time, usage_month, usage_type, direction, peer_number, duration_sec, data_kb, sms_cnt, charge_amount, is_roaming, roam_city, cell_id, network_type, rating_status, raw_json, created_at)
bills(bill_id, bill_no, customer_id, subscription_id, bill_month, plan_fee, voice_fee, data_fee, sms_fee, value_added_fee, discount_amount, adjust_amount, total_amount, paid_amount, unpaid_amount, bill_status, issue_time, due_time, pay_time, pay_channel, invoice_no, city_code, remark, fee_detail_json)
tickets(ticket_id, ticket_no, customer_id, subscription_id, parent_ticket_id, related_bill_id, category, sub_category, priority, status, channel, title, description, city_code, city_name, created_time, first_response_time, closed_time, sla_hours, is_escalated, satisfaction_score, handler_id, tags_json)
""".strip()

ALLOWED_COLUMNS = {}
for _line in SCHEMA.splitlines():
    _name, _cols = _line.split("(", 1)
    ALLOWED_COLUMNS[_name.strip()] = {col.strip() for col in _cols.rstrip(")").split(",")}

ALLOWED_FUNCTIONS = {
    "count", "sum", "avg", "max", "min", "total", "group_concat",
    "substr", "substring", "datetime", "date", "time", "strftime", "julianday",
    "length", "lower", "upper", "trim", "ltrim", "rtrim",
    "abs", "round", "coalesce", "nullif", "ifnull", "iif", "typeof",
    "printf", "replace", "instr", "cast",
}

SYSTEM = (
    "你是 SQLite 助手。只输出一条 SQL，不要解释，不要 Markdown。"
    "必须以 SELECT 开头。只能使用一张表，允许这张表自己连接自己。"
    "禁止 WITH、窗口函数、INSERT、UPDATE、DELETE。"
    "时间列是文本 YYYY-MM-DD HH:MM:SS，按月用 substr(列,1,7)。"
    "客户 status 只能是：在网、停机、销户、欠费停机。问在网必须写 status = '在网'。"
    "账单 bill_status：未出账、已出账、部分支付、已结清、坏账。"
    "投诉 priority：低、中、高、紧急。话费负数看 usage_records.charge_amount < 0。"
    "结果列用中文别名，别名加双引号。"
    f"表结构：\n{SCHEMA}"
)

PROVIDERS = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    },
    "grok": {
        "url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-4.5",
    },
}

BANNED = (
    " WITH ",
    " OVER ",
    " ROW_NUMBER",
    " RANK(",
    " LAG(",
    " LEAD(",
    " INSERT ",
    " UPDATE ",
    " DELETE ",
    " DROP ",
    " ALTER ",
    " ATTACH ",
    " DETACH ",
    " PRAGMA ",
    " VACUUM ",
    " REPLACE ",
)


def validate_sql(raw: str) -> dict:
    sql = raw.strip()
    sql = re.sub(r"^```(?:sql)?", "", sql, flags=re.I).strip()
    sql = re.sub(r"```$", "", sql).strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()
    if not sql:
        return {"ok": False, "error": "没有得到 SQL"}
    if len(sql) > 2500:
        return {"ok": False, "error": "SQL 太长了"}
    if ";" in sql:
        return {"ok": False, "error": "只接受一条语句"}
    if not re.match(r"select\b", sql, re.I):
        return {"ok": False, "error": "只能是 SELECT，不能改数据"}
    upper = " " + re.sub(r"\s+", " ", sql).upper() + " "
    for word in BANNED:
        if word in upper:
            return {"ok": False, "error": "用了不允许的写法。不要跨表，不要窗口函数，不要 WITH"}
    found = {name.lower() for name in re.findall(
        r"\b(customers|plans|subscriptions|usage_records|bills|tickets)\b", sql, re.I
    )}
    if not found:
        return {"ok": False, "error": "没有识别到库里的表"}
    if len(found) > 1:
        return {"ok": False, "error": "不能把两张不同的表连在一起。请改成只问一张表"}
    return {"ok": True, "sql": sql, "table": next(iter(found))}


def clause(sql: str, start: str, stops: list[str]) -> str | None:
    compact = re.sub(r"\s+", " ", sql)
    match = re.search(
        rf"\b{start}\b(.+?)(?=\b(?:{'|'.join(stops)})\b|$)",
        compact,
        re.I,
    )
    return match.group(1).strip() if match else None


def describe(sql: str, table: str) -> dict:
    labels = []
    for name, label in (("COUNT", "计数"), ("SUM", "求和"), ("AVG", "平均"), ("MAX", "最大"), ("MIN", "最小")):
        if re.search(rf"\b{name}\s*\(", sql, re.I):
            labels.append(label)
    if re.search(r"\bgroup\s+by\b", sql, re.I):
        labels.append("分组")
    where = clause(sql, "where", ["group", "order", "limit"])
    order = clause(sql, "order", ["limit"])
    limit = re.search(r"\blimit\s+(\d+)", sql, re.I)
    sort = "未排序"
    if order:
        sort = order
    if limit:
        tail = f"只要前 {limit.group(1)} 条"
        sort = tail if sort == "未排序" else f"{sort}，{tail}"
    return {
        "source": f"telecom_ops.db · {table}",
        "stats": "、".join(labels) if labels else "逐行列出，未做聚合",
        "filter": where or "未筛选",
        "sort": sort,
    }


def authorizer(action, arg1, arg2, _dbname, _source):
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        columns = ALLOWED_COLUMNS.get((arg1 or "").lower())
        if columns is not None and (arg2 or "").lower() in columns:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        if (arg2 or "").lower() in ALLOWED_FUNCTIONS:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_DENY


def open_db():
    conn = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.set_authorizer(authorizer)
    return conn


def run_select(sql: str) -> dict:
    """生成 SQL 和历史记录重查都只走这里。"""
    checked = validate_sql(sql)
    if not checked["ok"]:
        return checked
    if not DB_PATH.is_file():
        return {"ok": False, "error": "同一文件夹里没有 telecom_ops.db", "sql": checked["sql"]}
    wrapped = f"SELECT * FROM ({checked['sql']}) AS q LIMIT 200"
    started = time.monotonic()

    def progress():
        if time.monotonic() - started > QUERY_TIMEOUT_SECONDS:
            return 1
        return 0

    try:
        conn = open_db()
        conn.set_progress_handler(progress, 10000)
        try:
            cur = conn.execute(wrapped)
            columns = [item[0] for item in cur.description]
            rows = []
            for row in cur.fetchall():
                cells = []
                for name in columns:
                    value = row[name]
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    cells.append(value)
                rows.append(cells)
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        text = str(exc).lower()
        if "not authorized" in text or "prohibited" in text:
            return {"ok": False, "error": "这条语句读到了不允许的表或列，或者试图改数据", "sql": checked["sql"]}
        if "interrupt" in text:
            return {"ok": False, "error": "查询超过 3 秒，已中止", "sql": checked["sql"]}
        return {"ok": False, "error": f"SQL 没能执行：{exc}", "sql": checked["sql"]}
    return {
        "ok": True,
        "sql": checked["sql"],
        "columns": columns,
        "rows": rows,
        "truncated": len(rows) == 200,
        "provenance": describe(checked["sql"], checked["table"]),
    }


def ask_model(question: str, provider: str, api_key: str, model: str) -> dict:
    spec = PROVIDERS.get(provider)
    if spec is None:
        return {"ok": False, "error": "不认识这个接口"}
    if not api_key.strip():
        return {"ok": False, "error": "先填接口密钥。国内用 DeepSeek。"}
    chosen = model.strip() or spec["model"]
    body = json.dumps(
        {
            "model": chosen,
            "temperature": 0,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question},
            ],
        }
    ).encode()
    request = Request(
        spec["url"],
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key.strip()}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:180]
        return {"ok": False, "error": f"模型没有返回，状态 {exc.code}。{detail}"}
    except URLError as exc:
        hint = "国内直连 Grok 通常会被墙，改用 DeepSeek。" if provider == "grok" else "网络没有连上接口。"
        return {"ok": False, "error": f"{hint} {exc.reason}"}
    text = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not text:
        return {"ok": False, "error": "模型没有给出 SQL"}
    result = run_select(text)
    return result


PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>电信数据库智能问答</title>
<style>
  :root { color-scheme: light; --bg:#eef3ef; --surface:#fffcf8; --ink:#1a2420; --muted:#5e6d64; --primary:#0e6a4c; --on:#f4fbf7; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 "Source Sans 3","PingFang SC","Noto Sans SC",sans-serif; }
  main { max-width:1100px; margin:0 auto; padding:24px 16px 40px; }
  h1 { font-family:Georgia,"Songti SC",serif; font-size:32px; line-height:1.2; margin:0; font-weight:560; }
  .sub { color:var(--muted); margin:8px 0 16px; }
  .grid { display:grid; gap:16px; }
  @media (min-width:960px) { .grid { grid-template-columns:1fr 1fr; } }
  article { background:var(--surface); border:1px solid rgba(26,36,32,.1); border-radius:16px; padding:20px; min-width:0; }
  h2 { font-size:18px; margin:0 0 12px; }
  textarea, input, select { width:100%; border:1px solid rgba(26,36,32,.15); background:var(--bg); border-radius:12px; padding:10px 12px; color:inherit; font:inherit; }
  textarea { resize:none; }
  .row { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
  button { min-height:44px; border:0; border-radius:12px; background:transparent; color:var(--ink); font:inherit; cursor:pointer; }
  button.primary { background:var(--primary); color:var(--on); padding:0 18px; font-weight:650; }
  button.chip { background:rgba(14,106,76,.1); color:var(--primary); border-radius:999px; padding:0 12px; font-size:14px; }
  button.link { color:var(--primary); padding:0 8px; }
  button:disabled { opacity:.45; cursor:default; }
  .sql { background:var(--bg); color:var(--muted); border-radius:8px; padding:8px 12px; overflow:auto; font-family:ui-monospace,monospace; font-size:14px; }
  .table-wrap { max-height:320px; overflow:auto; }
  table { border-collapse:collapse; width:100%; font-size:14px; }
  th, td { border-bottom:1px solid rgba(26,36,32,.1); padding:8px; text-align:left; white-space:nowrap; }
  th { position:sticky; top:0; background:var(--surface); }
  tr:nth-child(odd) td { background:rgba(238,243,239,.6); }
  .muted { color:var(--muted); }
  .ok { color:var(--primary); font-size:14px; }
  .bad { font-weight:650; font-size:14px; }
  li { list-style:none; border:1px solid rgba(26,36,32,.1); border-radius:12px; padding:12px; margin:0 0 8px; }
  ul { margin:0; padding:0; max-height:320px; overflow:auto; }
  dt { color:var(--muted); font-size:14px; }
  dd { margin:4px 0 12px; overflow-wrap:anywhere; }
  label { display:block; font-size:14px; color:var(--muted); margin:8px 0 4px; }
</style>
</head>
<body>
<main>
  <h1>电信数据库智能问答系统</h1>
  <p class="sub">用自然语言提问，自动生成 SQL 并返回结果</p>
  <div class="grid">
    <article>
      <h2>提问</h2>
      <label for="provider">接口</label>
      <select id="provider">
        <option value="deepseek">DeepSeek（国内直连）</option>
        <option value="grok">Grok（内地通常需要代理）</option>
      </select>
      <label for="model">模型名，留空就用默认</label>
      <input id="model" placeholder="deepseek-chat">
      <label for="key">接口密钥，只在当前这次打开时有效</label>
      <input id="key" type="password" placeholder="粘贴密钥" autocomplete="off">
      <label for="question">问题</label>
      <textarea id="question" rows="5" placeholder="例如：杭州还有多少在网的人"></textarea>
      <div class="row" id="chips"></div>
      <div class="row"><button class="primary" id="go" type="button">生成 SQL</button></div>
    </article>
    <article>
      <h2>查询结果</h2>
      <div id="result"><p class="muted">输入问题后将在此处显示结果</p></div>
    </article>
    <article>
      <h2>问答记录</h2>
      <div id="history"><p class="muted">还没有记录。问过的问题会留在这里。</p></div>
    </article>
    <article>
      <h2>数据溯源</h2>
      <div id="prov"><p class="muted">生成成功后，这里会说明数据从哪来、怎么统计的。</p></div>
    </article>
  </div>
</main>
<script>
const EXAMPLES = ["杭州还有多少在网的人","各地市坏账有几笔","话费记成负数的话单","推荐超过5个人的推荐人"];
const HISTORY_KEY = "telecom_ops_qa_history";
const chips = document.getElementById("chips");
const question = document.getElementById("question");
const go = document.getElementById("go");
let history = [];
let active = null;
try { history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch (e) { history = []; }
localStorage.removeItem("telecom_ops_qa_key");
document.getElementById("provider").value = localStorage.getItem("telecom_ops_qa_provider") || "deepseek";
document.getElementById("model").value = localStorage.getItem("telecom_ops_qa_model") || "";
document.getElementById("key").value = sessionStorage.getItem("telecom_ops_qa_key") || "";
EXAMPLES.forEach((text) => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "chip";
  button.textContent = text;
  button.onclick = () => { question.value = text; };
  chips.appendChild(button);
});
function saveSettings() {
  localStorage.setItem("telecom_ops_qa_provider", document.getElementById("provider").value);
  localStorage.setItem("telecom_ops_qa_model", document.getElementById("model").value);
  sessionStorage.setItem("telecom_ops_qa_key", document.getElementById("key").value);
}
function persist() {
  history = history.slice(0, 12);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}
function esc(value) {
  var s = String(value == null ? "" : value);
  s = s.split("&").join("&" + "amp;");
  s = s.split("<").join("&" + "lt;");
  s = s.split(">").join("&" + "gt;");
  s = s.split('"').join("&" + "quot;");
  s = s.split("'").join("&#" + "39;");
  return s;
}
function showResult(item) {
  const box = document.getElementById("result");
  if (!item) { box.innerHTML = '<p class="muted">输入问题后将在此处显示结果</p>'; return; }
  if (!item.ok) { box.textContent = item.error || "没有完成"; return; }
  const head = (item.columns || []).map((name) => `<th>${esc(name)}</th>`).join("");
  const body = (item.rows || []).map((row) => `<tr>${row.map((value) => `<td>${value == null || value === "" ? "—" : esc(value)}</td>`).join("")}</tr>`).join("");
  const table = item.rows && item.rows.length
    ? `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`
    : "<p>没有符合条件的记录</p>";
  const cut = item.truncated ? '<p class="muted">只展示前 200 行</p>' : "";
  box.innerHTML = `<p class="sql"></p>${table}${cut}`;
  box.querySelector(".sql").textContent = item.sql || "";
}
function showProv(item) {
  const box = document.getElementById("prov");
  if (!item || !item.ok || !item.provenance) {
    box.innerHTML = '<p class="muted">生成成功后，这里会说明数据从哪来、怎么统计的。</p>';
    return;
  }
  const lines = [["数据来源", item.provenance.source], ["统计方式", item.provenance.stats], ["筛选条件", item.provenance.filter], ["排序方式", item.provenance.sort]];
  box.innerHTML = `<dl>${lines.map(([k,v]) => `<dt>${k}</dt><dd></dd>`).join("")}</dl>`;
  [...box.querySelectorAll("dd")].forEach((node, i) => { node.textContent = lines[i][1]; });
}
function showHistory() {
  const box = document.getElementById("history");
  if (!history.length) { box.innerHTML = '<p class="muted">还没有记录。问过的问题会留在这里。</p>'; return; }
  box.innerHTML = `<ul>${history.map((item) => `<li data-id="${item.id}">
    <button type="button" class="open" style="display:block;width:100%;text-align:left">
      <span class="muted">${esc(item.at)}</span><span style="display:block">${esc(item.question)}</span>
    </button>
    <div class="row"><span class="${item.ok ? "ok" : "bad"}">${item.ok ? "成功" : "失败"}</span>
    <button type="button" class="link rerun">重新查询</button>
    <button type="button" class="link del">删除</button></div></li>`).join("")}</ul>`;
  box.querySelectorAll("li").forEach((li) => {
    const item = history.find((row) => row.id === li.dataset.id);
    li.querySelector(".open").onclick = () => { active = item; showResult(item); showProv(item); };
    li.querySelector(".rerun").onclick = () => rerun(item);
    li.querySelector(".del").onclick = () => {
      history = history.filter((row) => row.id !== item.id);
      if (active && active.id === item.id) { active = null; showResult(null); showProv(null); }
      persist(); showHistory();
    };
  });
}
async function post(url, payload) {
  const response = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
  return response.json();
}
function stamp() { return new Date().toLocaleString("zh-CN", {hour12:false}); }
async function generate() {
  const text = question.value.trim();
  if (!text || go.disabled) return;
  saveSettings();
  go.disabled = true; go.textContent = "生成中";
  try {
    const result = await post("/api/ask", {
      question: text,
      provider: document.getElementById("provider").value,
      model: document.getElementById("model").value,
      api_key: document.getElementById("key").value
    });
    active = {id: crypto.randomUUID(), at: stamp(), question: text, ...result};
    history = [active, ...history];
    persist(); showResult(active); showProv(active); showHistory();
  } catch (error) {
    active = {id: crypto.randomUUID(), at: stamp(), question: text, ok:false, error:"没有连上本机页面"};
    history = [active, ...history]; persist(); showResult(active); showProv(active); showHistory();
  } finally { go.disabled = false; go.textContent = "生成 SQL"; }
}
async function rerun(item) {
  if (!item || !item.sql) return;
  go.disabled = true;
  try {
    const result = await post("/api/rerun", {sql: item.sql});
    active = {id: crypto.randomUUID(), at: stamp(), question: item.question, ...result};
    history = [active, ...history];
    persist(); showResult(active); showProv(active); showHistory();
  } finally { go.disabled = false; }
}
go.onclick = generate;
showHistory();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 20_000:
            raise ValueError("请求太大")
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode())
        if not isinstance(data, dict):
            raise ValueError("格式不对")
        return data

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] != "/":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        self._send(200, PAGE.encode(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            data = self._read_json()
        except (ValueError, json.JSONDecodeError):
            self._send(400, b'{"ok":false,"error":"\u8bf7\u6c42\u8bfb\u4e0d\u61c2"}', "application/json")
            return
        if path == "/api/ask":
            question = str(data.get("question") or "").strip()
            if not question:
                result = {"ok": False, "error": "先写一个问题"}
            elif len(question) > 400:
                result = {"ok": False, "error": "问题请控制在 400 字以内"}
            else:
                result = ask_model(
                    question,
                    str(data.get("provider") or "deepseek"),
                    str(data.get("api_key") or ""),
                    str(data.get("model") or ""),
                )
        elif path == "/api/rerun":
            result = run_select(str(data.get("sql") or ""))
        else:
            self._send(404, b'{"ok":false,"error":"\u6ca1\u6709\u8fd9\u4e2a\u5730\u5740"}', "application/json")
            return
        self._send(200, json.dumps(result, ensure_ascii=False).encode(), "application/json; charset=utf-8")


def main() -> None:
    if not DB_PATH.is_file():
        raise SystemExit(f"同一文件夹里没有数据库：{DB_PATH}")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"页面已打开 http://127.0.0.1:{PORT}/")
    print("关掉这个窗口就停。")
    webbrowser.open(f"http://127.0.0.1:{PORT}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
