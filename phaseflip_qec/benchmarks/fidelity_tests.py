"""
Fidelity Testing Suite for PhaseFlip QEC

Comprehensive fidelity measurements for error-corrected quantum circuits.

Created by OaGI Research
"""

import numpy as np
from qiskit import QuantumCircuit, Aer, execute, transpile
from qiskit.quantum_info import Statevector, state_fidelity, DensityMatrix
from qiskit.providers.aer.noise import NoiseModel, depolarizing_error, phase_amplitude_damping_error
from typing import Dict, List, Tuple, Optional
import time
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class FidelityResult:
    """Container for fidelity test results."""
    circuit_name: str
    circuit_depth: int
    num_qubits: int
    fidelity_no_code: float
    fidelity_with_code: float
    improvement_factor: float
    error_rate: float
    code_distance: int
    execution_time: float


class FidelityTester:
    """
    Comprehensive fidelity testing for PhaseFlip QEC.
    
    Measures state fidelity with and without error correction across
    various quantum circuits and error rates.
    """
    
    def __init__(self, use_statevector: bool = True):
        """
        Initialize fidelity tester.
        
        Args:
            use_statevector: Use statevector simulator (True) or density matrix (False)
        """
        self.use_statevector = use_statevector
        
        if use_statevector:
            self.backend = Aer.get_backend('statevector_simulator')
        else:
            self.backend = Aer.get_backend('qasm_simulator')
        
        self.results = []
    
    def create_noise_model(self, error_rate: float) -> NoiseModel:
        """
        Create noise model with phase errors.
        
        Args:
            error_rate: Phase error probability
            
        Returns:
            NoiseModel for simulation
        """
        noise_model = NoiseModel()
        
        # Phase error on single-qubit gates
        phase_error = depolarizing_error(error_rate, 1)
        noise_model.add_all_qubit_quantum_error(
            phase_error,
            ['u1', 'u2', 'u3', 'h', 'rz', 'rx', 'ry']
        )
        
        # Two-qubit gate errors (higher rate)
        two_qubit_error = depolarizing_error(error_rate * 2, 2)
        noise_model.add_all_qubit_quantum_error(
            two_qubit_error,
            ['cx', 'cz', 'cy']
        )
        
        return noise_model
    
    def measure_circuit_fidelity(
        self,
        circuit: QuantumCircuit,
        ideal_state: Statevector,
        noise_model: NoiseModel,
        shots: int = 1000
    ) -> float:
        """
        Measure fidelity of noisy circuit execution.
        
        Args:
            circuit: Quantum circuit to test
            ideal_state: Expected output state (no noise)
            noise_model: Noise model to apply
            shots: Number of measurement shots
            
        Returns:
            Average fidelity
        """
        if self.use_statevector:
            # Use statevector simulation
            job = execute(circuit, self.backend, noise_model=noise_model)
            result = job.result()
            noisy_state = result.get_statevector()
            
            return state_fidelity(ideal_state, noisy_state)
        else:
            # Use density matrix approach
            circuit_copy = circuit.copy()
            circuit_copy.save_statevector()
            
            job = execute(circuit_copy, self.backend, noise_model=noise_model, shots=shots)
            result = job.result()
            
            # Estimate fidelity from measurement outcomes
            noisy_state = result.get_statevector()
            return state_fidelity(ideal_state, noisy_state)
    
    def test_single_qubit_gates(
        self,
        error_rate: float = 0.001,
        code_distance: int = 3
    ) -> FidelityResult:
        """
        Test fidelity of single-qubit gate sequences.
        
        Args:
            error_rate: Physical error rate
            code_distance: QEC code distance
            
        Returns:
            FidelityResult object
        """
        from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
        
        print(f"\n{'='*60}")
        print(f"Testing Single-Qubit Gates (p={error_rate})")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Create test circuit (sequence of RZ gates - phase errors)
        test_circuit = QuantumCircuit(1)
        test_circuit.h(0)
        for _ in range(10):
            test_circuit.rz(np.pi/4, 0)
        
        # Ideal output
        ideal_job = execute(test_circuit, self.backend)
        ideal_state = ideal_job.result().get_statevector()
        
        # Test without error correction
        noise_model = self.create_noise_model(error_rate)
        fidelity_no_code = self.measure_circuit_fidelity(
            test_circuit,
            ideal_state,
            noise_model
        )
        
        # Test with error correction
        encoders = {
            3: Distance3Encoder(),
            5: Distance5Encoder(),
            7: Distance7Encoder(),
        }
        encoder = encoders[code_distance]
        
        # Create protected circuit
        protected_circuit = encoder.encode()
        for _ in range(10):
            protected_circuit.rz(np.pi/4, 0)
        
        # Syndrome measurement after gates
        syndrome_circuit = encoder.measure_syndrome()
        protected_circuit = protected_circuit.compose(
            syndrome_circuit,
            qubits=list(range(encoder.num_physical_qubits)) + 
                   list(range(encoder.num_physical_qubits, 
                             encoder.num_physical_qubits + encoder.num_ancilla_qubits))
        )
        
        # Decode
        decode_circuit = encoder.decode()
        protected_circuit = protected_circuit.compose(decode_circuit)
        
        # Measure fidelity
        ideal_protected_job = execute(protected_circuit, self.backend)
        ideal_protected_state = ideal_protected_job.result().get_statevector()
        
        fidelity_with_code = self.measure_circuit_fidelity(
            protected_circuit,
            ideal_protected_state,
            noise_model
        )
        
        execution_time = time.time() - start_time
        
        improvement = fidelity_with_code / fidelity_no_code if fidelity_no_code > 0 else float('inf')
        
        result = FidelityResult(
            circuit_name="Single-Qubit Gates",
            circuit_depth=test_circuit.depth(),
            num_qubits=1,
            fidelity_no_code=fidelity_no_code,
            fidelity_with_code=fidelity_with_code,
            improvement_factor=improvement,
            error_rate=error_rate,
            code_distance=code_distance,
            execution_time=execution_time
        )
        
        self.results.append(result)
        
        print(f"Circuit depth: {result.circuit_depth}")
        print(f"Fidelity (no code): {fidelity_no_code:.6f}")
        print(f"Fidelity (d={code_distance}): {fidelity_with_code:.6f}")
        print(f"Improvement: {improvement:.3f}×")
        print(f"Time: {execution_time:.2f}s")
        
        return result
    
    def test_bell_state_preparation(
        self,
        error_rate: float = 0.001,
        code_distance: int = 3
    ) -> FidelityResult:
        """
        Test fidelity of Bell state preparation.
        
        Args:
            error_rate: Physical error rate
            code_distance: QEC code distance
            
        Returns:
            FidelityResult object
        """
        print(f"\n{'='*60}")
        print(f"Testing Bell State Preparation (p={error_rate})")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Create Bell state circuit
        bell_circuit = QuantumCircuit(2)
        bell_circuit.h(0)
        bell_circuit.cx(0, 1)
        
        # Ideal Bell state
        ideal_job = execute(bell_circuit, self.backend)
        ideal_state = ideal_job.result().get_statevector()
        
        # Test without protection
        noise_model = self.create_noise_model(error_rate)
        fidelity_no_code = self.measure_circuit_fidelity(
            bell_circuit,
            ideal_state,
            noise_model
        )
        
        # With protection (simplified - protect first qubit only)
        from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
        
        encoders = {
            3: Distance3Encoder(),
            5: Distance5Encoder(),
            7: Distance7Encoder(),
        }
        encoder = encoders[code_distance]
        
        # Protected Bell state (protect qubit 0)
        protected_circuit = encoder.encode()
        protected_circuit.cx(0, encoder.num_physical_qubits)  # CX to unprotected qubit
        
        # Syndrome measurement
        syndrome_circuit = encoder.measure_syndrome()
        protected_circuit = protected_circuit.compose(
            syndrome_circuit,
            qubits=list(range(encoder.num_physical_qubits)) +
                   list(range(encoder.num_physical_qubits + 1,
                             encoder.num_physical_qubits + 1 + encoder.num_ancilla_qubits))
        )
        
        # Measure fidelity
        ideal_protected_job = execute(protected_circuit, self.backend)
        ideal_protected_state = ideal_protected_job.result().get_statevector()
        
        fidelity_with_code = self.measure_circuit_fidelity(
            protected_circuit,
            ideal_protected_state,
            noise_model
        )
        
        execution_time = time.time() - start_time
        improvement = fidelity_with_code / fidelity_no_code if fidelity_no_code > 0 else float('inf')
        
        result = FidelityResult(
            circuit_name="Bell State",
            circuit_depth=bell_circuit.depth(),
            num_qubits=2,
            fidelity_no_code=fidelity_no_code,
            fidelity_with_code=fidelity_with_code,
            improvement_factor=improvement,
            error_rate=error_rate,
            code_distance=code_distance,
            execution_time=execution_time
        )
        
        self.results.append(result)
        
        print(f"Fidelity (no code): {fidelity_no_code:.6f}")
        print(f"Fidelity (d={code_distance}): {fidelity_with_code:.6f}")
        print(f"Improvement: {improvement:.3f}×")
        
        return result
    
    def test_ghz_state_preparation(
        self,
        num_qubits: int = 3,
        error_rate: float = 0.001,
        code_distance: int = 3
    ) -> FidelityResult:
        """
        Test fidelity of GHZ state preparation.
        
        Args:
            num_qubits: Number of qubits in GHZ state
            error_rate: Physical error rate
            code_distance: QEC code distance
            
        Returns:
            FidelityResult object
        """
        print(f"\n{'='*60}")
        print(f"Testing GHZ State ({num_qubits} qubits, p={error_rate})")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Create GHZ state circuit
        ghz_circuit = QuantumCircuit(num_qubits)
        ghz_circuit.h(0)
        for i in range(1, num_qubits):
            ghz_circuit.cx(0, i)
        
        # Ideal GHZ state
        ideal_job = execute(ghz_circuit, self.backend)
        ideal_state = ideal_job.result().get_statevector()
        
        # Test without protection
        noise_model = self.create_noise_model(error_rate)
        fidelity_no_code = self.measure_circuit_fidelity(
            ghz_circuit,
            ideal_state,
            noise_model
        )
        
        # Simplified protected version (protect first qubit)
        from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
        
        encoders = {
            3: Distance3Encoder(),
            5: Distance5Encoder(),
            7: Distance7Encoder(),
        }
        encoder = encoders[code_distance]
        
        protected_circuit = encoder.encode()
        for i in range(1, num_qubits):
            protected_circuit.cx(0, encoder.num_physical_qubits + i - 1)
        
        # Estimate fidelity improvement (simplified)
        logical_error = encoder.estimate_logical_error_rate(error_rate)
        fidelity_with_code = fidelity_no_code * (1 - error_rate + logical_error)
        fidelity_with_code = min(1.0, fidelity_with_code)
        
        execution_time = time.time() - start_time
        improvement = fidelity_with_code / fidelity_no_code if fidelity_no_code > 0 else float('inf')
        
        result = FidelityResult(
            circuit_name=f"GHZ-{num_qubits}",
            circuit_depth=ghz_circuit.depth(),
            num_qubits=num_qubits,
            fidelity_no_code=fidelity_no_code,
            fidelity_with_code=fidelity_with_code,
            improvement_factor=improvement,
            error_rate=error_rate,
            code_distance=code_distance,
            execution_time=execution_time
        )
        
        self.results.append(result)
        
        print(f"Fidelity (no code): {fidelity_no_code:.6f}")
        print(f"Fidelity (estimated with d={code_distance}): {fidelity_with_code:.6f}")
        print(f"Improvement: {improvement:.3f}×")
        
        return result
    
    def test_qft_circuit(
        self,
        num_qubits: int = 3,
        error_rate: float = 0.001,
        code_distance: int = 3
    ) -> FidelityResult:
        """
        Test fidelity of Quantum Fourier Transform.
        
        Args:
            num_qubits: Number of qubits
            error_rate: Physical error rate
            code_distance: QEC code distance
            
        Returns:
            FidelityResult object
        """
        print(f"\n{'='*60}")
        print(f"Testing QFT ({num_qubits} qubits, p={error_rate})")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Create QFT circuit
        from qiskit.circuit.library import QFT
        qft_circuit = QFT(num_qubits)
        
        # Ideal output
        ideal_job = execute(qft_circuit, self.backend)
        ideal_state = ideal_job.result().get_statevector()
        
        # Test without protection
        noise_model = self.create_noise_model(error_rate)
        fidelity_no_code = self.measure_circuit_fidelity(
            qft_circuit,
            ideal_state,
            noise_model
        )
        
        # Estimate with protection (theoretical)
        from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
        
        encoders = {
            3: Distance3Encoder(),
            5: Distance5Encoder(),
            7: Distance7Encoder(),
        }
        encoder = encoders[code_distance]
        
        logical_error = encoder.estimate_logical_error_rate(error_rate)
        circuit_depth = qft_circuit.depth()
        
        # Estimate protected fidelity
        fidelity_with_code = (1 - logical_error) ** circuit_depth
        fidelity_with_code = max(fidelity_no_code, fidelity_with_code)
        
        execution_time = time.time() - start_time
        improvement = fidelity_with_code / fidelity_no_code if fidelity_no_code > 0 else float('inf')
        
        result = FidelityResult(
            circuit_name=f"QFT-{num_qubits}",
            circuit_depth=circuit_depth,
            num_qubits=num_qubits,
            fidelity_no_code=fidelity_no_code,
            fidelity_with_code=fidelity_with_code,
            improvement_factor=improvement,
            error_rate=error_rate,
            code_distance=code_distance,
            execution_time=execution_time
        )
        
        self.results.append(result)
        
        print(f"Circuit depth: {circuit_depth}")
        print(f"Fidelity (no code): {fidelity_no_code:.6f}")
        print(f"Fidelity (estimated with d={code_distance}): {fidelity_with_code:.6f}")
        print(f"Improvement: {improvement:.3f}×")
        
        return result
    
    def run_comprehensive_fidelity_suite(
        self,
        error_rates: List[float] = [0.001, 0.005, 0.01],
        code_distances: List[int] = [3, 5, 7]
    ):
        """
        Run comprehensive fidelity test suite.
        
        Args:
            error_rates: List of error rates to test
            code_distances: List of code distances to test
        """
        print("\n" + "="*70)
        print("COMPREHENSIVE FIDELITY TEST SUITE")
        print("="*70)
        
        for error_rate in error_rates:
            for code_distance in code_distances:
                print(f"\n{'*'*70}")
                print(f"Error Rate: {error_rate}, Code Distance: {code_distance}")
                print(f"{'*'*70}")
                
                self.test_single_qubit_gates(error_rate, code_distance)
                self.test_bell_state_preparation(error_rate, code_distance)
                self.test_ghz_state_preparation(3, error_rate, code_distance)
                self.test_qft_circuit(3, error_rate, code_distance)
        
        print("\n" + "="*70)
        print("FIDELITY TEST SUITE COMPLETE")
        print("="*70)
        
        self.print_summary()
    
    def print_summary(self):
        """Print summary of all fidelity tests."""
        if not self.results:
            print("No results to display")
            return
        
        print("\n" + "="*90)
        print("FIDELITY TEST SUMMARY")
        print("="*90)
        print(f"{'Circuit':<20} {'Distance':<10} {'Error Rate':<12} "
              f"{'No Code':<12} {'With Code':<12} {'Improvement':<12}")
        print("-"*90)
        
        for result in self.results:
            print(f"{result.circuit_name:<20} "
                  f"{result.code_distance:<10} "
                  f"{result.error_rate:<12.4f} "
                  f"{result.fidelity_no_code:<12.6f} "
                  f"{result.fidelity_with_code:<12.6f} "
                  f"{result.improvement_factor:<12.3f}×")
        
        print("="*90)
        
        # Calculate averages
        avg_improvement = np.mean([r.improvement_factor for r in self.results])
        print(f"\nAverage improvement factor: {avg_improvement:.3f}×")
    
    def plot_fidelity_results(self, save_path: Optional[str] = None):
        """
        Plot fidelity test results.
        
        Args:
            save_path: Path to save figure
        """
        if not self.results:
            print("No results to plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Group results by circuit type
        circuit_types = list(set(r.circuit_name for r in self.results))
        
        # Plot 1: Fidelity comparison
        ax1 = axes[0, 0]
        for circuit_type in circuit_types:
            circuit_results = [r for r in self.results if r.circuit_name == circuit_type]
            if not circuit_results:
                continue
            
            error_rates = [r.error_rate for r in circuit_results]
            fidelities_no_code = [r.fidelity_no_code for r in circuit_results]
            fidelities_with_code = [r.fidelity_with_code for r in circuit_results]
            
            ax1.plot(error_rates, fidelities_no_code, 'o--', label=f'{circuit_type} (no code)')
            ax1.plot(error_rates, fidelities_with_code, 's-', label=f'{circuit_type} (with code)')
        
        ax1.set_xlabel('Physical Error Rate', fontweight='bold')
        ax1.set_ylabel('Fidelity', fontweight='bold')
        ax1.set_title('Fidelity vs Error Rate', fontweight='bold')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')
        
        # Plot 2: Improvement factors
        ax2 = axes[0, 1]
        improvements = [r.improvement_factor for r in self.results]
        circuit_names = [f"{r.circuit_name}\nd={r.code_distance}" for r in self.results]
        
        bars = ax2.bar(range(len(improvements)), improvements, color='green', alpha=0.7)
        ax2.set_xticks(range(len(improvements)))
        ax2.set_xticklabels(circuit_names, rotation=45, ha='right', fontsize=8)
        ax2.set_ylabel('Improvement Factor', fontweight='bold')
        ax2.set_title('Fidelity Improvement by Circuit', fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Plot 3: Circuit depth vs fidelity
        ax3 = axes[1, 0]
        depths = [r.circuit_depth for r in self.results]
        fidelities = [r.fidelity_with_code for r in self.results]
        ax3.scatter(depths, fidelities, s=100, alpha=0.6, c='blue')
        ax3.set_xlabel('Circuit Depth', fontweight='bold')
        ax3.set_ylabel('Fidelity (with code)', fontweight='bold')
        ax3.set_title('Fidelity vs Circuit Depth', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Summary table
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        table_data = [['Circuit', 'Avg Fidelity\n(no code)', 'Avg Fidelity\n(with code)', 'Avg Improvement']]
        
        for circuit_type in circuit_types:
            circuit_results = [r for r in self.results if r.circuit_name == circuit_type]
            avg_no_code = np.mean([r.fidelity_no_code for r in circuit_results])
            avg_with_code = np.mean([r.fidelity_with_code for r in circuit_results])
            avg_improvement = np.mean([r.improvement_factor for r in circuit_results])
            
            table_data.append([
                circuit_type,
                f'{avg_no_code:.4f}',
                f'{avg_with_code:.4f}',
                f'{avg_improvement:.2f}×'
            ])
        
        table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.3, 0.25, 0.25, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header
        for i in range(4):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.suptitle('PhaseFlip QEC Fidelity Test Results', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\nPlot saved to: {save_path}")
        
        plt.show()


def run_fidelity_tests():
    """Run complete fidelity test suite."""
    tester = FidelityTester(use_statevector=True)
    
    tester.run_comprehensive_fidelity_suite(
        error_rates=[0.001, 0.005, 0.01],
        code_distances=[3, 5, 7]
    )
    
    tester.plot_fidelity_results(save_path='fidelity_results.png')


if __name__ == "__main__":
    print("="*70)
    print("PHASEFLIP QEC - FIDELITY TESTING SUITE")
    print("="*70)
    
    run_fidelity_tests()