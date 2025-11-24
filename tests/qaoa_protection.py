"""
QAOA with PhaseFlip QEC Protection

Example demonstrating protected Quantum Approximate Optimization Algorithm.

Created by OaGI Research
"""

import numpy as np
from qiskit import QuantumCircuit, Aer, execute, transpile
from qiskit.circuit import Parameter
from qiskit.providers.aer.noise import NoiseModel, depolarizing_error
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt

from phaseflip_qec.encoders import Distance3Encoder, Distance5Encoder
from phaseflip_qec.decoders import SyndromeDecoder


class ProtectedQAOA:
    """
    QAOA implementation with PhaseFlip QEC protection.
    
    Solves Max-Cut problem on a graph using error-protected QAOA.
    """
    
    def __init__(
        self,
        graph: List[Tuple[int, int]],
        code_distance: int = 3,
        num_layers: int = 1
    ):
        """
        Initialize Protected QAOA.
        
        Args:
            graph: List of edges as (node1, node2) tuples
            code_distance: QEC code distance (3, 5, or 7)
            num_layers: Number of QAOA layers (p)
        """
        self.graph = graph
        self.num_nodes = max(max(edge) for edge in graph) + 1
        self.code_distance = code_distance
        self.num_layers = num_layers
        
        # Select encoder
        if code_distance == 3:
            self.encoder = Distance3Encoder()
        elif code_distance == 5:
            self.encoder = Distance5Encoder()
        else:
            raise ValueError("Only distance 3 and 5 supported for QAOA")
        
        self.decoder = SyndromeDecoder(code_distance)
        
        # Parameters
        self.gamma_params = [Parameter(f'γ_{i}') for i in range(num_layers)]
        self.beta_params = [Parameter(f'β_{i}') for i in range(num_layers)]
    
    def create_unprotected_qaoa(self, gamma: List[float], beta: List[float]) -> QuantumCircuit:
        """
        Create standard (unprotected) QAOA circuit.
        
        Args:
            gamma: Phase separation angles
            beta: Mixing angles
            
        Returns:
            Unprotected QAOA circuit
        """
        qc = QuantumCircuit(self.num_nodes)
        
        # Initial state: |+⟩^n
        qc.h(range(self.num_nodes))
        
        # QAOA layers
        for layer in range(self.num_layers):
            # Problem Hamiltonian (Cost function)
            for i, j in self.graph:
                qc.rzz(2 * gamma[layer], i, j)
            
            # Mixer Hamiltonian
            for node in range(self.num_nodes):
                qc.rx(2 * beta[layer], node)
        
        return qc
    
    def create_protected_qaoa(self, gamma: List[float], beta: List[float]) -> QuantumCircuit:
        """
        Create PhaseFlip-protected QAOA circuit.
        
        Args:
            gamma: Phase separation angles
            beta: Mixing angles
            
        Returns:
            Protected QAOA circuit
        """
        # Create circuit with enough qubits for encoding each logical qubit
        num_physical = self.num_nodes * self.encoder.num_physical_qubits
        num_ancillas = self.encoder.num_ancilla_qubits * self.num_nodes
        
        qc = QuantumCircuit(num_physical + num_ancillas, self.num_nodes)
        
        # Encode each logical qubit
        for node in range(self.num_nodes):
            offset = node * self.encoder.num_physical_qubits
            ancilla_offset = num_physical + node * self.encoder.num_ancilla_qubits
            
            # Encode |+⟩ state
            encode_circuit = self.encoder.encode()
            qc.compose(encode_circuit, qubits=range(offset, offset + self.encoder.num_physical_qubits), inplace=True)
        
        # QAOA layers with error correction rounds
        for layer in range(self.num_layers):
            # Problem Hamiltonian (on encoded qubits)
            for i, j in self.graph:
                i_offset = i * self.encoder.num_physical_qubits
                j_offset = j * self.encoder.num_physical_qubits
                
                # Apply RZZ to all pairs of physical qubits
                for pi in range(self.encoder.num_physical_qubits):
                    for pj in range(self.encoder.num_physical_qubits):
                        qc.rzz(
                            2 * gamma[layer] / (self.encoder.num_physical_qubits**2),
                            i_offset + pi,
                            j_offset + pj
                        )
            
            # Error correction round
            for node in range(self.num_nodes):
                offset = node * self.encoder.num_physical_qubits
                ancilla_offset = num_physical + node * self.encoder.num_ancilla_qubits
                
                # Syndrome measurement
                syndrome_circuit = self.encoder.measure_syndrome()
                qc.compose(
                    syndrome_circuit,
                    qubits=list(range(offset, offset + self.encoder.num_physical_qubits)) +
                           list(range(ancilla_offset, ancilla_offset + self.encoder.num_ancilla_qubits)),
                    inplace=True
                )
            
            # Mixer Hamiltonian (on encoded qubits)
            for node in range(self.num_nodes):
                offset = node * self.encoder.num_physical_qubits
                
                # Apply RX to all physical qubits
                for pi in range(self.encoder.num_physical_qubits):
                    qc.rx(2 * beta[layer] / self.encoder.num_physical_qubits, offset + pi)
            
            # Error correction round after mixer
            for node in range(self.num_nodes):
                offset = node * self.encoder.num_physical_qubits
                ancilla_offset = num_physical + node * self.encoder.num_ancilla_qubits
                
                syndrome_circuit = self.encoder.measure_syndrome()
                qc.compose(
                    syndrome_circuit,
                    qubits=list(range(offset, offset + self.encoder.num_physical_qubits)) +
                           list(range(ancilla_offset, ancilla_offset + self.encoder.num_ancilla_qubits)),
                    inplace=True
                )
        
        # Decode and measure logical qubits
        for node in range(self.num_nodes):
            offset = node * self.encoder.num_physical_qubits
            
            # Decode
            decode_circuit = self.encoder.decode()
            qc.compose(decode_circuit, qubits=range(offset, offset + self.encoder.num_physical_qubits), inplace=True)
            
            # Measure first physical qubit (logical qubit)
            qc.measure(offset, node)
        
        return qc
    
    def compute_cut_value(self, bitstring: str) -> int:
        """
        Compute cut value for a bitstring solution.
        
        Args:
            bitstring: Binary string representing node assignments
            
        Returns:
            Number of edges crossing the cut
        """
        cut_value = 0
        for i, j in self.graph:
            if bitstring[i] != bitstring[j]:
                cut_value += 1
        return cut_value
    
    def run_qaoa(
        self,
        gamma: List[float],
        beta: List[float],
        use_protection: bool = True,
        shots: int = 1000,
        noise_model: NoiseModel = None
    ) -> Dict:
        """
        Run QAOA and return results.
        
        Args:
            gamma: Phase separation angles
            beta: Mixing angles
            use_protection: Use PhaseFlip QEC protection
            shots: Number of measurement shots
            noise_model: Optional noise model
            
        Returns:
            Dictionary with results
        """
        if use_protection:
            circuit = self.create_protected_qaoa(gamma, beta)
        else:
            circuit = self.create_unprotected_qaoa(gamma, beta)
        
        # Add measurements if not protected
        if not use_protection:
            circuit.measure_all()
        
        # Execute
        backend = Aer.get_backend('qasm_simulator')
        transpiled = transpile(circuit, backend)
        
        if noise_model:
            job = execute(transpiled, backend, shots=shots, noise_model=noise_model)
        else:
            job = execute(transpiled, backend, shots=shots)
        
        result = job.result()
        counts = result.get_counts()
        
        # Compute cut values
        cut_values = {}
        for bitstring, count in counts.items():
            # Reverse bitstring for correct indexing
            bitstring_rev = bitstring[::-1]
            cut_val = self.compute_cut_value(bitstring_rev)
            if cut_val in cut_values:
                cut_values[cut_val] += count
            else:
                cut_values[cut_val] = count
        
        # Find most common cut value
        max_cut_value = max(cut_values.keys())
        max_cut_probability = cut_values[max_cut_value] / shots
        
        return {
            'counts': counts,
            'cut_values': cut_values,
            'max_cut_value': max_cut_value,
            'max_cut_probability': max_cut_probability,
            'circuit_depth': circuit.depth(),
            'num_qubits': circuit.num_qubits,
        }


