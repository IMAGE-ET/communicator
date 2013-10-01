# python imports
import sys
import datetime
import logging

# imagis imports
import tasks
from imagis.utils.kronos import ThreadedScheduler, method

logger = logging.getLogger('imagis_cron.cron')

class StopTask(Exception):
    pass

class Cron(object):

    def __init__(self, tasks):
        self.tasks = tasks
        self.scheduler = ThreadedScheduler()
        self.setup_tasks()
        self.stopping = False

    def start(self):
        logger.info('Starting: Cron...')
        self.scheduler.start()

        scheduler_thread = self.scheduler.thread
        while scheduler_thread.is_alive():
            scheduler_thread.join(0.01)

    def stop(self):
        if self.stopping:
            return
        self.stopping = True

        logger.info('Shutting down: Cron...')
        tasks.stop = True
        self.scheduler.stop()

    def setup_tasks(self):
        for task in self.tasks:
            task_id, task_type, task_executioner, params = self.get_common_values(task)

            if task_type == 'interval':
                initial_delay, interval = self.get_interval_values(task)

                self.scheduler.add_interval_task(
                    task_executioner, task_id, initial_delay,
                    interval, method.threaded, [], params
                )
                logger.info(
                    ('Scheduling task: "%s" of type "%s" to be executed '
                     'every %s seconds from now on with an initial delay '
                     'of %s') % (task_id, task_type, interval, initial_delay)
                )
            elif task_type == 'single':
                initial_delay = self.get_single_values(task)

                self.scheduler.add_single_task(
                    task_executioner, task_id, initial_delay,
                    method.threaded, [], params
                )
                logger.info(
                    ('Scheduling task: "%s" of type "%s" to be executed '
                     'just once in %s seconds from now on') %
                     (task_id, task_type, initial_delay)
                )
            elif task_type == 'daytime':
                day_type, days, start_time = self.get_daytime_values(task)

                if day_type == 'weekdays':
                    self.scheduler.add_daytime_task(
                        task_executioner, task_id, days, None,
                        start_time, method.threaded, [], params
                    )
                    logger.info(
                        ('Scheduling task: "%s" of type "%s" to be executed '
                         'in days: %s of the week at time of %s') %
                         (task_id, task_type, days, datetime.time(*start_time))
                    )
                elif day_type == 'monthdays':
                    self.scheduler.add_daytime_task(
                        task_executioner, task_id, None, days,
                        start_time, method.threaded, [], params
                    )
                    logger.info(
                        ('Scheduling task: "%s" of type "%s" to be executed '
                         'in days %s of the month at time of %s') %
                         (task_id, task_type, days, datetime.time(*start_time))
                    )
                else:
                    raise ValueError, (
                        'Key "day_type" in config file must be '
                        'either "weekdays" or "monthdays"'
                    )
            else:
                raise ValueError, (
                    'Key "task_type" in config file must be '
                    '"interval", "single" or "monthdays" but '
                    'a value of "%s" was written' % task_type
                    )

    def _task_executioner(self, task_executioner):
        task_executioner = task_executioner.strip().split('.')
        module_name = 'tasks.' + '.'.join(task_executioner[:-1])
        task_executioner = task_executioner[-1]
        __import__(module_name, globals(), locals(), [], -1)
        return getattr(sys.modules['apps.imagis_cron.' + module_name], task_executioner)

    def get_common_values(self, task):
        task_id = task['task_id'].strip()
        task_type = task['task_type'].strip().lower()
        task_executioner = self._task_executioner(task['task_executioner'])
        params = task.get('params', {})
        return task_id, task_type, task_executioner, params

    def get_interval_values(self, task):
        initial_delay = task['initial_delay']
        interval = task['interval']
        return initial_delay, interval

    def get_single_values(self, task):
        initial_delay = task['initial_delay']
        return initial_delay

    def get_daytime_values(self, task):
        day_type = task['day_type']
        days = task['days']
        start_time = task['start_time']
        return day_type, days, start_time
