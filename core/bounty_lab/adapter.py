"""Explicit opt-in adapter for Jarvis's existing ExecutorRegistry."""
from core.cognition.execution_orchestrator.contracts import ExecutionResult
from .engine import CAPABILITY, Denied

class LabExecutor:
    capability = CAPABILITY

    def __init__(self, store):
        self.store = store

    def execute(self, context):
        try:
            if context.activity.required_capability != CAPABILITY or not context.approved:
                raise Denied('Approved lab activity required')
            with self.store.tx() as db:
                m = self.store.mission(db, context.mission_id)
                if m['decision'] != context.decision_id:
                    raise Denied('Decision does not match mission')
                task = db.execute('SELECT id FROM tasks WHERE id=? AND mission=?',
                                  (context.activity.activity_id, context.mission_id)).fetchone()
                if task is None:
                    raise Denied('Activity is not a stored task')
            self.store.run(context.mission_id, context.activity.activity_id)
            return ExecutionResult(True, 'Completed synthetic laboratory task',
                                   output_reference=f'lab-db:{context.mission_id}/{context.activity.activity_id}',
                                   telemetry={'simulation': 'true'})
        except Denied as error:
            return ExecutionResult(False, str(error), telemetry={'simulation': 'true'})
