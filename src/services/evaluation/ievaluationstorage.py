from src.models.evaluation import Evaluation
from src.models.attempt import Attempt


class IEvaluationStorage:
    def check_is_owner(self, user: str, evaluation_id: str):
        raise NotImplementedError()

    def create_evaluation(self, e: Evaluation):
        raise NotImplementedError()

    def list_evaluations(self, user: str):
        raise NotImplementedError()

    def update_evaluation(self, evaluation_id: str, field: str, value):
        raise NotImplementedError()

    def get_evaluation(self, evaluation_id):
        raise NotImplementedError()

    def create_attempt(self, a: Attempt):
        raise NotImplementedError()

    def update_attempt(self, attempt_id: str, field: str, value):
        raise NotImplementedError()

    def get_attempts(self, evaluation_id: str):
        raise NotImplementedError()
