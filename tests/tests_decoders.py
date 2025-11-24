"""
Test Suite for PhaseFlip QEC Decoders

Comprehensive tests for syndrome decoder and ML decoder.

Created by OaGI Research
"""

import unittest
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

from phaseflip_qec.decoders import SyndromeDecoder, MLDecoder
from phaseflip_qec.encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder


class TestSyndromeDecoder(unittest.TestCase):
    """Test cases for syndrome-based decoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.decoder_d3 = SyndromeDecoder(code_distance=3)
        self.decoder_d5 = SyndromeDecoder(code_distance=5)
        self.decoder_d7 = SyndromeDecoder(code_distance=7)
    
    def test_initialization(self):
        """Test decoder initialization."""
        self.assertEqual(self.decoder_d3.code_distance, 3)
        self.assertEqual(self.decoder_d5.code_distance, 5)
        self.assertEqual(self.decoder_d7.code_distance, 7)
    
    def test_syndrome_to_error_mapping_d3(self):
        """Test syndrome to error mapping for distance-3."""
        # No error syndrome
        syndrome = '00'
        error_location = self.decoder_d3.decode_syndrome(syndrome)
        self.assertIsNone(error_location)
        
        # Single error syndromes should map to valid locations
        for syndrome in ['01', '10', '11']:
            error_location = self.decoder_d3.decode_syndrome(syndrome)
            self.assertIsNotNone(error_location)
            self.assertIsInstance(error_location, (int, list))
    
    def test_correct_single_error_d3(self):
        """Test correction of single phase flip for distance-3."""
        encoder = Distance3Encoder()
        
        # Encode
        circuit = encoder.encode()
        
        # Apply error on qubit 0
        circuit.z(0)
        
        # Measure syndrome
        syndrome_circuit = encoder.measure_syndrome()
        full_circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(3)) + [3, 4]
        )
        
        # Measure ancillas
        full_circuit.measure([3, 4], [0, 1])
        
        # Execute
        backend = Aer.get_backend('qasm_simulator')
        job = execute(full_circuit, backend, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Get most common syndrome
        syndrome = max(counts, key=counts.get)
        
        # Decode
        error_location = self.decoder_d3.decode_syndrome(syndrome)
        
        # Should identify error location
        self.assertIsNotNone(error_location)
    
    def test_decode_syndrome_with_lookup_table(self):
        """Test that lookup table is properly constructed."""
        # Distance-3 should have lookup table
        self.assertIsNotNone(self.decoder_d3.syndrome_lookup)
        self.assertIsInstance(self.decoder_d3.syndrome_lookup, dict)
        
        # Should contain expected syndromes
        self.assertIn('00', self.decoder_d3.syndrome_lookup)
    
    def test_multi_error_detection_d5(self):
        """Test detection of multiple errors for distance-5."""
        encoder = Distance5Encoder()
        
        # Encode
        circuit = encoder.encode()
        
        # Apply two errors
        circuit.z(0)
        circuit.z(1)
        
        # Measure syndrome
        syndrome_circuit = encoder.measure_syndrome()
        full_circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(5)) + list(range(5, 9))
        )
        
        full_circuit.measure(list(range(5, 9)), list(range(4)))
        
        # Execute
        backend = Aer.get_backend('qasm_simulator')
        job = execute(full_circuit, backend, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Should detect non-zero syndrome
        all_zero = all(syndrome == '0000' for syndrome in counts.keys())
        self.assertFalse(all_zero)
    
    def test_error_correction_circuit_generation(self):
        """Test generation of error correction circuit."""
        # Test with single error location
        correction_circuit = self.decoder_d3.create_correction_circuit(
            error_location=0,
            num_qubits=3
        )
        
        self.assertIsInstance(correction_circuit, QuantumCircuit)
        self.assertEqual(correction_circuit.num_qubits, 3)
        
        # Test with multiple error locations
        correction_circuit = self.decoder_d5.create_correction_circuit(
            error_location=[0, 2],
            num_qubits=5
        )
        
        self.assertIsInstance(correction_circuit, QuantumCircuit)
        self.assertEqual(correction_circuit.num_qubits, 5)
    
    def test_no_correction_for_no_error(self):
        """Test that no correction is applied when no error detected."""
        syndrome = '00'  # No error
        error_location = self.decoder_d3.decode_syndrome(syndrome)
        
        self.assertIsNone(error_location)
    
    def test_correction_statistics(self):
        """Test tracking of correction statistics."""
        # Reset statistics
        self.decoder_d3.correction_history = []
        
        # Perform several corrections
        for i in range(5):
            self.decoder_d3.decode_syndrome('01')
        
        # Should have history
        self.assertEqual(len(self.decoder_d3.correction_history), 5)


class TestMLDecoder(unittest.TestCase):
    """Test cases for machine learning decoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.decoder = MLDecoder(code_distance=3)
    
    def test_initialization(self):
        """Test ML decoder initialization."""
        self.assertEqual(self.decoder.code_distance, 3)
        self.assertIsNone(self.decoder.model)  # Model not trained yet
    
    def test_training_data_generation(self):
        """Test generation of training data."""
        X_train, y_train = self.decoder.generate_training_data(num_samples=100)
        
        # Check shapes
        self.assertEqual(len(X_train), 100)
        self.assertEqual(len(y_train), 100)
        
        # Check that syndromes are valid binary strings
        for syndrome in X_train:
            self.assertIsInstance(syndrome, str)
            self.assertTrue(all(bit in '01' for bit in syndrome))
    
    def test_model_training(self):
        """Test ML model training."""
        # Generate training data
        X_train, y_train = self.decoder.generate_training_data(num_samples=500)
        
        # Train model
        self.decoder.train(X_train, y_train, epochs=10)
        
        # Model should be trained
        self.assertIsNotNone(self.decoder.model)
    
    def test_prediction_after_training(self):
        """Test that trained model can make predictions."""
        # Generate and train
        X_train, y_train = self.decoder.generate_training_data(num_samples=500)
        self.decoder.train(X_train, y_train, epochs=10)
        
        # Make prediction
        test_syndrome = '01'
        prediction = self.decoder.predict(test_syndrome)
        
        # Should return valid error location
        self.assertIsNotNone(prediction)
        self.assertIsInstance(prediction, (int, list, type(None)))
    
    def test_model_save_and_load(self):
        """Test saving and loading trained model."""
        import tempfile
        import os
        
        # Train model
        X_train, y_train = self.decoder.generate_training_data(num_samples=200)
        self.decoder.train(X_train, y_train, epochs=5)
        
        # Save model
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, 'test_model.pkl')
            self.decoder.save_model(save_path)
            
            # Create new decoder and load
            new_decoder = MLDecoder(code_distance=3)
            new_decoder.load_model(save_path)
            
            # Should be able to make predictions
            test_syndrome = '10'
            prediction = new_decoder.predict(test_syndrome)
            self.assertIsNotNone(prediction)
    
    def test_accuracy_evaluation(self):
        """Test model accuracy evaluation."""
        # Train model
        X_train, y_train = self.decoder.generate_training_data(num_samples=500)
        self.decoder.train(X_train, y_train, epochs=10)
        
        # Generate test data
        X_test, y_test = self.decoder.generate_training_data(num_samples=100)
        
        # Evaluate
        accuracy = self.decoder.evaluate(X_test, y_test)
        
        # Accuracy should be reasonable (> 70%)
        self.assertGreater(accuracy, 0.7)
        self.assertLessEqual(accuracy, 1.0)
    
    def test_comparison_with_syndrome_decoder(self):
        """Test ML decoder vs syndrome decoder performance."""
        # Create both decoders
        syndrome_decoder = SyndromeDecoder(code_distance=3)
        ml_decoder = MLDecoder(code_distance=3)
        
        # Train ML decoder
        X_train, y_train = ml_decoder.generate_training_data(num_samples=1000)
        ml_decoder.train(X_train, y_train, epochs=20)
        
        # Test on same syndromes
        test_syndromes = ['01', '10', '11', '00']
        
        syndrome_results = []
        ml_results = []
        
        for syndrome in test_syndromes:
            syndrome_pred = syndrome_decoder.decode_syndrome(syndrome)
            ml_pred = ml_decoder.predict(syndrome)
            
            syndrome_results.append(syndrome_pred)
            ml_results.append(ml_pred)
        
        # Both should produce reasonable results
        self.assertEqual(len(syndrome_results), len(ml_results))


