import uuid
from celery import signals
from .logging import correlation_id, operation_id, log


@signals.before_task_publish.connect
def published(sender=None, headers=None, **kwargs):
    headers['x_correlation_id'] = correlation_id.get() or str(uuid.uuid4())
    headers['operation_id'] = operation_id.get() or headers['id']
    headers['argsrepr'] = '<redacted>'
    headers['kwargsrepr'] = '<redacted>'
    token = correlation_id.set(headers['x_correlation_id'])
    try:
        log('worker' if operation_id.get() else 'api', 'task_queued',
            operation_id=headers['operation_id'], celery_task_id=headers['id'],
            task=sender, retry_attempt=headers.get('retries', 0), outcome='pending')
    finally:
        correlation_id.reset(token)


@signals.task_prerun.connect
def started(task_id=None, task=None, **kwargs):
    headers = task.request.headers or {}
    task.request.log_tokens = (
        correlation_id.set(headers.get('x_correlation_id', str(uuid.uuid4()))),
        operation_id.set(headers.get('operation_id', task_id)),
    )
    task_event(task, 'task_started', 'running')


def task_event(task, event, outcome, severity='INFO', **fields):
    log('worker', event, severity, operation_id=operation_id.get(),
        celery_task_id=task.request.id, task=task.name,
        retry_attempt=task.request.retries, outcome=outcome, **fields)


@signals.task_retry.connect
def retry(sender=None, **kwargs):
    task_event(sender, 'task_retry', 'retrying', 'WARNING')


@signals.task_failure.connect
def failed(sender=None, exception=None, **kwargs):
    task_event(sender, 'task_failed', 'failed', 'ERROR', error_type=type(exception).__name__)


@signals.task_postrun.connect
def finished(task=None, state=None, **kwargs):
    if state == 'SUCCESS':
        task_event(task, 'task_finished', 'succeeded')
    tokens = getattr(task.request, 'log_tokens', None)
    if tokens:
        correlation_id.reset(tokens[0])
        operation_id.reset(tokens[1])
