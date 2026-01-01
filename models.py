"""
TEALS - データモデル定義
監査ログテーブルのSQLAlchemy ORM定義
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class AuditLog(Base):
    """
    監査ログテーブル
    ブロックチェーン形式でハッシュチェーンを持つ
    """
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(String(100), nullable=False)
    action_type = Column(String(10), nullable=False)  # INSERT, UPDATE, DELETE
    target_table = Column(String(100), nullable=False)
    before_data = Column(Text, nullable=True)  # JSON形式
    after_data = Column(Text, nullable=True)   # JSON形式
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, action={self.action_type}, "
            f"table={self.target_table}, user={self.user_id})>"
        )


def init_db(db_path: str = "audit_log.db"):
    """
    データベースを初期化し、セッションファクトリを返す
    
    Args:
        db_path: SQLiteデータベースのパス
        
    Returns:
        tuple: (engine, Session)
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
