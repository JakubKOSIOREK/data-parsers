import os
import logging
import argparse
from prettytable import PrettyTable
from typing import List, Tuple, Dict
import sys
from charset_normalizer import from_path

def configure_logging(verbose: bool) -> None:
    """Konfiguruje logger w zależności od trybu verbose."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

def validate_file(input_file: str) -> None:
    """Sprawdza, czy plik istnieje i czy nie jest pusty."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Błąd: Plik {input_file} nie istnieje.")
    if os.path.getsize(input_file) == 0:
        raise ValueError(f"Błąd: Plik {input_file} jest pusty.")

def detect_encoding(file_path: str) -> str:
    """
    Automatyczne wykrywanie kodowania pliku.
    
    Args:
        file_path (str): Ścieżka do pliku.
    
    Returns:
        str: Nazwa wykrytego kodowania.
    """
    try:
        result = from_path(file_path).best()
        if result is None:
            raise ValueError(f"Nie udało się wykryć kodowania dla pliku: {file_path}")
        return result.encoding
    except Exception as e:
        logging.error(f"Nie udało się wykryć kodowania pliku: {e}")
        raise

def read_file(file_path: str) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Odczytuje zawartość pliku, usuwa niepotrzebne wiersze i zwraca oczyszczone dane.
    
    Args:
        file_path (str): Ścieżka do pliku.
    
    Returns:
        dict: Słownik z 'Kod' jako klucz i listą pozostałych pól jako wartość.
        list: Lista pominiętych linii.
    """
    try:
        # Automatyczne wykrywanie kodowania pliku
        encoding = detect_encoding(file_path)
        logging.info(f"Wykryto kodowanie: {encoding} dla pliku {file_path}")

        with open(file_path, 'r', encoding=encoding) as file:
            content = file.readlines()

        data = {}
        skipped_lines = []

        for line in content:
            # Pomijaj nagłówek
            if line.strip() == "Kod\tNazwisko\tImie\tDział\tZatrudnienie":
                skipped_lines.append(line.strip())
                continue

            fields = line.strip().split("\t")
            if len(fields) == 5:
                kod, nazwisko, imie, dzial, zatrudnienie = fields
                data[kod] = [nazwisko, imie, dzial, zatrudnienie]
            else:
                skipped_lines.append(line.strip())

        return data, skipped_lines

    except Exception as e:
        logging.error(f"An error occurred while reading the file: {e}", exc_info=True)
        return {}, []

def display_content(content: List[Tuple[str, List[str], bool]], title: str) -> None:
    """
    Wyświetla zawartość pliku w formie tabeli z numerami wierszy i flagą is_active.
    
    Args:
        content (list): Lista zawierająca oczyszczone wiersze z flagami is_active.
        title (str): Tytuł tabeli.
    """
    table = PrettyTable()
    table.title = title
    table.field_names = ["Kod", "Nazwisko", "Imię", "Dział", "Zatrudnienie", "is_active"]
    
    for kod, fields, is_active in content:
        table.add_row([kod] + fields + [is_active])
    
    print(table)

def find_differences(content1: Dict[str, List[str]], content2: Dict[str, List[str]]) -> Tuple[List[Tuple[str, List[str], bool]], List[Tuple[str, List[str], bool]], List[Tuple[str, List[str], bool]]]:
    """
    Znajduje różnice między dwoma plikami na podstawie pola 'Kod'.
    
    Args:
        content1 (dict): Dane z pierwszego pliku.
        content2 (dict): Dane z drugiego pliku.
    
    Returns:
        tuple: (list, list, list)
            - Lista wierszy unikalnych dla pierwszego pliku.
            - Lista wierszy unikalnych dla drugiego pliku.
            - Lista wierszy wspólnych dla obu plików, ale z różnicami w polach.
    """
    set1 = set(content1.keys())
    set2 = set(content2.keys())

    unique_to_file1 = [(kod, content1[kod], False) for kod in set1 - set2]
    unique_to_file2 = [(kod, content2[kod], True) for kod in set2 - set1]
    modified_rows = [(kod, content1[kod], True) for kod in set1 & set2 if content1[kod] != content2[kod]]

    return unique_to_file1, unique_to_file2, modified_rows

def compare_files(file1: str, file2: str, verbose: bool = False, show_tables: bool = False) -> None:
    """
    Porównuje dwa pliki na podstawie ich zawartości i wyświetla różnice.
    
    Args:
        file1 (str): Ścieżka do pierwszego pliku.
        file2 (str): Ścieżka do drugiego pliku.
        verbose (bool): Czy wyświetlać szczegółowe logi.
        show_tables (bool): Czy wyświetlać tabelę z danymi.
    """
    configure_logging(verbose)

    try:
        # Walidacja plików
        validate_file(file1)
        validate_file(file2)

        # Odczytaj zawartość plików
        content1, skipped1 = read_file(file1)
        content2, skipped2 = read_file(file2)

        # Logowanie informacji po odczytaniu plików
        logging.info(f"Plik {file1} został pomyślnie odczytany.")
        logging.info(f"Plik {file2} został pomyślnie odczytany.")

        logging.debug(f"Plik {file1} został odczytany, pominięto {len(skipped1)} wierszy.")
        logging.debug(f"Plik {file2} został odczytany, pominięto {len(skipped2)} wierszy.")

        # Znajdź unikalne i zmienione wiersze dla obu plików
        unique_to_file1, unique_to_file2, modified_rows = find_differences(content1, content2)

        # Wyświetlanie wyników
        if show_tables:
            if unique_to_file1:
                display_content(unique_to_file1, "Unikalne wiersze - Plik 1")
            if unique_to_file2:
                display_content(unique_to_file2, "Unikalne wiersze - Plik 2")
            if modified_rows:
                display_content(modified_rows, "Zmodyfikowane wiersze")

        # Logowanie po zakończeniu działania skryptu
        logging.info("Porównanie plików zakończone pomyślnie.")

    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        sys.exit(1)  # Zakończenie programu z kodem błędu
    except Exception as e:
        logging.critical(f"Wystąpił nieoczekiwany błąd: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Argument parser do obsługi opcji --file1, --file2, --verbose, --tables
    parser = argparse.ArgumentParser(description="Porównaj dwa pliki i znajdź różnice.")
    parser.add_argument("--file1", required=True, help="Ścieżka do pierwszego pliku")
    parser.add_argument("--file2", required=True, help="Ścieżka do drugiego pliku")
    parser.add_argument("-v", "--verbose", action="store_true", help="Wyświetl szczegółowe informacje o przetwarzaniu pliku (DEBUG)")
    parser.add_argument("-t", "--tables", action="store_true", help="Wyświetl tabelę z danymi na konsoli")

    # Parsowanie argumentów
    args = parser.parse_args()
    file1 = args.file1
    file2 = args.file2
    verbose = args.verbose
    show_tables = args.tables

    # Uruchomienie porównania plików
    compare_files(file1, file2, verbose, show_tables)
