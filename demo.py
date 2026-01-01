"""
TEALS - デモ実行スクリプト
正常動作と改ざん検出の一連の流れを実演
"""

import os
import sys
from datetime import datetime

from models import init_db, AuditLog
from log_manager import add_log
from verifier import verify_all


DB_PATH = "demo_audit.db"


def print_separator(title: str = ""):
    """区切り線を出力"""
    if title:
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}\n")
    else:
        print("-" * 60)


def print_logs(session):
    """全ログを表形式で出力"""
    logs = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
    
    if not logs:
        print("ログはありません")
        return
    
    print(f"{'ID':>4} | {'操作':>8} | {'テーブル':<12} | {'ユーザー':<10} | ハッシュ(先頭16文字)")
    print("-" * 70)
    
    for log in logs:
        print(
            f"{log.id:>4} | {log.action_type:>8} | {log.target_table:<12} | "
            f"{log.user_id:<10} | {log.current_hash[:16]}..."
        )


def run_demo():
    """デモを実行"""
    # 既存のDBファイルを削除してクリーンな状態で開始
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"既存のデータベース '{DB_PATH}' を削除しました")
    
    # データベース初期化
    engine, Session = init_db(DB_PATH)
    session = Session()
    
    # ========================================
    # STEP 1: ログを追加
    # ========================================
    print_separator("STEP 1: 監査ログを追加")
    
    # サンプルデータを追加
    sample_data = [
        {
            "user_id": "user001",
            "action_type": "INSERT",
            "target_table": "accounts",
            "after_data": {"account_id": "A001", "name": "現金", "balance": 100000}
        },
        {
            "user_id": "user001",
            "action_type": "INSERT",
            "target_table": "accounts",
            "after_data": {"account_id": "A002", "name": "売掛金", "balance": 50000}
        },
        {
            "user_id": "user002",
            "action_type": "UPDATE",
            "target_table": "accounts",
            "before_data": {"account_id": "A001", "balance": 100000},
            "after_data": {"account_id": "A001", "balance": 150000}
        },
        {
            "user_id": "admin",
            "action_type": "DELETE",
            "target_table": "temp_records",
            "before_data": {"record_id": "T001", "status": "expired"}
        },
    ]
    
    for data in sample_data:
        log = add_log(session, **data)
        print(f"追加: {log}")
    
    print(f"\n合計 {len(sample_data)} 件のログを追加しました")
    
    print_separator("現在のログ一覧")
    print_logs(session)
    
    # ========================================
    # STEP 2: 正常状態で検証
    # ========================================
    print_separator("STEP 2: 正常状態での検証")
    
    result = verify_all(session)
    print(result)
    
    # ========================================
    # STEP 3: データを直接改ざん（SQLiteを直接操作）
    # ========================================
    print_separator("STEP 3: データを直接改ざん（悪意のある操作をシミュレート）")
    
    # ID=2のレコードを取得して改ざん
    target_log = session.query(AuditLog).filter(AuditLog.id == 2).first()
    original_data = target_log.after_data
    
    print(f"改ざん対象: ID={target_log.id}")
    print(f"改ざん前のafter_data: {original_data}")
    
    # 直接SQLで改ざん（通常のアプリケーション処理をバイパス）
    from sqlalchemy import text
    session.execute(
        text("UPDATE audit_logs SET after_data = :new_data WHERE id = :id"),
        {"new_data": '{"account_id": "A002", "name": "売掛金", "balance": 999999999}', "id": 2}
    )
    session.commit()
    
    # 改ざん後のデータを確認
    session.expire_all()  # キャッシュをクリア
    tampered_log = session.query(AuditLog).filter(AuditLog.id == 2).first()
    print(f"改ざん後のafter_data: {tampered_log.after_data}")
    print("\n※ 50000円が999999999円に不正に書き換えられました")
    
    # ========================================
    # STEP 4: 改ざん検出
    # ========================================
    print_separator("STEP 4: 改ざん検出の検証")
    
    result = verify_all(session)
    print(result)
    
    # ========================================
    # まとめ
    # ========================================
    print_separator("デモ完了")
    print("""
このデモでは以下を実証しました：

1. 監査ログの追加
   - 各ログは前のログのハッシュ値を参照してチェーンを形成

2. 正常状態での検証
   - すべてのハッシュ値が正しいことを確認

3. データの改ざん
   - SQLを直接実行してデータを不正に書き換え

4. 改ざんの検出
   - ハッシュ値の再計算により改ざんを検出

このシステムにより、簿記の「訂正仕訳の原則」をプログラムで強制し、
一度記録した数字は削除や改変ができず、必ず履歴が残ります。
""")
    
    session.close()
    engine.dispose()  # Windowsでファイルロックを解放
    
    # クリーンアップ
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"デモ用データベース '{DB_PATH}' を削除しました")


if __name__ == "__main__":
    run_demo()
