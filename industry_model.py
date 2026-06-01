"""
產業估值模型模組。

目的：
- 依股票代號、stocklist.txt 分類、yfinance sector/industry，選擇較適合的估值框架。
- 不直接取代原本公式估值，而是提供「建議估值重點、風險警戒、Cap 建議、可操作估值折減」。
"""
import os
import re
import pandas as pd


def _safe_str(x):
    return "" if x is None else str(x)


def _read_stocklist_category(stock_id):
    """從 stocklist.txt 找出股票所在分類。找不到回傳空字串。"""
    sid = _safe_str(stock_id).strip()
    if not sid:
        return ""
    paths = ["stocklist.txt", os.path.join(os.getcwd(), "stocklist.txt")]
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            current_cat = ""
            with open(path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    # 分類列常見格式：★【核心算力與高階封測】
                    if "【" in line and "】" in line:
                        m = re.search(r"【(.+?)】", line)
                        current_cat = m.group(1).strip() if m else line.strip("★ ")
                        continue
                    if line.startswith(sid + ","):
                        return current_cat
        except Exception:
            continue
    return ""


# 題材 / 財報支撐度較低或較不適合用純 P/E 的常見案例，可逐步擴充。
THEMATIC_STOCK_IDS = {
    "8033": "軍工/無人機題材股",
}


PROFILES = {
    "foundry_ic": {
        "model_key": "foundry_ic",
        "model_label": "晶圓代工 / IC 設計 / 半導體核心",
        "valuation_method": "P/E + Forward P/E + P/B + ROE + 毛利率交叉；避免只看單一 PEG。",
        "primary_metrics": "P/E、Forward P/E、P/B、ROE、毛利率、研發/先進製程或設計案能見度",
        "caution_points": "景氣循環、庫存調整、匯率、資本支出、客戶集中與估值均值回歸。",
        "cap_hint": 35.0,
        "cap_adjust": 5.0,
        "operable_discount_factor": 0.96,
        "pe_model_suitable": True,
        "warning_note": "可使用 P/E 估值，但需搭配 P/B、ROE 與毛利率確認品質。",
    },
    "abf_pcb": {
        "model_key": "abf_pcb",
        "model_label": "PCB / ABF / 高階載板",
        "valuation_method": "Forward P/E + P/B + 月營收動能 + 毛利率；報價與稼動率需另行人工確認。",
        "primary_metrics": "Forward P/E、P/B、月營收 YoY/MoM、毛利率、產品報價、客戶拉貨",
        "caution_points": "ABF 報價、T-glass 供需、庫存循環、單月營收轉弱、資本支出高峰。",
        "cap_hint": 30.0,
        "cap_adjust": 0.0,
        "operable_discount_factor": 0.93,
        "pe_model_suitable": True,
        "warning_note": "P/E 可用，但可操作價需對月營收轉弱與報價循環折價。",
    },
    "advanced_packaging_equipment": {
        "model_key": "advanced_packaging_equipment",
        "model_label": "CoWoS / 先進封裝 / 半導體設備",
        "valuation_method": "Forward P/E + 訂單能見度 + 毛利率 + FCF；避免單靠題材推高 Cap。",
        "primary_metrics": "Forward P/E、毛利率、FCF、訂單能見度、交期、法人 EPS 上修",
        "caution_points": "接單認列時程、客戶驗證、營收基期、法人預估分歧、高估值修正。",
        "cap_hint": 40.0,
        "cap_adjust": 8.0,
        "operable_discount_factor": 0.90,
        "pe_model_suitable": True,
        "warning_note": "成長股可給較高 Cap，但需對導入時程與 EPS 分歧折價。",
    },
    "ai_server": {
        "model_key": "ai_server",
        "model_label": "AI 伺服器代工 / 組裝 / 主板零組件",
        "valuation_method": "Forward P/E + 營收動能 + 毛利率 + 客戶訂單；低毛利代工不宜過度拉高 P/E。",
        "primary_metrics": "Forward P/E、月營收、毛利率、存貨、客戶集中、AI 伺服器占比",
        "caution_points": "低毛利、出貨高峰後衰退、客戶砍單、匯率與價格競爭。",
        "cap_hint": 25.0,
        "cap_adjust": 0.0,
        "operable_discount_factor": 0.92,
        "pe_model_suitable": True,
        "warning_note": "可用 P/E，但代工/組裝股需用毛利率與訂單品質下修可操作區間。",
    },
    "thermal": {
        "model_key": "thermal",
        "model_label": "散熱 / 水冷 / 機構熱管理",
        "valuation_method": "Forward P/E + EPS 上修 + 月營收 + 毛利率；AI 水冷題材需防估值過熱。",
        "primary_metrics": "Forward P/E、EPS 上修、月營收、毛利率、AI 水冷滲透率、客戶導入",
        "caution_points": "估值偏高、月營收轉弱、競爭者擴產、法人下修、題材鈍化。",
        "cap_hint": 45.0,
        "cap_adjust": 10.0,
        "operable_discount_factor": 0.88,
        "pe_model_suitable": True,
        "warning_note": "成長性高但波動大，可操作估值需較公式價明顯折價。",
    },
    "optical_comm": {
        "model_key": "optical_comm",
        "model_label": "矽光子 / 光通訊 / 網通",
        "valuation_method": "Forward P/E + 營收動能 + 訂單/規格升級；高題材股需降低公式價可信度。",
        "primary_metrics": "Forward P/E、月營收、毛利率、800G/1.6T/CPO 導入、客戶認證",
        "caution_points": "題材波動、規格轉換、客戶驗證失敗、法人樣本不足、單月營收大幅波動。",
        "cap_hint": 40.0,
        "cap_adjust": 8.0,
        "operable_discount_factor": 0.86,
        "pe_model_suitable": True,
        "warning_note": "題材與獲利落差可能大，操作區間需保守。",
    },
    "power_memory": {
        "model_key": "power_memory",
        "model_label": "電源 / 記憶體 / 週期性零組件",
        "valuation_method": "P/B + 週期位置 + Forward P/E；獲利低谷時 P/E 可能失真。",
        "primary_metrics": "P/B、月營收、毛利率、庫存、報價循環、Forward P/E",
        "caution_points": "記憶體報價循環、庫存、獲利低谷導致 P/E 虛高或無意義。",
        "cap_hint": 22.0,
        "cap_adjust": -3.0,
        "operable_discount_factor": 0.90,
        "pe_model_suitable": True,
        "warning_note": "週期股需搭配 P/B 與報價循環，不宜只看 Forward P/E。",
    },
    "software_service": {
        "model_key": "software_service",
        "model_label": "軟體 / 資安 / 系統整合",
        "valuation_method": "P/E + 營收成長 + 毛利率 + 經常性收入；FCF 品質重要。",
        "primary_metrics": "P/E、營收成長、毛利率、FCF、續約率/經常性收入",
        "caution_points": "專案認列遞延、政府標案時程、人力成本、AI 題材溢價。",
        "cap_hint": 35.0,
        "cap_adjust": 5.0,
        "operable_discount_factor": 0.94,
        "pe_model_suitable": True,
        "warning_note": "高毛利可支撐較高估值，但需看現金流與收入穩定度。",
    },
    "thematic": {
        "model_key": "thematic",
        "model_label": "題材股 / 事件驅動股",
        "valuation_method": "題材、訂單事件、籌碼與技術面為主；不適合用一般 P/E 合理價當買進建議。",
        "primary_metrics": "事件催化、訂單真實性、籌碼、成交量、毛利率、現金流",
        "caution_points": "財報不支撐、法人目標缺乏、籌碼急轉、漲多後消息鈍化。",
        "cap_hint": 18.0,
        "cap_adjust": -10.0,
        "operable_discount_factor": 0.65,
        "pe_model_suitable": False,
        "warning_note": "不建議用 P/E 公式價作投資買進依據，應優先顯示題材與籌碼風險。",
    },
    "general": {
        "model_key": "general",
        "model_label": "一般產業 / 尚未分類",
        "valuation_method": "P/E + P/B + ROE + 月營收 + 現金流交叉驗證。",
        "primary_metrics": "P/E、Forward P/E、P/B、ROE、月營收、FCF",
        "caution_points": "若資料不足或 AI/系統分歧，需降低操作可信度。",
        "cap_hint": 25.0,
        "cap_adjust": 0.0,
        "operable_discount_factor": 0.95,
        "pe_model_suitable": True,
        "warning_note": "通用模型，建議人工確認產業屬性後再提高可信度。",
    },
}


def _choose_model_key(stock_id, stock_name="", category="", sector="", industry=""):
    text = " ".join([_safe_str(stock_id), _safe_str(stock_name), _safe_str(category), _safe_str(sector), _safe_str(industry)]).lower()
    sid = _safe_str(stock_id).strip()
    if sid in THEMATIC_STOCK_IDS:
        return "thematic"
    if any(k.lower() in text for k in ["題材", "軍工", "無人機", "drone"]):
        return "thematic"
    if any(k.lower() in text for k in ["abf", "pcb", "載板", "主板", "連接線", "印刷電路"]):
        return "abf_pcb"
    if any(k.lower() in text for k in ["cowos", "先進封裝", "封裝設備", "半導體設備", "檢測設備", "設備"]):
        return "advanced_packaging_equipment"
    if any(k.lower() in text for k in ["散熱", "水冷", "thermal", "heat"]):
        return "thermal"
    if any(k.lower() in text for k in ["矽光子", "光通訊", "光學", "optic", "optical", "網通"]):
        return "optical_comm"
    if any(k.lower() in text for k in ["伺服器代工", "組裝", "ai 伺服器", "server", "computer hardware"]):
        return "ai_server"
    if any(k.lower() in text for k in ["電源", "記憶體", "dram", "memory", "power"]):
        return "power_memory"
    if any(k.lower() in text for k in ["軟體", "資安", "系統整合", "software", "it services"]):
        return "software_service"
    if any(k.lower() in text for k in ["晶圓", "半導體", "ic", "semiconductor", "高階封測", "核心算力"]):
        return "foundry_ic"
    return "general"


def get_industry_valuation_profile(stock_id, stock_name="", sector="", industry=""):
    """回傳產業估值模型 profile。"""
    category = _read_stocklist_category(stock_id)
    key = _choose_model_key(stock_id, stock_name, category, sector, industry)
    profile = dict(PROFILES.get(key, PROFILES["general"]))
    profile["matched_category"] = category or "未在 stocklist.txt 找到分類"
    profile["stock_id"] = _safe_str(stock_id)
    profile["stock_name"] = _safe_str(stock_name)
    return profile


def build_industry_valuation_model_report(profile):
    """產業估值模型說明表。"""
    p = profile or PROFILES["general"]
    rows = [
        {"項目": "匹配產業模型", "內容": p.get("model_label", "一般產業")},
        {"項目": "stocklist 分類", "內容": p.get("matched_category", "—")},
        {"項目": "主要估值框架", "內容": p.get("valuation_method", "—")},
        {"項目": "優先觀察指標", "內容": p.get("primary_metrics", "—")},
        {"項目": "警戒重點", "內容": p.get("caution_points", "—")},
        {"項目": "建議 Cap 參考", "內容": f"{p.get('cap_hint', '—')}x" if p.get("cap_hint") is not None else "—"},
        {"項目": "可操作估值折減", "內容": f"{p.get('operable_discount_factor', 1.0):.2f} 倍"},
        {"項目": "P/E 模型適用性", "內容": "可用，但需交叉驗證" if p.get("pe_model_suitable", True) else "不適合作為買進建議主模型"},
        {"項目": "模型提醒", "內容": p.get("warning_note", "—")},
    ]
    return pd.DataFrame(rows)
