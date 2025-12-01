import fitz  # PyMuPDF
import math

def color_distance(c1, c2):
    """Oblicza różnicę między dwoma kolorami (pitagoras w 3D)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def label_waste_schedule_images(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    # DEFINICJA KOLORÓW (Wartości RGB 0-255)
    # Wartości przybliżone na podstawie Twojego zrzutu ekranu
    legend = [
        {"name": "Papier",           "color": (0, 95, 170)},    # Niebieski
        {"name": "Metale/Plastik",   "color": (245, 170, 0)},   # Żółty
        {"name": "Szkło",            "color": (45, 160, 45)},   # Zielony
        {"name": "Bio",              "color": (140, 90, 60)},   # Brązowy (jasny)
        {"name": "Zmieszane",        "color": (40, 40, 40)},    # Czarny/Ciemnoszary
        {"name": "Zielone",          "color": (85, 90, 95)},    # Szary (liść)
        {"name": "Gabaryty",         "color": (230, 90, 20)},   # Pomarańczowy/Rudy
        {"name": "Bio Gastronomia",  "color": (110, 70, 40)},   # Ciemny brąz
    ]

    print(f"Przetwarzanie pliku: {input_pdf}...")
    
    labeled_count = 0

    for page in doc:
        # Krok 1: Renderujemy stronę do pamięci jako obrazek, żeby móc sprawdzić kolory pikseli
        pix = page.get_pixmap()
        
        # Krok 2: Pobieramy informacje o wszystkich obrazkach wklejonych w PDF
        images_info = page.get_image_info(xrefs=True)

        for img in images_info:
            bbox = fitz.Rect(img['bbox'])
            
            # Filtrowanie: Ignorujemy tła i bardzo małe elementy
            # Zakładamy, że ikonka ma szerokość między 10 a 60 punktów
            if bbox.width < 10 or bbox.width > 60:
                continue
            
            # Pobieramy kolor ze środka obrazka
            mid_x = int(bbox.x0 + bbox.width / 2)
            mid_y = int(bbox.y0 + bbox.height / 2)

            # Sprawdzamy czy punkt mieści się w granicach strony
            if mid_x >= pix.width or mid_y >= pix.height:
                continue

            # Pobieramy kolor piksela (r, g, b)
            pixel_color = pix.pixel(mid_x, mid_y)
            
            # Szukamy pasującego koloru w legendzie
            found_label = None
            best_dist = 1000
            
            for item in legend:
                dist = color_distance(pixel_color, item["color"])
                # Jeśli kolor jest wystarczająco blisko (tolerancja 60)
                if dist < 60: 
                    if dist < best_dist:
                        best_dist = dist
                        found_label = item["name"]

            if found_label:
                # Wstaw tekst obok ikonki
                text_point = fitz.Point(bbox.x1 + 2, bbox.y1 - 4) # x1 to prawa krawędź
                
                page.insert_text(
                    text_point, 
                    found_label, 
                    fontsize=6, 
                    color=(0.2, 0.2, 0.2)
                )
                labeled_count += 1
                # Debug: odkomentuj linię poniżej, jeśli chcesz widzieć co wykryto
                # print(f"Wykryto {found_label} w kolorze {pixel_color}")

    if labeled_count == 0:
        print("UWAGA: Nie oznaczono żadnej ikonki.")
        print("Możliwe przyczyny:")
        print("1. Ikonki nie są obrazkami (metoda get_image_info zawiodła).")
        print("2. Kolory w legendzie różnią się zbyt mocno od tych w pliku.")
    else:
        doc.save(output_pdf)
        print(f"Sukces! Oznaczono {labeled_count} ikon. Zapisano: {output_pdf}")

# --- KONFIGURACJA ---
plik_wejsciowy = "harmonogram.pdf"
plik_wyjsciowy = "harmonogram_opisany.pdf"

try:
    label_waste_schedule_images(plik_wejsciowy, plik_wyjsciowy)
except Exception as e:
    print(f"Wystąpił błąd: {e}")