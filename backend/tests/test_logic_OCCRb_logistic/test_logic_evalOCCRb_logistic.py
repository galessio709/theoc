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

    for i in range(1,11):
        set_filenames.append(f"./tests/data/{chunk}/{log}_{i}.json")

    return set_filenames


# Example usage
name = "ContainerLogistics"
chunk = 100000
file_names = set_filenames(name, chunk)

data_list = process_files(file_names)

# unary
epU1: EventPattern = EventPattern(et='Register Customer Order', phiet={}, op='=', n=1, q='registered CO', ot='Customer Order', phiot={})
fpU1: FlowPattern = FlowPattern(fp ='occurs', opD='>', td=0, psi=[])

# psi = 2 no constraint EP
epA3a: EventPattern = EventPattern(et="Book Vehicles", phiet={}, op="=", n=1, q="VHs booked for TD", ot="Transport Document", phiot={})
fpB3a: FlowPattern = FlowPattern(fp="corequisite", opD=">", td=0, psi=["CR for TD", "TR loads CR"])
epB3a: EventPattern = EventPattern(et="Drive to Terminal", phiet={}, op="=", n=1, q="TR moved", ot="Truck", phiot={})

# psi = 2 yes constraint EP 
epA3b: EventPattern = EventPattern(et="Book Vehicles", phiet={'0': {'attr': 'timestamp', 'op': '<', 'val': '2023-12-31T10:05:16.000Z'}}, op="=", n=1, q="VHs booked for TD", ot="Transport Document", phiot={})
fpB3b: FlowPattern = FlowPattern(fp="corequisite", opD=">", td=0, psi=["CR for TD", "TR loads CR"])
epB3b: EventPattern = EventPattern(et="Drive to Terminal", phiet={}, op="=", n=1, q="TR moved", ot="Truck", phiot={})

# psi = 1 no constraint EP
epA2a: EventPattern = EventPattern(et='Register Customer Order', phiet={}, op="=", n=1, q="registered CO", ot='Customer Order', phiot={})
fpB2a: FlowPattern = FlowPattern(fp="precedes", opD=">", td=0, psi=["TD for CO"])
epB2a: EventPattern = EventPattern(et="Create Transport Document", phiet={}, op="=", n=1, q="created TD", ot="Transport Document", phiot={})

# psi = 1 yes constraint EP
epA2b: EventPattern = EventPattern(et='Register Customer Order', phiet={'0': {'attr': 'timestamp', 'op': '<', 'val': '2023-12-31T10:05:16.000Z'}}, op="=", n=1, q="registered CO", ot='Customer Order', phiot={})
fpB2b: FlowPattern = FlowPattern(fp="precedes", opD=">", td=0, psi=["TD for CO"])
epB2b: EventPattern = EventPattern(et="Create Transport Document", phiet={}, op="=", n=1, q="created TD", ot="Transport Document", phiot={})

# xLeadsTo psi = 1 no constraint EP
epA4: EventPattern = EventPattern(et='Register Customer Order', phiet={}, op="=", n=1, q="registered CO", ot='Customer Order', phiot={})
fpB4: FlowPattern = FlowPattern(fp="xLeadsTo", opD=">", td=0, psi=["TD for CO"])
epB4: EventPattern = EventPattern(et="Create Transport Document", phiet={}, op="=", n=1, q="created TD", ot="Transport Document", phiot={})

'''
pytest tests/test_logic_OCCRb_logistic --benchmark-json tests/results/benchmark_results_log.json --benchmark-histogram tests/results/benchmark_plot_log
'''

# Helper function to initialize test data
def setup_test_data(test_case):
    """Initialize global variables with test dataset."""
    logic.objects = test_case["objects"]
    logic.events = test_case["events"]

@pytest.fixture(autouse=True)
def cleanup():
    yield  # Run the test first
    gc.collect()  # Force garbage collection after each test

