"""
checking.py - Keyword Map Conflict Detector
用法: python checking.py
會掃描 keyword_map.json，自動搵出：
1. 完全重複的關鍵字（同一個字出現在兩個唔同 key）
2. 子字串攔截風險（短字是另一個長字的子字串，可能造成優先掃描時誤判）

注意：_meta/services/* 同 _meta/actions/* 係頂層分類器，
佢哋嘅關鍵字（如 WhatsApp、HA Go）出現喺 data/* 嘅長關鍵字入面屬於
正常設計，checker 會自動略過呢類 _meta → data 方向嘅子字串警報。
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


def is_meta_key(key):
    return key.startswith("_meta/")


def find_substring_conflicts(data):
    all_keywords = [(kw, key) for key, kws in data.items() for kw in kws]
    conflicts = []
    seen = set()
    for kw1, key1 in all_keywords:
        for kw2, key2 in all_keywords:
            if key1 == key2 or kw1 == kw2:
                continue
            if kw1 not in kw2 or len(kw1) >= len(kw2):
                continue
            # Skip expected pattern: _meta key's short keyword inside a data key's longer keyword
            # This is by design — meta keys are top-level classifiers
            if is_meta_key(key1) and not is_meta_key(key2):
                continue
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
        print("✅ No conflicts found.")
    else:
        high = report[report["risk"].str.startswith("高")]
        mid = report[report["risk"].str.startswith("中")]
        if not high.empty:
            print("=== 🔴 高風險衝突 ===")
            print(high.to_string(index=False))
            print()
        if not mid.empty:
            print("=== 🟡 中風險衝突（同域，longest-match 可自動處理）===")
            print(mid.to_string(index=False))


if __name__ == "__main__":
    main()
