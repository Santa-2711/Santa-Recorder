# SANTA RECORDER

Grabador de pantalla para Windows con captura de pantalla y audio interno.

## Primera versión

- Interfaz PySide6 con tema oscuro y acentos morados.
- Captura de escritorio con FFmpeg (gdigrab).
- Captura de audio de sistema mediante WASAPI (requiere FFmpeg compatible).
- Opciones de FPS, resolución de salida y carpeta de destino.
- Compilación Windows mediante GitHub Actions.

## Ejecutar localmente

Python 3.11+ y FFmpeg con soporte gdigrab/WASAPI.

```bash
pip install -r requirements.txt
python app.py
```

## Descargar ejecutable

En GitHub: Actions → Build SANTA RECORDER for Windows → Artifacts.

## Nota

Esta base inicial no incluye todavía el logotipo personalizado ni un icono .ICO; se añadirán cuando los archivos gráficos estén disponibles en el repositorio. El audio WASAPI requiere FFmpeg Windows con soporte WASAPI.
