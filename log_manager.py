"""
TEALS - ログ追加ロジック
ハッシュチェーンを維持しながら監査ログを追加
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, Any

from models import AuditLog


# 最初のレコードに使用する初期ハッシュ値
GENESIS_HASH = "0" * 64


def calculate_hash(
    timestamp: datetime,
    user_id: str,
    action_type: str,
    target_table: str,
    before_data: Optional[str],
    after_data: Optional[str],
    previous_hash: str
) -> str:
    """
    監査ログのハッシュ値を計算する
    
    SHA256(timestamp + user_id + action_type + target_table + 
           before_data + after_data + previous_hash)
    
    Args:
        timestamp: 記録日時
        user_id: 操作者ID
        action_type: 操作種別
        target_table: 対象テーブル名
        before_data: 変更前データ（JSON文字列）
        after_data: 変更後データ（JSON文字列）
        previous_hash: 前のレコードのハッシュ値
        
    Returns:
        64文字のSHA-256ハッシュ値
    """
    # タイムスタンプをISO形式の文字列に変換
    timestamp_str = timestamp.isoformat()
    
    # None値を空文字列に変換
    before_str = before_data if before_data else ""
    after_str = after_data if after_data else ""
    
    # 連結してハッシュ計算
    data = (
        timestamp_str +
        user_id +
        action_type +
        target_table +
        before_str +
        after_str +
        previous_hash
    )
    
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def add_log(
    session,
    user_id: str,
    action_type: str,
    target_table: str,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None,
    timestamp: Optional[datetime] = None
) -> AuditLog:
    """
    監査ログを追加する
    
    自動的に前のレコードのハッシュを取得して連鎖させる
    
    Args:
        session: SQLAlchemyセッション
        user_id: 操作者ID
        action_type: 操作種別（INSERT/UPDATE/DELETE）
        target_table: 対象テーブル名
        before_data: 変更前データ（dict）
        after_data: 変更後データ（dict）
        timestamp: 記録日時（省略時は現在時刻）
        
    Returns:
        作成されたAuditLogオブジェクト
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # 前のレコードのハッシュを取得
    last_log = session.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last_log.current_hash if last_log else GENESIS_HASH
    
    # データをJSON文字列に変換
    before_json = json.dumps(before_data, ensure_ascii=False, sort_keys=True) if before_data else None
    after_json = json.dumps(after_data, ensure_ascii=False, sort_keys=True) if after_data else None
    
    # ハッシュを計算
    current_hash = calculate_hash(
        timestamp=timestamp,
        user_id=user_id,
        action_type=action_type,
        target_table=target_table,
        before_data=before_json,
        after_data=after_json,
        previous_hash=previous_hash
    )
    
    # レコードを作成
    log = AuditLog(
        timestamp=timestamp,
        user_id=user_id,
        action_type=action_type,
        target_table=target_table,
        before_data=before_json,
        after_data=after_json,
        previous_hash=previous_hash,
        current_hash=current_hash
    )
    
    session.add(log)
    session.commit()
    
    return log
