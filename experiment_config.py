import os
import platform
import psutil
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any
import json
from datetime import datetime

@dataclass
class SystemInfo:
    cpu_count: int
    cpu_freq: float
    memory_total: int
    memory_available: int
    platform: str
    python_version: str

@dataclass
class ExperimentConfig:
    # Control Factors
    thread_counts: List[int] = None
    input_sizes: List[int] = None
    cache_sizes: List[int] = None
    iterations: int = None
    
    # Response Variables
    metrics: List[str] = None
    
    # Control Variables
    system_info: SystemInfo = None
    environment_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.thread_counts is None:
            self.thread_counts = [1, 2, 4, 8, 16]
        if self.input_sizes is None:
            self.input_sizes = [20000, 40000, 80000]
        if self.cache_sizes is None:
            self.cache_sizes = [64, 128, 256]  # KB
        if self.iterations is None:
            self.iterations = 20
        if self.metrics is None:
            self.metrics = ['execution_time', 'speedup', 'efficiency']
        if self.system_info is None:
            self.system_info = self._get_system_info()
        if self.environment_vars is None:
            self.environment_vars = self._get_environment_vars()

    @staticmethod
    def _get_system_info() -> SystemInfo:
        return SystemInfo(
            cpu_count=os.cpu_count(),
            cpu_freq=psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            memory_total=psutil.virtual_memory().total,
            memory_available=psutil.virtual_memory().available,
            platform=platform.platform(),
            python_version=platform.python_version()
        )

    @staticmethod
    def _get_environment_vars() -> Dict[str, str]:
        return {
            'OMP_NUM_THREADS': os.environ.get('OMP_NUM_THREADS', ''),
            'OMP_PROC_BIND': os.environ.get('OMP_PROC_BIND', ''),
            'OMP_PLACES': os.environ.get('OMP_PLACES', ''),
            'OMP_SCHEDULE': os.environ.get('OMP_SCHEDULE', ''),
        }

    def save_config(self, filename: str):
        """Save experiment configuration to a JSON file"""
        config_dict = {
            'thread_counts': self.thread_counts,
            'input_sizes': self.input_sizes,
            'cache_sizes': self.cache_sizes,
            'iterations': self.iterations,
            'metrics': self.metrics,
            'system_info': {
                'cpu_count': self.system_info.cpu_count,
                'cpu_freq': self.system_info.cpu_freq,
                'memory_total': self.system_info.memory_total,
                'memory_available': self.system_info.memory_available,
                'platform': self.system_info.platform,
                'python_version': self.system_info.python_version
            },
            'environment_vars': self.environment_vars,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(config_dict, f, indent=4)

    @classmethod
    def load_config(cls, filename: str) -> 'ExperimentConfig':
        """Load experiment configuration from a JSON file"""
        with open(filename, 'r') as f:
            config_dict = json.load(f)
        
        system_info = SystemInfo(**config_dict['system_info'])
        return cls(
            thread_counts=config_dict['thread_counts'],
            input_sizes=config_dict['input_sizes'],
            cache_sizes=config_dict['cache_sizes'],
            iterations=config_dict['iterations'],
            metrics=config_dict['metrics'],
            system_info=system_info,
            environment_vars=config_dict['environment_vars']
        ) 
