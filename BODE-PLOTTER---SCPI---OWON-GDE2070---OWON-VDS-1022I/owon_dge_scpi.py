#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Libreria Python per il controllo SCPI dei generatori di forme d'onda
arbitrarie (AWG) Owon serie DGE2000/3000.

*** VERSIONE AGGIORNATA ***
Utilizza PyVISA per la connessione hardware diretta.
Richiede: pip install pyvisa
"""

import socket
import time
import pyvisa # <-- AGGIUNTO

class SCPI_Subsystem:
    """Classe base per tutti i sottosistemi SCPI."""
    def __init__(self, parent_gen, prefix=""):
        self._gen = parent_gen
        self._prefix = prefix

    def _set(self, command_suffix):
        """Invia un comando SET (senza '?')."""
        cmd = f"{self._prefix}{command_suffix}"
        self._gen._send_command(cmd)

    def _query(self, command_suffix):
        """Invia un comando QUERY (con '?')."""
        cmd = f"{self._prefix}{command_suffix}"
        return self._gen._query_command(cmd)

# --- Sottosistemi SOURce[1/2] ---
# (Tutte le classi da AmCommands a VoltageCommands 
#  rimangono identiche a prima, non c'è bisogno di copiarle di nuovo.
#  Le includo qui per completezza)

class AmCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:AM:..."""
    def set_depth(self, depth):
        self._set(f":AM:DEPTh {depth}")
    def get_depth(self):
        return self._query(f":AM:DEPTh?")
    def set_internal_frequency(self, freq):
        self._set(f":AM:INTernal:FREQuency {freq}")
    def get_internal_frequency(self):
        return self._query(f":AM:INTernal:FREQuency?")
    def set_internal_function(self, shape):
        self._set(f":AM:INTernal:FUNCtion {shape}")
    def get_internal_function(self):
        return self._query(f":AM:INTernal:FUNCtion?")
    def set_source(self, source):
        self._set(f":AM:SOURce {source}")
    def get_source(self):
        return self._query(f":AM:SOURce?")
    def set_state(self, state):
        self._set(f":AM:STATE {state}")
    def get_state(self):
        return self._query(f":AM:STATE?")

class BurstCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:BURSt:..."""
    def set_gate_polarity(self, polarity):
        self._set(f":BURSt:GATE:POLarity {polarity}")
    def get_gate_polarity(self):
        return self._query(f":BURSt:GATE:POLarity?")
    def set_internal_period(self, period):
        self._set(f":BURSt:INTernal:PERiod {period}")
    def get_internal_period(self):
        return self._query(f":BURSt:INTernal:PERiod?")
    def set_mode(self, mode):
        self._set(f":BURSt:MODE {mode}")
    def get_mode(self):
        return self._query(f":BURSt:MODE?")
    def set_n_cycles(self, cycles):
        self._set(f":BURSt:NCYCles {cycles}")
    def get_n_cycles(self):
        return self._query(f":BURSt:NCYCles?")
    def set_source(self, source):
        self._set(f":BURSt:SOURce {source}")
    def get_source(self):
        return self._query(f":BURSt:SOURce?")
    def set_state(self, state):
        self._set(f":BURSt:STATE {state}")
    def get_state(self):
        return self._query(f":BURSt:STATE?")

class FmCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:FM:..."""
    def set_deviation(self, deviation):
        self._set(f":FM:DEViation {deviation}")
    def get_deviation(self):
        return self._query(f":FM:DEViation?")
    def set_internal_frequency(self, freq):
        self._set(f":FM:INTernal:FREQuency {freq}")
    def get_internal_frequency(self):
        return self._query(f":FM:INTernal:FREQuency?")
    def set_internal_function(self, shape):
        self._set(f":FM:INTernal:FUNCtion {shape}")
    def get_internal_function(self):
        return self._query(f":FM:INTernal:FUNCtion?")
    def set_source(self, source):
        self._set(f":FM:SOURce {source}")
    def get_source(self):
        return self._query(f":FM:SOURce?")
    def set_state(self, state):
        self._set(f":FM:STATE {state}")
    def get_state(self):
        return self._query(f":FM:STATE?")

class FrequencyCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:FREQuency:..."""
    def set_center(self, freq):
        self._set(f":FREQuency:CENTer {freq}")
    def get_center(self):
        return self._query(f":FREQuency:CENTer?")
    def set_fixed(self, freq):
        self._set(f":FREQuency:FIXed {freq}")
    def get_fixed(self):
        return self._query(f":FREQuency:FIXed?")
    def set_span(self, freq):
        self._set(f":FREQuency:SPAN {freq}")
    def get_span(self):
        return self._query(f":FREQuency:SPAN?")
    def set_start(self, freq):
        self._set(f":FREQuency:STARt {freq}")
    def get_start(self):
        return self._query(f":FREQuency:STARt?")
    def set_stop(self, freq):
        self._set(f":FREQuency:STOP {freq}")
    def get_stop(self):
        return self._query(f":FREQuency:STOP?")

class FunctionCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:FUNCtion:..."""
    def set_shape(self, shape):
        self._set(f":FUNCtion:SHAPE {shape}")
    def get_shape(self):
        return self._query(f":FUNCtion:SHAPE?")
    def set_ramp_symmetry(self, percent):
        self._set(f":FUNCtion:RAMP:SYMMetry {percent}")
    def get_ramp_symmetry(self):
        return self._query(f":FUNCtion:RAMP:SYMMetry?")

class PmCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:PM:..."""
    def set_deviation(self, deviation):
        self._set(f":PM:DEViation {deviation}")
    def get_deviation(self):
        return self._query(f":PM:DEViation?")
    def set_internal_frequency(self, freq):
        self._set(f":PM:INTernal:FREQuency {freq}")
    def get_internal_frequency(self):
        return self._query(f":PM:INTernal:FREQuency?")
    def set_internal_function(self, shape):
        self._set(f":PM:INTernal:FUNCtion {shape}")
    def get_internal_function(self):
        return self._query(f":PM:INTernal:FUNCtion?")
    def set_source(self, source):
        self._set(f":PM:SOURce {source}")
    def get_source(self):
        return self._query(f":PM:SOURce?")
    def set_state(self, state):
        self._set(f":PM:STATE {state}")
    def get_state(self):
        return self._query(f":PM:STATE?")

class PulseCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:PULSe:..."""
    def set_duty_cycle(self, percent):
        self._set(f":PULSe:DCYCle {percent}")
    def get_duty_cycle(self):
        return self._query(f":PULSe:DCYCle?")
    def set_leading_edge(self, seconds):
        self._set(f":PULSe:TRANsition:LEADing {seconds}")
    def get_leading_edge(self):
        return self._query(f":PULSe:TRANsition:LEADing?")
    def set_trailing_edge(self, seconds):
        self._set(f":PULSe:TRANsition:TRAiling {seconds}")
    def get_trailing_edge(self):
        return self._query(f":PULSe:TRANsition:TRAiling?")
    def set_width(self, seconds):
        self._set(f":PULSe:WIDTh {seconds}")
    def get_width(self):
        return self._query(f":PULSe:WIDTh?")

class SweepCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:SWEep:..."""
    def set_source(self, source):
        self._set(f":SWEep:SOURce {source}")
    def get_source(self):
        return self._query(f":SWEep:SOURce?")
    def set_spacing(self, spacing):
        self._set(f":SWEep:SPACing {spacing}")
    def get_spacing(self):
        return self._query(f":SWEep:SPACing?")
    def set_state(self, state):
        self._set(f":SWEep:STATE {state}")
    def get_state(self):
        return self._query(f":SWEep:STATE?")
    def set_time(self, seconds):
        self._set(f":SWEep:TIME {seconds}")
    def get_time(self):
        return self._query(f":SWEep:TIME?")

class VoltageCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:VOLTage:..."""
    def set_offset(self, volts):
        self._set(f":VOLTage:OFFSet {volts}")
    def get_offset(self):
        return self._query(f":VOLTage:OFFSet?")
    def set_amplitude(self, vpp):
        self._set(f":VOLTage:AMPLitude {vpp}")
    def get_amplitude(self):
        return self._query(f":VOLTage:AMPLitude?")

