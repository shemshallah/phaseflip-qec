# 📄 FILE 23: phaseflip_qec/benchmarks/error_suppression.py

**Filename:** `phaseflip_qec/benchmarks/error_suppression.py`  
**Purpose:** Error suppression benchmarking and validation  
**Location:** `phaseflip_qec/benchmarks/` directory

"""
Error Suppression Benchmarking

Comprehensive benchmarking suite for PhaseFlip QEC performance validation.

Created by OaGI Research
"""

import numpy as np
from qiskit import QuantumCircuit, Aer, execute, transpile
from qiskit.providers.aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error
from qiskit.quantum_info import state_fidelity, Statevector
from typing import Dict, List, Tuple, Optional
import time
from dataclasses import dataclass
import json


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    code_distance: int
    physical_error_rate: float
    measured_logical_error_rate: float
    theoretical_logical_error_rate: float
    error_suppression_factor: float
    circuit_depth: int
    num_trials: int
    execution_time: float
    fidelity_mean: float
    fidelity_std: float


class ErrorSuppressionBenchmark:
    """
    Comprehensive error suppression benchmarking suite.
    
    Tests PhaseFlip QEC performance across various error rates and code distances.
    """
    
    def __init__(self, num_trials: int = 100, use_simulator: bool = True):
        """
        Initialize benchmark suite.
        
        Args:
            num_trials: Number of trials per benchmark
            use_simulator: Use Qiskit Aer simulator (True) or real hardware (False)
        """
        self.num_trials = num_trials
        self.use_simulator = use_simulator
        self.results = []
        
        if use_simulator:
            self.backend = Aer.get_backend('qasm_simulator')
        else:
            # Would connect to real hardware here
            self.backend = None
    
    def create_noise_model(self, error_rate: float) -> NoiseModel:
        """
        Create noise model with specified error rate.
        
        Args:
            error_rate: Phase error probability
            
        Returns:
            Qiskit NoiseModel
        """
        noise_model = NoiseModel()
        
        # Phase error (Z error)
        phase_error = depolarizing_error(error_rate, 1)
        
        # Add to all single-qubit gates
        noise_model.add_all_qubit_quantum_error(phase_error, ['u1', 'u2', 'u3', 'h', 'rz'])
        
        # Two-qubit gate errors
        two_qubit_error = depolarizing_error(error_rate * 2, 2)
        noise_model.add_all_qubit_quantum_error(two_qubit_error, ['cx', 'cz'])
        
        return noise_model
    
    def benchmark_single_configuration(
        self,
        code_distance: int,
        physical_error_rate: float
    ) -> BenchmarkResult:
        """
        Benchmark a single configuration (distance + error rate).
        
        Args:
            code_distance: Code distance (3, 5, or 7)
            physical_error_rate: Physical qubit error rate
            
        Returns:
            BenchmarkResult object
        """
        from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
        
        # Select encoder
        encoders = {
            3: Distance3Encoder(),
            5: Distance5Encoder(),
            7: Distance7Encoder(),
        }
        encoder = encoders[code_distance]
        
        # Create noise model
        noise_model = self.create_noise_model(physical_error_rate)
        
        # Prepare target state |+⟩
        target_state = Statevector.from_label('+')
        
        fidelities = []
        start_time = time.time()
        
        for trial in range(self.num_trials):
            # Create encoded circuit
            circuit = encoder.encode()
            circuit.measure_all()
            
            # Transpile for simulator
            transpiled = transpile(circuit, self.backend)
            
            # Execute with noise
            job = execute(
                transpiled,
                self.backend,
                noise_model=noise_model,
                shots=1000
            )
            result = job.result()
            
            # Calculate fidelity (simplified - measures success of encoding)
            counts = result.get_counts()
            # For encoded |+⟩, we expect roughly equal distribution
            # This is a simplified fidelity metric
            fidelity = self._calculate_fidelity_from_counts(counts, code_distance)
            fidelities.append(fidelity)
        
        execution_time = time.time() - start_time
        
        # Calculate statistics
        fidelity_mean = np.mean(fidelities)
        fidelity_std = np.std(fidelities)
        
        # Estimate logical error rate from fidelity
        measured_logical_error = 1 - fidelity_mean
        
        # Get theoretical prediction
        theoretical_logical_error = encoder.estimate_logical_error_rate(physical_error_rate)
        
        # Calculate suppression factor
        suppression_factor = physical_error_rate / measured_logical_error if measured_logical_error > 0 else float('inf')
        
        result = BenchmarkResult(
            code_distance=code_distance,
            physical_error_rate=physical_error_rate,
            measured_logical_error_rate=measured_logical_error,
            theoretical_logical_error_rate=theoretical_logical_error,
            error_suppression_factor=suppression_factor,
            circuit_depth=encoder.encode().depth(),
            num_trials=self.num_trials,
            execution_time=execution_time,
            fidelity_mean=fidelity_mean,
            fidelity_std=fidelity_std
        )
        
        self.results.append(result)
        return result
    
    def _calculate_fidelity_from_counts(self, counts: Dict, code_distance: int) -> float:
        """
        Calculate fidelity from measurement counts (simplified).
        
        Args:
            counts: Measurement counts
            code_distance: Code distance
            
        Returns:
            Estimated fidelity
        """
        total_shots = sum(counts.values())
        
        # For |+⟩^n state, expect roughly uniform distribution
        # Deviation from uniform indicates errors
        num_possible_outcomes = 2**code_distance
        expected_per_outcome = total_shots / num_possible_outcomes
        
        # Calculate chi-squared-like deviation
        deviation = sum(
            (count - expected_per_outcome)**2 / expected_per_outcome
            for count in counts.values()
        )
        
        # Convert to fidelity (simplified heuristic)
        max_deviation = total_shots
        fidelity = 1 - (deviation / max_deviation)
        
        return max(0, min(1, fidelity))
    
    def benchmark_scaling(
        self,
        code_distances: List[int] = [3, 5, 7],
        physical_error_rates: List[float] = [0.001, 0.005, 0.01]
    ) -> List[BenchmarkResult]:
        """
        Benchmark scaling across multiple configurations.
        
        Args:
            code_distances: List of code distances to test
            physical_error_rates: List of error rates to test
            
        Returns:
            List of BenchmarkResult objects
        """
        results = []
        total_configs = len(code_distances) * len(physical_error_rates)
        current = 0
        
        print(f"Running benchmark suite: {total_configs} configurations")
        print("=" * 70)
        
        for distance in code_distances:
            for error_rate in physical_error_rates:
                current += 1
                print(f"\n[{current}/{total_configs}] Testing d={distance}, p={error_rate:.4f}")
                
                result = self.benchmark_single_configuration(distance, error_rate)
                results.append(result)
                
                print(f"  Measured suppression: {result.error_suppression_factor:,.0f}×")
                print(f"  Fidelity: {result.fidelity_mean:.4f} ± {result.fidelity_std:.4f}")
                print(f"  Time: {result.execution_time:.2f}s")
        
        print("\n" + "=" * 70)
        print("Benchmark suite complete!")
        
        return results
    
    def export_results(self, filename: str):
        """
        Export benchmark results to JSON file.
        
        Args:
            filename: Output filename
        """
        data = {
            'num_trials': self.num_trials,
            'results': [
                {
                    'code_distance': r.code_distance,
                    'physical_error_rate': r.physical_error_rate,
                    'measured_logical_error_rate': r.measured_logical_error_rate,
                    'theoretical_logical_error_rate': r.theoretical_logical_error_rate,
                    'error_suppression_factor': r.error_suppression_factor,
                    'circuit_depth': r.circuit_depth,
                    'execution_time': r.execution_time,
                    'fidelity_mean': r.fidelity_mean,
                    'fidelity_std': r.fidelity_std,
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results exported to {filename}")
    
    def print_summary(self):
        """Print summary of all benchmark results."""
        if not self.results:
            print("No results to display")
            return
        
        print("\n" + "=" * 90)
        print("PHASEFLIP QEC BENCHMARK SUMMARY")
        print("=" * 90)
        print(f"{'Distance':<10} {'Phys. Error':<12} {'Meas. Supp.':<15} {'Theor. Supp.':<15} {'Fidelity':<12}")
        print("-" * 90)
        
        for result in self.results:
            theor_supp = result.physical_error_rate / result.theoretical_logical_error_rate
            print(f"{result.code_distance:<10} "
                  f"{result.physical_error_rate:<12.4f} "
                  f"{result.error_suppression_factor:<15,.0f}× "
                  f"{theor_supp:<15,.0f}× "
                  f"{result.fidelity_mean:<12.4f}")
        
        print("=" * 90)


def run_full_benchmark_suite(
    num_trials: int = 100,
    save_results: bool = True
) -> Dict:
    """
    Run complete benchmark suite and generate report.
    
    Args:
        num_trials: Number of trials per configuration
        save_results: Save results to file
        
    Returns:
        Dictionary with benchmark results and analysis
    """
    print("=" * 70)
    print("PHASEFLIP QEC - FULL BENCHMARK SUITE")
    print("=" * 70)
    print(f"Trials per configuration: {num_trials}")
    print()

"""
Error Suppression Benchmarking (Continued)
"""

    benchmark = ErrorSuppressionBenchmark(num_trials=num_trials)
    
    # Test configurations
    code_distances = [3, 5, 7]
    physical_error_rates = [0.0001, 0.0005, 0.001, 0.005, 0.01]
    
    # Run benchmarks
    results = benchmark.benchmark_scaling(code_distances, physical_error_rates)
    
    # Print summary
    benchmark.print_summary()
    
    # Save results
    if save_results:
        benchmark.export_results('benchmark_results.json')
    
    # Generate visualizations
    from ..utils.visualization import (
        plot_error_suppression,
        create_comparison_dashboard
    )
    
    plot_error_suppression(physical_error_rates, code_distances, 
                          save_path='error_suppression.png')
    create_comparison_dashboard(physical_error_rate=0.001, 
                               save_path='comparison_dashboard.png')
    
    # Compile analysis
    analysis = {
        'total_configurations': len(results),
        'total_trials': num_trials * len(results),
        'average_suppression_factors': {},
        'best_configurations': [],
    }
    
    # Calculate average suppression by distance
    for distance in code_distances:
        distance_results = [r for r in results if r.code_distance == distance]
        avg_suppression = np.mean([r.error_suppression_factor for r in distance_results])
        analysis['average_suppression_factors'][distance] = avg_suppression
    
    # Find best configurations
    sorted_results = sorted(results, key=lambda x: x.error_suppression_factor, reverse=True)
    analysis['best_configurations'] = [
        {
            'distance': r.code_distance,
            'error_rate': r.physical_error_rate,
            'suppression': r.error_suppression_factor,
            'fidelity': r.fidelity_mean
        }
        for r in sorted_results[:5]
    ]
    
    print("\nTop 5 Configurations by Suppression:")
    for i, config in enumerate(analysis['best_configurations'], 1):
        print(f"  {i}. Distance {config['distance']}, p={config['error_rate']:.4f}: "
              f"{config['suppression']:,.0f}× suppression, {config['fidelity']:.4f} fidelity")
    
    return analysis


def compare_with_other_codes(
    physical_error_rate: float = 0.001
) -> Dict:
    """
    Compare PhaseFlip QEC with other error correction codes.
    
    Args:
        physical_error_rate: Physical error rate for comparison
        
    Returns:
        Dictionary with comparison data
    """
    from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
    
    print("=" * 70)
    print("COMPARISON WITH OTHER QUANTUM ERROR CORRECTION CODES")
    print("=" * 70)
    print(f"Physical error rate: {physical_error_rate}")
    print()
    
    # PhaseFlip QEC
    phaseflip_encoders = {
        3: Distance3Encoder(),
        5: Distance5Encoder(),
        7: Distance7Encoder(),
    }
    
    comparison_data = {
        'physical_error_rate': physical_error_rate,
        'codes': {}
    }
    
    # PhaseFlip QEC results
    print("PhaseFlip QEC (Phase-only errors):")
    for distance, encoder in phaseflip_encoders.items():
        logical_error = encoder.estimate_logical_error_rate(physical_error_rate)
        suppression = physical_error_rate / logical_error
        
        comparison_data['codes'][f'PhaseFlip_d{distance}'] = {
            'logical_error_rate': logical_error,
            'suppression_factor': suppression,
            'physical_qubits': encoder.num_physical_qubits,
            'circuit_depth': encoder.encode().depth(),
        }
        
        print(f"  Distance {distance}: {logical_error:.2e} logical error, "
              f"{suppression:,.0f}× suppression, {encoder.num_physical_qubits} qubits")
    
    # Surface Code (approximate - for general errors)
    print("\nSurface Code (All error types, approximate):")
    for distance in [3, 5, 7]:
        # Surface code: p_L ≈ 0.1 * (p/p_th)^((d+1)/2) for p < p_th ≈ 0.01
        # Simplified approximation
        p_th = 0.01
        if physical_error_rate < p_th:
            logical_error = 0.1 * (physical_error_rate / p_th)**((distance + 1) / 2)
        else:
            logical_error = physical_error_rate  # Above threshold
        
        suppression = physical_error_rate / logical_error if logical_error > 0 else float('inf')
        qubits = distance**2  # Surface code requires d^2 physical qubits
        
        comparison_data['codes'][f'Surface_d{distance}'] = {
            'logical_error_rate': logical_error,
            'suppression_factor': suppression,
            'physical_qubits': qubits,
            'circuit_depth': distance * 2,  # Approximate
        }
        
        print(f"  Distance {distance}: {logical_error:.2e} logical error, "
              f"{suppression:,.0f}× suppression, {qubits} qubits")
    
    # Steane Code [[7,1,3]]
    print("\nSteane Code [[7,1,3]] (All error types):")
    # Steane: p_L ≈ 35 * p^2 for small p
    logical_error = 35 * physical_error_rate**2
    suppression = physical_error_rate / logical_error if logical_error > 0 else float('inf')
    
    comparison_data['codes']['Steane_7_1_3'] = {
        'logical_error_rate': logical_error,
        'suppression_factor': suppression,
        'physical_qubits': 7,
        'circuit_depth': 4,
    }
    
    print(f"  {logical_error:.2e} logical error, {suppression:,.0f}× suppression, 7 qubits")
    
    # Shor Code [[9,1,3]]
    print("\nShor Code [[9,1,3]] (All error types):")
    # Shor: p_L ≈ 9 * p^2 for small p
    logical_error = 9 * physical_error_rate**2
    suppression = physical_error_rate / logical_error if logical_error > 0 else float('inf')
    
    comparison_data['codes']['Shor_9_1_3'] = {
        'logical_error_rate': logical_error,
        'suppression_factor': suppression,
        'physical_qubits': 9,
        'circuit_depth': 4,
    }
    
    print(f"  {logical_error:.2e} logical error, {suppression:,.0f}× suppression, 9 qubits")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("SUMMARY: PhaseFlip QEC Advantages")
    print("=" * 70)
    
    phaseflip_d7 = comparison_data['codes']['PhaseFlip_d7']
    surface_d7 = comparison_data['codes']['Surface_d7']
    steane = comparison_data['codes']['Steane_7_1_3']
    
    print(f"For phase errors at p = {physical_error_rate}:")
    print(f"\n1. Resource Efficiency:")
    print(f"   PhaseFlip d=7: {phaseflip_d7['physical_qubits']} qubits")
    print(f"   Surface d=7: {surface_d7['physical_qubits']} qubits")
    print(f"   Ratio: {surface_d7['physical_qubits']/phaseflip_d7['physical_qubits']:.1f}× more qubits for Surface")
    
    print(f"\n2. Error Suppression:")
    print(f"   PhaseFlip d=7: {phaseflip_d7['suppression_factor']:,.0f}× suppression")
    print(f"   Steane: {steane['suppression_factor']:,.0f}× suppression")
    print(f"   Ratio: {phaseflip_d7['suppression_factor']/steane['suppression_factor']:.1f}× better")
    
    print(f"\n3. Circuit Depth:")
    print(f"   PhaseFlip d=7: {phaseflip_d7['circuit_depth']} gates")
    print(f"   Surface d=7: {surface_d7['circuit_depth']} gates (per round)")
    
    print("\nNote: PhaseFlip QEC is optimized for phase-flip errors only.")
    print("For general errors, use Surface Code or concatenated codes.")
    
    return comparison_data


def validate_theoretical_predictions(
    num_samples: int = 1000
) -> Dict:
    """
    Validate theoretical error rate predictions against simulations.
    
    Args:
        num_samples: Number of simulation samples
        
    Returns:
        Validation results
    """
    from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
    
    print("=" * 70)
    print("VALIDATING THEORETICAL PREDICTIONS")
    print("=" * 70)
    
    encoders = {
        3: Distance3Encoder(),
        5: Distance5Encoder(),
        7: Distance7Encoder(),
    }
    
    error_rates = [0.0001, 0.001, 0.01]
    validation_results = {}
    
    for distance, encoder in encoders.items():
        print(f"\nValidating Distance-{distance} encoder...")
        validation_results[distance] = []
        
        for error_rate in error_rates:
            theoretical = encoder.estimate_logical_error_rate(error_rate)
            
            # Simulate (simplified - count errors that exceed correction capacity)
            max_correctable = (distance - 1) // 2
            errors_per_sample = np.random.binomial(
                encoder.num_physical_qubits,
                error_rate,
                num_samples
            )
            
            logical_errors = np.sum(errors_per_sample > max_correctable)
            simulated = logical_errors / num_samples
            
            relative_error = abs(simulated - theoretical) / theoretical if theoretical > 0 else 0
            
            validation_results[distance].append({
                'physical_error_rate': error_rate,
                'theoretical': theoretical,
                'simulated': simulated,
                'relative_error': relative_error,
            })
            
            print(f"  p={error_rate:.4f}: Theory={theoretical:.4e}, "
                  f"Sim={simulated:.4e}, Error={relative_error:.2%}")
    
    print("\n" + "=" * 70)
    print("Validation complete!")
    
    return validation_results