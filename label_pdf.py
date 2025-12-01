import fitz  # PyMuPDF
import math

def color_distance(c1, c2):
    """Oblicza różnicę między kolorami."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def label_waste_schedule_final(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    # Rozmiar czcionki
    FONT_SIZE = 9
    
    # DEFINICJA KOLORÓW I NAZW (WIELKIMI LITERAMI)
    legend = [
        {"name": "PAPIER",          "color": (0, 95, 170)},    # Niebieski
        {"name": "PLASTIK",         "color": (245, 170, 0)},   # Żółty/Pomarańczowy (dawniej Metale...)
        {"name": "SZKŁO",           "color": (45, 160, 45)},   # Zielony
        {"name": "BIO",             "color": (140, 90, 60)},   # Brązowy
        {"name": "ZMIESZANE",       "color": (40, 40, 40)},    # Ciemny
        {"name": "ZIELONE",         "color": (85, 90, 95)},    # Szary
        {"name": "BIO GASTRO",      "color": (110, 70, 40)},   # Ciemny brąz
        
        # Definiujemy gabaryty, żeby program wiedział co to jest, 
        # ale nazwiemy je "SKIP", żeby ich nie pisał.
        {"name": "SKIP",            "color": (230, 90, 20)},   # Rudy (Gabaryty)
    ]

    print(f"Przetwarzanie pliku: {input_pdf}...")
    labeled_count = 0

    for page in doc:
        pix = page.get_pixmap()
        images_info = page.get_image_info(xrefs=True)

        for img in images_info:
            bbox = fitz.Rect(img['bbox'])
            
            # Filtrowanie wielkości ikonki
            if bbox.width < 10 or bbox.width > 60:
                continue
            
            # Pobieranie koloru środka
            mid_x = int(bbox.x0 + bbox.width / 2)
            mid_y = int(bbox.y0 + bbox.height / 2)

            if mid_x >= pix.width or mid_y >= pix.height:
                continue

            pixel_color = pix.pixel(mid_x, mid_y)
            
            found_label = None
            best_dist = 1000
            
            # Szukanie najlepszego koloru
            for item in legend:
                dist = color_distance(pixel_color, item["color"])
                if dist < 60: 
                    if dist < best_dist:
                        best_dist = dist
                        found_label = item["name"]

            # Logika wpisywania tekstu
            if found_label and found_label != "SKIP":
                # Obliczamy szerokość tekstu, żeby wyrównać go do lewej
                text_len = fitz.get_text_length(found_label, fontsize=FONT_SIZE)
                
                # Ustawiamy punkt wstawienia po lewej stronie ikonki (bbox.x0)
                # Odejmujemy szerokość tekstu i mały margines (4 punkty)
                x_pos = bbox.x0 - text_len - 4
                
                # Ustawiamy wysokość (lekka korekta w dół, żeby było równo z ikonką)
                y_pos = bbox.y1 - 4
                
                text_point = fitz.Point(x_pos, y_pos)
                
                page.insert_text(
                    text_point, 
                    found_label, 
                    fontsize=FONT_SIZE, 
                    color=(0, 0, 0) # Czarny tekst dla lepszego kontrastu
                )
                labeled_count += 1

    doc.save(output_pdf)
    print(f"Gotowe! Oznaczono {labeled_count} frakcji (pominięto gabaryty).")
    print(f"Plik zapisany jako: {output_pdf}")

# --- KONFIGURACJA ---
plik_wejsciowy = "harmonogram.pdf"
plik_wyjsciowy = "harmonogram_opisany.pdf"

try:
    label_waste_schedule_final(plik_wejsciowy, plik_wyjsciowy)
except Exception as e:
    print(f"Wystąpił błąd: {e}")