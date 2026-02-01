import pyvisa

# Inizializza il gestore delle risorse VISA
# Se hai installato NI-VISA o un altro driver, lascia le parentesi vuote:
# rm = pyvisa.ResourceManager()

# Se non hai driver e usi solo pyvisa-py, usa:
rm = pyvisa.ResourceManager('@py')

print("Sto cercando gli strumenti collegati...")

try:
    # Chiedi a VISA di elencare tutti gli strumenti che vede
    resources = rm.list_resources()

    if not resources:
        print("\nNessuno strumento trovato.")
        print("Controlla che:")
        print("  1. Lo strumento sia acceso e collegato via USB.")
        print("  2. Siano installati i driver corretti (es. NI-VISA).")
    else:
        print("\n--- Strumenti Trovati ---")
        for res in resources:
            print(res)
        print("-------------------------")
        print("\nCopia la stringa che inizia con 'USB...' e incollala")
        print("nel file 'bode_plotter.py' alla variabile GEN_VISA_STRING.")

except Exception as e:
    print(f"Si è verificato un errore: {e}")
    print("Potrebbe essere necessario installare un backend VISA come NI-VISA.")

input("\nPremi Invio per uscire.")