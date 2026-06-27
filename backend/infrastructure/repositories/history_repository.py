from infrastructure.models.db_models import UserHistory
from extensions import db

class HistoryRepository:
    def log_activity(self, id_user, id_product, fit_status, body_shape):
        log = UserHistory(
            id_user=id_user, 
            id_product=id_product,
            fit_status=fit_status, 
            body_shape=body_shape
        )
        db.session.add(log)
        db.session.commit()