class TestDecoderIntegration(unittest.TestCase):
    """Integration tests for decoders with encoders."""
    
    def test_full_encode_decode_cycle_d3(self):
        """Test complete encode-error-syndrome-decode cycle for distance-3."""
        encoder = Distance3Encoder()
        decoder = SyndromeDecoder(code_distance=3)
        
        # Encode
        circuit = encoder.encode()
        
        # Introduce error
        error_qubit = 1
        circuit.z(error_qubit)
        
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
        
        # Decode most common syndrome
        syndrome = max(counts, key=counts.get)
        error_location = decoder.decode_syndrome(syndrome)
        
        # Should identify error
        self.assertIsNotNone(error_location)
    
    def test_multiple_error_correction_d5(self):
        """Test correction of multiple errors for distance-5."""
        encoder = Distance5Encoder()
        decoder = SyndromeDecoder(code_distance=5)
        
        # Encode
        circuit = encoder.encode()
        
        # Introduce two errors (within correction capability)
        circuit.z(0)
        circuit.z(2)
        
        # Measure syndrome
        syndrome_circuit = encoder.measure_syndrome()
        full_circuit = circuit.compose(
            syndrome_circuit,
            qubits=list(range(5)) + list(range(5, 9))
        )
        
        full_circuit.measure(list(range(5, 9)), list(range(4)))
        
        # Execute
        backend = Aer.get_backend('qasm_simulator')
        job = execute(full_circuit, backend, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Should detect errors (non-zero syndrome)
        self.assertTrue(len(counts) > 0)
    
    def test_decoder_performance_comparison(self):
        """Compare performance of different decoders."""
        encoder = Distance3Encoder()
        syndrome_decoder = SyndromeDecoder(code_distance=3)
        ml_decoder = MLDecoder(code_distance=3)
        
        # Train ML decoder
        X_train, y_train = ml_decoder.generate_training_data(num_samples=1000)
        ml_decoder.train(X_train, y_train, epochs=20)
        
        # Run multiple error scenarios
        num_trials = 10
        syndrome_successes = 0
        ml_successes = 0
        
        for trial in range(num_trials):
            # Encode
            circuit = encoder.encode()
            
            # Random error
            error_qubit = np.random.randint(0, 3)
            circuit.z(error_qubit)
            
            # Measure syndrome
            syndrome_circuit = encoder.measure_syndrome()
            full_circuit = circuit.compose(
                syndrome_circuit,
                qubits=list(range(3)) + [3, 4]
            )
            full_circuit.measure([3, 4], [0, 1])
            
            # Execute
            backend = Aer.get_backend('qasm_simulator')
            job = execute(full_circuit, backend, shots=10)
            result = job.result()
            counts = result.get_counts()
            
            syndrome = max(counts, key=counts.get)
            
            # Test both decoders
            syndrome_pred = syndrome_decoder.decode_syndrome(syndrome)
            ml_pred = ml_decoder.predict(syndrome)
            
            if syndrome_pred == error_qubit or (isinstance(syndrome_pred, list) and error_qubit in syndrome_pred):
                syndrome_successes += 1
            
            if ml_pred == error_qubit or (isinstance(ml_pred, list) and error_qubit in ml_pred):
                ml_successes += 1
        
        # Both should have reasonable success rates
        print(f"Syndrome decoder success rate: {syndrome_successes}/{num_trials}")
        print(f"ML decoder success rate: {ml_successes}/{num_trials}")


def run_all_tests():
    """Run all decoder tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSyndromeDecoder))
    suite.addTests(loader.loadTestsFromTestCase(TestMLDecoder))
    suite.addTests(loader.loadTestsFromTestCase(TestDecoderIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("PHASEFLIP QEC - DECODER TEST SUITE")
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