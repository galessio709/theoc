import json
import pytest
import backend.logic as logic
import time
import tracemalloc  # For memory profiling
from pydantic import BaseModel
import gc

data: dict = {}
objects: dict = {}
events: dict = {} 

class EventPattern(BaseModel):
    et: str
    phiet: dict
    op: str
    n: int
    q: str
    ot: str
    phiot: dict

class FlowPattern(BaseModel):
    fp: str
    opD: str
    td: int
    psi: list

# Sample test datasets
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        exit(999)

def process_files(file_list):
    data_list = []
    
    for idx, file_path in enumerate(file_list, start=1):
        data = load_json(file_path)
        objects = {obj['id']: obj for obj in data.get("objects", [])}
        events = {obj['id']: obj for obj in data.get("events", [])}
        
        data_list.append({
            "objects": objects,
            "events": events
        })
        print(f"Processed {file_path} as data_{idx}")
    
    return data_list

def set_filenames(log, chunk):
    set_filenames = []

    for i in range(1,8):
        set_filenames.append(f"./tests/data/{chunk}/{log}_{i}.json")

    return set_filenames

name = "Procure2Payment"
chunk = 2000
file_names = set_filenames(name, chunk)

data_list = process_files(file_names)

# unary
epU1: EventPattern = EventPattern(et='Create Invoice Receipt', phiet={}, op='=', n=1, q='invoice receipt', ot='invoice receipt', phiot={})
fpU1: FlowPattern = FlowPattern(fp ='occurs', opD='>', td=0, psi=[])

# psi = 2 no constraint EP
epA3a: EventPattern = EventPattern(et="Create Goods Receipt", phiet={}, op="=", n=1, q="goods receipt", ot="goods receipt", phiot={})
fpB3a: FlowPattern = FlowPattern(fp="precedes", opD=">", td=0, psi=["Invoice Receipt of Goods Receipt", "invoice_receipt_pm"])
epB3a: EventPattern = EventPattern(et="Execute Payment", phiet={}, op="=", n=1, q="payment", ot="payment", phiot={})

# psi = 2 yes constraint EP 
epA3b: EventPattern = EventPattern(et="Create Goods Receipt", phiet={'0': {'attr': 'timestamp', 'op': '<', 'val': '2023-07-28T08:37:00.000Z'}}, op="=", n=1, q="goods receipt", ot="goods receipt", phiot={})
fpB3b: FlowPattern = FlowPattern(fp="precedes", opD=">", td=0, psi=["Invoice Receipt of Goods Receipt", "invoice_receipt_pm"])
epB3b: EventPattern = EventPattern(et="Execute Payment", phiet={}, op="=", n=1, q="payment", ot="payment", phiot={})

# psi = 1 no constraint EP
epA2a: EventPattern = EventPattern(et='Create Invoice Receipt', phiet={}, op="=", n=1, q="invoice receipt", ot='invoice receipt', phiot={})
fpB2a: FlowPattern = FlowPattern(fp="precedes", opD=">", td=0, psi=["invoice_receipt_pm"])
epB2a: EventPattern = EventPattern(et="Execute Payment", phiet={}, op="=", n=1, q="payment", ot="payment", phiot={})

# psi = 1 yes constraint EP
epA2b: EventPattern = EventPattern(et='Create Invoice Receipt', phiet={'0': {'attr': 'timestamp', 'op': '<', 'val': '2023-07-28T08:37:00.000Z'}}, op="=", n=1, q="invoice receipt", ot='invoice receipt', phiot={})
fpB2b: FlowPattern = FlowPattern(fp="precedes", opD=">", td=0, psi=["invoice_receipt_pm"])
epB2b: EventPattern = EventPattern(et="Execute Payment", phiet={}, op="=", n=1, q="payment", ot="payment", phiot={})

# Helper function to initialize test data
def setup_test_data(test_case):
    """Initialize global variables with test dataset."""
    logic.objects = test_case["objects"]
    logic.events = test_case["events"]

@pytest.fixture(autouse=True)
def cleanup():
    yield  
    gc.collect() 

@pytest.mark.parametrize("dataset", data_list)
def test_R1_p2p(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    benchmark(lambda: logic.evalOCCRu(epU1, fpU1))

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRu(epU1, fpU1)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()


    eA = logic.evalP(epU1.et, epU1.phiet, epU1.op, epU1.n, epU1.q, epU1.ot, epU1.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "R1"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = 0 # len(eB)
    benchmark.extra_info["|psi|"] = 0 # len(fpU1.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_R3_p2p(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    benchmark(lambda: logic.evalOCCRb(epA2a, fpB2a, epB2a))

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA2a, fpB2a, epB2a)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    eA = logic.evalP(epA2a.et, epA2a.phiet, epA2a.op, epA2a.n, epA2a.q, epA2a.ot, epA2a.phiot)
    eB = logic.evalP(epB2a.et, epB2a.phiet, epB2a.op, epB2a.n, epB2a.q, epB2a.ot, epB2a.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "R3"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB2a.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_R2_p2p(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    benchmark(lambda: logic.evalOCCRb(epA2b, fpB2b, epB2b))

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA2b, fpB2b, epB2b)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    eA = logic.evalP(epA2b.et, epA2b.phiet, epA2b.op, epA2b.n, epA2b.q, epA2b.ot, epA2b.phiot)
    eB = logic.evalP(epB2b.et, epB2b.phiet, epB2b.op, epB2b.n, epB2b.q, epB2b.ot, epB2b.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "R2"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB2b.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_R5_p2p(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    benchmark(lambda: logic.evalOCCRb(epA3a, fpB3a, epB3a))

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA3a, fpB3a, epB3a)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    eA = logic.evalP(epA3a.et, epA3a.phiet, epA3a.op, epA3a.n, epA3a.q, epA3a.ot, epA3a.phiot)
    eB = logic.evalP(epB3a.et, epB3a.phiet, epB3a.op, epB3a.n, epB3a.q, epB3a.ot, epB3a.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "R5"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB3a.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_R4_p2p(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    benchmark(lambda: logic.evalOCCRb(epA3b, fpB3b, epB3b))

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA3b, fpB3b, epB3b)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    eA = logic.evalP(epA3b.et, epA3b.phiet, epA3b.op, epA3b.n, epA3b.q, epA3b.ot, epA3b.phiot)
    eB = logic.evalP(epB3b.et, epB3b.phiet, epB3b.op, epB3b.n, epB3b.q, epB3b.ot, epB3b.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "R4"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB3b.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"
