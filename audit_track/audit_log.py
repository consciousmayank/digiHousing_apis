from sqlalchemy.orm import Session
from database.database_models import AuditLogsDbModel
import json

def add_audit_log(db: Session, table_name: str, record_id: int, changed_by: int, old_values: dict, new_values: dict):
    audit_log = AuditLogsDbModel(
        table_name=table_name,
        record_id=record_id,
        changed_by=changed_by,
        old_values=json.dumps(old_values),
        new_values=json.dumps(new_values)
    )
    db.add(audit_log)
    db.commit()