@pytest.mark.parametrize("dataset", data_list)
def test_u_log(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    # start_time = time.time()
    benchmark(lambda: logic.evalOCCRu(epU1, fpU1))
    # elapsed_time = time.time() - start_time

    # print(f"evalOCCRb - Dataset size: {len(dataset['objects'])} objects, {len(dataset['events'])} events")
    # print(f"Execution Time: {elapsed_time:.4f} seconds")

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRu(epU1, fpU1)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # print(f"Memory Usage: {memory_usage[1] / 1024:.2f} KB")

    eA = logic.evalP(epU1.et, epU1.phiet, epU1.op, epU1.n, epU1.q, epU1.ot, epU1.phiot)
    # eB = logic.evalP(epB2a.et, epB2a.phiet, epB2a.op, epB2a.n, epB2a.q, epB2a.ot, epB2a.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "u"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = 0 # len(eB)
    benchmark.extra_info["|psi|"] = 0 # len(fpB2a.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_b_log_2a(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    # start_time = time.time()
    benchmark(lambda: logic.evalOCCRb(epA2a, fpB2a, epB2a))
    # elapsed_time = time.time() - start_time

    # print(f"evalOCCRb - Dataset size: {len(dataset['objects'])} objects, {len(dataset['events'])} events")
    # print(f"Execution Time: {elapsed_time:.4f} seconds")

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA2a, fpB2a, epB2a)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # print(f"Memory Usage: {memory_usage[1] / 1024:.2f} KB")

    eA = logic.evalP(epA2a.et, epA2a.phiet, epA2a.op, epA2a.n, epA2a.q, epA2a.ot, epA2a.phiot)
    eB = logic.evalP(epB2a.et, epB2a.phiet, epB2a.op, epB2a.n, epB2a.q, epB2a.ot, epB2a.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "b_simple"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB2a.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_b_log_2b(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)
    
    # Performance Benchmarking
    # start_time = time.time()
    benchmark(lambda: logic.evalOCCRb(epA2b, fpB2b, epB2b))
    # elapsed_time = time.time() - start_time

    # print(f"evalOCCRb - Dataset size: {len(dataset['objects'])} objects, {len(dataset['events'])} events")
    # print(f"Execution Time: {elapsed_time:.4f} seconds")

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA2b, fpB2b, epB2b)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # print(f"Memory Usage: {memory_usage[1] / 1024:.2f} KB")

    eA = logic.evalP(epA2b.et, epA2b.phiet, epA2b.op, epA2b.n, epA2b.q, epA2b.ot, epA2b.phiot)
    eB = logic.evalP(epB2b.et, epB2b.phiet, epB2b.op, epB2b.n, epB2b.q, epB2b.ot, epB2b.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "b_simple_filt"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB2b.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_b_log_3a(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    # start_time = time.time()
    benchmark(lambda: logic.evalOCCRb(epA3a, fpB3a, epB3b))
    # elapsed_time = time.time() - start_time

    # print(f"evalOCCRb - Dataset size: {len(dataset['objects'])} objects, {len(dataset['events'])} events")
    # print(f"Execution Time: {elapsed_time:.4f} seconds")

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA3a, fpB3a, epB3a)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # print(f"Memory Usage: {memory_usage[1] / 1024:.2f} KB")

    eA = logic.evalP(epA3a.et, epA3a.phiet, epA3a.op, epA3a.n, epA3a.q, epA3a.ot, epA3a.phiot)
    eB = logic.evalP(epB3a.et, epB3a.phiet, epB3a.op, epB3a.n, epB3a.q, epB3a.ot, epB3a.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "b_int"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB3a.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_b_log_3b(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    # start_time = time.time()
    benchmark(lambda: logic.evalOCCRb(epA3b, fpB3b, epB3b))
    # elapsed_time = time.time() - start_time

    # print(f"evalOCCRb - Dataset size: {len(dataset['objects'])} objects, {len(dataset['events'])} events")
    # print(f"Execution Time: {elapsed_time:.4f} seconds")

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA3b, fpB3b, epB3b)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # print(f"Memory Usage: {memory_usage[1] / 1024:.2f} KB")

    eA = logic.evalP(epA3b.et, epA3b.phiet, epA3b.op, epA3b.n, epA3b.q, epA3b.ot, epA3b.phiot)
    eB = logic.evalP(epB3b.et, epB3b.phiet, epB3b.op, epB3b.n, epB3b.q, epB3b.ot, epB3b.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "b_int_filt"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB3b.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"

@pytest.mark.parametrize("dataset", data_list)
def test_b_log_4(benchmark, dataset):
    """Test evalOCCRb for correctness and scalability."""
    setup_test_data(dataset)

    # Performance Benchmarking
    # start_time = time.time()
    benchmark(lambda: logic.evalOCCRb(epA4, fpB4, epB4))
    # elapsed_time = time.time() - start_time

    # print(f"evalOCCRb - Dataset size: {len(dataset['objects'])} objects, {len(dataset['events'])} events")
    # print(f"Execution Time: {elapsed_time:.4f} seconds")

    # Memory Profiling
    tracemalloc.start()
    logic.evalOCCRb(epA4, fpB4, epB4)
    memory_usage = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # print(f"Memory Usage: {memory_usage[1] / 1024:.2f} KB")

    eA = logic.evalP(epA4.et, epA4.phiet, epA4.op, epA4.n, epA4.q, epA4.ot, epA4.phiot)
    eB = logic.evalP(epB4.et, epB4.phiet, epB4.op, epB4.n, epB4.q, epB4.ot, epB4.phiot)
    # Add extra info to benchmark results
    benchmark.extra_info["Event log"] = name
    benchmark.extra_info["Rule id"] = "b_compl"
    benchmark.extra_info["|events|"] = len(dataset['events'])
    benchmark.extra_info["|objects|"] = len(dataset['objects'])
    benchmark.extra_info["|epA|"] = len(eA)
    benchmark.extra_info["|epB|"] = len(eB)
    benchmark.extra_info["|psi|"] = len(fpB4.psi)
    benchmark.extra_info["memory_used"] = f"{memory_usage[1] / 1024:.2f} KB"