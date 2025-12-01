import fitz  # PyMuPDF
import math
import os

def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def find_matching_fraction(pix, bbox, legend):
    # Margines 2px
    start_x = max(0, int(bbox.x0) + 2)
    end_x = min(pix.width, int(bbox.x1) - 2)
    start_y = max(0, int(bbox.y0) + 2)
    end_y = min(pix.height, int(bbox.y1) - 2)

    if start_x >= end_x or start_y >= end_y:
        return None

    for x in range(start_x, end_x, 2):
        for y in range(start_y, end_y, 2):
            pixel_color = pix.pixel(x, y)
            if sum(pixel_color) > 700: continue # Ignoruj jasne tła

            for item in legend:
                if color_distance(pixel_color, item["color"]) < 45:
                    return item["name"]
    return None

def label_waste_schedule_final_v8(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    FONT_SIZE = 10
    font_path = "C:/Windows/Fonts/arialbd.ttf"
    
    # --- PRZYGOTOWANIE CZCIONKI (OBIEKT) ---
    # Tworzymy obiekt czcionki raz i używamy go wszędzie (do mierzenia i pisania)
    custom_font = None
    use_custom_font = False

    if os.path.exists(font_path):
        try:
            custom_font = fitz.Font(fontfile=font_path)
            use_custom_font = True
            print("Załadowano czcionkę Arial Bold (TextWriter gotowy).")
        except Exception as e:
            print(f"Błąd ładowania czcionki: {e}")
    else:
        print("UWAGA: Nie znaleziono Arial Bold. Polskie znaki mogą nie działać.")

    # DEFINICJA KOLORÓW
    legend = [
        {"name": "ZIELONE",         "color": (83, 88, 90)},
        {"name": "ZMIESZANE",       "color": (33, 35, 35)},
        {"name": "PAPIER",          "color": (0, 95, 170)},
        {"name": "SZKŁO",           "color": (45, 160, 45)},
        {"name": "PLASTIK",         "color": (255, 205, 0)},
        {"name": "PLASTIK",         "color": (245, 170, 0)},
        {"name": "PLASTIK",         "color": (230, 150, 0)},
        {"name": "SKIP",            "color": (140, 90, 60)}, 
        {"name": "SKIP",            "color": (110, 70, 40)}, 
        {"name": "SKIP",            "color": (230, 90, 20)}, 
    ]

    print(f"Przetwarzanie pliku: {input_pdf}...")
    
    for page in doc:
        pix = page.get_pixmap()
        images_info = page.get_image_info(xrefs=True)
        
        # --- FILTR LEGENDY (0.9) ---
        page_height = page.rect.height
        legend_cutoff_y = page_height * 0.9

        # Inicjalizacja TextWritera dla tej strony
        # TextWriter to profesjonalne narzędzie do składania tekstu w PyMuPDF
        writer = fitz.TextWriter(page.rect)
        
        page_icons = []
        for img in images_info:
            bbox = fitz.Rect(img['bbox'])
            if bbox.width < 8 or bbox.width > 80: continue
            
            # Ignorowanie legendy na dole
            if bbox.y0 > legend_cutoff_y:
                continue

            label = find_matching_fraction(pix, bbox, legend)
            if label:
                page_icons.append({"rect": bbox, "label": label})

        for icon in page_icons:
            if icon["label"] == "SKIP": continue

            text_str = icon["label"]
            
            # --- POMIARY ---
            if use_custom_font:
                # Mierzymy używając obiektu font
                text_len = custom_font.text_length(text_str, fontsize=FONT_SIZE)
            else:
                text_len = fitz.get_text_length(text_str, fontsize=FONT_SIZE, fontname="Helvetica-Bold")

            right_edge_of_text = icon["rect"].x0 - 5
            
            # --- KOLIZJE ---
            collision = True
            while collision:
                collision = False
                text_rect = fitz.Rect(
                    right_edge_of_text - text_len, 
                    icon["rect"].y0,               
                    right_edge_of_text,            
                    icon["rect"].y1                
                )

                for obstacle in page_icons:
                    if obstacle is icon: continue 
                    if text_rect.intersects(obstacle["rect"]):
                        right_edge_of_text = obstacle["rect"].x0 - 5
                        collision = True
                        break 

            final_x = right_edge_of_text - text_len
            final_y = icon["rect"].y1 - 2
            
            # --- WPISYWANIE DO BUFORA (TextWriter) ---
            if use_custom_font:
                # append(pos, text, font=...) gwarantuje poprawne kodowanie polskich znaków
                writer.append((final_x, final_y), text_str, font=custom_font, fontsize=FONT_SIZE)
            else:
                # Fallback (gdyby Arial nie istniał)
                # W tym przypadku musimy użyć innej metody, bo writer wymaga fontu
                page.insert_text((final_x, final_y), text_str, fontsize=FONT_SIZE, fontname="Helvetica-Bold", color=(0,0,0))

        # --- ZAPIS BUFORA NA STRONĘ ---
        # Dopiero teraz fizycznie nanosimy cały tekst na stronę
        if use_custom_font:
            writer.write_text(page, color=(0, 0, 0))

    doc.save(output_pdf)
    print(f"Gotowe! Plik zapisany jako: {output_pdf}")

# --- URUCHOMIENIE ---
plik_wejsciowy = "harmonogram.pdf"
plik_wyjsciowy = "harmonogram_opisany.pdf"

try:
    label_waste_schedule_final_v8(plik_wejsciowy, plik_wyjsciowy)
except Exception as e:
    print(f"Wystąpił błąd krytyczny: {e}")