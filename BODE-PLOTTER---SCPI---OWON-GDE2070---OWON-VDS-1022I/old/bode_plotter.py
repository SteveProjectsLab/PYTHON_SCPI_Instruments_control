import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time

# --- CONFIGURAZIONE ---
# Sostituisci con gli indirizzi VISA dei tuoi strumenti
RESOURCE_MANAGER = '@py' # Usa '@py' per pyvisa-py
FG_ADDRESS = 'USB0::0x5121::0x2501::DGE207000000::INSTR' # Esempio per Owon DGE2070
SCOPE_ADDRESS = 'USB0::0x5345::0x1234::VDS1022I00000::INSTR' # Esempio per Owon VDS1022i

# Parametri della scansione in frequenza
start_freq = 100       # Frequenza iniziale in Hz
end_freq = 2000000   # Frequenza finale in Hz (2 MHz)
points_per_decade = 10 # Punti di misurazione per ogni decade di frequenza

# Parametri del segnale di test
amplitude_vpp = 2.0  # Ampiezza picco-picco in Volt

# --- INIZIALIZZAZIONE STRUMENTI ---
print("🔬 Inizializzazione degli strumenti...")
try:
    rm = pyvisa.ResourceManager(RESOURCE_MANAGER)
    fg = rm.open_resource(FG_ADDRESS)
    scope = rm.open_resource(SCOPE_ADDRESS)

    # Imposta timeout più lunghi per dare tempo agli strumenti di rispondere
    fg.timeout = 5000  # 5 secondi
    scope.timeout = 5000 # 5 secondi

    # Identifica gli strumenti (buona pratica)
    print(f"Generatore di Funzioni: {fg.query('*IDN?')}")
    print(f"Oscilloscopio: {scope.query('*IDN?')}")

except pyvisa.errors.VisaIOError as e:
    print(f"Errore di connessione: {e}")
    print("Controlla gli indirizzi VISA e le connessioni degli strumenti.")
    exit()

# --- PREPARAZIONE MISURAZIONE ---
# Resetta e configura gli strumenti
fg.write('*RST')
scope.write('*RST')
time.sleep(1)

# Configura il generatore di funzioni
fg.write(f'SOUR1:FUNC SIN') # Imposta forma d'onda sinusoidale
fg.write(f'SOUR1:VOLT {amplitude_vpp}') # Imposta ampiezza
fg.write(f'SOUR1:VOLT:OFFS 0') # Imposta offset a 0
fg.write('OUTP1:LOAD HIZ') # Imposta alta impedenza in uscita
fg.write('OUTP1:STAT ON') # Attiva l'uscita del generatore

# Configura l'oscilloscopio per le misurazioni
scope.write(':MEAS:SOUR CHAN1') # Imposta la sorgente per le misurazioni su Canale 1
scope.write(':MEAS:SOUR CHAN2') # Imposta la sorgente per le misurazioni su Canale 2
scope.write(':ACQ:TYPE NORM') # Modalità di acquisizione normale

print("✅ Strumenti configurati. Inizio della scansione in frequenza...")

# --- CICLO DI MISURAZIONE ---
# Genera le frequenze su una scala logaritmica
num_points = int(points_per_decade * np.log10(end_freq / start_freq))
frequencies = np.logspace(np.log10(start_freq), np.log10(end_freq), num_points)

gains_db = []
phases = []

try:
    for i, freq in enumerate(frequencies):
        print(f"Passo {i+1}/{len(frequencies)}: Misurazione a {freq:.2f} Hz")
        
        # 1. Imposta la frequenza sul generatore
        fg.write(f'SOUR1:FREQ {freq}')
        
        # 2. Lascia tempo al circuito e agli strumenti di stabilizzarsi
        #    Questo valore potrebbe dover essere aumentato per basse frequenze
        time.sleep(0.5)

        # 3. Esegui le misurazioni sull'oscilloscopio
        #    NOTA: I comandi esatti possono variare. Consulta il manuale del tuo oscilloscopio.
        try:
            v_in_vpp = float(scope.query(':MEAS:VPP? CHAN1'))
            v_out_vpp = float(scope.query(':MEAS:VPP? CHAN2'))
            phase_deg = float(scope.query(':MEAS:PHAS? CHAN1,CHAN2')) # Fase da CH1 a CH2
        except pyvisa.errors.VisaIOError:
            print(f"Timeout o errore di misurazione a {freq:.2f} Hz. Salto il punto.")
            continue
            
        # 4. Calcola il guadagno in dB
        if v_in_vpp > 0 and v_out_vpp > 0:
            gain = v_out_vpp / v_in_vpp
            gain_db = 20 * np.log10(gain)
        else:
            gain_db = -np.inf # Valore nullo se l'input è zero
        
        # 5. Salva i risultati
        gains_db.append(gain_db)
        phases.append(phase_deg)

finally:
    # --- PULIZIA FINALE ---
    print("🔌 Scansione completata. Disattivazione strumenti.")
    fg.write('OUTP1:STAT OFF') # Spegni l'uscita del generatore
    fg.close()
    scope.close()
    rm.close()

# --- PLOT DEI RISULTATI ---
print("📊 Creazione del diagramma di Bode...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.suptitle('Diagramma di Bode', fontsize=16)

# Plot del Guadagno
ax1.semilogx(frequencies, gains_db, 'o-', color='b')
ax1.set_ylabel('Guadagno (dB)')
ax1.grid(which='both', linestyle='--')
ax1.set_title('Risposta in Ampiezza')

# Plot della Fase
ax2.semilogx(frequencies, phases, 'o-', color='r')
ax2.set_xlabel('Frequenza (Hz)')
ax2.set_ylabel('Fase (°)')
ax2.grid(which='both', linestyle='--')
ax2.set_title('Risposta in Fase')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

print("🏁 Programma terminato.")