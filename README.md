# TEALS - 改ざん検知機能付き監査ログシステム

**T**amper-**E**vident **A**udit **L**og **S**ystem

会計データの入力履歴を記録し、ブロックチェーン技術（ハッシュチェーン）でデータの改ざんを検知するPythonシステムです。

## 設計思想

このシステムは、**簿記の「訂正仕訳の原則」**をプログラムで強制することを目的としています。

- 一度記録した数字は消しゴムで消さない
- 訂正は取消仕訳 + 正しい仕訳で行う
- すべての履歴が追跡可能

これをハッシュチェーン技術で技術的に実装し、不正な改ざんを検出可能にしています。

## 技術スタック

- Python 3.11
- SQLAlchemy（ORM）
- SQLite（データベース）
- hashlib（SHA-256ハッシュ）

## ファイル構成

```
teals/
├── models.py       # データモデル定義（AuditLogテーブル）
├── log_manager.py  # ログ追加ロジック（ハッシュ計算・連鎖）
├── verifier.py     # 検証ロジック（改ざん検出）
├── demo.py         # デモ実行スクリプト
└── README.md       # このファイル
```

## インストール

```bash
pip install sqlalchemy
```

## 使い方

### デモの実行

```bash
python demo.py
```

デモでは以下を実演します：

1. ログの追加
2. 正常状態での検証 → 「検証完了」
3. データの直接改ざん
4. 再検証 → 「改ざん検出」

### プログラムからの利用

```python
from models import init_db
from log_manager import add_log
from verifier import verify_all

# データベース初期化
engine, Session = init_db("my_audit.db")
session = Session()

# ログ追加
add_log(
    session,
    user_id="user001",
    action_type="INSERT",
    target_table="accounts",
    after_data={"account_id": "A001", "balance": 100000}
)

# 検証
result = verify_all(session)
print(result)  # ✓ 検証完了: 1件のログが正常です
```

## データモデル

| カラム | 型 | 説明 |
|--------|------|------|
| id | Integer | 主キー（自動採番） |
| timestamp | DateTime | 記録日時 |
| user_id | String | 操作者ID |
| action_type | String | 操作種別（INSERT/UPDATE/DELETE） |
| target_table | String | 対象テーブル名 |
| before_data | Text | 変更前データ（JSON） |
| after_data | Text | 変更後データ（JSON） |
| previous_hash | String(64) | 前レコードのハッシュ値 |
| current_hash | String(64) | 自身のハッシュ値 |

## ハッシュ計算ロジック

```
current_hash = SHA256(timestamp + user_id + action_type + target_table 
                      + before_data + after_data + previous_hash)
```

- 最初のレコードの `previous_hash` は `"0" × 64文字`
- 各レコードは直前のレコードのハッシュ値を参照し、チェーンを形成

---

# English

## Overview

**TEALS** (Tamper-Evident Audit Log System) is a Python library that records data changes and detects tampering using blockchain technology (hash chains).

### Design Philosophy

This system enforces the **"correction journal entry principle"** from accounting:

- Never erase a recorded number
- Corrections must use reversal entry + correct entry
- All history must be traceable

### Key Features

| Feature | Description |
|:--|:--|
| **Hash Chain** | Each record links to the previous one via SHA-256 hash |
| **Tamper Detection** | Any modification breaks the chain, enabling instant detection |
| **Audit Trail** | Complete history of INSERT/UPDATE/DELETE operations |

### Technical Stack

- Python 3.11+
- SQLAlchemy (ORM)
- SQLite (Database)
- hashlib (SHA-256)

### Quick Start

```bash
pip install sqlalchemy
python demo.py
```

### Use Case

Ideal for:

- Financial systems requiring audit trails
- Compliance-critical applications
- Any system where data integrity is essential

---

*Built with 🔐 integrity in mind*
