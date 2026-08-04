import pandas as pd

rows = []
for kw, k1, k2 in duplicates:
    rows.append({"type": "完全重複", "keyword_short": kw, "key_A": k1, "key_B": k2, "risk": "高 - 兩邊都可能被觸發"})

# rebuild seen mapping with full info
seen_full = {}
for kw1, key1, kw2, key2 in substring_conflicts:
    sig = (kw1, key1, key2)
    if sig not in seen_full:
        seen_full[sig] = kw2

for (kw1, key1, key2), kw2 in seen_full.items():
    cross_domain = key1.split("/")[1] != key2.split("/")[1] if "/" in key1 and "/" in key2 else True
    risk = "高 - 跨功能誤判" if cross_domain else "中 - 同域內細微差異"
    rows.append({"type": "子字串攔截", "keyword_short": kw1, "key_A": key1, "key_B": f"{kw2} @ {key2}", "risk": risk})

df = pd.DataFrame(rows)
df.to_csv("output/keyword_conflict_report.csv", index=False, encoding="utf-8-sig")
print(df.shape)
print(df[df['risk'].str.startswith('高')].to_string())