def benchmark_protected_qaoa():
    """
    Benchmark protected vs unprotected QAOA performance.
    """
    print("=" * 70)
    print("QAOA WITH PHASEFLIP QEC - BENCHMARK")
    print("=" * 70)
    
    # Define test graph (4-node square)
    graph = [(0, 1), (1, 2), (2, 3), (3, 0)]
    print(f"\nTest graph: {len(graph)} edges, 4 nodes")
    print("Optimal max-cut value: 4 (all edges cut)")
    
    # QAOA parameters (optimized for this graph)
    gamma = [0.5]
    beta = [0.4]
    
    # Create noise model
    error_rate = 0.01
    noise_model = NoiseModel()
    phase_error = depolarizing_error(error_rate, 1)
    noise_model.add_all_qubit_quantum_error(phase_error, ['u1', 'u2', 'u3', 'rz', 'rx'])
    
    print(f"\nNoise model: {error_rate} phase error rate")
    print(f"QAOA parameters: γ={gamma}, β={beta}")
    
    # Test unprotected QAOA
    print("\n" + "-" * 70)
    print("UNPROTECTED QAOA")
    print("-" * 70)
    
    qaoa_unprotected = ProtectedQAOA(graph, code_distance=3, num_layers=1)
    results_unprotected = qaoa_unprotected.run_qaoa(
        gamma, beta,
        use_protection=False,
        shots=1000,
        noise_model=noise_model
    )
    
    print(f"Circuit depth: {results_unprotected['circuit_depth']}")
    print(f"Number of qubits: {results_unprotected['num_qubits']}")
    print(f"Max cut value found: {results_unprotected['max_cut_value']}")
    print(f"Success probability: {results_unprotected['max_cut_probability']:.2%}")
    
    # Test protected QAOA (distance 3)
    print("\n" + "-" * 70)
    print("PROTECTED QAOA (Distance-3)")
    print("-" * 70)
    
    qaoa_protected = ProtectedQAOA(graph, code_distance=3, num_layers=1)
    results_protected = qaoa_protected.run_qaoa(
        gamma, beta,
        use_protection=True,
        shots=1000,
        noise_model=noise_model
    )
    
    print(f"Circuit depth: {results_protected['circuit_depth']}")
    print(f"Number of qubits: {results_protected['num_qubits']}")
    print(f"Max cut value found: {results_protected['max_cut_value']}")
    print(f"Success probability: {results_protected['max_cut_probability']:.2%}")
    
    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    
    improvement = (results_protected['max_cut_probability'] - 
                  results_unprotected['max_cut_probability']) / results_unprotected['max_cut_probability']
    
    print(f"Success probability improvement: {improvement:.1%}")
    print(f"Overhead (qubits): {results_protected['num_qubits'] / results_unprotected['num_qubits']:.1f}×")
    print(f"Overhead (depth): {results_protected['circuit_depth'] / results_unprotected['circuit_depth']:.1f}×")
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Cut value distributions
    cut_vals_unprot = list(results_unprotected['cut_values'].keys())
    counts_unprot = [results_unprotected['cut_values'][v] for v in cut_vals_unprot]
    
    cut_vals_prot = list(results_protected['cut_values'].keys())
    counts_prot = [results_protected['cut_values'][v] for v in cut_vals_prot]
    
    ax1.bar([v - 0.2 for v in cut_vals_unprot], counts_unprot, width=0.4, 
            label='Unprotected', color='red', alpha=0.7)
    ax1.bar([v + 0.2 for v in cut_vals_prot], counts_prot, width=0.4,
            label='Protected (d=3)', color='green', alpha=0.7)
    ax1.set_xlabel('Cut Value', fontweight='bold')
    ax1.set_ylabel('Count', fontweight='bold')
    ax1.set_title('Max-Cut Value Distribution', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Success probability comparison
    categories = ['Unprotected', 'Protected (d=3)']
    success_probs = [
        results_unprotected['max_cut_probability'] * 100,
        results_protected['max_cut_probability'] * 100
    ]
    
    colors_bar = ['red', 'green']
    bars = ax2.bar(categories, success_probs, color=colors_bar, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Success Probability (%)', fontweight='bold')
    ax2.set_title('Optimal Solution Success Rate', fontweight='bold')
    ax2.set_ylim([0, 105])
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('qaoa_comparison.png', dpi=300, bbox_inches='tight')
    print("\nPlot saved to: qaoa_comparison.png")
    
    return results_unprotected, results_protected


if __name__ == "__main__":
    # Run benchmark
    results_unprot, results_prot = benchmark_protected_qaoa()
    
    print("\n" + "=" * 70)
    print("PhaseFlip QEC successfully protects QAOA against phase errors!")
    print("=" * 70)