class SourceCommands(SCPI_Subsystem):
    """Gestisce i comandi [SOURce[1/2]]:..."""
    def __init__(self, parent_gen, channel):
        super().__init__(parent_gen, f"SOURce{channel}") 
        self.am = AmCommands(parent_gen, self._prefix)
        self.burst = BurstCommands(parent_gen, self._prefix)
        self.fm = FmCommands(parent_gen, self._prefix)
        self.pm = PmCommands(parent_gen, self._prefix)
        self.sweep = SweepCommands(parent_gen, self._prefix)
        self.frequency = FrequencyCommands(parent_gen, self._prefix)
        self.function = FunctionCommands(parent_gen, self._prefix)
        self.pulse = PulseCommands(parent_gen, self._prefix)
        self.voltage = VoltageCommands(parent_gen, self._prefix)
    
    def set_modulation_state(self, state):
        self._set(f":MODE:STATE {state}")
    def get_modulation_state(self):
        return self._query(f":MODE:STATE?")
    def set_phase(self, phase_value, units="RAD"):
        if "DEG" in str(phase_value).upper() or "RAD" in str(phase_value).upper():
             self._set(f":PHASe:ADJust {phase_value}")
        else:
             self._set(f":PHASe:ADJust {phase_value}{units}")
    def get_phase(self):
        return self._query(f":PHASe:ADJust?")

# --- Sottosistemi di Livello Superiore ---

class CounterCommands(SCPI_Subsystem):
    """Gestisce i comandi COUNter:..."""
    def __init__(self, parent_gen):
        super().__init__(parent_gen, "COUNter")
    def set_coupling(self, mode):
        self._set(f":COUPling {mode}")
    def get_coupling(self):
        return self._query(f":COUPling?")
    def get_duty_cycle(self):
        return self._query(f":DUTYcycle?")
    def get_frequency(self):
        return self._query(f":FREQ?")
    def set_high_freq_reject(self, state):
        self._set(f":HFR {state}")
    def get_high_freq_reject(self):
        return self._query(f":HFR?")
    def get_period(self):
        return self._query(f":PERiod?")
    def get_pulse_width(self):
        return self._query(f":PULSewidth?")
    def set_sensitivity(self, level):
        self._set(f":SENSitivity {level}")
    def get_sensitivity(self):
        return self._query(f":SENSitivity?")

class DisplayCommands(SCPI_Subsystem):
    """Gestisce i comandi DISPlay:..."""
    def __init__(self, parent_gen):
        super().__init__(parent_gen, "DISPlay")
    def set_brightness(self, level):
        self._set(f":BRIGhtness {level}")
    def get_brightness(self):
        return self._query(f":BRIGhtness?")
    def set_saver_delay(self, minutes):
        self._set(f":SAVer:DELay {minutes}")
    def get_saver_delay(self):
        return self._query(f":SAVer:DELay?")
    def trigger_saver_now(self):
        self._set(f":SAVer:IMMediate")
    def set_saver_state(self, state):
        self._set(f":SAVer:STATE {state}")
    def get_saver_state(self):
        return self._query(f":SAVer:STATE?")

class HardcopyCommands(SCPI_Subsystem):
    """Gestisce i comandi HCOPY:..."""
    def __init__(self, parent_gen):
        super().__init__(parent_gen, "HCOPY")
    def get_screen_dump_data(self):
        return self._query(f":SDUMP:DATA?")
    def save_screen_to_usb(self):
        self._set(f":SDUMp:IMMediate")

class OutputCommands(SCPI_Subsystem):
    """Gestisce i comandi OUTPut[1/2]:..."""
    def __init__(self, parent_gen, channel):
        super().__init__(parent_gen, f"OUTPut{channel}")
    def set_impedance(self, ohms):
        self._set(f":IMPedance {ohms}")
    def get_impedance(self):
        return self._query(f":IMPedance?")
    def set_state(self, state):
        self._set(f":STATE {state}")
    def get_state(self):
        return self._query(f":STATE?")

