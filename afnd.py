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
        self.q1 = False
        self.q2 = False
        self.q3 = False
        self.q4 = False
        self.q5 = False
        self.q6 = False
        self.q7 = False
        self.q8 = False
        self.tipo_detectado = None
        self.q9 = True
        self.pasos = [] # Se añaden los caminos tomados en función del alfabeto

    def automata_check(self, cadena, pasos):
        """itera sobre la cadena que contiene el alfabeto una "n" cantidad de pasos, o "-1" para evaluar toda la cadena.
        Retorna:
        - estado final del autómata [bool]
        - texto explicativo del estado [str]
        - Lista final de los estados -> List<Bool>"""
        for simbolo in cadena:
            if simbolo not in "qgvicae":
                return False, f"Cadena inválida: símbolo '{simbolo}' no pertenece al alfabeto", self._foto_estados()

        simbolos = list(cadena)
        if pasos == -1:
            pasos = len(simbolos)

        return self.evaluacion(simbolos, pasos)


    def evaluacion(self, simbolos, n_pasos):
        if n_pasos == 0 or not simbolos:
            return self._resultado_final()
 
        simbolo_actual = simbolos[0]
        resto = simbolos[1:]
 
        self.transicion(simbolo_actual)
 
        return self.evaluacion(resto, n_pasos - 1)

    
    def transicion(self, simbolo):
        self.q9 = False  
 
        if not self.q1 and simbolo in "qc":
            self.q1 = True
            self.pasos.append(f"'{simbolo}' -> Q1 (ticket recibido)")
 
        elif self.q1 and not (self.q2 or self.q3) and simbolo == "q":
            self.q2 = True
            self.pasos.append(f"'{simbolo}' -> Q2 (esperando QR / entrada digital)")
 
        elif self.q1 and not (self.q2 or self.q3) and simbolo == "c":
            self.q3 = True
            self.pasos.append(f"'{simbolo}' -> Q3 (esperando código / entrada manual)")
 
        elif (self.q2 or self.q3) and not self.q4 and simbolo in "vgi":
            self.q4 = True
            self.tipo_detectado = simbolo
            self.pasos.append(f"'{simbolo}' -> Q4 (verificando tipo de entrada)")
 
        elif self.q4 and not self.q5 and simbolo in "vgi":
            # Excepción: una invitación ('i') no se confirma repitiendo 'i',
            # sino con el tipo real de acceso que la invitación otorga (g o v).
            if self.tipo_detectado == "i":
                confirmacion_valida = simbolo in ("g", "v")
            else:
                confirmacion_valida = simbolo == self.tipo_detectado

            if confirmacion_valida:
                self.q5 = True
                self.tipo_detectado = simbolo  # se reemplaza 'i' por el tipo real confirmado (g o v)
                self.pasos.append(f"'{simbolo}' -> Q5 (confirmación de tipo correcta, verificando autorización)")
            else:                
                self.q8 = True
                if simbolo == "i":
                    self.pasos.append(f"'{simbolo}' -> Q8 (ERROR: Se repite el símbolo'{simbolo}', pero nunca se confirma de qué tipo es '{self.tipo_detectado}')")
                else:
                    self.pasos.append(f"'{simbolo}' -> Q8 (FRAUDE: confirmación '{simbolo}' no coincide con la detección inicial '{self.tipo_detectado}')")

        elif self.q5 and simbolo == "a" and self.tipo_detectado == "g":
            self.q6 = True
            self.pasos.append(f"'{simbolo}' -> Q6 (acceso GENERAL autorizado)")

        elif self.q5 and simbolo == "a" and self.tipo_detectado == "v":
            self.q7 = True
            self.pasos.append(f"'{simbolo}' -> Q7 (acceso VIP autorizado)")

        elif simbolo == "e":
            self.q8 = True
            self.pasos.append(f"'{simbolo}' -> Q8 (acceso rechazado)")
 
        else:
            self.pasos.append(f"'{simbolo}' -> (sin transición válida desde el estado actual)")
 
  
    def _foto_estados(self):
        return [self.q1, self.q2, self.q3, self.q4, self.q5, self.q6, self.q7, self.q8, self.q9]
 
    def _resultado_final(self):
        if self.q6:
            return True, "Acceso GENERAL autorizado (Q6)", self._foto_estados()
        if self.q7:
            return True, "Acceso VIP autorizado (Q7)", self._foto_estados()
        if self.q8:
            return False, "Acceso rechazado (Q8)", self._foto_estados()
        return False, "Cadena incompleta: no se alcanzó un estado final", self._foto_estados()

    def estados_activos(self):
        """
        Versión serializable (lista de strings 'Q0'..'Q8') para mandar por
        JSON a la página del simulador. Si todavía no entró ningún símbolo
        (self.q9 sigue True), el autómata está en reposo en Q0.
        """
        if self.q9:
            return ["Q0"]
 
        nombres = {
            "q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4",
            "q5": "Q5", "q6": "Q6", "q7": "Q7", "q8": "Q8",
        }
        activos = [nombre for attr, nombre in nombres.items() if getattr(self, attr)]
        return activos if activos else ["Q0"]


    