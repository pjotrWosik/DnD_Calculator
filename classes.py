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

# Główna statystyka castowania zaklęć per klasa (atrybut Postac: s/z/k/i/m/c)
CASTING_ABILITY = {
    "bard": "c",
    "cleric": "m",
    "druid": "m",
    "paladin": "c",
    "ranger": "m",
    "sorcerer": "c",
    "warlock": "c",
    "wizard": "i",
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

    # ---------- Bonus biegłości, atak, AC, DC ----------

    def get_proficiency_bonus(self):
        """Standardowy bonus biegłości D&D wg poziomu (2 na lvl 1-4, 3 na 5-8, itd.)."""
        return 2 + (self.ch_lvl - 1) // 4

    def get_ac(self):
        """
        AC bez pancerza (brak jeszcze danych o ekwipunku):
        - Barbarian / Monk mają Unarmoured Defence -> DEX + KON / DEX + MDR
        - reszta klas: bazowe 10 + DEX (założenie: bez zbroi)
        """
        dex_mod = self.modifier(self.z)

        if self.class_name == "barbarian":
            return 10 + dex_mod + self.modifier(self.k)
        if self.class_name == "monk":
            return 10 + dex_mod + self.modifier(self.m)

        return 10 + dex_mod

    def get_melee_attack_bonus(self):
        """Bonus do trafienia bronią orężną (STR) + bonus biegłości."""
        return self.get_proficiency_bonus() + self.modifier(self.s)

    def get_ranged_attack_bonus(self):
        """Bonus do trafienia bronią finezyjną/dystansową (DEX) + bonus biegłości."""
        return self.get_proficiency_bonus() + self.modifier(self.z)

    def get_spell_save_dc(self):
        """DC rzutu obronnego na zaklęcia (tylko dla klas castujących). None jeśli nie dotyczy."""
        ability = CASTING_ABILITY.get(self.class_name)
        if ability is None:
            return None
        stat_value = getattr(self, ability)
        return 8 + self.get_proficiency_bonus() + self.modifier(stat_value)

    def get_spell_attack_bonus(self):
        """Bonus do trafienia zaklęciem (dla klas castujących). None jeśli nie dotyczy."""
        ability = CASTING_ABILITY.get(self.class_name)
        if ability is None:
            return None
        stat_value = getattr(self, ability)
        return self.get_proficiency_bonus() + self.modifier(stat_value)

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
        print(f"Atak: STR {self.get_melee_attack_bonus():+d}  |  DEX (finezja/dystans) {self.get_ranged_attack_bonus():+d}")
        print(f"AC: {self.get_ac()}")
        print(f"Inicjatywa: {self.modifier(self.z):+d}")
        print(f"Bonus biegłości: +{self.get_proficiency_bonus()}")

        dc = self.get_spell_save_dc()
        if dc is not None:
            print(f"DC rzutu obronnego na zaklęcia: {dc}  |  Atak zaklęciem: {self.get_spell_attack_bonus():+d}")

        print("-" * 60)

        if not features:
            print("(brak odblokowanych featurów na tym poziomie)")
            return

        idx = 0
        while idx < len(features):
            f = features[idx]
            typ = "zaklęcie" if f["type"] == "spell" else "umiejętność"
            extra = f", poziom zaklęcia: {f['lvl']}" if f["lvl"] else ""

            activity_labels = {
                "passive": "pasywne",
                "action": "akcja",
                "bonus_action": "akcja dodatkowa",
                "reaction": "reakcja",
            }
            activity = activity_labels.get(f.get("activity"), "?")

            print(f"[{f['ch_lvl']:>2}] {f['name']}  ({typ}{extra}) — {activity}")
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
