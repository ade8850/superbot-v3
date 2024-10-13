import asyncio
import re
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Tuple

from google.cloud import pubsub_v1


class PubSubSubscriber:
    def __init__(self, app):
        self.app = app
        self.message_queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor()
        self.loop = asyncio.get_event_loop()
        self.subscription_tasks = []
        self.process_functions: Dict[str, Tuple[re.Pattern, Callable]] = {}

    def add_process_function_for_subject(self, subject_pattern: str, func: Callable):
        compiled_pattern = re.compile(subject_pattern)
        self.process_functions[subject_pattern] = (compiled_pattern, func)

    def message_callback(self, message):
        asyncio.run_coroutine_threadsafe(self.message_queue.put(message), self.loop)

    async def process_message(self, message):
        try:
            subject = message.attributes.get('subject', '')
            processed = False
            for pattern, func in self.process_functions.values():
                if pattern.match(subject):
                    await func(message)
                    processed = True
                    break
            #if not processed:
            #    self.app.logger.warning(f"No matching process function for subject: {subject}")
            message.ack()
        except Exception as e:
            self.app.logger.error(f"Error processing message: {e}")
            message.nack()

    async def run_subscriber(self, subscription_path):
        subscriber = pubsub_v1.SubscriberClient()
        future = subscriber.subscribe(subscription_path, callback=self.message_callback)
        self.app.logger.info(f"Listening for messages on {subscription_path}")

        try:
            await self.loop.run_in_executor(self.executor, future.result)
        except Exception as ex:
            self.app.logger.error(f"Error in subscription {subscription_path}: {ex}")
        finally:
            future.cancel()
            subscriber.close()

    async def process_queue(self):
        while True:
            message = await self.message_queue.get()
            await self.process_message(message)
            self.message_queue.task_done()

    async def start(self):
        for env_var, value in os.environ.items():
            if env_var.startswith("SUBSCRIPTION_"):
                self.app.logger.info(f"Starting subscription: {value}")
                task = asyncio.create_task(self.run_subscriber(value))
                self.subscription_tasks.append(task)

        self.queue_task = asyncio.create_task(self.process_queue())

    async def stop(self):
        for task in self.subscription_tasks:
            task.cancel()
        self.queue_task.cancel()

        await asyncio.gather(*self.subscription_tasks, self.queue_task, return_exceptions=True)
        self.executor.shutdown(wait=True)
