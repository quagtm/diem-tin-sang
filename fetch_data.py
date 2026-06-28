"""
fetch_data.py — chạy mỗi sáng qua GitHub Actions
Fetch TCBS + Yahoo Finance → ghi data.json
"""
import json, time, datetime, requests, sys

def yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        meta = r.json()["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev  = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        chg   = (price - prev) / prev * 100 if prev else 0
        return {"price": round(price, 2), "chgPct": round(chg, 2)}
    except Exception as e:
        print(f"Yahoo {symbol} error: {e}", file=sys.stderr)
        return None

def tcbs(ticker):
    try:
        to   = int(time.time())
        frm  = to - 86400 * 7
        url  = (f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"
                f"?ticker={ticker}&type=stock&resolution=D&from={frm}&to={to}")
        r = requests.get(url, timeout=10)
        bars = r.json().get("data", [])
        if len(bars) < 2:
            return None
        last, prev = bars[-1], bars[-2]
        price  = last["close"] * 1000
        chg    = (last["close"] - prev["close"]) / prev["close"] * 100
        volume = last.get("volume", 0)
        return {"price": round(price), "chgPct": round(chg, 2), "volume": volume}
    except Exception as e:
        print(f"TCBS {ticker} error: {e}", file=sys.stderr)
        return None

def tcbs_index(ticker):
    """Fetch VN indices via TCBS index endpoint"""
    try:
        to   = int(time.time())
        frm  = to - 86400 * 7
        url  = (f"https://apipubaws.tcbs.com.vn/stock-insight/v1/index/bars-long-term"
                f"?ticker={ticker}&resolution=D&from={frm}&to={to}")
        r = requests.get(url, timeout=10)
        bars = r.json().get("data", [])
        if len(bars) < 2:
            return None
        last, prev = bars[-1], bars[-2]
        price = last["close"]
        chg   = (last["close"] - prev["close"]) / prev["close"] * 100
        vol   = last.get("volume", 0)
        return {"price": round(price, 2), "chgPct": round(chg, 2), "volume": vol}
    except Exception as e:
        print(f"TCBS index {ticker} error: {e}", file=sys.stderr)
        return None

now_vn = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

print("Fetching world markets...")
world = {
    "sp500":    yahoo("^GSPC"),
    "nasdaq":   yahoo("^IXIC"),
    "nikkei":   yahoo("^N225"),
    "shanghai": yahoo("000001.SS"),
    "oil":      yahoo("BZ=F"),
    "gold":     yahoo("GC=F"),
    "usdvnd":   yahoo("VND=X"),
}

print("Fetching VN indices...")
vn = {
    "vnindex": tcbs_index("VNINDEX") or yahoo("^VNINDEX"),
    "vn30":    tcbs_index("VN30")    or yahoo("^VN30"),
    "hnx":     tcbs_index("HNX")     or yahoo("^HNX"),
}

print("Fetching stock picks...")
stocks = {}
tickers = ["VCB","HPG","FPT","SSI","VNM","MWG","TCB","VHM","GAS","PVD"]
for t in tickers:
    stocks[t] = tcbs(t)
    time.sleep(0.3)

data = {
    "updated": now_vn.strftime("%H:%M — %d/%m/%Y"),
    "updated_iso": now_vn.isoformat(),
    "world": world,
    "vn": vn,
    "stocks": stocks,
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ data.json written")
print(json.dumps({k: v for k,v in data["vn"].items()}, indent=2))
