"""
Kalkulator postaci BG3 / DnD.

Wpisujesz staty + poziom (+ opcjonalnie subklasę) i program wypisuje
wszystkie umiejętności/zaklęcia (featury), które postać ma odblokowane
do jej aktualnego poziomu.

Przykład użycia:
    player01 = Barbarian(s=16, z=14, k=14, i=8, m=10, c=10,
                          ch_lvl=5, subclass="berserker")
    player01.print_features()
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Kość życia (Hit Die) każdej klasy — standard D&D 5e / BG3
HIT_DICE = {
    "barbarian": 12,
    "fighter": 10,
    "paladin": 10,
    "ranger": 10,
    "bard": 8,
    "cleric": 8,
    "druid": 8,
    "monk": 8,
    "rogue": 8,
    "warlock": 8,
    "sorcerer": 6,
    "wizard": 6,
}


class Postac:
    """Klasa bazowa dla wszystkich klas postaci (Barbarian, Monk, itd.)."""

    def __init__(self, s, z, k, i, m, c, ch_lvl, subclass=None):
        # Statystyki: Siła, Zręczność, Kondycja, Inteligencja, Mądrość, Charyzma
        self.s = s
        self.z = z
        self.k = k
        self.i = i
        self.m = m
        self.c = c

        self.ch_lvl = ch_lvl
        self.subclass = subclass

        # Nazwa klasy = nazwa klasy Pythona zapisana małymi literami,
        # np. Barbarian -> "barbarian" -> szuka pliku data/barbarian.json
        self.class_name = self.__class__.__name__.lower()
        self.data = self._load_data()

    # ---------- Wczytywanie danych ----------

    def _load_data(self):
        path = os.path.join(DATA_DIR, f"{self.class_name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Brak pliku z danymi dla klasy '{self.class_name}': {path}"
            )
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------- Modyfikatory statystyk ----------

    @staticmethod
    def modifier(stat_value):
        """Standardowy modyfikator D&D: (wartość - 10) // 2."""
        return (stat_value - 10) // 2

    # ---------- HP ----------

    def get_hp(self):
        """
        HP liczone jak w BG3 (metoda uśredniona, bez losowości):
        - poziom 1: pełna kość życia + mod. KON
        - każdy kolejny poziom: (kość/2 + 1, zaokrąglone w górę) + mod. KON
        """
        hit_die = HIT_DICE[self.class_name]
        con_mod = self.modifier(self.k)
        avg_per_level = hit_die // 2 + 1

        hp = hit_die + con_mod  # poziom 1

        level = 2
        while level <= self.ch_lvl:
            hp += avg_per_level + con_mod
            level += 1

        return hp

    # ---------- Zbieranie featurów ----------

    def get_base_features(self):
        """Featury bazowe klasy (bez subklasy), odblokowane do self.ch_lvl."""
        all_base = self.data.get(self.class_name, [])
        unlocked = []

        idx = 0
        while idx < len(all_base):
            feature = all_base[idx]
            if feature["ch_lvl"] <= self.ch_lvl:
                unlocked.append(feature)
            idx += 1

        return unlocked

    def get_subclass_features(self):
        """Featury subklasy, odblokowane do self.ch_lvl (jeśli subklasa podana)."""
        if not self.subclass:
            return []

        subclasses = self.data.get("subclasses", {})
        all_sub = subclasses.get(self.subclass)

        if all_sub is None:
            available = ", ".join(subclasses.keys())
            raise ValueError(
                f"Nieznana subklasa '{self.subclass}' dla klasy "
                f"'{self.class_name}'. Dostępne: {available}"
            )

        unlocked = []
        idx = 0
        while idx < len(all_sub):
            feature = all_sub[idx]
            if feature["ch_lvl"] <= self.ch_lvl:
                unlocked.append(feature)
            idx += 1

        return unlocked

    def get_all_features(self):
        """Wszystkie featury (bazowe + subklasa) odblokowane do self.ch_lvl."""
        return self.get_base_features() + self.get_subclass_features()

    # ---------- Wyświetlanie ----------

    def print_features(self):
        features = self.get_all_features()

        header = f"=== {self.class_name.capitalize()} — poziom {self.ch_lvl}"
        if self.subclass:
            header += f" ({self.subclass})"
        header += " ==="
        print(header)

        print(
            f"STR {self.s} ({self.modifier(self.s):+d})  "
            f"DEX {self.z} ({self.modifier(self.z):+d})  "
            f"CON {self.k} ({self.modifier(self.k):+d})  "
            f"INT {self.i} ({self.modifier(self.i):+d})  "
            f"WIS {self.m} ({self.modifier(self.m):+d})  "
            f"CHA {self.c} ({self.modifier(self.c):+d})"
        )
        print(f"HP: {self.get_hp()}  (kość życia: d{HIT_DICE[self.class_name]})")
        print("-" * 60)

        if not features:
            print("(brak odblokowanych featurów na tym poziomie)")
            return

        idx = 0
        while idx < len(features):
            f = features[idx]
            typ = "zaklęcie" if f["type"] == "spell" else "umiejętność"
            extra = f", poziom zaklęcia: {f['lvl']}" if f["lvl"] else ""
            print(f"[{f['ch_lvl']:>2}] {f['name']}  ({typ}{extra})")
            idx += 1


# ---------------------------------------------------------------------
# Klasy postaci — każda tylko wskazuje nazwę pliku danych (przez nazwę
# klasy Pythona), cała logika jest odziedziczona z Postac.
# ---------------------------------------------------------------------

class Barbarian(Postac):
    pass


class Bard(Postac):
    pass


class Cleric(Postac):
    pass


class Druid(Postac):
    pass


class Fighter(Postac):
    pass


class Monk(Postac):
    pass


class Paladin(Postac):
    pass


class Ranger(Postac):
    pass


class Rogue(Postac):
    pass


class Sorcerer(Postac):
    pass


class Warlock(Postac):
    pass


class Wizard(Postac):
    pass
