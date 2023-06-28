from __future__ import unicode_literals

__author__ = 'David Baum'

import logging, sys

from django.core.management.base import BaseCommand

from utils.rq import clean_queue


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-q", "--queue", type=str)
        parser.add_argument('-l',
                            '--level',
                            type=str,
                            dest="level",
                            help="Specify the level of logging",
                            default="DEBUG"
                            )

    def handle(self, *args, **options):
        queue_name = options.get("queue")
        level_logging = options['level']

        root = logging.getLogger(__name__)
        root.setLevel(logging.getLevelName(level_logging))

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.getLevelName(level_logging))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

        clean_queue(queue_name)
