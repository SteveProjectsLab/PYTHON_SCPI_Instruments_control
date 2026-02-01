#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bode Plotter - Funzioni Core (V47 Refactored)

V47: Logica "Stima Fissa" + "Inganno Sonda" (NO AUTO-RANGING).
     L'auto-ranging dinamico è troppo instabile con il VDS.
     
     Questa logica V47 è la più robusta finora:
     1. Per ogni freq: scope.set_stop()
     2. Attendi 1.5s
     3. Imposta Timebase e CH1 (calcolati) -> ATTENDI
     4. Esegui "Inganno Sonda" (X1 -> set_scale -> X10)
        ma usa la *stessa scala di CH1* come "stima fissa".
     5. Imposta Offsets a 0 -> ATTENDI
     6. scope.set_run() (in modalità AUTO)
     7. Attendi stabilizzazione 3s
     8. Esegui la misura media V30.
"""

import time
import math
import numpy
import matplotlib.pyplot as plt
import json 
import os 
import csv 

# --- GESTIONE CONFIGURAZIONE ---
CONFIG_FILENAME = 'bode_config.json'

# --- NUOVE COSTANTI PER IL SALVATAGGIO ---

# Trova il percorso assoluto della directory in cui si trova QUESTO script
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# Crea i percorsi per DATA e PLOTS partendo da SCRIPT_DIR
DATA_DIR = os.path.join(SCRIPT_DIR, "DATA")
PLOTS_DIR = os.path.join(DATA_DIR, "PLOTS")

FACTORY_DEFAULTS = {
    'f_start': 1.0,
    'f_stop': 100000.0,
    'num_points': 20, 
    'num_points_lin': 50, 
    'scale': 'log',
    'num_averages': 3,
    'gen_amplitude_vpp': 1.0,
    'y_mag_min': -100.0, 
    'y_mag_max': 10.0,
    'y_mag_min_lin': -40.0 
}

# Mappatura dei valori di timebase (in secondi) alle stringhe SCPI
VDS_TIMEBASE_MAP = {
    5e-9: '5ns', 10e-9: '10ns', 20e-9: '20ns', 50e-9: '50ns',
    100e-9: '100ns', 200e-9: '200ns', 500e-9: '500ns',
    1e-6: '1us', 2e-6: '2us', 5e-6: '5us',
    10e-6: '10us', 20e-6: '20us', 50e-6: '50us',
    100e-6: '100us', 200e-6: '200us', 500e-6: '500us',
    1e-3: '1ms', 2e-3: '2ms', 5e-3: '5ms',
    10e-3: '10ms', 20e-3: '20ms', 50e-3: '50ms',
    100e-3: '100ms', 200e-3: '200ms', 500e-3: '500ms',
    1.0: '1s', 2.0: '2s', 5.0: '5s',
    10.0: '10s', 20.0: '20s', 50.0: '50s', 100.0: '100s'
}
VALID_TIMEBASES = sorted(VDS_TIMEBASE_MAP.keys())

# Lista di float (Volt) per i comandi SCPI
VALID_VDIVS = sorted([
    0.005, 0.01, 0.02, 0.05,
    0.1, 0.2, 0.5,
    1.0, 2.0, 5.0
])

# --- FUNZIONI HELPER (V42) ---

#def get_optimal_vdiv(vpp):
#    """
#    Calcola la V/div ottimale (come float in Volt)
#    per visualizzare un segnale Vpp su circa 5 divisioni.
#    """
#    if vpp < 0.001: vpp = 0.001 # Prevenzione divisione per zero
#    ideal_v_per_div = vpp / 5.0 
#    for v_div in VALID_VDIVS:
#        if v_div >= ideal_v_per_div:
#            return v_div # Ritorna il float, es. 0.2
#    return VALID_VDIVS[-1] # Ritorna il float, es. 5.0#

