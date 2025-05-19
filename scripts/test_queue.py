# app/scripts/test_queue.py
import os
import sys
import time
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from redis import Redis
from rq import Queue, Worker

def test_func(x):
    "
