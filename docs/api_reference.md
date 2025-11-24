# API Reference - PhaseFlip QEC

Complete API documentation for PhaseFlip Quantum Error Correction package.

---

## Table of Contents

1. [Encoders](#encoders)
2. [Decoders](#decoders)
3. [Integration](#integration)
4. [Benchmarks](#benchmarks)
5. [Utilities](#utilities)

---

## Encoders

### `Distance3Encoder`

Distance-3 PhaseFlip QEC encoder for correcting single phase-flip errors.

#### Class Definition
```python
class Distance3Encoder(PhaseFlipEncoder):
    """Distance-3 PhaseFlip quantum error correction encoder."""
```

#### Attributes
- `code_distance` (int): Code distance = 3
- `num_physical_qubits` (int): Number of physical qubits = 3
- `num_ancilla_qubits` (int): Number of ancilla qubits = 2
- `max_correctable_errors` (int): Maximum correctable errors = 1

#### Methods

##### `encode() -> QuantumCircuit`
Encode logical |+⟩ state into distance-3 PhaseFlip code.

**Returns:**
- `QuantumCircuit`: Encoded quantum circuit

**Example:**
```python
from phaseflip_qec.encoders import Distance3Encoder

encoder = Distance3Encoder()
circuit = encoder.encode()
print(f"Circuit depth: {circuit.depth()}")
```

##### `decode() -> QuantumCircuit`
Decode physical qubits back to logical qubit.

**Returns:**
- `QuantumCircuit`: Decoding circuit

**Example:**
```python
decode_circuit = encoder.decode()
```

##### `measure_syndrome() -> QuantumCircuit`
Create syndrome measurement circuit.

**Returns:**
- `QuantumCircuit`: Syndrome measurement circuit with ancilla qubits

**Example:**
```python
syndrome_circuit = encoder.measure_syndrome()
# Compose with encoded circuit
full_circuit = encoded_circuit.compose(
    syndrome_circuit,
    qubits=list(range(3)) + [3, 4]
)
```

##### `estimate_logical_error_rate(physical_error_rate: float) -> float`
Estimate logical error rate from physical error rate.

**Parameters:**
- `physical_error_rate` (float): Physical qubit error rate (0 to 1)

**Returns:**
- `float`: Estimated logical error rate

**Example:**
```python
p_physical = 0.001
p_logical = encoder.estimate_logical_error_rate(p_physical)
suppression = p_physical / p_logical
print(f"Error suppression: {suppression:,.0f}×")
```

---

### `Distance5Encoder`

Distance-5 PhaseFlip QEC encoder for correcting up to 2 phase-flip errors.

#### Class Definition
```python
class Distance5Encoder(PhaseFlipEncoder):
    """Distance-5 PhaseFlip quantum error correction encoder."""
```

#### Attributes
- `code_distance` (int): Code distance = 5
- `num_physical_qubits` (int): Number of physical qubits = 5
- `num_ancilla_qubits` (int): Number of ancilla qubits = 4
- `max_correctable_errors` (int): Maximum correctable errors = 2

#### Methods
Same interface as `Distance3Encoder` but with enhanced error correction.

**Example:**
```python
from phaseflip_qec.encoders import Distance5Encoder

encoder = Distance5Encoder()
circuit = encoder.encode()

# Higher suppression than distance-3
p_logical = encoder.estimate_logical_error_rate(0.001)
print(f"Logical error rate: {p_logical:.2e}")
```

---

### `Distance7Encoder`

Distance-7 PhaseFlip QEC encoder for correcting up to 3 phase-flip errors.

#### Class Definition
```python
class Distance7Encoder(PhaseFlipEncoder):
    """Distance-7 PhaseFlip quantum error correction encoder."""
```

#### Attributes
- `code_distance` (int): Code distance = 7
- `num_physical_qubits` (int): Number of physical qubits = 7
- `num_ancilla_qubits` (int): Number of ancilla qubits = 6
- `max_correctable_errors` (int): Maximum correctable errors = 3

**Example:**
```python
from phaseflip_qec.encoders import Distance7Encoder

encoder = Distance7Encoder()
circuit = encoder.encode()

# Best error suppression
p_logical = encoder.estimate_logical_error_rate(0.001)
print(f"Logical error rate: {p_logical:.2e}")
```

---

### `AdaptiveEncoder`

Dynamically selects optimal code distance based on error rates.

#### Class Definition
```python
class AdaptiveEncoder:
    """Adaptive encoder that selects code distance based on error rate."""
```

#### Methods

##### `select_distance(error_rate: float, circuit_depth: int = None) -> int`
Select optimal code distance based on error rate.

**Parameters:**
- `error_rate` (float): Measured or estimated physical error rate
- `circuit_depth` (int, optional): Circuit depth for optimization

**Returns:**
- `int`: Recommended code distance (3, 5, or 7)

**Example:**
```python
from phaseflip_qec.encoders import AdaptiveEncoder

adaptive = AdaptiveEncoder()

# Low error rate -> distance 3
distance = adaptive.select_distance(error_rate=0.0001)
print(f"Selected distance: {distance}")  # 3

# High error rate -> distance 7
distance = adaptive.select_distance(error_rate=0.02)
print(f"Selected distance: {distance}")  # 7
```

##### `adaptive_encode(error_rate: float) -> QuantumCircuit`
Automatically encode with optimal distance.

**Parameters:**
- `error_rate` (float): Physical error rate

**Returns:**
- `QuantumCircuit`: Encoded circuit with selected distance

**Example:**
```python
circuit = adaptive.adaptive_encode(error_rate=0.005)
```

##### `adjust_distance_dynamically(measured_error_rate: float) -> int`
Dynamically adjust code distance during execution.

**Parameters:**
- `measured_error_rate` (float): Currently measured error rate

**Returns:**
- `int`: New recommended code distance

**Example:**
```python
# Monitor and adjust
new_distance = adaptive.adjust_distance_dynamically(
    measured_error_rate=0.012
)
```

---

## Decoders

### `SyndromeDecoder`

Classical syndrome-based decoder using lookup tables.

#### Class Definition
```python
class SyndromeDecoder:
    """Classical syndrome-based decoder for PhaseFlip codes."""
```

#### Constructor
```python
def __init__(self, code_distance: int):
    """
    Initialize decoder.
    
    Args:
        code_distance: Code distance (3, 5, or 7)
    """
```

#### Methods

##### `decode_syndrome(syndrome: str) -> Union[int, List[int], None]`
Decode syndrome to error location(s).

**Parameters:**
- `syndrome` (str): Binary syndrome string (e.g., "01", "1010")

**Returns:**
- `int | List[int] | None`: Error qubit location(s) or None if no error

**Example:**
```python
from phaseflip_qec.decoders import SyndromeDecoder

decoder = SyndromeDecoder(code_distance=3)

# Decode syndrome
syndrome = "01"  # From measurement
error_location = decoder.decode_syndrome(syndrome)

if error_location is not None:
    print(f"Error detected on qubit {error_location}")
```

##### `create_correction_circuit(error_location, num_qubits: int) -> QuantumCircuit`
Create correction circuit for detected errors.

**Parameters:**
- `error_location` (int | List[int]): Qubit(s) with errors
- `num_qubits` (int): Total number of qubits

**Returns:**
- `QuantumCircuit`: Correction circuit applying Z gates

**Example:**
```python
# Create correction
correction = decoder.create_correction_circuit(
    error_location=1,
    num_qubits=3
)

# Apply to circuit
circuit.compose(correction, inplace=True)
```

##### `get_statistics() -> Dict`
Get decoding statistics.

**Returns:**
- `Dict`: Statistics including correction counts

**Example:**
```python
stats = decoder.get_statistics()
print(f"Total corrections: {stats['total_corrections']}")
```

---

### `MLDecoder`

Machine learning-based decoder using trained models.

#### Class Definition
```python
class MLDecoder:
    """ML-based decoder for PhaseFlip codes."""
```

#### Constructor
```python
def __init__(self, code_distance: int, model_type: str = 'neural_network'):
    """
    Initialize ML decoder.
    
    Args:
        code_distance: Code distance
        model_type: Type of ML model ('neural_network', 'random_forest')
    """
```

#### Methods

##### `train(X_train: List[str], y_train: List[int], epochs: int = 50)`
Train the ML model.

**Parameters:**
- `X_train` (List[str]): Training syndromes
- `y_train` (List[int]): Training error locations
- `epochs` (int): Training epochs

**Example:**
```python
from phaseflip_qec.decoders import MLDecoder

decoder = MLDecoder(code_distance=3)

# Generate training data
X_train, y_train = decoder.generate_training_data(num_samples=1000)

# Train model
decoder.train(X_train, y_train, epochs=100)
```

##### `predict(syndrome: str) -> Union[int, List[int]]`
Predict error location from syndrome.

**Parameters:**
- `syndrome` (str): Binary syndrome string

**Returns:**
- `int | List[int]`: Predicted error location(s)

**Example:**
```python
# Make prediction
error_location = decoder.predict("01")
print(f"Predicted error on qubit {error_location}")
```

##### `evaluate(X_test: List[str], y_test: List[int]) -> float`
Evaluate model accuracy.

**Parameters:**
- `X_test` (List[str]): Test syndromes
- `y_test` (List[int]): True error locations

**Returns:**
- `float`: Accuracy (0 to 1)

**Example:**
```python
# Generate test data
X_test, y_test = decoder.generate_training_data(num_samples=200)

# Evaluate
accuracy = decoder.evaluate(X_test, y_test)
print(f"Model accuracy: {accuracy:.2%}")
```

##### `save_model(filepath: str)`
Save trained model to file.

**Example:**
```python
decoder.save_model('ml_decoder_d3.pkl')
```

##### `load_model(filepath: str)`
Load trained model from file.

**Example:**
```python
decoder.load_model('ml_decoder_d3.pkl')
```

---

## Integration

### `QiskitTranspilerPlugin`

Integration with Qiskit transpiler for automatic protection.

#### Class Definition
```python
class QiskitTranspilerPlugin:
    """Qiskit transpiler plugin for automatic QEC protection."""
```

#### Constructor
```python
def __init__(
    self,
    code_distance: int = 3,
    syndrome_interval: int = 10,
    auto_adapt: bool = False
):
    """
    Initialize plugin.
    
    Args:
        code_distance: Initial code distance
        syndrome_interval: Gates between syndrome measurements
        auto_adapt: Enable adaptive distance selection
    """
```

#### Methods

##### `apply_qec_protection(circuit: QuantumCircuit) -> QuantumCircuit`
Apply QEC protection to circuit.

**Parameters:**
- `circuit` (QuantumCircuit): Unprotected circuit

**Returns:**
- `QuantumCircuit`: Protected circuit

**Example:**
```python
from phaseflip_qec.integration import QiskitTranspilerPlugin
from qiskit import QuantumCircuit

plugin = QiskitTranspilerPlugin(code_distance=3)

# Original circuit
circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)

# Apply protection
protected = plugin.apply_qec_protection(circuit)
print(f"Physical qubits: {protected.num_qubits}")
```

##### `insert_syndrome_measurements(circuit: QuantumCircuit, interval: int) -> QuantumCircuit`
Insert syndrome measurements at regular intervals.

**Parameters:**
- `circuit` (QuantumCircuit): Encoded circuit
- `interval` (int): Number of gates between measurements

**Returns:**
- `QuantumCircuit`: Circuit with syndrome measurements

**Example:**
```python
with_syndrome = plugin.insert_syndrome_measurements(
    circuit,
    interval=5
)
```

##### `transpile_with_qec(circuit: QuantumCircuit, backend) -> QuantumCircuit`
Transpile with QEC for specific backend.

**Example:**
```python
from qiskit import Aer

backend = Aer.get_backend('qasm_simulator')
transpiled = plugin.transpile_with_qec(circuit, backend)
```

---

## Benchmarks

### `ErrorSuppressionBenchmark`

Comprehensive benchmarking suite.

#### Constructor
```python
def __init__(self, num_trials: int = 100, use_simulator: bool = True):
    """
    Initialize benchmark.
    
    Args:
        num_trials: Trials per configuration
        use_simulator: Use simulator (True) or hardware (False)
    """
```

#### Methods

##### `benchmark_single_configuration(code_distance: int, physical_error_rate: float) -> BenchmarkResult`
Benchmark single configuration.

**Example:**
```python
from phaseflip_qec.benchmarks import ErrorSuppressionBenchmark

benchmark = ErrorSuppressionBenchmark(num_trials=100)

result = benchmark.benchmark_single_configuration(
    code_distance=3,
    physical_error_rate=0.001
)

print(f"Suppression: {result.error_suppression_factor:,.0f}×")
```

##### `benchmark_scaling(code_distances: List[int], physical_error_rates: List[float]) -> List[BenchmarkResult]`
Benchmark multiple configurations.

**Example:**
```python
results = benchmark.benchmark_scaling(
    code_distances=[3, 5, 7],
    physical_error_rates=[0.001, 0.005, 0.01]
)
```

##### `export_results(filename: str)`
Export results to JSON.

**Example:**
```python
benchmark.export_results('benchmark_results.json')
```

---

## Utilities

### Visualization Functions

#### `plot_error_suppression()`
Plot error suppression curves.

**Example:**
```python
from phaseflip_qec.utils import plot_error_suppression

plot_error_suppression(
    physical_error_rates=[0.0001, 0.001, 0.01],
    code_distances=[3, 5, 7],
    save_path='suppression.png'
)
```

#### `plot_syndrome_distribution()`
Plot syndrome measurement distribution.

#### `plot_fidelity_comparison()`
Compare fidelities with/without protection.

#### `create_comparison_dashboard()`
Generate comprehensive comparison dashboard.

---

## Complete Examples

### Full Workflow Example

```python
from phaseflip_qec.encoders import Distance3Encoder
from phaseflip_qec.decoders import SyndromeDecoder
from qiskit import QuantumCircuit, Aer, execute

# Initialize
encoder = Distance3Encoder()
decoder = SyndromeDecoder(code_distance=3)

# Encode
circuit = encoder.encode()

# Simulate error
circuit.z(1)

# Measure syndrome
syndrome_circuit = encoder.measure_syndrome()
full_circuit = circuit.compose(
    syndrome_circuit,
    qubits=list(range(3)) + [3, 4]
)
full_circuit.measure([3, 4], [0, 1])

# Execute
backend = Aer.get_backend('qasm_simulator')
job = execute(full_circuit, backend, shots=100)
result = job.result()
counts = result.get_counts()

# Decode
syndrome = max(counts, key=counts.get)
error_location = decoder.decode_syndrome(syndrome)

# Correct
if error_location is not None:
    correction = decoder.create_correction_circuit(error_location, 3)
    circuit.compose(correction, inplace=True)

# Decode logical qubit
decode_circuit = encoder.decode()
circuit.compose(decode_circuit, inplace=True)
```

---

## Error Handling

All functions raise appropriate exceptions:
- `ValueError`: Invalid parameters
- `RuntimeError`: Execution errors
- `ImportError`: Missing dependencies

---

For more examples, see the `examples/` directory in the repository.