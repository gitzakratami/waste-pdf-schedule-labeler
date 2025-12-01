import fitz  # PyMuPDF

def are_colors_close(c1, c2, tolerance=0.1):
    """Sprawdza czy dwa kolory są do siebie podobne (dla formatu RGB 0-1)."""
    if not c1 or not c2: return False
    # Jeśli kolor jest zdefiniowany jako float (skala szarości), zamień na krotkę
    if isinstance(c1, float): c1 = (c1, c1, c1)
    if isinstance(c2, float): c2 = (c2, c2, c2)
    
    # Sprawdź długość (niektóre kolory to CMYK, tutaj upraszczamy do RGB)
    if len(c1) != 3 or len(c2) != 3: return False

    return all(abs(c1[i] - c2[i]) < tolerance for i in range(3))

def label_waste_schedule(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)

    # DEFINICJA KOLORÓW I NAZW (Wartości RGB w skali 0.0 - 1.0)
    # Kolory pobrane "na oko" z typowych harmonogramów, mogą wymagać drobnej korekty
    legend = [
        {"name": "Papier",    "color": (0.0, 0.45, 0.75)},   # Niebieski
        {"name": "Metale/Plastik", "color": (1.0, 0.8, 0.0)}, # Żółty/Pomarańczowy
        {"name": "Szkło",     "color": (0.2, 0.6, 0.2)},     # Zielony (butelka)
        {"name": "Bio",       "color": (0.6, 0.3, 0.1)},     # Brązowy
        {"name": "Zmieszane", "color": (0.0, 0.0, 0.0)},     # Czarny
        {"name": "Zielone",   "color": (0.5, 0.5, 0.5)},     # Szary/Zgniła zieleń (liść)
        {"name": "Gabaryty",  "color": (0.8, 0.4, 0.1)},     # Rdzawy/Czerwony (meble)
    ]

    print(f"Przetwarzanie pliku: {input_pdf}...")

    for page in doc:
        # Pobierz wszystkie rysunki wektorowe (ikonki są zazwyczaj wektorami)
        drawings = page.get_drawings()
        
        # Lista miejsc, gdzie już wpisaliśmy tekst (żeby nie dublować dla skomplikowanych ikon)
        labeled_locations = []

        for path in drawings:
            fill_color = path.get("fill") # Pobierz kolor wypełnienia kształtu
            rect = path["rect"]           # Pobierz współrzędne (x, y, szer, wys)

            # Filtrowanie: Pomiń bardzo małe kropki lub wielkie tła oraz linie tabeli
            if rect.width > 50 or rect.width < 5 or rect.height < 5:
                continue

            found_label = None
            
            # Sprawdź czy kolor pasuje do naszej legendy
            for item in legend:
                if are_colors_close(fill_color, item["color"]):
                    found_label = item["name"]
                    break
            
            if found_label:
                # Sprawdź czy nie opisaliśmy już tej ikonki (ikonka może składać się z wielu kształtów)
                # Sprawdzamy czy w promieniu 10 punktów już czegoś nie wstawiliśmy
                already_labeled = False
                for loc in labeled_locations:
                    if abs(loc.x - rect.x) < 15 and abs(loc.y - rect.y) < 15:
                        already_labeled = True
                        break
                
                if not already_labeled:
                    # Wstaw tekst
                    # x + width + 2 = wstawiamy zaraz za ikonką
                    # y + height - 2 = wyrównanie do dołu ikonki
                    text_point = fitz.Point(rect.x + rect.width + 2, rect.y + rect.height/1.2)
                    
                    page.insert_text(
                        text_point, 
                        found_label, 
                        fontsize=6,           # Mała czcionka, żeby się zmieściło
                        color=(0.2, 0.2, 0.2) # Ciemnoszary kolor tekstu
                    )
                    
                    labeled_locations.append(rect)

    doc.save(output_pdf)
    print(f"Gotowe! Zapisano jako: {output_pdf}")

# --- KONFIGURACJA ---
# Podaj tutaj nazwę swojego pliku PDF
plik_wejsciowy = "harmonogram.pdf" 
plik_wyjsciowy = "harmonogram_opisany.pdf"

try:
    label_waste_schedule(plik_wejsciowy, plik_wyjsciowy)
except Exception as e:
    print(f"Wystąpił błąd: {e}")
    print("Upewnij się, że nazwa pliku jest poprawna i plik nie jest otwarty w innym programie.")