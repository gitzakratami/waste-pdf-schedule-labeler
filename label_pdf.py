import fitz  # PyMuPDF
import math

def color_distance(c1, c2):
    """Oblicza różnicę między kolorami."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def label_waste_schedule_final(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    # Ustawienia tekstu
    FONT_SIZE = 10         
    FONT_NAME = "Helvetica-Bold" 
    
    # DEFINICJA KOLORÓW
    legend = [
        {"name": "PAPIER",          "color": (0, 95, 170)},    # Niebieski
        
        # --- PLASTIK (Różne odcienie żółtego/pomarańczowego) ---
        {"name": "PLASTIK",         "color": (255, 205, 0)},   
        {"name": "PLASTIK",         "color": (245, 170, 0)},   
        {"name": "PLASTIK",         "color": (230, 150, 0)},   
        
        {"name": "SZKŁO",           "color": (45, 160, 45)},   # Zielony
        {"name": "ZMIESZANE",       "color": (40, 40, 40)},    # Bardzo ciemny/Czarny
        
        # --- ZIELONE (Różne odcienie szarości) ---
        # Dodajemy kilka wariantów, żeby trafić w ten konkretny ze zrzutu ekranu
        {"name": "ZIELONE",         "color": (85, 90, 95)},    # Szary (standardowy)
        {"name": "ZIELONE",         "color": (105, 105, 105)}, # Jaśniejszy szary (DimGray)
        {"name": "ZIELONE",         "color": (80, 80, 80)},    # Ciemny szary (ale nie czarny)
        {"name": "ZIELONE",         "color": (96, 106, 116)},  # Szaro-niebieskawy (częsty w druku)
        
        # --- FRAKCJE IGNOROWANE (SKIP) ---
        {"name": "SKIP",            "color": (140, 90, 60)},   # BIO
        {"name": "SKIP",            "color": (110, 70, 40)},   # BIO GASTRO
        {"name": "SKIP",            "color": (230, 90, 20)},   # GABARYTY
    ]

    print(f"Przetwarzanie pliku: {input_pdf}...")
    labeled_count = 0

    for page in doc:
        pix = page.get_pixmap()
        images_info = page.get_image_info(xrefs=True)

        for img in images_info:
            bbox = fitz.Rect(img['bbox'])
            
            # Filtrowanie po rozmiarze
            if bbox.width < 10 or bbox.width > 70:
                continue
            
            # Próbkowanie koloru ze środka
            mid_x = int(bbox.x0 + bbox.width / 2) + 2
            mid_y = int(bbox.y0 + bbox.height / 2) + 2

            if mid_x >= pix.width or mid_y >= pix.height:
                continue

            pixel_color = pix.pixel(mid_x, mid_y)
            
            # Jeśli trafiliśmy w biały (liść w środku), bierzemy kolor z lewego górnego rogu tła
            if sum(pixel_color) > 700: 
                 pixel_color = pix.pixel(int(bbox.x0 + 2), int(bbox.y0 + 2))

            found_label = None
            best_dist = 1000
            
            # Szukanie pasującego koloru
            for item in legend:
                dist = color_distance(pixel_color, item["color"])
                
                # Tolerancja 65 jest bezpieczna, żeby nie pomylić ZIELONE (szary) ze ZMIESZANE (czarny)
                if dist < 65: 
                    if dist < best_dist:
                        best_dist = dist
                        found_label = item["name"]

            # Wpisanie tekstu
            if found_label and found_label != "SKIP":
                text_len = fitz.get_text_length(found_label, fontsize=FONT_SIZE, fontname=FONT_NAME)
                
                # Pozycjonowanie po lewej stronie
                x_pos = bbox.x0 - text_len - 5
                y_pos = bbox.y1 - 4
                
                text_point = fitz.Point(x_pos, y_pos)
                
                page.insert_text(
                    text_point, 
                    found_label, 
                    fontsize=FONT_SIZE, 
                    fontname=FONT_NAME,
                    color=(0, 0, 0) 
                )
                labeled_count += 1

    doc.save(output_pdf)
    print(f"Gotowe! Oznaczono {labeled_count} frakcji.")
    print(f"Plik zapisany jako: {output_pdf}")

# --- KONFIGURACJA ---
plik_wejsciowy = "harmonogram.pdf"
plik_wyjsciowy = "harmonogram_opisany.pdf"

try:
    label_waste_schedule_final(plik_wejsciowy, plik_wyjsciowy)
except Exception as e:
    print(f"Wystąpił błąd: {e}")