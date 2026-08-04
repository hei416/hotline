"""
checking.py - Keyword Map Conflict Detector
用法: python checking.py
會掃描 keyword_map.json，自動搵出：
1. 完全重複的關鍵字（同一個字出現在兩個唔同 key）
2. 子字串攔截風險（短字是另一個長字的子字串，可能造成優先掃描時誤判）
"""

import json
import pandas as pd
import os

def load_keyword_map(path="keyword_map.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def find_duplicates(data):
    keyword_owner = {}
    duplicates = []
    for key, kws in data.items():
        for kw in kws:
            if kw in keyword_owner:
                duplicates.append((kw, keyword_owner[kw], key))
            else:
                keyword_owner[kw] = key
    return duplicates

def find_substring_conflicts(data):
    all_keywords = [(kw, key) for key, kws in data.items() for kw in kws]
    conflicts = []
    seen = set()
    for kw1, key1 in all_keywords:
        for kw2, key2 in all_keywords:
            if key1 != key2 and kw1 != kw2 and kw1 in kw2 and len(kw1) < len(kw2):
                sig = (kw1, key1, key2)
                if sig not in seen:
                    seen.add(sig)
                    conflicts.append((kw1, key1, kw2, key2))
    return conflicts

def build_report(duplicates, substring_conflicts):
    rows = []
    for kw, k1, k2 in duplicates:
        rows.append({
            "type": "完全重複",
            "keyword_short": kw,
            "key_A": k1,
            "key_B": k2,
            "risk": "高 - 兩邊都可能被觸發"
        })

    for kw1, key1, kw2, key2 in substring_conflicts:
        domain1 = key1.split("/")[1] if "/" in key1 else key1
        domain2 = key2.split("/")[1] if "/" in key2 else key2
        cross_domain = domain1 != domain2
        risk = "高 - 跨功能誤判" if cross_domain else "中 - 同域內細微差異"
        rows.append({
            "type": "子字串攔截",
            "keyword_short": kw1,
            "key_A": key1,
            "key_B": f"{kw2} @ {key2}",
            "risk": risk
        })

    return pd.DataFrame(rows)

def main():
    data = load_keyword_map("keyword_map.json")
    duplicates = find_duplicates(data)
    substring_conflicts = find_substring_conflicts(data)
    report = build_report(duplicates, substring_conflicts)

    if report.empty:
        print("No conflicts found.")
    else:
        print(report.to_string(index=False))

if __name__ == "__main__":
    main()