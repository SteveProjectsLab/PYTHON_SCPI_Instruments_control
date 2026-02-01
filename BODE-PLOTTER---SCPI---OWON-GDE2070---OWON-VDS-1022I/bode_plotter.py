#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programma per Analisi di Risposta in Frequenza (Bode Plot)
Utilizza un generatore Owon DGE (via PyVISA) e un oscilloscopio Owon VDS (via Socket).

*** VERSIONE 27.4 (Salvataggio post-visualizzazione) ***
Logica di business separata in 'bode_core.py'.
Questo file contiene solo la connessione e il loop 'main'.
Ora mostra il grafico, e POI chiede se salvare.
"""

import time
import sys
import os 

# Import delle librerie degli strumenti
try:
    import pyvisa
    from owon_dge_scpi import OwonDGE_SCPI
    from owon_vds_scpi import OwonVDS_SCPI
except ImportError as e:
    print(f"ERRORE: Impossibile importare le librerie degli strumenti: {e}")
    print("Assicurati che 'owon_dge_scpi.py' e 'owon_vds_scpi.py' siano nella stessa cartella.")
    print("Esegui: pip install pyvisa")
    sys.exit(1)

# Import di tutta la logica dal file core
try:
    # --- IMPORT MODIFICATI ---
    from bode_core import (
        load_config, save_config, get_user_config, print_config, 
        setup_initial_state, run_full_experiment, 
        plot_results,           # Modificato
        save_plot_to_file,      # Aggiunto
        save_data_to_csv, get_next_filename, DATA_DIR, PLOTS_DIR
    )
    # --- FINE IMPORT MODIFICATI ---
except ImportError as e:
    print(f"ERRORE: Impossibile importare 'bode_core.py': {e}")
    print("Assicurati che 'bode_core.py' sia nella stessa cartella.")
    sys.exit(1)


# --- IMPOSTAZIONI DI CONNESSIONE (DA MODIFICARE) ---
# RICORDA DI INSERIRE LA TUA STRINGA VISA CORRETTA!
GEN_VISA_STRING = 'USB0::0x5345::0x1235::23380879::INSTR' 
OSC_HOST = '127.0.0.1' 
OSC_PORT = 3000 
# --------------------------------------------------


def main():
    """Funzione principale del programma."""
    print("--- Programma di Analisi Risposta in Frequenza (Bode Plot V27.4) ---")
    
    gen = None
    scope = None
    
    try:
        print("Connessione al Generatore (via PyVISA)...")
        gen = OwonDGE_SCPI(visa_resource_string=GEN_VISA_STRING)
        gen.connect()
        print(f"  -> IDN Generatore: {gen.get_idn()}")
        
        print("\nConnessione all'Oscilloscopio (via Software VDS)...")
        scope = OwonVDS_SCPI(host=OSC_HOST, port=OSC_PORT)
        scope.connect()
        print(f"  -> IDN Oscilloscopio: {scope.get_idn()}")

        print("  Invio comando di Reset (*RST) all'oscilloscopio...")
        scope.reset_instrument()
        time.sleep(2.0) # Pausa di 2s per consentire allo scope di resettarsi
        print("  Reset completato.")
        
        while True:
            current_config = load_config()
            
            print("\n--- Configurazione Default Attuale ---")
            print_config(current_config, GEN_VISA_STRING, f"{OSC_HOST}:{OSC_PORT}")
            
            modify = input("Vuoi modificare questa configurazione? (s/n) [n]: ").lower() or 'n'
            
            config_to_use = current_config 

            if modify == 's':
                new_config = get_user_config(current_config) 
                
                save = input("Vuoi salvare questa nuova configurazione come default? (s/n) [n]: ").lower() or 'n'
                if save == 's':
                    save_config(new_config)
                
                config_to_use = new_config 
            
            print("\n--- Configurazione Pronta per l'Esperimento ---")
            print_config(config_to_use, GEN_VISA_STRING, f"{OSC_HOST}:{OSC_PORT}") 
            
            confirm = input("Confermare e avviare l'esperimento? (s/n) [s]: ").lower() or 's'
            
            if confirm == 's':
                
                # --- CODICE PER ESECUZIONE NORMALE (MODIFICATO) ---
                
                print("\nAvvio esperimento completo...")
                freq, mag, phase, config_used = run_full_experiment(gen, scope, config_to_use) 
                
                if freq: 
                    # --- NUOVA LOGICA DI SALVATAGGIO (post-visualizzazione) ---
                    print("\n--- Esperimento Completato ---")
                    
                    # 1. Mostra il grafico. 
                    #    plt.show() è bloccante. Il codice prosegue
                    #    dopo che l'utente chiude la finestra.
                    #    Salviamo l'oggetto 'fig' restituito.
                    print("Mostrando il grafico. Chiudi la finestra per continuare...")
                    figura_grafico = plot_results(freq, mag, phase, config_used) 
                    
                    # 2. DOPO che il grafico è stato chiuso, chiedi se salvare.
                    print("\n--- Salvataggio Risultati ---")
                    save_plot = input("Salvare l'immagine del grafico appena visto? (s/n) [s]: ").lower() or 's'
                    if save_plot == 's':
                        plot_save_path = get_next_filename(PLOTS_DIR, "BODE_plot", ".png")
                        save_plot_to_file(figura_grafico, plot_save_path) # Usa la nuova funzione
                    
                    # 3. Chiedi se salvare i DATI (CSV)
                    save_csv = input("Salvare i dati grezzi (CSV)? (s/n) [s]: ").lower() or 's'
                    if save_csv == 's':
                        csv_save_path = get_next_filename(DATA_DIR, "BODE_data", ".csv")
                        save_data_to_csv(freq, mag, phase, csv_save_path)
                    
                    print("Salvataggio completato.")
                    # --- FINE NUOVA LOGICA ---
                    
                else:
                    print("Nessun dato raccolto, impossibile generare il grafico.")
                # --- FINE CODICE MODIFICATO ---

            else:
                print("Esperimento annullato.")

            restart = input("\nVuoi iniziare un nuovo esperimento? (s/n) [n]: ").lower() or 'n'
            if restart != 's':
                break
                
    except ConnectionError as e:
        print(f"\nERRORE FATALE DI CONNESSIONE: {e}")
        print("Controlla gli indirizzi IP/Porte, le connessioni e che il software VDS sia in esecuzione.")
    except KeyboardInterrupt:
        print("\n--- Uscita dal programma ---")
    except Exception as e:
        print(f"\ERRORE FATALE IMPREVISTO: {e}")
    finally:
        try:
            if gen and gen._is_connected:
                gen.output1.set_state("OFF") 
                gen.disconnect()
                print("Generatore disconnesso.")
            if scope and scope._is_connected:
                scope.trigger.set_mode("AUTO") # Rimette lo scope in auto
                scope.disconnect()
                print("Oscilloscopio disconnesso.")
        except (KeyboardInterrupt, Exception) as e:
             print(f"Errore during la disconnesione: {e}")
            
    print("\n--- Programma terminato ---")


if __name__ == "__main__":
    main()