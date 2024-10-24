import os
import re
import argparse
import logging
from prettytable import PrettyTable
from typing import List, Tuple

def configure_logging(verbose: bool) -> None:
    """Konfiguruje logger w zależności od trybu verbose."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, 
                        format="%(asctime)s %(levelname)s: %(message)s", 
                        datefmt="%Y-%m-%d %H:%M:%S")

def validate_file(input_file: str) -> None:
    """Sprawdza, czy plik istnieje i czy nie jest pusty."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Błąd: Plik {input_file} nie istnieje.")
    if os.path.getsize(input_file) == 0:
        raise ValueError(f"Błąd: Plik {input_file} jest pusty.")

def process_file_content(content: List[str], expected_header: str) -> Tuple[List[str], List[str], PrettyTable]:
    """Przetwarza zawartość pliku i zwraca oczyszczoną zawartość oraz listę pominiętych wierszy."""
    cleaned_content = []
    skipped_lines = []
    table = PrettyTable()
    table.field_names = ["Kod", "Nazwisko", "Imię", "Dział", "Stanowisko"]

    for line in content:
        line_cleaned = line.strip()

        # Sprawdzanie i pomijanie nagłówka
        if re.sub(r"\s+", "", line_cleaned) == re.sub(r"\s+", "", expected_header):
            skipped_lines.append(line_cleaned)
            continue

        # Podział na pola przy użyciu tabulatorów lub wielu spacji
        fields = re.split(r'\t| {2,}', line_cleaned)

        # Usunięcie cudzysłowów
        fields = [field.replace('"', '') for field in fields]

        # Sprawdzenie, czy mamy 5 kolumn (Kod, Nazwisko, Imię, Dział, Stanowisko)
        if len(fields) == 5:
            table.add_row(fields)
            cleaned_content.append("\t".join(fields) + "\n")
        else:
            skipped_lines.append(line_cleaned)
    
    return cleaned_content, skipped_lines, table

def convert_to_utf8(input_file: str, verbose: bool = False, show_table: bool = False) -> None:
    configure_logging(verbose)
    
    try:
        # Walidacja pliku
        validate_file(input_file)

        # Tworzenie nazwy pliku wyjściowego, dodając '-utf8' przed rozszerzeniem
        output_file = os.path.splitext(input_file)[0] + '-utf8.txt'

        # Otwieranie pliku z kodowaniem UTF-16
        try:
            with open(input_file, 'r', encoding='utf-16') as file:
                content = file.readlines()
            logging.info(f"Plik {input_file} został pomyślnie otwarty.")
        except UnicodeDecodeError:
            logging.error(f"Błąd: Plik {input_file} nie jest w formacie UTF-16.")
            return

        # Oczekiwany nagłówek
        expected_header = "Kod\tNazwisko\tImie\tDział\tZatrudnienie".strip()

        # Przetwarzanie zawartości
        cleaned_content, skipped_lines, table = process_file_content(content, expected_header)
        
        logging.debug(f"Liczba odczytanych wierszy: {len(content)}")

        # Zapis do nowego pliku w UTF-8
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.writelines(cleaned_content)
            logging.info(f"Plik wyjściowy {output_file} został zapisany pomyślnie.")
        except OSError as os_err:
            logging.error(f"Błąd podczas zapisywania pliku: {output_file}, {os_err}")
            return

        # Sprawdzanie różnicy w liczbie zapisanych wierszy
        if len(content) != len(cleaned_content):
            logging.warning(f"Liczba odczytanych ({len(content)}) i zapisanych ({len(cleaned_content)}) wierszy jest różna!")
            logging.debug("Wiersze, które nie zostały zapisane:")
            for idx, skipped in enumerate(skipped_lines, start=1):
                logging.debug(f"{idx}. [{skipped}]")

        # Wyświetlenie tabeli, jeśli --table (-t) jest podane
        if show_table:
            print(table)

    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
    except OSError as os_err:
        logging.error(f"Wystąpił błąd operacji na pliku: {os_err}")
    except Exception as e:
        logging.critical(f"Wystąpił nieoczekiwany błąd: {e}")

if __name__ == "__main__":
    # Argument parser do obsługi opcji --path, --verbose, --table
    parser = argparse.ArgumentParser(description="Konwertuj plik z UTF-16 do UTF-8 i wyświetl wiersze w tabeli")
    parser.add_argument("--path", required=True, help="Ścieżka do pliku wejściowego w kodowaniu UTF-16")
    parser.add_argument("-v", "--verbose", action="store_true", help="Wyświetl szczegółowe informacje o przetwarzaniu pliku (DEBUG)")
    parser.add_argument("-t", "--table", action="store_true", help="Wyświetl tabelę z danymi na konsoli")

    # Parsowanie argumentów
    args = parser.parse_args()
    input_file = args.path
    verbose = args.verbose
    show_table = args.table

    # Uruchomienie funkcji konwersji
    convert_to_utf8(input_file, verbose, show_table)
