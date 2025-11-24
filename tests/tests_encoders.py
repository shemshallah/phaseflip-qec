"""
Test Suite for PhaseFlip QEC Encoders

Comprehensive tests for all encoder implementations.

Created by OaGI Research
"""

import unittest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute, transpile
from qiskit.quantum_info import Statevector, state_fidelity
from qiskit.providers.aer.noise import NoiseModel, phase_amplitude_damping_error

from phaseflip_qec.encoders import (
    Distance3Encoder,
    Distance5Encoder,
    Distance7Encoder,
    AdaptiveEncoder
)


class TestDistance3Encoder(unittest.TestCase):
    """Test cases for Distance-3 PhaseFlip encoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = Distance3Encoder()
        self.backend = Aer.get_backend('statevector_simulator')
    
    def test_initialization(self):
        """Test encoder initialization."""
        self.assertEqual(self.encoder.code_distance, 3)
        self.assertEqual(self.encoder.num_physical_qubits, 3)
        self.assertEqual(self.encoder.num_ancilla_qubits, 2)
        self.assertEqual(self.encoder.max_correctable_errors, 1)
    
    def test_encode_circuit_structure(self):
        """Test encoding circuit creates proper structure."""
        circuit = self.encoder.encode()
        
        # Check number of qubits
        self.assertEqual(circuit.num_qubits, 3)
        
        # Check circuit depth is reasonable
        self.assertGreater(circuit.depth(), 0)
        self.assertLess(circuit.depth(), 10)
    
    def test_encode_creates_equal_superposition(self):
        """Test that encoding |+⟩ creates proper encoded state."""
        circuit = self.encoder.encode()
        
        # Execute
        job = execute(circuit, self.backend)
        result = job.result()
        statevector = result.get_statevector()
        
        # Check all-zeros and all-ones have equal amplitude
        amplitude_000 = abs(statevector[0])
        amplitude_111 = abs(statevector[7])
        
        self.assertAlmostEqual(amplitude_000, amplitude_111, places=5)
    
    def test_syndrome_measurement_circuit(self):
        """Test syndrome measurement circuit structure."""
        circuit = self.encoder.measure_syndrome()
        
        # Should have 3 data qubits + 2 ancilla qubits
        self.assertEqual(circuit.num_qubits, 5)
        
        # Should have measurements on ancilla qubits
        self.assertEqual(circuit.num_clbits, 2)
    
    def test_single_error_detection(self):
        """Test that single phase flip is detectable."""
        # Create encoded state
        circuit = self.encoder.encode()
        
        # Introduce single phase flip on qubit 0
        circuit.z(0)
        
        # Add syndrome measurement
        syndrome_circuit = self.encoder.measure_syndrome()
        circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(3)) + [3, 4]
        )
        
        # Execute
        backend = Aer.get_backend('qasm_simulator')
        circuit.measure([3, 4], [0, 1])
        job = execute(circuit, backend, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Syndrome should be non-zero
        self.assertNotIn('00', counts.keys() if counts else [])
    
    def test_error_rate_estimation(self):
        """Test logical error rate estimation."""
        physical_error_rate = 0.001
        logical_error_rate = self.encoder.estimate_logical_error_rate(physical_error_rate)
        
        # Logical error should be less than physical error
        self.assertLess(logical_error_rate, physical_error_rate)
        
        # Check approximate scaling (should be ~ p^2 for d=3)
        expected = 3 * physical_error_rate**2
        self.assertAlmostEqual(logical_error_rate, expected, delta=expected * 0.1)
    
    def test_decode_recovers_logical_qubit(self):
        """Test that decode operation properly recovers logical qubit."""
        # Encode
        encode_circuit = self.encoder.encode()
        
        # Decode
        decode_circuit = self.encoder.decode()
        
        # Full circuit
        full_circuit = encode_circuit.compose(decode_circuit)
        
        # Execute
        job = execute(full_circuit, self.backend)
        result = job.result()
        statevector = result.get_statevector()
        
        # Should recover |+⟩ state on first qubit
        # Check that probability of |0⟩ and |1⟩ on first qubit are equal
        prob_0 = sum(abs(statevector[i])**2 for i in range(len(statevector)) 
                    if (i & 4) == 0)  # Qubit 0 is |0⟩
        
        self.assertAlmostEqual(prob_0, 0.5, places=5)


class TestDistance5Encoder(unittest.TestCase):
    """Test cases for Distance-5 PhaseFlip encoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = Distance5Encoder()
        self.backend = Aer.get_backend('statevector_simulator')
    
    def test_initialization(self):
        """Test encoder initialization."""
        self.assertEqual(self.encoder.code_distance, 5)
        self.assertEqual(self.encoder.num_physical_qubits, 5)
        self.assertEqual(self.encoder.num_ancilla_qubits, 4)
        self.assertEqual(self.encoder.max_correctable_errors, 2)
    
    def test_error_rate_scaling(self):
        """Test that distance-5 has better scaling than distance-3."""
        d3_encoder = Distance3Encoder()
        
        physical_error_rate = 0.001
        
        d3_logical = d3_encoder.estimate_logical_error_rate(physical_error_rate)
        d5_logical = self.encoder.estimate_logical_error_rate(physical_error_rate)
        
        # Distance-5 should have lower logical error
        self.assertLess(d5_logical, d3_logical)
    
    def test_two_error_correction(self):
        """Test that two errors can be corrected."""
        # This is a simplified test - full test would require decoder
        circuit = self.encoder.encode()
        
        # Apply two phase flips
        circuit.z(0)
        circuit.z(1)
        
        # Measure syndrome
        syndrome_circuit = self.encoder.measure_syndrome()
        full_circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(5)) + list(range(5, 9))
        )
        
        # Should detect errors (non-zero syndrome)
        backend = Aer.get_backend('qasm_simulator')
        full_circuit.measure(list(range(5, 9)), list(range(4)))
        job = execute(full_circuit, backend, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Syndrome should indicate errors
        self.assertNotIn('0000', counts.keys() if counts else [])


class TestDistance7Encoder(unittest.TestCase):
    """Test cases for Distance-7 PhaseFlip encoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = Distance7Encoder()
    
    def test_initialization(self):
        """Test encoder initialization."""
        self.assertEqual(self.encoder.code_distance, 7)
        self.assertEqual(self.encoder.num_physical_qubits, 7)
        self.assertEqual(self.encoder.num_ancilla_qubits, 6)
        self.assertEqual(self.encoder.max_correctable_errors, 3)
    
    def test_superior_error_suppression(self):
        """Test that distance-7 provides best error suppression."""
        d3_encoder = Distance3Encoder()
        d5_encoder = Distance5Encoder()
        
        physical_error_rate = 0.001
        
        d3_logical = d3_encoder.estimate_logical_error_rate(physical_error_rate)
        d5_logical = d5_encoder.estimate_logical_error_rate(physical_error_rate)
        d7_logical = self.encoder.estimate_logical_error_rate(physical_error_rate)
        
        # Distance-7 should have lowest logical error
        self.assertLess(d7_logical, d5_logical)
        self.assertLess(d5_logical, d3_logical)


class TestAdaptiveEncoder(unittest.TestCase):
    """Test cases for Adaptive PhaseFlip encoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = AdaptiveEncoder()
    
    def test_distance_selection_low_error(self):
        """Test that low error rates select distance-3."""
        distance = self.encoder.select_distance(error_rate=0.0001)
        self.assertEqual(distance, 3)
    
    def test_distance_selection_medium_error(self):
        """Test that medium error rates select distance-5."""
        distance = self.encoder.select_distance(error_rate=0.005)
        self.assertEqual(distance, 5)
    
    def test_distance_selection_high_error(self):
        """Test that high error rates select distance-7."""
        distance = self.encoder.select_distance(error_rate=0.02)
        self.assertEqual(distance, 7)
    
    def test_adaptive_encoding(self):
        """Test adaptive encoding returns proper circuit."""
        circuit = self.encoder.adaptive_encode(error_rate=0.001)
        
        # Should return a valid circuit
        self.assertIsInstance(circuit, QuantumCircuit)
        self.assertGreater(circuit.num_qubits, 0)
    
    def test_dynamic_adjustment(self):
        """Test dynamic distance adjustment based on measured errors."""
        # Start with distance 3
        self.encoder.current_distance = 3
        
        # Simulate high error rate
        measured_error_rate = 0.015
        
        # Should recommend higher distance
        recommended = self.encoder.adjust_distance_dynamically(measured_error_rate)
        self.assertGreater(recommended, 3)


class TestEncoderIntegration(unittest.TestCase):
    """Integration tests across all encoders."""
    
    def test_all_encoders_produce_valid_circuits(self):
        """Test that all encoders produce executable circuits."""
        encoders = [
            Distance3Encoder(),
            Distance5Encoder(),
            Distance7Encoder(),
        ]
        
        backend = Aer.get_backend('statevector_simulator')
        
        for encoder in encoders:
            circuit = encoder.encode()
            
            # Should execute without error
            job = execute(circuit, backend)
            result = job.result()
            statevector = result.get_statevector()
            
            # Statevector should be normalized
            norm = sum(abs(amp)**2 for amp in statevector)
            self.assertAlmostEqual(norm, 1.0, places=10)
    
    def test_error_suppression_scaling(self):
        """Test that error suppression improves with distance."""
        encoders = [
            Distance3Encoder(),
            Distance5Encoder(),
            Distance7Encoder(),
        ]
        
        physical_error_rate = 0.001
        suppressions = []
        
        for encoder in encoders:
            logical_error = encoder.estimate_logical_error_rate(physical_error_rate)
            suppression = physical_error_rate / logical_error
            suppressions.append(suppression)
        
        # Suppression should increase with distance
        self.assertLess(suppressions[0], suppressions[1])
        self.assertLess(suppressions[1], suppressions[2])
    
    def test_resource_scaling(self):
        """Test that resource requirements scale properly."""
        encoders = [
            Distance3Encoder(),
            Distance5Encoder(),
            Distance7Encoder(),
        ]
        
        prev_qubits = 0
        for encoder in encoders:
            # More qubits for higher distance
            self.assertGreater(encoder.num_physical_qubits, prev_qubits)
            prev_qubits = encoder.num_physical_qubits


def run_all_tests():
    """Run all encoder tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDistance3Encoder))
    suite.addTests(loader.loadTestsFromTestCase(TestDistance5Encoder))
    suite.addTests(loader.loadTestsFromTestCase(TestDistance7Encoder))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveEncoder))
    suite.addTests(loader.loadTestsFromTestCase(TestEncoderIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("PHASEFLIP QEC - ENCODER TEST SUITE")
    print("=" * 70)
    print()
    
    result = run_all_tests()
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    print("=" * 70)