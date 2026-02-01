#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Console SCPI per Oscilloscopio Owon VDS (V42+)

Questo programma si connette al software VDS e permette
di inviare comandi SCPI manualmente dalla console.
Riconosce automaticamente i comandi di query (che finiscono con '?')
e attende una risposta.

Usa la libreria owon_vds_scpi.py per la connessione.
"""

import sys
import time
import os

try:
    from owon_vds_scpi import OwonVDS_SCPI
except ImportError as e:
    print(f"ERRORE: Impossibile importare 'owon_vds_scpi.py': {e}")
    print("Assicurati che 'owon_vds_scpi.py' sia nella stessa cartella.")
    sys.exit(1)

# --- IMPOSTAZIONI DI CONNESSIONE (DA MODIFICARE SE NECESSARIO) ---
OSC_HOST = '127.0.0.1' 
OSC_PORT = 3000 
# --------------------------------------------------

def main_console():
    """Avvia la console SCPI interattiva."""
    print("--- Console SCPI per Owon VDS ---")
    
    scope = None
    
    try:
        print(f"Connessione a {OSC_HOST}:{OSC_PORT}...")
        scope = OwonVDS_SCPI(host=OSC_HOST, port=OSC_PORT)
        scope.connect()
        
        # Prova a prendere l'IDN per confermare la connessione
        idn_str = scope.get_idn()
        if idn_str:
            print(f"Connesso! IDN: {idn_str}")
        else:
            print("Connesso, ma impossibile recuperare IDN. Lo scope è acceso?")

        print("\nDigitare 'exit' o 'quit' per uscire.")
        print("I comandi di query (es. *IDN?) stamperanno una risposta.")
        print("I comandi di scrittura (es. :CHANnel1:SCALe 0.5) stamperanno 'Sent'.\n")

        while True:
            # Legge l'input dell'utente
            command = input("SCPI > ")
            
            # Pulisce il comando
            command_clean = command.strip()

            # 1. Controlla se uscire
            if command_clean.lower() in ['exit', 'quit']:
                print("Disconnessione in corso...")
                break
            
            # 2. Controlla se è vuoto
            if not command_clean:
                continue

            try:
                # 3. Logica Scrittura/Lettura
                if command_clean.endswith('?'):
                    # È una QUERY (lettura)
                    print(f"  -> QUERY: {command_clean}")
                    # Usiamo la funzione di basso livello della libreria
                    response = scope._query_command(command_clean)
                    print(f"  <- RESPONSE: {response}\n")
                
                else:
                    # È un SET (scrittura)
                    print(f"  -> SET: {command_clean}")
                    # Usiamo la funzione di basso livello della libreria
                    scope._send_command(command_clean)
                    print("  <- Sent.\n")

            except Exception as e:
                print(f"ERRORE durante l'invio del comando: {e}")
                print("La connessione potrebbe essersi interrotta.")
                break # Esce dal loop in caso di errore grave

    except ConnectionError as e:
        print(f"\nERRORE FATALE DI CONNESSIONE: {e}")
        print("Controlla che il software Owon VDS sia in esecuzione.")
    except KeyboardInterrupt:
        print("\n--- Uscita forzata (Ctrl+C) ---")
    except Exception as e:
        print(f"\nERRORE FATALE IMPREVISTO: {e}")
    finally:
        try:
            if scope and scope._is_connected:
                # Prova a rimetterlo in AUTO prima di chiudere
                scope.trigger.set_mode("AUTO")
                scope.disconnect()
                print("Oscilloscopio disconnesso.")
        except Exception as e:
             print(f"Errore during la disconnessione: {e}")
            
    print("\n--- Console terminata ---")


if __name__ == "__main__":
    main_console()
