import html
import json
from pathlib import Path

# Cambiá este nombre si tu archivo JSON se llama distinto
ARCHIVO_JSON = Path("departamentos-jujuy.json")
ARCHIVO_SALIDA = Path("mapa_jujuy_generado.html")

REGION_POR_DEPTO = {
    "COCHINOCA": "Puna",
    "RINCONADA": "Puna",
    "SANTA CATALINA": "Puna",
    "SUSQUES": "Puna",
    "YAVI": "Puna",
    "HUMAHUACA": "Quebrada",
    "TILCARA": "Quebrada",
    "TUMBAYA": "Quebrada",
    "DOCTOR MANUEL BELGRANO": "Valles",
    "EL CARMEN": "Valles",
    "PALPALA": "Valles",
    "SAN ANTONIO": "Valles",
    "LEDESMA": "Yungas",
    "SAN PEDRO": "Yungas",
    "SANTA BARBARA": "Yungas",
    "VALLE GRANDE": "Yungas",
}

COLOR_POR_REGION = {
    "Puna": "#9C7A54",
    "Quebrada": "#F3A683",
    "Valles": "#C5D88D",
    "Yungas": "#78C28E",
}


def iter_anillos(geometry):
    """Extrae todos los anillos de coordenadas de Polygon o MultiPolygon."""
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if gtype == "Polygon":
        for anillo in coords:
            yield anillo
    elif gtype == "MultiPolygon":
        for poligono in coords:
            for anillo in poligono:
                yield anillo


def main():
    if not ARCHIVO_JSON.exists():
        raise FileNotFoundError(f"No se encontró el archivo {ARCHIVO_JSON.resolve()}")

    with ARCHIVO_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    deptos = []

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for feat in features:
        props = feat.get("properties", {})
        nombre_raw = (
            props.get("departamento")
            or props.get("nombre")
            or props.get("name")
            or ""
        ).strip().upper()

        if not nombre_raw:
            continue

        anillos = list(iter_anillos(feat.get("geometry", {})))
        if not anillos:
            continue

        for anillo in anillos:
            for lon, lat in anillo:
                if lon < min_x:
                    min_x = lon
                if lon > max_x:
                    max_x = lon
                if lat < min_y:
                    min_y = lat
                if lat > max_y:
                    max_y = lat

        region = REGION_POR_DEPTO.get(nombre_raw, "Valles")
        deptos.append((nombre_raw, region, anillos))

    ancho = 600.0
    alto = 680.0
    margen = 24.0

    rango_x = max(max_x - min_x, 1e-9)
    rango_y = max(max_y - min_y, 1e-9)
    escala = min((ancho - 2 * margen) / rango_x, (alto - 2 * margen) / rango_y)

    ancho_dibujado = rango_x * escala
    alto_dibujado = rango_y * escala
    offset_x = (ancho - ancho_dibujado) / 2.0
    offset_y = (alto - alto_dibujado) / 2.0

    def a_svg(lon, lat):
        x = offset_x + (lon - min_x) * escala
        y = offset_y + (max_y - lat) * escala
        return round(x, 2), round(y, 2)

    lineas_path = []
    detectados = set()

    for nombre, region, anillos in deptos:
        detectados.add(nombre)
        partes_d = []

        for anillo in anillos:
            if not anillo:
                continue
            x0, y0 = a_svg(anillo[0][0], anillo[0][1])
            partes_d.append(f"M {x0} {y0}")
            for lon, lat in anillo[1:]:
                x, y = a_svg(lon, lat)
                partes_d.append(f"L {x} {y}")
            partes_d.append("Z")

        d_str = " ".join(partes_d)
        fill = COLOR_POR_REGION.get(region, "#CBD5E1")
        titulo = html.escape(nombre.title())
        region_esc = html.escape(region)
        slug = nombre.lower().replace(" ", "-")

        lineas_path.append(
            f'  <path id="depto-{slug}" data-depto="{titulo}" data-region="{region_esc}" '
            f'd="{d_str}" fill="{fill}" stroke="#FFFFFF" stroke-width="1.6" '
            f'style="cursor:pointer;transition:opacity .2s,stroke-width .2s;">'
            f"<title>{titulo} ({region_esc})</title></path>"
        )

    svg_final = (
        f'<svg id="mapa-jujuy-svg" viewBox="0 0 {int(ancho)} {int(alto)}" '
        f'width="100%" role="img" aria-label="Mapa interactivo de Jujuy">\n'
        + "\n".join(lineas_path)
        + "\n</svg>\n"
    )

    ARCHIVO_SALIDA.write_text(svg_final, encoding="utf-8")

    faltantes = sorted(set(REGION_POR_DEPTO.keys()) - detectados)
    print(f"Departamentos dibujados: {len(detectados)} / {len(REGION_POR_DEPTO)}")
    if faltantes:
        print("Faltaron estos departamentos en el JSON:", faltantes)
    print(f"Archivo generado: {ARCHIVO_SALIDA.resolve()}")


if __name__ == "__main__":
    main()