def get_optimal_timebase(freq):
    """
    Calcola la timebase ottimale per visualizzare ~2 PERIODI.
    """
    if freq <= 0: return '1s', 1.0
    period = 1.0 / freq
    ideal_time_per_div = (period * 2.0) / 10.0 
    for t_base_sec in VALID_TIMEBASES:
        if t_base_sec >= ideal_time_per_div:
            return VDS_TIMEBASE_MAP[t_base_sec], t_base_sec
    t_base_sec = VALID_TIMEBASES[-1]
    return VDS_TIMEBASE_MAP[t_base_sec], t_base_sec

# --- FUNZIONI DI CONFIGURAZIONE (JSON E UTENTE) ---
# (Invariate)

def load_config():
    if os.path.exists(CONFIG_FILENAME):
        try:
            with open(CONFIG_FILENAME, 'r') as f:
                config = json.load(f)
                config.update({k: v for k, v in FACTORY_DEFAULTS.items() if k not in config})
                return config
        except json.JSONDecodeError:
            print(f"Attenzione: file di configurazione '{CONFIG_FILENAME}' corrotto. Uso i default di fabbrica.")
            return FACTORY_DEFAULTS.copy()
    else:
        return FACTORY_DEFAULTS.copy()

def save_config(config):
    try:
        with open(CONFIG_FILENAME, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configurazione salvata come nuovo default in '{CONFIG_FILENAME}'.")
    except IOError as e:
        print(f"ERRORE: Impossibile salvare la configurazione: {e}")

def get_user_config(default_config):
    print("\n--- Modifica Configurazione Esperimento ---")
    config = default_config.copy() 
    while True:
        scale_default = config['scale']
        scale = input(f"Scala Frequenza Lineare (lin) o Logaritmica (log)? [{scale_default}]: ").lower() or scale_default
        if scale in ["lin", "log"]:
            config['scale'] = scale
            break
        print("Errore: inserisci 'lin' o 'log'.")
    while True:
        f_start_default = config['f_start']
        try:
            f_start_str = input(f"Inserisci Frequenza Iniziale (Hz) [{f_start_default}]: ") or str(f_start_default)
            f_start = float(f_start_str)
            if config['scale'] == 'log' and f_start <= 0:
                print("ERRORE: La frequenza iniziale per una scala logaritmica deve essere MAGGIORE di zero.")
            else:
                config['f_start'] = f_start
                break
        except ValueError:
            print("Errore: inserisci un numero.")
    while True:
        f_stop_default = config['f_stop']
        try:
            f_stop_str = input(f"Inserisci Frequenza Finale (Hz) [{f_stop_default}]: ") or str(f_stop_default)
            f_stop = float(f_stop_str)
            if f_stop <= config['f_start']:
                print("ERRORE: La frequenza finale deve essere maggiore di quella iniziale.")
            else:
                config['f_stop'] = f_stop
                break
        except ValueError:
            print("Errore: inserisci un numero.")
    if config['scale'] == 'lin':
        points_default = config.get('num_points_lin', FACTORY_DEFAULTS['num_points_lin'])
    else:
        points_default = config.get('num_points', FACTORY_DEFAULTS['num_points'])
    config['num_points'] = int(input(f"Inserisci Numero di Punti [{points_default}]: ") or points_default)
    if config['scale'] == 'lin':
        config['num_points_lin'] = config['num_points']
    avg_default = config['num_averages']
    config['num_averages'] = int(input(f"Inserisci Numero di Medie per Punto [{avg_default}]: ") or avg_default)
    amp_default = config['gen_amplitude_vpp']
    config['gen_amplitude_vpp'] = float(input(f"Inserisci Ampiezza Generatore (Vpp) [{amp_default}]: ") or amp_default)
    if config['scale'] == 'lin':
        mag_min_default = config.get('y_mag_min_lin', FACTORY_DEFAULTS['y_mag_min_lin'])
    else:
        mag_min_default = config.get('y_mag_min', FACTORY_DEFAULTS['y_mag_min'])
    config['y_mag_min'] = float(input(f"Ampiezza Minima Grafico (dB) [{mag_min_default}]: ") or mag_min_default)
    if config['scale'] == 'lin':
         config['y_mag_min_lin'] = config['y_mag_min']
    mag_max_default = config['y_mag_max']
    config['y_mag_max'] = float(input(f"Ampiezza Massima Grafico (dB) [{mag_max_default}]: ") or mag_max_default)
    return config

def print_config(config, gen_string, scope_string):
    """Mostra un riepilogo della configurazione."""
    print("\n--- Riepilogo Configurazione ---")
    print(f"  Strumenti:")
    print(f"    Generatore:    {gen_string}")
    print(f"    Oscilloscopio: {scope_string}")
    print(f"\n  Parametri Sweep:")
    print(f"    Frequenza:     {config['f_start']} Hz a {config['f_stop']} Hz")
    print(f"    Punti:         {config['num_points']} (Scala {config['scale']})")
    print(f"    Ampiezza GEN: {config['gen_amplitude_vpp']} Vpp")
    print(f"\n  Parametri Misura:")
    print(f"    Medie:         {config['num_averages']}")
    print(f"\n  Parametri Grafico:")
    print(f"    Range Modulo: {config['y_mag_min']} dB a {config['y_mag_max']} dB")
    print("---------------------------------")

# --- FUNZIONI DI ACQUISIZIONE (V30) ---

def read_measurement_with_polling(scope_measure_func, *args, timeout_sec=10.0, invalid_val=1e30, **kwargs):
    """
    Continua a chiamare una funzione di misura finché non restituisce
    un valore valido.
    Restituisce ANCHE i valori di overload (>1e30).
    """
    start_time = time.time()
    last_val_str = "N/A" 

    while time.time() - start_time < timeout_sec:
        try:
            val_str = scope_measure_func(*args, **kwargs) 
            last_val_str = val_str
            val_float = float(val_str)
            return val_float 
        except ValueError:
            pass
        except Exception as e:
            print(f"  Errore polling misura ({scope_measure_func.__name__}): {e}")
            return None
        time.sleep(0.25) 

    print(f"  ERRORE: Timeout leggendo {scope_measure_func.__name__}. Ultimo valore: {last_val_str}")
    return None


def get_measurement_avg_auto(scope, num_averages, t_base_sec):
    """
    Esegue una MEDIA SOFTWARE (V30) leggendo N volte
    i valori dallo scope in modalità AUTO.
    """
    vpp1_vals = []
    vpp2_vals = []
    delay_vals = []
    
    VDS_PAUSE_MEAS = 0.2
    wait_per_reading = max(t_base_sec * 2.0, 0.5) # Attendi 2 divisioni o 0.5s
    
    print(f"  Acquisizione di {num_averages} medie software (in modo AUTO)...")
    
    try:
        # 1. Aggiungi le misure
        scope.measure.delete_all()
        time.sleep(VDS_PAUSE_MEAS)
        scope.measure.set_source("CHAN1")
        time.sleep(VDS_PAUSE_MEAS)
        scope.measure.add("PKPK")
        time.sleep(VDS_PAUSE_MEAS)
        scope.measure.add("FDELay") 
        time.sleep(VDS_PAUSE_MEAS)
        scope.measure.set_source("CHAN2")
        time.sleep(VDS_PAUSE_MEAS)
        scope.measure.add("PKPK")
        time.sleep(VDS_PAUSE_MEAS)

        # 2. Ciclo di lettura
        for i in range(num_averages):
            print(f"  Media {i+1}/{num_averages}: Attesa per nuova misura ({wait_per_reading:.2f}s)...")
            time.sleep(min(wait_per_reading, 5.0)) # Limita attesa a 5s

            # 3. LEGGI le misure (con polling)
            vpp1 = read_measurement_with_polling(scope.measure.get_pkpk, n=1, timeout_sec=10.0)
            vpp2 = read_measurement_with_polling(scope.measure.get_pkpk, n=2, timeout_sec=10.0)
            delay = read_measurement_with_polling(scope.measure.get_fdelay, n=1, timeout_sec=10.0)

            if vpp1 is None or vpp2 is None or delay is None \
               or vpp1 > 1e30 or vpp2 > 1e30 or abs(delay) > 1e30:
                print(f"  Media {i+1}: Errore (Overload o Timeout). Salto.")
                continue

            if vpp1 < 1e-9:
                print(f"  Media {i+1}: Errore (Vpp1 troppo basso: {vpp1}). Salto.")
                continue

            vpp1_vals.append(vpp1)
            vpp2_vals.append(vpp2)
            delay_vals.append(delay)
            
    except Exception as e:
        print(f"  Errore fatale durante la misura: {e}. Salto.")
        return None, None, None
    finally:
        pass

    if not vpp1_vals or not vpp2_vals or not delay_vals: 
        return None, None, None

    # Calcola le medie
    avg_vpp1 = sum(vpp1_vals) / len(vpp1_vals)
    avg_vpp2 = sum(vpp2_vals) / len(vpp2_vals)
    avg_delay = sum(delay_vals) / len(delay_vals)
    
    return avg_vpp1, avg_vpp2, avg_delay

# --- FUNZIONI DI ESECUZIONE (V47 Modificata) ---

def setup_initial_state(gen, scope, config):
    """
    Applica la configurazione *minima* necessaria (V47).
    """
    VDS_PAUSE = 0.3 # 300ms

    print("\n--- 1. Configurazione Strumenti ---")
    
    vpp_in = config['gen_amplitude_vpp']
    
    gen.source1.function.set_shape("SINusoid")
    gen.source1.voltage.set_amplitude(f"{vpp_in}Vpp")
    gen.output1.set_impedance("INFinity")
    gen.source1.voltage.set_offset("0V") 
    print("  Generatore: Configurazione impostata (Alta Z, Offset 0V).")
    
    
    print("  Oscilloscopio: Configurazione minima (Accoppiamento e Sonde)...")
    scope.channel1.set_display(True); time.sleep(VDS_PAUSE)
    scope.channel2.set_display(True); time.sleep(VDS_PAUSE)
    
    scope.channel1.set_coupling("DC"); time.sleep(VDS_PAUSE)
    scope.channel2.set_coupling("DC"); time.sleep(VDS_PAUSE)
    print("  Oscilloscopio: Accoppiamento CH1 e CH2 impostato su DC.")

    scope.channel1.set_probe_attenuation("X1"); time.sleep(VDS_PAUSE)
    print("  Oscilloscopio: Sonda CH1 impostata su 1X.")
    # La sonda CH2 la impostiamo *durante* lo sweep
    
    # Impostiamo la modalità di acquisizione QUI, una sola volta.
    scope.acquire.set_type("SAMPle"); time.sleep(VDS_PAUSE)
    print("  Oscilloscopio: Modo acquisizione impostato su SAMPle.")
    
    # Impostiamo l'offset a 0 qui, come stato iniziale
    print("  Oscilloscopio: Imposto Offset a 0...")
    scope.channel1.set_offset(0); time.sleep(VDS_PAUSE)
    scope.channel2.set_offset(0); time.sleep(VDS_PAUSE)

    print("  Generatore: Avvio Uscita CH1 (ON).")
    gen.output1.set_state("ON")


def run_full_experiment(gen, scope, config):
    """
    Esegue l'intero esperimento: setup, sweep, acquisizione
    e restituisce i risultati. (Logica V47 - "Inganno Sonda" + Stima Fissa)
    """
    
    VDS_PAUSE = 0.3 # Pausa breve
    STOP_WAIT = 1.5 # Attesa dopo STOP
    RUN_STABILIZE_WAIT = 3.0 # Attesa dopo RUN
    SCALE_WAIT = 2.0 # Attesa dopo ogni comando di scala/sonda
    
    # 1. Applica la configurazione minima
    setup_initial_state(gen, scope, config)
    vpp_in = config['gen_amplitude_vpp'] 

    # 2. Genera lista frequenze
    if config['scale'] == 'log':
        freq_list = numpy.logspace(
            math.log10(config['f_start']), 
            math.log10(config['f_stop']), 
            config['num_points']
        )
    else:
        freq_list = numpy.linspace(
            config['f_start'], 
            config['f_stop'], 
            config['num_points']
        )
        
    results_freq = []
    results_mag = []
    results_phase = []
    
    print("\n--- 2. Avvio Esperimento (Sweep) ---")
    v_div_ch1_val = 1#get_optimal_vdiv(vpp_in)
    print(f"  Forzo V/div CH1 a: {v_div_ch1_val}V (attesa {SCALE_WAIT}s)...")
    scope.channel1.set_scale(v_div_ch1_val); time.sleep(SCALE_WAIT) 
    
    print("  Forzo trigger su CH1...")
    scope.trigger.single.edge.set_source("CH1"); time.sleep(VDS_PAUSE)
 

    
    print(f"  CH2 Config: Imposto scala stima a: {1}V (attesa {SCALE_WAIT}s)...")
    scope.channel2.set_scale(1); time.sleep(SCALE_WAIT)
    

    
    # Correzione Offset (SOLO QUI)
    print("  Correzione Offset a 0...")
    scope.channel1.set_offset(0); time.sleep(VDS_PAUSE)
    scope.channel2.set_offset(0); time.sleep(VDS_PAUSE)
    
    # 3. AVVIA LO SCOPE (in AUTO)
    print(f"  Invio comando RUN (AUTO) e attesa stabilizzazione ({RUN_STABILIZE_WAIT}s)...")
    scope.trigger.set_mode("AUTO"); time.sleep(VDS_PAUSE) 
    scope.set_run()
    time.sleep(RUN_STABILIZE_WAIT)
    try:
        for i, freq in enumerate(freq_list):
            if freq <= 0: 
                print(f"Salto Frequenza non valida: {freq} Hz")
                continue
                
            print(f"\nPunto {i+1}/{config['num_points']} - Frequenza: {freq:.2f} Hz")
            
            gen.source1.frequency.set_fixed(f"{freq}Hz")
            
            period = 1.0 / freq
            wait_for_signal = max(period * 3, 0.5) 
            print(f"  Attesa stabilizzazione segnale ({wait_for_signal:.2f}s)...")
            time.sleep(min(wait_for_signal, 5.0))
            
            # --- LOGICA V47 ---
            
            # 1. FERMA LO SCOPE
            print(f"  Invio comando STOP per configurare (attesa {STOP_WAIT}s)...")
            scope.set_stop()
            time.sleep(STOP_WAIT)

            # 2. CONFIGURA (mentre è in STOP e con pause lunghe)
            print("  Configurazione scale (da fermo)...")
            t_base_str, t_base_sec = get_optimal_timebase(freq)
            print(f"  Forzo Timebase a: {t_base_str} (attesa {SCALE_WAIT}s)...")
            scope.timebase.set_scale(t_base_str); time.sleep(SCALE_WAIT)
            
            
            
            # 4. Misure (V30)
            vpp1, vpp2, delay = get_measurement_avg_auto(scope, config['num_averages'], t_base_sec) 
            
            if vpp1 is None or vpp2 is None or delay is None:
                print("  Misure fallite per questo punto. Salto.")
                continue

            if vpp1 < 1e-9: vpp1 = 1e-9 
            
            magnitude_db = 20 * math.log10(vpp2 / vpp1)
            
            phase_deg = (-delay * freq * 360.0) % 360.0 
            if phase_deg > 180.0:
                phase_deg -= 360.0
            
            results_freq.append(freq)
            results_mag.append(magnitude_db)
            results_phase.append(phase_deg)
            
            print(f"  -> Risultato: Ampiezza: {magnitude_db:.2f} dB | Fase: {phase_deg:.2f}°")
            
    except KeyboardInterrupt:
        print("\n--- Interruzione utente ---")
    finally:
        try:
            gen.output1.set_state("OFF")
            print("\n--- Esperimento Terminato. Uscita Generatore SPENTA ---")
        except KeyboardInterrupt:
            print("\nInterrotto during lo spegnimento del generatore.")
        except Exception as e:
            print(f"Errore during lo spegnimento del generatore: {e}")

    # Rimette lo scope in modalità AUTO e SAMPle alla fine
    try:
        if scope and scope._is_connected:
            scope.acquire.set_type("SAMPle")
            scope.trigger.set_mode("AUTO")
    except Exception:
        pass # Ignora errori se la connessione è già chiusa

    return results_freq, results_mag, results_phase, config

# --- NUOVE FUNZIONI DI SALVATAGGIO ---

def ensure_save_directories():
    """Crea le cartelle DATA e DATA/PLOTS se non esistono."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)

def get_next_filename(directory, prefix, extension):
    """
    Trova il prossimo nome file incrementale (es. BODE_data_001.csv).
    """
    ensure_save_directories() # Assicura che le cartelle esistano
    i = 1
    while True:
        # Formatta il nome file con 3 cifre (001, 002, ...)
        filename = f"{prefix}_{i:03d}{extension}"
        full_path = os.path.join(directory, filename)
        
        # Se il file NON esiste, abbiamo trovato il nome giusto
        if not os.path.exists(full_path):
            return full_path
        i += 1

def save_data_to_csv(freq_list, mag_list, phase_list, filepath):
    """Salva i risultati dell'esperimento in un file CSV."""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Scrivi l'intestazione
            writer.writerow(["Frequency (Hz)", "Magnitude (dB)", "Phase (deg)"])
            # Scrivi i dati
            for i in range(len(freq_list)):
                writer.writerow([freq_list[i], mag_list[i], phase_list[i]])
        print(f"Dati salvati con successo in: {filepath}")
    except IOError as e:
        print(f"ERRORE: Impossibile salvare il file CSV: {e}")
    except Exception as e:
        print(f"ERRORE inaspettato durante salvataggio CSV: {e}")

# --- FUNZIONE DI PLOTTING (MODIFICATA) ---

def plot_results(freq, mag, phase, config):
    """
    Crea e *mostra* i diagrammi di Bode in una finestra grafica.
    Restituisce l'oggetto 'figure' per un eventuale salvataggio.
    """
    print("Visualizzazione grafici...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
    fig.suptitle('Diagramma di Bode - Risposta in Frequenza', fontsize=16)
    
    ax1.plot(freq, mag, 'bo-') 
    ax1.set_xscale(config['scale']) 
    ax1.set_ylabel('Modulo (dB)')
    ax1.grid(True, which="both", ls='--') 
    ax1.set_ylim(config['y_mag_min'], config['y_mag_max']) 
    
    ax2.plot(freq, phase, 'ro-') 
    ax2.set_xscale(config['scale']) 
    ax2.set_xlabel('Frequenza (Hz)')
    ax2.set_ylabel('Fase (gradi)')
    ax2.grid(True, which="both", ls='--')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
            
    plt.show() # Mostra il grafico (è bloccante)
    
    # Restituisce l'oggetto figura DOPO che la finestra è stata chiusa
    return fig

# --- NUOVA FUNZIONE DI SALVATAGGIO GRAFICO ---

def save_plot_to_file(fig, filepath):
    """Salva l'oggetto 'figure' in un file."""
    try:
        ensure_save_directories() # Assicura che la cartella esista
        fig.savefig(filepath)
        print(f"Grafico salvato con successo in: {filepath}")
    except IOError as e:
        print(f"ERRORE: Impossibile salvare il grafico: {e}")
    except Exception as e:
        print(f"ERRORE inaspettato durante salvataggio grafico: {e}")