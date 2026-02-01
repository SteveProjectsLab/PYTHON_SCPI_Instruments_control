#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programma per Analisi di Spettro
Utilizza un oscilloscopio Owon VDS (via Socket) per acquisire
i dati e esegue la FFT in Python.

*** VERSIONE 1.0 ***
Logica di business separata in 'spectrum_core.py'.
Questo file contiene solo la connessione e il loop 'main'.
"""

import time
import sys
import os 

# Import delle librerie degli strumenti
try:
    from owon_vds_scpi import OwonVDS_SCPI
except ImportError as e:
    print(f"ERRORE: Impossibile importare 'owon_vds_scpi.py': {e}")
    print("Assicurati che 'owon_vds_scpi.py' sia nella stessa cartella.")
    sys.exit(1)

# Import della logica dal file core
try:
    from spectrum_core import (
        load_config, save_config, get_user_config, print_config, 
        setup_initial_state, run_spectrum_analysis, 
        plot_results, save_plot_to_file, 
        save_data_to_csv, get_next_filename, DATA_DIR, PLOTS_DIR
    )
except ImportError as e:
    print(f"ERRORE: Impossibile importare 'spectrum_core.py': {e}")
    print("Assicurati che 'spectrum_core.py' sia nella stessa cartella.")
    sys.exit(1)


# --- IMPOSTAZIONI DI CONNESSIONE (DA MODIFICARE) ---
OSC_HOST = '127.0.0.1' 
OSC_PORT = 3000 
# --------------------------------------------------


def main():
    """Funzione principale del programma."""
    print("--- Programma di Analisi di Spettro (V1.0) ---")
    
    scope = None
    
    try:
        print("\nConnessione all'Oscilloscopio (via Software VDS)...")
        scope = OwonVDS_SCPI(host=OSC_HOST, port=OSC_PORT)
        scope.connect()
        print(f"  -> IDN Oscilloscopio: {scope.get_idn()}") #

        print("  Invio comando di Reset (*RST) all'oscilloscopio...")
        scope.reset_instrument() #
        time.sleep(2.0) # Pausa di 2s per consentire allo scope di resettarsi
        print("  Reset completato.")
        
        while True:
            current_config = load_config()
            
            print("\n--- Configurazione Default Attuale ---")
            print_config(current_config, f"{OSC_HOST}:{OSC_PORT}")
            
            modify = input("Vuoi modificare questa configurazione? (s/n) [n]: ").lower() or 'n'
            
            config_to_use = current_config 

            if modify == 's':
                new_config = get_user_config(current_config) 
                
                save = input("Vuoi salvare questa nuova configurazione come default? (s/n) [n]: ").lower() or 'n'
                if save == 's':
                    save_config(new_config)
                
                config_to_use = new_config 
            
            print("\n--- Configurazione Pronta per l'Analisi ---")
            print_config(config_to_use, f"{OSC_HOST}:{OSC_PORT}") 
            
            confirm = input("Confermare e avviare l'analisi? (s/n) [s]: ").lower() or 's'
            
            if confirm == 's':
                
                print("\nAvvio analisi di spettro...")
                
                # Esegui l'analisi
                freq, v_rms, v_db, config_used = run_spectrum_analysis(scope, config_to_use) 
                
                if freq is not None: 
                    # --- LOGICA DI SALVATAGGIO (post-visualizzazione) ---
                    print("\n--- Analisi Completata ---")
                    
                    # 1. Mostra il grafico. 
                    print("Mostrando il grafico. Chiudi la finestra per continuare...")
                    figura_grafico = plot_results(freq, v_rms, v_db, config_used) 
                    
                    # 2. DOPO che il grafico è stato chiuso, chiedi se salvare.
                    print("\n--- Salvataggio Risultati ---")
                    save_plot = input("Salvare l'immagine del grafico appena visto? (s/n) [s]: ").lower() or 's'
                    if save_plot == 's':
                        plot_save_path = get_next_filename(PLOTS_DIR, "SPECTRUM_plot", ".png")
                        save_plot_to_file(figura_grafico, plot_save_path)
                    
                    # 3. Chiedi se salvare i DATI (CSV)
                    save_csv = input("Salvare i dati grezzi (CSV)? (s/n) [s]: ").lower() or 's'
                    if save_csv == 's':
                        csv_save_path = get_next_filename(DATA_DIR, "SPECTRUM_data", ".csv")
                        save_data_to_csv(freq, v_rms, v_db, csv_save_path)
                    
                    print("Salvataggio completato.")
                    
                else:
                    print("Nessun dato raccolto, impossibile generare il grafico.")

            else:
                print("Analisi annullata.")

            restart = input("\nVuoi iniziare una nuova analisi? (s/n) [n]: ").lower() or 'n'
            if restart != 's':
                break
                
    except ConnectionError as e:
        print(f"\nERRORE FATALE DI CONNESSIONE: {e}")
        print("Controlla che il software VDS sia in esecuzione.")
    except KeyboardInterrupt:
        print("\n--- Uscita dal programma ---")
    except Exception as e:
        print(f"\nERRORE FATALE IMPREVISTO: {e}")
    finally:
        try:
            if scope and scope._is_connected:
                scope.trigger.set_mode("AUTO") # Rimette lo scope in auto
                scope.disconnect()
                print("Oscilloscopio disconnesso.")
        except (KeyboardInterrupt, Exception) as e:
             print(f"Errore during la disconnesione: {e}")
            
    print("\n--- Programma terminato ---")


if __name__ == "__main__":
    main()