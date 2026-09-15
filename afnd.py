"""
MÓDULO: Motor del Autómata Finito No Determinista (AFND)
    Implementa la definición formal de la 5-tupla M = (Q, Σ, δ, q0, F) del AFND.
    Contiene la matriz de transiciones, el evaluador de cadenas de entrada,
    la detección de no determinismo (transiciones múltiples) y el cálculo
    del historial de conjuntos de estados activos paso a paso.
"""

"""
alfabeto del AFND:
q = entrada mediante QR. 
g = entrada general.
v = entrada VIP.
i = invitación.
c = código válido.
a = acceso autorizado.
e = error.
* en todos los tipos de entrada, se puede usar la digital o la manual, pero la manual suele ser si la física no funciona

"""
class AFND:
    """
    Clase para que el autómata funcione
    definición:
        Q0 - esperando ticket
        Q1 - ticket recibido
        Q2 - esperando QR (entrada digital)
        Q3 - esperando código (entrada manual)
        Q4 - verificando tipo de entrada
        Q5 - verificando autorización
        Q6 - Acceso para ticket general autorizado (caso completo 1)
        Q7 - acceso para ticket de alta gama (VIP) autorizado (caso completo 2)
        Q8 - Acceso rechazado (caso fallido)
        Q9 - cierre del programa
    """
    def __init__(self):
        self.q1 = True
        self.q2 = False
        self.q3 = False
        self.q4 = False
        self.q5 = False
        self.q6 = False
        self.q7 = False
        self.q8 = False
        self.pasos = [] # Se añaden los caminos tomados en función del alfabeto

    def automata_check(self, cadena):
        cadena_events = cadena.split("")

    def evaluacion(self, cadena_events, paso):
        paso += 1

        return self.evaluacion(cadena_events[paso:], paso)

    