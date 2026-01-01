"""
TEALS - 検証ロジック
ハッシュチェーンの整合性を検証し、改ざんを検出する
"""

from typing import List, Tuple
from models import AuditLog
from log_manager import calculate_hash, GENESIS_HASH


class VerificationResult:
    """検証結果を表すクラス"""
    
    def __init__(self, is_valid: bool, total_count: int, errors: List[str]):
        self.is_valid = is_valid
        self.total_count = total_count
        self.errors = errors
    
    def __str__(self):
        if self.is_valid:
            return f"[OK] 検証完了: {self.total_count}件のログが正常です"
        else:
            error_msg = "\n".join(f"  - {e}" for e in self.errors)
            return f"[NG] 改ざん検出！\n{error_msg}"


def verify_all(session) -> VerificationResult:
    """
    全レコードを走査し、ハッシュの整合性をチェックする
    
    検証内容:
    1. 各レコードのcurrent_hashを再計算し、保存値と比較
    2. 前後レコードのprevious_hashとcurrent_hashの連鎖を確認
    
    Args:
        session: SQLAlchemyセッション
        
    Returns:
        VerificationResult: 検証結果
    """
    logs = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
    
    if not logs:
        return VerificationResult(True, 0, [])
    
    errors = []
    expected_previous_hash = GENESIS_HASH
    
    for log in logs:
        # 1. previous_hashの連鎖チェック
        if log.previous_hash != expected_previous_hash:
            errors.append(
                f"ID={log.id}: previous_hashの不整合 "
                f"(期待値: {expected_previous_hash[:16]}..., "
                f"実際: {log.previous_hash[:16]}...)"
            )
        
        # 2. current_hashの再計算チェック
        recalculated_hash = calculate_hash(
            timestamp=log.timestamp,
            user_id=log.user_id,
            action_type=log.action_type,
            target_table=log.target_table,
            before_data=log.before_data,
            after_data=log.after_data,
            previous_hash=log.previous_hash
        )
        
        if log.current_hash != recalculated_hash:
            errors.append(
                f"ID={log.id}: current_hashの不整合（データが改ざんされた可能性）"
            )
        
        # 次のレコードのために現在のハッシュを保存
        expected_previous_hash = log.current_hash
    
    is_valid = len(errors) == 0
    return VerificationResult(is_valid, len(logs), errors)


def verify_single(session, log_id: int) -> Tuple[bool, str]:
    """
    単一レコードのハッシュ整合性を検証する
    
    Args:
        session: SQLAlchemyセッション
        log_id: 検証対象のログID
        
    Returns:
        tuple: (is_valid, message)
    """
    log = session.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        return False, f"ID={log_id}のログが見つかりません"
    
    # ハッシュを再計算
    recalculated_hash = calculate_hash(
        timestamp=log.timestamp,
        user_id=log.user_id,
        action_type=log.action_type,
        target_table=log.target_table,
        before_data=log.before_data,
        after_data=log.after_data,
        previous_hash=log.previous_hash
    )
    
    if log.current_hash == recalculated_hash:
        return True, f"ID={log_id}: ハッシュ値が正常です"
    else:
        return False, f"ID={log_id}: ハッシュ値が不正です（改ざんの可能性）"
