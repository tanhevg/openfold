# Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
import operator
import sys
import time
from pathlib import Path

import dllogger as logger
import typing

import torch.utils.data
from dllogger import JSONStreamBackend, StdOutBackend, Verbosity
import numpy as np
from pytorch_lightning import Callback
import torch.cuda.profiler as profiler

def setup_logging(save_path: typing.Optional[str] = None,
                  log_level: typing.Union[str, int] = 'info',
                  log_console: bool = True,
                  formatter: typing.Optional[logging.Formatter] = None) -> None:
    if isinstance(log_level, str):
        level = getattr(logging, log_level.upper())
    else:
        level = log_level

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    if formatter is None:
        formatter = logging.Formatter(
            "%(levelname)s %(asctime)s.%(msecs)03d [%(process)d:%(threadName)s] <%(name)s> - %(message)s",
            datefmt="%d/%b/%Y %H:%M:%S")

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    if log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        # console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if save_path is not None:
        out_path = Path(save_path)
        worker_info = torch.utils.data.get_worker_info()
        rank = os.getenv("LOCAL_RANK", "0")
        if worker_info is None:
            out_path = out_path / f'model_worker_{rank}.log'
        else:
            out_path = out_path / f'data_worker_{rank}_{worker_info.id}.log'
        file_handler = logging.FileHandler(out_path)
        # file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def is_main_process():
    return int(os.getenv("LOCAL_RANK", "0")) == 0


class PerformanceLoggingCallback(Callback):
    def __init__(self, log_file, global_batch_size, warmup_steps: int = 0, profile: bool = False):
        logger.init(backends=[JSONStreamBackend(Verbosity.VERBOSE, log_file), StdOutBackend(Verbosity.VERBOSE)])
        self.warmup_steps = warmup_steps
        self.global_batch_size = global_batch_size
        self.step = 0
        self.profile = profile
        self.timestamps = []

    def do_step(self):
        self.step += 1
        if self.profile and self.step == self.warmup_steps:
            profiler.start()
        if self.step > self.warmup_steps:
            self.timestamps.append(time.time())

    def on_train_batch_start(self, trainer, pl_module, batch, batch_idx, dataloader_idx):
        self.do_step()

    def on_test_batch_start(self, trainer, pl_module, batch, batch_idx, dataloader_idx):
        self.do_step()

    def process_performance_stats(self, deltas):
        def _round3(val):
            return round(val, 3)

        throughput_imgps = _round3(self.global_batch_size / np.mean(deltas))
        timestamps_ms = 1000 * deltas
        stats = {
            f"throughput": throughput_imgps,
            f"latency_mean": _round3(timestamps_ms.mean()),
        }
        for level in [90, 95, 99]:
            stats.update({f"latency_{level}": _round3(np.percentile(timestamps_ms, level))})

        return stats

    def _log(self):
        if is_main_process():
            diffs = list(map(operator.sub, self.timestamps[1:], self.timestamps[:-1]))
            deltas = np.array(diffs)
            stats = self.process_performance_stats(deltas)
            logger.log(step=(), data=stats)
            logger.flush()

    def on_train_end(self, trainer, pl_module):
        if self.profile:
            profiler.stop()
        self._log()

    def on_epoch_end(self, trainer, pl_module):
        self._log()
