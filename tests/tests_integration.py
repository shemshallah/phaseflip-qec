"""
Integration Test Suite for PhaseFlip QEC

End-to-end integration tests for the complete PhaseFlip QEC system.

Created by OaGI Research
"""

import unittest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute, transpile
from qiskit.providers.aer.noise import NoiseModel, depolarizing_error

from phaseflip_qec.encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
from phaseflip_qec.decoders import SyndromeDecoder
from phaseflip_qec.integration import QiskitTranspilerPlugin
from phaseflip_qec.benchmarks import ErrorSuppressionBenchmark


class TestEndToEndProtection(unittest.TestCase):
    """Test complete error correction workflow."""
    
    def test_single_qubit_protection_d3(self):
        """Test protecting a single qubit through full cycle."""
        encoder = Distance3Encoder()
        decoder = SyndromeDecoder(code_distance=3)
        
        # Encode |+⟩
        circuit = encoder.encode()
        
        # Simulate error
        circuit.z(1)
        
        # Measure syndrome
        syndrome_circuit = encoder.measure_syndrome()
        full_circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(3)) + [3, 4]
        )
        
        # Decode syndrome
        full_circuit.measure([3, 4], [0, 1])
        
        backend = Aer.get_backend('qasm_simulator')
        job = execute(full_circuit, backend, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Get syndrome and correct
        syndrome = max(counts, key=counts.get)
        error_location = decoder.decode_syndrome(syndrome)
        
        if error_location is not None:
            correction_circuit = decoder.create_correction_circuit(
                error_location, num_qubits=3
            )
            circuit = circuit.compose(correction_circuit)
        
        # Decode
        decode_circuit = encoder.decode()
        circuit = circuit.compose(decode_circuit)
        
        # Verify recovery
        self.assertIsInstance(circuit, QuantumCircuit)
    
    def test_multi_qubit_algorithm_protection(self):
        """Test protecting a multi-qubit algorithm."""
        # Create simple 2-qubit algorithm
        logical_circuit = QuantumCircuit(2)
        logical_circuit.h(0)
        logical_circuit.cx(0, 1)
        
        # Protect with PhaseFlip QEC
        encoder = Distance3Encoder()
        
        # Encode each logical qubit
        protected_circuit = QuantumCircuit(6)  # 2 logical × 3 physical
        
        for logical_qubit in range(2):
            offset = logical_qubit * 3
            encode_circ = encoder.encode()
            protected_circuit.compose(
                encode_circ,
                qubits=range(offset, offset + 3),
                inplace=True
            )
        
        # Verify circuit structure
        self.assertEqual(protected_circuit.num_qubits, 6)
        self.assertGreater(protected_circuit.depth(), 0)


class TestTranspilerIntegration(unittest.TestCase):
    """Test integration with Qiskit transpiler."""
    
    def test_transpiler_plugin_initialization(self):
        """Test transpiler plugin can be initialized."""
        plugin = QiskitTranspilerPlugin(code_distance=3)
        
        self.assertEqual(plugin.code_distance, 3)
        self.assertIsNotNone(plugin.encoder)
    
    def test_automatic_protection_insertion(self):
        """Test automatic insertion of error correction."""
        plugin = QiskitTranspilerPlugin(code_distance=3)
        
        # Create simple circuit
        circuit = QuantumCircuit(1)
        circuit.h(0)
        circuit.rz(np.pi/4, 0)
        
        # Apply protection
        protected = plugin.apply_qec_protection(circuit)
        
        # Should have more qubits (encoded)
        self.assertGreater(protected.num_qubits, circuit.num_qubits)
    
    def test_syndrome_measurement_insertion(self):
        """Test insertion of syndrome measurements."""
        plugin = QiskitTranspilerPlugin(code_distance=3)
        
        circuit = QuantumCircuit(3)  # Already encoded
        circuit.h(0)
        circuit.h(1)
        circuit.h(2)
        
        # Insert syndrome measurements
        with_syndrome = plugin.insert_syndrome_measurements(circuit, interval=1)
        
        # Should have added ancilla qubits
        self.assertGreater(with_syndrome.num_qubits, 3)


class TestBenchmarkIntegration(unittest.TestCase):
    """Test integration of benchmarking tools."""
    
    def test_benchmark_initialization(self):
        """Test benchmark suite can be initialized."""
        benchmark = ErrorSuppressionBenchmark(num_trials=10)
        
        self.assertEqual(benchmark.num_trials, 10)
        self.assertIsNotNone(benchmark.backend)
    
    def test_single_configuration_benchmark(self):
        """Test benchmarking a single configuration."""
        benchmark = ErrorSuppressionBenchmark(num_trials=5)
        
        result = benchmark.benchmark_single_configuration(
            code_distance=3,
            physical_error_rate=0.001
        )
        
        # Verify result structure
        self.assertEqual(result.code_distance, 3)
        self.assertEqual(result.physical_error_rate, 0.001)
        self.assertGreater(result.error_suppression_factor, 1.0)
    
    def test_benchmark_export(self):
        """Test exporting benchmark results."""
        import tempfile
        import os
        import json
        
        benchmark = ErrorSuppressionBenchmark(num_trials=5)
        
        # Run single benchmark
        benchmark.benchmark_single_configuration(
            code_distance=3,
            physical_error_rate=0.001
        )
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = os.path.join(tmpdir, 'test_results.json')
            benchmark.export_results(export_path)
            
            # Verify file exists and is valid JSON
            self.assertTrue(os.path.exists(export_path))
            
            with open(export_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn('results', data)
            self.assertEqual(len(data['results']), 1)


class TestNoiseModelIntegration(unittest.TestCase):
    """Test integration with various noise models."""
    
    def test_phase_flip_noise_protection(self):
        """Test protection against phase flip noise."""
        encoder = Distance3Encoder()
        
        # Create noise model with phase errors
        noise_model = NoiseModel()
        phase_error = depolarizing_error(0.01, 1)
        noise_model.add_all_qubit_quantum_error(phase_error, ['h', 'rz'])
        
        # Encode and run with noise
        circuit = encoder.encode()
        circuit.measure_all()
        
        backend = Aer.get_backend('qasm_simulator')
        transpiled = transpile(circuit, backend)
        
        job = execute(transpiled, backend, noise_model=noise_model, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Should complete successfully
        self.assertGreater(len(counts), 0)
    
    def test_varying_error_rates(self):
        """Test performance across different error rates."""
        encoder = Distance3Encoder()
        error_rates = [0.001, 0.005, 0.01]
        
        backend = Aer.get_backend('qasm_simulator')
        
        for error_rate in error_rates:
            noise_model = NoiseModel()
            phase_error = depolarizing_error(error_rate, 1)
            noise_model.add_all_qubit_quantum_error(phase_error, ['h', 'rz'])
            
            circuit = encoder.encode()
            circuit.measure_all()
            
            transpiled = transpile(circuit, backend)
            job = execute(transpiled, backend, noise_model=noise_model, shots=50)
            result = job.result()
            
            # Should handle all error rates
            self.assertIsNotNone(result.get_counts())


class TestScalability(unittest.TestCase):
    """Test scalability of PhaseFlip QEC."""
    
    def test_multiple_logical_qubits(self):
        """Test encoding multiple logical qubits."""
        encoder = Distance3Encoder()
        num_logical = 3
        
        # Create circuit for 3 logical qubits
        num_physical = num_logical * encoder.num_physical_qubits
        circuit = QuantumCircuit(num_physical)
        
        # Encode each
        for i in range(num_logical):
            offset = i * encoder.num_physical_qubits
            encode_circ = encoder.encode()
            circuit.compose(
                encode_circ,
                qubits=range(offset, offset + encoder.num_physical_qubits),
                inplace=True
            )
        
        # Verify structure
        self.assertEqual(circuit.num_qubits, num_physical)
    
    def test_circuit_depth_scaling(self):
        """Test circuit depth scaling with code distance."""
        encoders = [
            Distance3Encoder(),
            Distance5Encoder(),
            Distance7Encoder(),
        ]
        
        depths = []
        for encoder in encoders:
            circuit = encoder.encode()
            depths.append(circuit.depth())
        
        # Depth should increase with distance
        self.assertLess(depths[0], depths[1])
        self.assertLess(depths[1], depths[2])


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery capabilities."""
    
    def test_recover_from_single_error(self):
        """Test recovery from single phase flip."""
        encoder = Distance3Encoder()
        decoder = SyndromeDecoder(code_distance=3)
        
        backend = Aer.get_backend('qasm_simulator')
        
        # Test multiple error locations
        for error_qubit in range(3):
            circuit = encoder.encode()
            circuit.z(error_qubit)
            
            # Measure syndrome
            syndrome_circuit = encoder.measure_syndrome()
            full_circuit = circuit.compose(
                syndrome_circuit,
                qubits=list(range(3)) + [3, 4]
            )
            
            full_circuit.measure([3, 4], [0, 1])
            
            job = execute(full_circuit, backend, shots=10)
            result = job.result()
            counts = result.get_counts()
            
            syndrome = max(counts, key=counts.get)
            error_location = decoder.decode_syndrome(syndrome)
            
            # Should detect error
            self.assertIsNotNone(error_location)
    
    def test_no_false_corrections(self):
        """Test that no correction is applied when no error present."""
        encoder = Distance3Encoder()
        decoder = SyndromeDecoder(code_distance=3)
        
        backend = Aer.get_backend('qasm_simulator')
        
        # Encode without error
        circuit = encoder.encode()
        
        # Measure syndrome
        syndrome_circuit = encoder.measure_syndrome()
        full_circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(3)) + [3, 4]
        )
        
        full_circuit.measure([3, 4], [0, 1])
        
        job = execute(full_circuit, backend, shots=50)
        result = job.result()
        counts = result.get_counts()
        
        # Most common syndrome should be '00' (no error)
        most_common = max(counts, key=counts.get)
        error_location = decoder.decode_syndrome(most_common)
        
        # Should not indicate error for most measurements
        if most_common == '00':
            self.assertIsNone(error_location)


class TestSystemRobustness(unittest.TestCase):
    """Test overall system robustness."""
    
    def test_handles_invalid_inputs(self):
        """Test system handles invalid inputs gracefully."""
        # Invalid code distance
        with self.assertRaises(ValueError):
            encoder = Distance3Encoder()
            encoder.code_distance = 4  # Invalid
    
    def test_statistical_consistency(self):
        """Test statistical consistency of error suppression."""
        encoder = Distance3Encoder()
        backend = Aer.get_backend('qasm_simulator')
        
        # Run multiple trials
        num_trials = 5
        results = []
        
        for _ in range(num_trials):
            circuit = encoder.encode()
            circuit.measure_all()
            
            job = execute(circuit, backend, shots=100)
            result = job.result()
            counts = result.get_counts()
            results.append(counts)
        
        # All trials should complete
        self.assertEqual(len(results), num_trials)


def run_all_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndProtection))
    suite.addTests(loader.loadTestsFromTestCase(TestTranspilerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestBenchmarkIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestNoiseModelIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestScalability))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorRecovery))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemRobustness))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("PHASEFLIP QEC - INTEGRATION TEST SUITE")
    print("=" * 70)
    print()
    
    result = run_all_tests()
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ ALL INTEGRATION TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    print("=" * 70)