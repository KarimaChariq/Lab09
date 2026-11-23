from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0


        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()
        if not relazioni:
            return

        for esc in self.escursioni_map.values():
            esc.punti_interesse.clear()
        for punto in self.punti_interesse_map.values():
            punto.escursioni.clear()

        for rel in relazioni:
            id_esc = rel["id_escursione"]
            id_punto = rel["id_punto_interesse"]

            esc = self.escursioni_map.get(id_esc)
            punto = self.punti_interesse_map.get(id_punto)

            if esc is not None and punto is not None:
                esc.punti_interesse.add(punto)
                punto.escursioni.add(esc)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        escursioni_parco = [
            esc for esc in self.escursioni_map.values()
            if esc.id_parco == id_parco
        ]

        self._ricorsione(
            start_index=0,
            escursioni_parco=escursioni_parco,
            max_giorni=max_giorni,
            max_budget=max_budget,
            pacchetto_parziale=[],
            durata_corrente=0,
            costo_corrente=0.0,
            valore_corrente=0,
            punti_usati=set(),
        )

        if self._valore_ottimo == -1:
            self._valore_ottimo = 0

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, max_giorni: int,
        max_budget: float, valore_corrente: int, escursioni_parco: list, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente
        for i in range(start_index, len(escursioni_parco)):
            esc = escursioni_parco[i]

            nuova_durata = durata_corrente + esc.durata_giorni
            if max_giorni is not None and nuova_durata > max_giorni:
                continue

            nuovo_costo = costo_corrente + esc.costo
            if max_budget is not None and nuovo_costo > max_budget:
                continue

            # Controllo che non ci siano punti di interesse già inclusi nel pacchetto

            if not esc.punti_interesse.isdisjoint(punti_usati):
                continue

            valore_aggiunto = sum(p.voto_visitatori for p in esc.punti_interesse)
            nuovo_valore = valore_corrente + valore_aggiunto

            pacchetto_parziale.append(esc)
            punti_usati.update(esc.punti_interesse)

            self._ricorsione(
                start_index=i + 1,
                escursioni_parco=escursioni_parco,
                max_giorni=max_giorni,
                max_budget=max_budget,
                pacchetto_parziale=pacchetto_parziale,
                durata_corrente=nuova_durata,
                costo_corrente=nuovo_costo,
                valore_corrente=nuovo_valore,
                punti_usati=punti_usati,
            )


            pacchetto_parziale.pop()
            punti_usati.difference_update(esc.punti_interesse)