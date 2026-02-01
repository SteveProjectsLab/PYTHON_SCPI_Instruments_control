#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Spectrum Analyzer - Funzioni Core (V1.8)

Esegue la FFT in Python (via Numpy) sui dati grezzi
acquisiti dall'Owon VDS.
V1.8: Rimosso OGNI comando :ACQuire:MDEPth.
      Ci affidiamo allo stato MDEPth automatico
      impostato dal timebase (es. "D 5k").
"""

import time
import math
import numpy as np
import matplotlib.pyplot as plt
import json 
import os 
import csv 

# --- GESTIONE CONFIGURAZIONE ---
CONFIG_FILENAME = 'spectrum_config.json'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "DATA")
PLOTS_DIR = os.path.join(DATA_DIR, "PLOTS")

FACTORY_DEFAULTS = {
    'f_start': 0.0,
    'f_stop': 100000.0,
    'resolution_hz': 100.0,
    'num_averages': 3,
    'channel': 1,
    'coupling': 'DC',
    'window': 'HANNing'
}

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
VDS_PAUSE = 0.3 

# --- FUNZIONI DI CONFIGURAZIONE (Invariate) ---

def load_config():
    if os.path.exists(CONFIG_FILENAME):
        try:
            with open(CONFIG_FILENAME, 'r') as f:
                config = json.load(f)
                config.update({k: v for k, v in FACTORY_DEFAULTS.items() if k not in config})
                return config
        except json.JSONDecodeError:
            print(f"Attenzione: file '{CONFIG_FILENAME}' corrotto. Uso i default.")
            return FACTORY_DEFAULTS.copy()
    else:
        return FACTORY_DEFAULTS.copy()

def save_config(config):
    try:
        with open(CONFIG_FILENAME, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configurazione salvata in '{CONFIG_FILENAME}'.")
    except IOError as e:
        print(f"ERRORE: Impossibile salvare la configurazione: {e}")

def get_user_config(default_config):
    print("\n--- Modifica Configurazione Analisi ---")
    config = default_config.copy() 
    config['f_start'] = float(input(f"Freq. Iniziale Grafico (Hz) [{config['f_start']}]: ") or config['f_start'])
    config['f_stop'] = float(input(f"Freq. Finale Grafico (Hz) [{config['f_stop']}]: ") or config['f_stop'])
    config['resolution_hz'] = float(input(f"Risoluzione desiderata (Hz) [{config['resolution_hz']}]: ") or config['resolution_hz'])
    config['num_averages'] = int(input(f"Numero di Medie [{config['num_averages']}]: ") or config['num_averages'])
    config['channel'] = int(input(f"Canale (1 o 2) [{config['channel']}]: ") or config['channel'])
    config['coupling'] = (input(f"Accoppiamento (AC o DC) [{config['coupling']}]: ") or config['coupling']).upper()
    config['window'] = (input(f"Finestra FFT (HANNing, RECTangle) [{config['window']}]: ") or config['window']).upper()
    return config

def print_config(config, scope_string):
    print("\n--- Riepilogo Configurazione ---")
    print(f"  Strumenti:")
    print(f"    Oscilloscopio: {scope_string}")
    print(f"\n  Parametri Analisi:")
    print(f"    Canale:        CH{config['channel']} ({config['coupling']})")
    print(f"    Risoluzione:   ~{config['resolution_hz']} Hz (target)")
    print(f"    Medie:         {config['num_averages']}")
    print(f"    Finestra FFT:  {config['window']}")
    print(f"\n  Parametri Grafico:")
    print(f"    Range Freq.:   {config['f_start']} Hz a {config['f_stop']} Hz")
    print("---------------------------------")


# --- FUNZIONI HELPER ---

def get_best_timebase(target_resolution_hz):
    ideal_time_per_div = 1.0 / (target_resolution_hz * 10.0)
    for t_base_sec in VALID_TIMEBASES:
        if t_base_sec >= ideal_time_per_div:
            return VDS_TIMEBASE_MAP[t_base_sec], t_base_sec
    t_base_sec = VALID_TIMEBASES[-1]
    return VDS_TIMEBASE_MAP[t_base_sec], t_base_sec

def get_scope_channel(scope, config):
    return scope.channel1 if config['channel'] == 1 else scope.channel2

# --- FUNZIONI DI ESECUZIONE (MODIFICATE) ---

def setup_initial_state(scope, config):
    """Imposta lo stato iniziale dello scope per la misura."""
    print("\n--- 1. Configurazione Oscilloscopio ---")
    
    scope_ch = get_scope_channel(scope, config)
    
    scope_ch.set_display(True); time.sleep(VDS_PAUSE) 
    
    coupling = "DC" if "DC" in config['coupling'].upper() else "AC"
    scope_ch.set_coupling(coupling); time.sleep(VDS_PAUSE) 
    print(f"  Canale CH{config['channel']} impostato su {coupling}.")
    
    scope_ch.set_probe_attenuation("X1"); time.sleep(VDS_PAUSE) 
    print(f"  Sonda CH{config['channel']} impostata su 1X (assicurati sia corretto!).")
    
    scope.acquire.set_type("SAMPle"); time.sleep(VDS_PAUSE) 
    
    scope.trigger.set_mode("AUTO"); time.sleep(VDS_PAUSE) 
    scope.set_run() # Avvia lo scope
    
    print("  Scope in modalità RUN, AUTO, SAMPLE.")

def run_spectrum_analysis(scope, config):
    """
    Esegue l'acquisizione e l'analisi FFT.
    (Versione 1.8 - Logica AUTO, NESSUN MDEPth)
    """
    
    t_base_str, t_base_sec = get_best_timebase(config['resolution_hz'])
    
    N = 500 # Come da libreria originale
    total_time_s = t_base_sec * 10.0 # 10 divisioni
    sample_rate_hz = N / total_time_s
    actual_resolution_hz = 1.0 / total_time_s
    nyquist_freq_hz = sample_rate_hz / 2.0
    
    print(f"\n--- 2. Avvio Acquisizione ---")
    print(f"  Risoluzione Target: {config['resolution_hz']:.2f} Hz")
    print(f"  Timebase scelto:    {t_base_str} / div")
    print(f"  Risoluzione Reale:  {actual_resolution_hz:.2f} Hz")
    print(f"  Freq. Massima (Nyquist): {nyquist_freq_hz:.2f} Hz")
    
    if config['f_stop'] > nyquist_freq_hz:
        print(f"  ATTENZIONE: Freq. Finale ({config['f_stop']} Hz) supera la Freq. Massima.")
        
    scope_ch = get_scope_channel(scope, config)

    print("\n-----------------------------------------------------------------")
    print(f"  IMPORTANTE: Regola il V/div di CH{config['channel']} sul software Owon")
    print(f"  in modo che il segnale sia ben visibile e NON CLIPPATO.")
    print("-----------------------------------------------------------------")
    try:
        input("  Premi INVIO per continuare...")
    except KeyboardInterrupt:
        print("\nAnalisi interrotta.")
        return None, None, None, config

    print("  Configurazione timebase e lettura V/div...")
    
    # Dobbiamo fermare lo scope per configurarlo
    scope.set_stop() 
    time.sleep(1.0) 
    
    scope.timebase.set_scale(t_base_str); time.sleep(1.0) 
    
    # --- *** MODIFICA CHIAVE V1.8 *** ---
    # Rimosso ogni comando set_memory_depth()
    # Ci affidiamo allo stato automatico (es. 5K)
    # --- *** FINE MODIFICA CHIAVE V1.8 *** ---

    try:
        v_div_str = scope_ch.get_scale() 
        v_div_val = float(v_div_str)
        probe_str = scope_ch.get_probe_attenuation() 
        probe_val = int(probe_str.upper().replace('X', '')) 
    except Exception as e:
        print(f"ERRORE: Impossibile leggere V/div o Sonda: {e}")
        return None, None, None, config
        
    print(f"  Letto V/div: {v_div_val} V (Sonda {probe_val}X)")

    volts_per_step = (8.0 * v_div_val * probe_val) / 255.0
    
    all_complex_ffts = []
    
    for i in range(config['num_averages']):
        print(f"  Acquisizione Media {i+1}/{config['num_averages']}...")
        
        scope.set_run()
        
        wait_for_acq_s = (t_base_sec * 5.0) + 1.0
        print(f"  Attesa stabilizzazione acquisizione ({wait_for_acq_s:.2f}s)...")
        time.sleep(wait_for_acq_s)
        
        scope.set_stop()
        
        wait_for_buffer_s = 2.0 
        print(f"  Preparazione buffer per download (attesa {wait_for_buffer_s:.2f}s)...")
        time.sleep(wait_for_buffer_s)
        
        print("  Download dati ADC...")
        raw_data = scope.get_adc_data(config['channel'])
        
        if raw_data is None or len(raw_data) != N:
            # Questa è la condizione di errore che abbiamo visto
            print(f"  Errore: Dati ADC non validi (ricevuti {len(raw_data) if raw_data else 'None'} byte). Salto.")
            continue
            
        volts = (raw_data.astype(float) - 127.5) * volts_per_step
        
        if "HANN" in config['window']:
            window = np.hanning(N) 
        else:
            window = np.ones(N) 
            
        volts_windowed = volts * window
        
        complex_fft = np.fft.fft(volts_windowed)
        all_complex_ffts.append(complex_fft)

    scope.set_run()
    
    if not all_complex_ffts:
        print("ERRORE: Nessuna acquisizione riuscita.")
        return None, None, None, config
        
    print("  Calcolo medie e risultati...")
    
    avg_complex_fft = np.mean(np.array(all_complex_ffts), axis=0)
    fft_mag = np.abs(avg_complex_fft[0:N//2])
    freq_axis_hz = np.fft.fftfreq(N, d=1.0/sample_rate_hz)[0:N//2]
    
    window_sum = np.sum(window)
    v_peak = (fft_mag * 2.0) / window_sum
    v_rms = v_peak / np.sqrt(2)
    v_rms[0] = np.abs(avg_complex_fft[0]) / window_sum
    
    epsilon = 1e-12 
    v_db = 20 * np.log10(v_rms + epsilon)
    
    return freq_axis_hz, v_rms, v_db, config


# --- FUNZIONI DI SALVATAGGIO E PLOT (Invariate) ---

def ensure_save_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)

def get_next_filename(directory, prefix, extension):
    ensure_save_directories() 
    i = 1
    while True:
        filename = f"{prefix}_{i:03d}{extension}"
        full_path = os.path.join(directory, filename)
        if not os.path.exists(full_path):
            return full_path
        i += 1

def save_data_to_csv(freq_list, vrms_list, vdb_list, filepath):
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Frequency (Hz)", "Amplitude (Vrms)", "Amplitude (dB)"])
            for i in range(len(freq_list)):
                writer.writerow([freq_list[i], vrms_list[i], vdb_list[i]])
        print(f"Dati salvati con successo in: {filepath}")
    except IOError as e:
        print(f"ERRORE: Impossibile salvare il file CSV: {e}")

def plot_results(freq, v_rms, v_db, config):
    print("Visualizzazione grafici...")
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(12, 8))
    fig.suptitle('Analisi di Spettro', fontsize=16)
    
    ax1.plot(freq, v_db) 
    ax1.set_ylabel('Ampiezza (dB)')
    ax1.grid(True, which="both", ls='--') 
    ax1.set_xlim(config['f_start'], config['f_stop']) 
    
    ax2.plot(freq, v_rms) 
    ax2.set_xlabel('Frequenza (Hz)')
    ax2.set_ylabel('Ampiezza (Vrms)')
    ax2.grid(True, which="both", ls='--')
    ax2.set_xlim(config['f_start'], config['f_stop'])
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
    plt.show() 
    return fig

def save_plot_to_file(fig, filepath):
    try:
        ensure_save_directories()
        fig.savefig(filepath)
        print(f"Grafico salvato con successo in: {filepath}")
    except IOError as e:
        print(f"ERRORE: Impossibile salvare il grafico: {e}")