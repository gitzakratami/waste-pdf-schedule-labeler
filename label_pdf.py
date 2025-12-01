import fitz  # PyMuPDF
import math
import os

def color_distance(c1, c2):
    """Oblicza różnicę między kolorami."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def find_matching_fraction(pix, bbox, legend):
    """Skanuje obszar ikonki piksel po pikselu."""
    start_x = max(0, int(bbox.x0) + 2)
    end_x = min(pix.width, int(bbox.x1) - 2)
    start_y = max(0, int(bbox.y0) + 2)
    end_y = min(pix.height, int(bbox.y1) - 2)

    if start_x >= end_x or start_y >= end_y:
        return None

    for x in range(start_x, end_x, 2):
        for y in range(start_y, end_y, 2):
            pixel_color = pix.pixel(x, y)
            
            # Ignoruj jasne tła (biały)
            if sum(pixel_color) > 700: 
                continue

            for item in legend:
                # Tolerancja 45 dla precyzyjnych kolorów
                if color_distance(pixel_color, item["color"]) < 45:
                    return item["name"]
    return None

def label_waste_schedule_final_v6(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    FONT_SIZE = 10
    font_path = "C:/Windows/Fonts/arialbd.ttf"
    
    # --- PRZYGOTOWANIE CZCIONKI ---
    calc_font = None # Obiekt do obliczania długości
    use_custom_font = False

    if os.path.exists(font_path):
        try:
            # Tworzymy obiekt czcionki TYLKO do pomiarów długości
            calc_font = fitz.Font(fontfile=font_path)
            use_custom_font = True
            print("Załadowano czcionkę Arial Bold (Polskie znaki i pomiary OK).")
        except Exception as e:
            print(f"Nie udało się wczytać czcionki do pomiarów: {e}")

    # DEFINICJA KOLORÓW
    legend = [
        {"name": "ZIELONE",         "color": (83, 88, 90)},    # 53585A
        {"name": "ZMIESZANE",       "color": (33, 35, 35)},    # 212323
        {"name": "PAPIER",          "color": (0, 95, 170)},
        {"name": "SZKŁO",           "color": (45, 160, 45)},
        {"name": "PLASTIK",         "color": (255, 205, 0)},
        {"name": "PLASTIK",         "color": (245, 170, 0)},
        {"name": "PLASTIK",         "color": (230, 150, 0)},
        {"name": "SKIP",            "color": (140, 90, 60)},   # BIO
        {"name": "SKIP",            "color": (110, 70, 40)},   # BIO GASTRO
        {"name": "SKIP",            "color": (230, 90, 20)},   # GABARYTY
    ]

    print(f"Przetwarzanie pliku: {input_pdf}...")
    
    for page in doc:
        pix = page.get_pixmap()
        images_info = page.get_image_info(xrefs=True)
        
        # KROK 1: Zbierz wszystkie ikonki
        page_icons = []
        for img in images_info:
            bbox = fitz.Rect(img['bbox'])
            # Filtr rozmiaru
            if bbox.width < 8 or bbox.width > 80: continue
            
            label = find_matching_fraction(pix, bbox, legend)
            if label:
                page_icons.append({"rect": bbox, "label": label})

        # KROK 2: Przetwórz etykiety i sprawdź kolizje
        for icon in page_icons:
            if icon["label"] == "SKIP":
                continue

            text_str = icon["label"]
            
            # --- OBLICZANIE DŁUGOŚCI TEKSTU ---
            if use_custom_font and calc_font:
                # Używamy obiektu font do obliczenia długości (to działa!)
                text_len = calc_font.text_length(text_str, fontsize=FONT_SIZE)
            else:
                # Fallback do Helvetica (może być niedokładne dla PL znaków)
                text_len = fitz.get_text_length(text_str, fontsize=FONT_SIZE, fontname="Helvetica-Bold")

            # Początkowa pozycja (5px na lewo od ikonki)
            right_edge_of_text = icon["rect"].x0 - 5
            
            # --- ALGORYTM UNIKANIA KOLIZJI ---
            collision = True
            while collision:
                collision = False
                # Prostokąt, który zajmie tekst
                text_rect = fitz.Rect(
                    right_edge_of_text - text_len, 
                    icon["rect"].y0,               
                    right_edge_of_text,            
                    icon["rect"].y1                
                )

                # Sprawdź każdą inną ikonkę na stronie
                for obstacle in page_icons:
                    if obstacle is icon: continue 
                    
                    # Jeśli tekst nachodzi na przeszkodę
                    if text_rect.intersects(obstacle["rect"]):
                        # Przesuń tekst w lewo, przed przeszkodę
                        right_edge_of_text = obstacle["rect"].x0 - 5
                        collision = True
                        break 

            # --- WPISANIE TEKSTU ---
            final_x = right_edge_of_text - text_len
            final_y = icon["rect"].y1 - 4
            
            if use_custom_font:
                # Tutaj używamy fontfile, bo insert_text to obsługuje
                page.insert_text(
                    (final_x, final_y), 
                    text_str, 
                    fontsize=FONT_SIZE, 
                    fontfile=font_path, 
                    color=(0,0,0)
                )
            else:
                page.insert_text(
                    (final_x, final_y), 
                    text_str, 
                    fontsize=FONT_SIZE, 
                    fontname="Helvetica-Bold", 
                    color=(0,0,0)
                )

    doc.save(output_pdf)
    print(f"Gotowe! Plik zapisany jako: {output_pdf}")

# --- URUCHOMIENIE ---
plik_wejsciowy = "harmonogram.pdf"
plik_wyjsciowy = "harmonogram_opisany.pdf"

try:
    label_waste_schedule_final_v6(plik_wejsciowy, plik_wyjsciowy)
except Exception as e:
    print(f"Wystąpił błąd krytyczny: {e}")