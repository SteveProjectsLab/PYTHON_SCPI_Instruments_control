PROCEDURA DI TEST 

1- spegni tutto
2- la batteria DEVE essere staccata dal suo attacco
3- controlla il collegamento dei cavi relativi alla batteria secondo lo schema
4- con l'adattatore USB del PC, collega il cavo seriale del carico al PC
5- con il cavo USB, collega il sistema di acquisizione stm32 all'usb
6- accendi lo strumento

	[da fare la prima volta:
	7- configura manualmente lo strumento per la connessione RS232 (user guide pag 58)
		premo address e con le freccie su e giu configuro RS232, baud 9600, flow NONE, parity NONE
		invio ogni volta
	8- testo la connessione con NI-MAX dal PC
		seleziono la COM interessata
		apro VISA test panel
		configuro come per lo strumento ( baud ecc..) e invido il comando *IDN?
		se risponde con una stringa "Agilent.ecc.." il collegamento funziona
	- controlla su quali COM si trovano il carico e l'stm32
	- controlla di avere inserito il path giusto di dove si trova il file
	
	
	]


- apri il programma in Python
- esegui il programma (doppio click su "Electronic load data logger")
- scegli la voce 1 del menù e manda qualche comando di prova
	- inserisci il comando "MENU" per tornare al menù
- scegli la voce 2 del menù per fare partire il test automatico
	- premi s per terminare il test e per salvare il file




