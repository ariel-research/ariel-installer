from __future__ import unicode_literals

__author__ = 'David Baum'

import django_rq, logging

from rq.registry import (
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    ScheduledJobRegistry,
    StartedJobRegistry
)

logger = logging.getLogger(__name__)


def clean_queue(queue_name):
    queue = django_rq.get_queue(queue_name)
    queue.empty()

    registry = FailedJobRegistry(queue.name, queue.connection)
    for job_id in registry.get_job_ids():
        registry.remove(job_id)
        logging.info(f'Removed job {job_id} from RQ queue {queue.name}')

    registry = DeferredJobRegistry(queue.name, queue.connection)
    for job_id in registry.get_job_ids():
        registry.remove(job_id)
        logging.info(f'Removed job {job_id} from RQ queue {queue.name}')

    registry = FinishedJobRegistry(queue.name, queue.connection)
    for job_id in registry.get_job_ids():
        registry.remove(job_id)
        logging.info(f'Removed job {job_id} from RQ queue {queue.name}')

    registry = ScheduledJobRegistry(queue.name, queue.connection)
    for job_id in registry.get_job_ids():
        registry.remove(job_id)
        logging.info(f'Removed job {job_id} from RQ queue {queue.name}')

    registry = StartedJobRegistry(queue.name, queue.connection)
    for job_id in registry.get_job_ids():
        registry.remove(job_id)
        logging.info(f'Removed job {job_id} from RQ queue {queue.name}')

    logging.info(f'The RQ queue "{queue.name}" has been successfully flushed')
