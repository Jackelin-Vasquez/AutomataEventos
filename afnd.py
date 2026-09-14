"""
MÓDULO: Motor del Autómata Finito No Determinista (AFND)
    Implementa la definición formal de la 5-tupla M = (Q, Σ, δ, q0, F) del AFND.
    Contiene la matriz de transiciones, el evaluador de cadenas de entrada,
    la detección de no determinismo (transiciones múltiples) y el cálculo
    del historial de conjuntos de estados activos paso a paso.
"""