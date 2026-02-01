#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Libreria Python per il controllo SCPI degli oscilloscopi Owon serie VDS.
Si connette al software Owon VDS (che deve essere in esecuzione) 
tramite un socket TCP.

*** VERSIONE 41 ***
- Assicura che set_run() e set_stop() siano presenti
  per la logica "Stop-Configura-Avvia".
"""

import socket
import time
import numpy as np 

class SCPI_Subsystem:
    """Classe base per tutti i sottosistemi SCPI."""
    def __init__(self, parent_scope, prefix=""):
        self._scope = parent_scope
        self._prefix = prefix

    def _set(self, command_suffix):
        """Invia un comando SET (senza '?')."""
        cmd = f"{self._prefix}{command_suffix}"
        self._scope._send_command(cmd)

    def _query(self, command_suffix, is_binary=False):
        """Invia un comando QUERY (con '?')."""
        cmd = f"{self._prefix}{command_suffix}"
        return self._scope._query_command(cmd, is_binary=is_binary)

# --- Sottosistemi :TRIGGER ---
class TriggerSingleEdgeCommands(SCPI_Subsystem):
    def set_source(self, source="CH1"): self._set(f":SOURce {source}")
    def get_source(self): return self._query(f":SOURce?")
    def set_slope(self, slope="RISE"): self._set(f":SLOPE {slope}")
    def get_slope(self): return self._query(f":SLOPE?")
    def set_level(self, level_pixels=0): self._set(f":LEVel {level_pixels}")
    def get_level(self): return self._query(f":LEVel?")

class TriggerSingleVideoCommands(SCPI_Subsystem):
    def set_source(self, source="CH1"): self._set(f":SOURce {source}")
    def get_source(self): return self._query(f":SOURce?")
    def set_standard(self, standard="NTSC"): self._set(f":MODU {standard}")
    def get_standard(self): return self._query(f":MODU?")
    def set_sync_type(self, sync_mode="LINE"): self._set(f":SYNC {sync_mode}")
    def get_sync_type(self): return self._query(f":SYNC?")
    def set_line_number(self, line=1): self._set(f":LNUM{line}") 
    def get_line_number(self): return self._query(f":LNUM?")

class TriggerSingleCommands(SCPI_Subsystem):
    def __init__(self, parent_scope, prefix):
        super().__init__(parent_scope, prefix)
        self.edge = TriggerSingleEdgeCommands(parent_scope, f"{self._prefix}:EDGE")
        self.video = TriggerSingleVideoCommands(parent_scope, f"{self._prefix}:VIDeo")
    def set_trigger_type(self, smode="EDGE"): self._set(f" {smode}") 
    def get_trigger_type(self): return self._query(f"?")

class TriggerAltEdgeCommands(SCPI_Subsystem):
    def set_source(self, source="CH1"): self._set(f":SOURce {source}")
    def get_source(self): return self._query(f":SOURce?")
    def set_slope(self, slope="RISE"): self._set(f":SLOPE {slope}")
    def get_slope(self): return self._query(f":SLOPE?")
    def set_level(self, level_pixels=0): self._set(f":LEVel {level_pixels}")
    def get_level(self): return self._query(f":LEVel?")

class TriggerAltVideoCommands(SCPI_Subsystem):
    def set_source(self, source="CH1"): self._set(f":SOURce {source}")
    def get_source(self): return self._query(f":SOURce?")
    def set_standard(self, standard="NTSC"): self._set(f":MODU {standard}")
    def get_standard(self): return self._query(f":MODU?")
    def set_sync_type(self, sync_mode="LINE"): self._set(f":SYNC {sync_mode}")
    def get_sync_type(self): return self._query(f":SYNC?")
    def set_line_number(self, line=1): self._set(f":LNUM{line}")
    def get_line_number(self): return self._query(f":LNUM?")

class TriggerAltCommands(SCPI_Subsystem):
    def __init__(self, parent_scope, prefix):
        super().__init__(parent_scope, prefix)
        self.edge = TriggerAltEdgeCommands(parent_scope, f"{self._prefix}:EDGE")
        self.video = TriggerAltVideoCommands(parent_scope, f"{self._prefix}:VIDeo")
    def set_trigger_type(self, smode="EDGE"): self._set(f" {smode}") 
    def get_trigger_type(self): return self._query(f"?")

class TriggerCommands(SCPI_Subsystem):
    def __init__(self, parent_scope):
        super().__init__(parent_scope, ":TRIGger")
        self.single = TriggerSingleCommands(parent_scope, f"{self._prefix}:SINGle")
        self.alt = TriggerAltCommands(parent_scope, f"{self._prefix}:ALT")
    def set_type(self, trig_type="SINGle"): self._set(f":TYPE {trig_type}")
    def get_type(self): return self._query(f":TYPE?")
    def set_mode(self, mode="AUTO"): self._set(f":MODE {mode}")
    def get_mode(self): return self._query(f":MODE?")

# --- Sottosistemi Principali ---

class MeasureCommands(SCPI_Subsystem):
    """Gestisce i comandi :MEASure"""
    def __init__(self, parent_scope):
        super().__init__(parent_scope, ":MEASure")

    def set_source(self, source="CH1"): self._set(f":SOURce {source}")
    def get_source(self): return self._query(f":SOURce?")
    def add(self, item): self._set(f":ADD {item}")
    def delete(self, item): self._set(f":DELete {item}")
    def delete_all(self): self.delete("ALL")

    def query_specific_channel(self, item, channel_num=1):
        return self._query(f"{channel_num}:{item}?")
    
    def get_period(self, n=1): return self.query_specific_channel("PERiod", n)
    def get_frequency(self, n=1): return self.query_specific_channel("FREQuency", n)
    def get_average(self, n=1): return self.query_specific_channel("AVERage", n)
    def get_max(self, n=1): return self.query_specific_channel("MAX", n)
    def get_min(self, n=1): return self.query_specific_channel("MIN", n)
    def get_vtop(self, n=1): return self.query_specific_channel("VTOP", n)
    def get_vbase(self, n=1): return self.query_specific_channel("VBASE", n)
    def get_vamp(self, n=1): return self.query_specific_channel("VAMP", n)
    def get_pkpk(self, n=1): return self.query_specific_channel("PKPK", n)
    def get_cycrms(self, n=1): return self.query_specific_channel("CYCRms", n)
    def get_rdelay(self, n=1): return self.query_specific_channel("RDELay", n)
    def get_fdelay(self, n=1): return self.query_specific_channel("FDELay", n)

class AcquireCommands(SCPI_Subsystem):
    def __init__(self, parent_scope): super().__init__(parent_scope, ":ACQuire")
    def set_type(self, acq_type="SAMPle"): self._set(f":TYPE {acq_type}")
    def get_type(self): return self._query(f":TYPE?")
    def set_average_count(self, count=4): self._set(f":AVERage {count}")
    def get_average_count(self): return self._query(f":AVERage?")
    def set_memory_depth(self, depth="1K"): self._set(f":MDEPth {depth}") 
    def get_memory_depth(self): return self._query(f":MDEPth?")

class TimebaseCommands(SCPI_Subsystem):
    def __init__(self, parent_scope): super().__init__(parent_scope, ":TIMebase")
    def set_scale(self, scale="200us"): self._set(f":SCALE {scale}")
    def get_scale(self): return self._query(f":SCALE?")
    def set_horizontal_offset(self, offset_pixels=0): self._set(f":HOFFset {offset_pixels}")
    def get_horizontal_offset(self): return self._query(f":HOFFset?")

class FftCommands(SCPI_Subsystem):
    def __init__(self, parent_scope): super().__init__(parent_scope, ":FFT")
    def set_display(self, state=False):
        param = "ON" if state else "OFF"
        self._set(f":DISPlay {param}")
    def get_display(self): return self._query(f":DISPlay?")
    def set_center_frequency(self, freq_hz="10MHz"): self._set(f":FREQbase {freq_hz}")
    def get_center_frequency(self): return self._query(f":FREQbase?")
    def set_source(self, source="CH1"): self._set(f":SOURce {source}")
    def get_source(self): return self._query(f":SOURce?")
    def set_format_vrms(self, vrms_scale="0.5"): self._set(f":FORMat VRMS {vrms_scale}")
    def set_format_db(self, db_scale="2DB"): self._set(f":FORMat DB {db_scale}")
    def get_format(self): return self._query(f":FORMat?")
    def set_window(self, window_type="RECTangle"): self._set(f":WINDow {window_type}")
    def get_window(self): return self._query(f":WINDow?")
    def set_zone(self, factor="X1"): self._set(f":ZONE {factor}")
    def get_zone(self): return self._query(f":ZONE?")

class ChannelCommands(SCPI_Subsystem):
    def __init__(self, parent_scope, channel_num):
        self.channel_num = channel_num
        super().__init__(parent_scope, f":CHANnel{channel_num}")
    def set_display(self, state=False):
        param = "ON" if state else "OFF"
        self._set(f":DISPlay {param}")
    def get_display(self): return self._query(f":DISPlay?")
    def set_coupling(self, coupling="DC"): self._set(f":COUPling {coupling}")
    def get_coupling(self): return self._query(f":COUPling?")
    def set_probe_attenuation(self, atten="X10"): self._set(f":PROBe {atten}")
    def get_probe_attenuation(self): return self._query(f":PROBe?")
    def set_scale(self, scale_v="0.5"): self._set(f":SCALE {scale_v}")
    def get_scale(self): return self._query(f":SCALE?")
    def set_offset(self, offset_pixels=0): self._set(f":OFFSet {offset_pixels}")
    def get_offset(self): return self._query(f":OFFSet?")
    def get_hardware_frequency(self): return self._query(f":HARDfreq?")
    def set_inverse(self, state=False):
        param = "ON" if state else "OFF"
        self._set(f":INVerse {param}")
    def get_inverse(self): return self._query(f":INVerse?")

class LanCommands(SCPI_Subsystem):
    def __init__(self, parent_scope): super().__init__(parent_scope, ":LAN")
    def set_ip_address(self, ip_address): self._set(f":IPADdress {ip_address}")
    def get_ip_address(self): return self._query(f":IPADdress?")
    def set_port(self, port=3000): self._set(f":PORT {port}")
    def get_port(self): return self._query(f":PORT?")
    def set_gateway(self, ip_address): self._set(f":GATeway {ip_address}")
    def get_gateway(self): return self._query(f":GATeway?")
    def set_subnet_mask(self, mask): self._set(f":SMASK {mask}")
    def get_subnet_mask(self): return self._query(f":SMASK?")
    def restart(self): self._set(f":RESTart ON")

# --- CLASSE PRINCIPALE ---
class OwonVDS_SCPI:
    """
    Classe principale per la comunicazione SCPI con l'oscilloscopio
    Owon VDS tramite il software per PC.
    """
    def __init__(self, host='127.0.0.1', port=3000):
        self.host = host
        self.port = port
        self._socket = None
        self._is_connected = False
        
        self.measure = MeasureCommands(self)
        self.acquire = AcquireCommands(self)
        self.timebase = TimebaseCommands(self)
        self.fft = FftCommands(self)
        self.lan = LanCommands(self)
        self.trigger = TriggerCommands(self)
        
        self.channel1 = ChannelCommands(self, 1)
        self.channel2 = ChannelCommands(self, 2)

    def connect(self):
        if self._is_connected:
            print("Già connesso.")
            return
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10.0) 
            self._socket.connect((self.host, self.port))
            self._is_connected = True
            print(f"Connesso a {self.host}:{self.port}")
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Impossibile connettersi a {self.host}:{self.port}. "
                                  f"Il software Owon è attivo e il server SCPI è abilitato? "
                                  f"Errore: {e}")

    def disconnect(self):
        if self._socket:
            self._socket.close()
            self._socket = None
        self._is_connected = False
        
    def _ensure_connection(self):
        if not self._is_connected:
            raise ConnectionError("Non connesso. Chiamare prima il metodo .connect()")

    def _send_command(self, command):
        self._ensure_connection()
        command = command.strip()
        if not command.endswith('\n'):
            command += '\n'
        try:
            self._socket.sendall(command.encode('utf-8'))
            time.sleep(0.1) # Pausa standard dopo ogni invio
        except Exception as e:
            print(f"Errore durante l'invio del comando '{command.strip()}': {e}")
            self.disconnect()

    def _query_command(self, command, is_binary=False):
        """Funzione interna per inviare un comando QUERY."""
        self._ensure_connection()
        command = command.strip()
        if not command.endswith('\n'):
            command += '\n'
        
        try:
            # Pulisce il buffer di ricezione
            self._socket.settimeout(0.1) 
            try:
                while True: self._socket.recv(4096)
            except socket.timeout:
                pass 

            self._socket.settimeout(10.0) 
            self._socket.sendall(command.encode('utf-8'))
            
            response_data = self._socket.recv(65536) 
            
            if is_binary:
                return response_data
            else:
                return response_data.decode('utf-8').strip()
            
        except socket.timeout:
            print(f"TIMEOUT durante l'attesa di risposta per: {command.strip()}")
            return None
        except Exception as e:
            print(f"Errore durante il comando query '{command.strip()}': {e}")
            self.disconnect()
            return None

    # --- Comandi Comuni (Root level) ---
    def get_idn(self):
        return self._query_command("*IDN?")
    def reset_instrument(self):
        return self._query_command("*RST") 
    def autoset(self):
        return self._query_command("*AUToset")
    def toggle_run_stop(self):
        return self._query_command("*RUNStop") 
        
    # --- FUNZIONI AGGIUNTE (V41) ---
    def set_run(self):
        """Avvia l'acquisizione (RUN)."""
        self._send_command("*RUN")

    def set_stop(self):
        """Ferma l'acquisizione (STOP)."""
        self._send_command("*STOP")
    # --- FINE AGGIUNTA ---
        
    def get_adc_data(self, channel_num=1):
        channel_str = f"CH{channel_num}"
        raw_data = self._query_command(f"*ADC? {channel_str}", is_binary=True)
        
        if not raw_data:
            print(f"Errore: Nessun dato ADC ricevuto per {channel_str}")
            return None
        try:
            if len(raw_data) < 500:
                print(f"Errore: Dati ADC incompleti. Ricevuti {len(raw_data)} byte, attesi 500.")
                return None
            
            data_array = np.frombuffer(raw_data[:500], dtype=np.uint8).astype(int)
            return data_array
        except Exception as e:
            print(f"Errore durante la conversione dei dati ADC: {e}")
            return None

    def get_local_deep_memory(self, address=None):
        if address: return self._query_command(f"*LDM? {address}")
        return self._query_command(f"*LDM?")
    def get_remote_deep_memory(self):
        return self._query_command(f"*RDM?")
