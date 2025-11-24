"""
Adaptive Phase-Flip Encoder
Automatically selects optimal code distance based on error rates and fidelity requirements
"""

from typing import Optional
from qiskit import QuantumCircuit
from .distance_3 import Distance3Encoder
from .distance_5 import Distance5Encoder
from .distance_7 import Distance7Encoder


class AdaptiveEncoder:
    """
    Intelligently selects code distance based on:
    - Measured error rates
    - Target fidelity
    - Available qubits
    - Circuit depth constraints
    """
    
    def __init__(self):
        self.encoders = {
            3: Distance3Encoder(),
            5: Distance5Encoder(),
            7: Distance7Encoder(),
        }
        self.current_encoder = None
        
    def select_encoder(self, 
                      physical_error_rate: float,
                      target_fidelity: float = 0.99,
                      max_qubits: Optional[int] = None) -> int:
        """
        Select optimal code distance based on requirements.
        
        Args:
            physical_error_rate: Measured error rate of physical qubits
            target_fidelity: Desired logical qubit fidelity
            max_qubits: Maximum number of qubits available
            
        Returns:
            Selected code distance (3, 5, or 7)
        """
        target_error_rate = 1 - target_fidelity
        
        # Check each code distance
        for distance in [3, 5, 7]:
            if max_qubits and distance > max_qubits:
                continue
                
            encoder = self.encoders[distance]
            logical_error_rate = encoder.estimate_logical_error_rate(physical_error_rate)
            
            if logical_error_rate <= target_error_rate:
                self.current_encoder = encoder
                return distance
        
        # If no code meets requirement, use largest available
        if max_qubits:
            for distance in [7, 5, 3]:
                if distance <= max_qubits:
                    self.current_encoder = self.encoders[distance]
                    return distance
        
        # Default to distance-7
        self.current_encoder = self.encoders[7]
        return 7
    
    def encode(self, circuit: Optional[QuantumCircuit] = None,
               physical_error_rate: float = 0.001,
               target_fidelity: float = 0.99) -> QuantumCircuit:
        """
        Encode with adaptively selected code distance.
        
        Args:
            circuit: Existing circuit (creates new if None)
            physical_error_rate: Measured error rate
            target_fidelity: Target logical fidelity
            
        Returns:
            Encoded circuit
        """
        if self.current_encoder is None:
            self.select_encoder(physical_error_rate, target_fidelity)
        
        return self.current_encoder.encode(circuit)
    
    def get_recommendation(self, 
                          physical_error_rate: float,
                          num_logical_gates: int) -> dict:
        """
        Get detailed recommendation for code selection.
        
        Args:
            physical_error_rate: Measured error rate
            num_logical_gates: Number of gates in algorithm
            
        Returns:
            Dictionary with recommendation details
        """
        recommendations = {}
        
        for distance, encoder in self.encoders.items():
            logical_error = encoder.estimate_logical_error_rate(physical_error_rate)
            circuit_error = 1 - (1 - logical_error)**num_logical_gates
            
            recommendations[distance] = {
                'logical_error_rate': logical_error,
                'circuit_success_probability': 1 - circuit_error,
                'physical_qubits_required': encoder.num_physical_qubits,
                'error_suppression': encoder.error_suppression_factor,
            }
        
        return recommendations
    
    def __repr__(self) -> str:
        current = self.current_encoder.__class__.__name__ if self.current_encoder else "None"
        return f"AdaptiveEncoder(current={current})"