class SystemCommands(SCPI_Subsystem):
    """Gestisce i comandi SYSTem:..."""
    def __init__(self, parent_gen):
        super().__init__(parent_gen, "SYSTem")
    def beep(self):
        self._set(f":BEEPer:IMMediate")
    def set_beeper_state(self, state):
        self._set(f":BEEPer:STATE {state}")
    def get_beeper_state(self):
        return self._query(f":BEEPer:STATE?")
    def get_error(self):
        return self._query(f":ERRor:NEXT?")
    def set_language(self, lang):
        self._set(f":LANguage {lang}")
    def get_language(self):
        return self._query(f":LANguage?")
    def get_version(self):
        return self._query(f":VERSion?")

class TraceCommands(SCPI_Subsystem):
    """Gestisce i comandi TRACE:DATA:..."""
    def __init__(self, parent_gen):
        super().__init__(parent_gen, "TRACE:DATA")
    def set_data(self, binary_block_data):
        self._set(f":DATA EMEMory, {binary_block_data}")
    def get_data(self):
        return self._query(f":DATA? EMEMory")

# --- CLASSE PRINCIPALE DEL GENERATORE (MODIFICATA PER PYVISA) ---

class OwonDGE_SCPI:
    """
    Classe principale per la comunicazione SCPI con il generatore
    Owon serie DGE2000/3000. Usa PyVISA.
    """
    def __init__(self, visa_resource_string):
        """Inizializza la connessione usando una stringa di risorsa VISA."""
        self.visa_string = visa_resource_string
        self.instrument = None
        self._is_connected = False
        
        # Inizializza tutti i sottosistemi di primo livello
        self.counter = CounterCommands(self)
        self.display = DisplayCommands(self)
        self.hardcopy = HardcopyCommands(self)
        self.system = SystemCommands(self)
        self.trace = TraceCommands(self)
        
        # Inizializza i sottosistemi per-canale
        self.output1 = OutputCommands(self, 1)
        self.output2 = OutputCommands(self, 2)
        self.source1 = SourceCommands(self, 1)
        self.source2 = SourceCommands(self, 2)

    def connect(self):
        """Si connette al generatore tramite PyVISA."""
        if self._is_connected:
            print("Già connesso.")
            return
        try:
            rm = pyvisa.ResourceManager()
            self.instrument = rm.open_resource(self.visa_string)
            self.instrument.timeout = 5000 # 5 secondi di timeout
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            self._is_connected = True
            print(f"Connesso a {self.visa_string}")
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Impossibile connettersi a {self.visa_string}. "
                                  f"Controllare la stringa VISA e la connessione. Errore: {e}")

    def disconnect(self):
        """Si disconnette dal generatore."""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        self._is_connected = False
        
    def _ensure_connection(self):
        if not self._is_connected:
            raise ConnectionError("Non connesso. Chiamare prima il metodo .connect()")

    def _send_command(self, command):
        """Funzione interna per inviare un comando SET."""
        self._ensure_connection()
        command = command.strip()
        try:
            self.instrument.write(command)
            time.sleep(0.1) # Piccolo delay per l'elaborazione
        except Exception as e:
            print(f"Errore durante l'invio del comando '{command.strip()}': {e}")
            self.disconnect()

    def _query_command(self, command):
        """Funzione interna per inviare un comando QUERY."""
        self._ensure_connection()
        command = command.strip()
        try:
            response = self.instrument.query(command)
            return response.strip()
            
        except socket.timeout:
            print(f"TIMEOUT durante l'attesa di risposta per: {command.strip()}")
            return None
        except Exception as e:
            print(f"Errore durante il comando query '{command.strip()}': {e}")
            self.disconnect()
            return None

    # --- Comandi Comuni (Root level) ---
    def get_idn(self):
        """Interroga la stringa di identificazione del dispositivo. [*IDN?]"""
        return self._query_command("*IDN?")

    def reset(self):
        """Resetta lo strumento ai valori di fabbrica. [*RST]"""
        self._send_command("*RST")