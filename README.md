# Gestión Documental de Instalaciones de Internet

Herramientas en Python para convertir imágenes a PDF y gestionar contratos en Google Drive.

---

## Instalación

1. Crear y activar el entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Colocar el archivo `credentials.json` (descargado desde Google Cloud Console) en la raíz del proyecto.

> En la primera ejecución se abrirá el navegador para autorizar. El token se guarda en `token.json` automáticamente para usos futuros.

---

## Interfaz gráfica

```bash
python gui.py
```

Permite seleccionar imágenes JPG/PNG y convertirlas a PDF desde una ventana gráfica.

---

## Comandos de terminal

El `FOLDER_ID` es el código al final de la URL de Google Drive:
`https://drive.google.com/drive/folders/<FOLDER_ID>`

### Subir una semana completa de clientes

Procesa cada subcarpeta de clientes (convierte imágenes a PDF) y las sube a Drive.

```bash
python -m contratos.cli.subir_semana --ruta_local <carpeta_semana> --drive_folder_id <FOLDER_ID>
```

**Ejemplo:**
```bash
python -m contratos.cli.subir_semana --ruta_local "C:\Yoro\Semana 8" --drive_folder_id 1BxiMVs0XRA5nFMdKvBd
```

Opción adicional:
```
--credentials ruta/a/credentials.json   # por defecto: credentials.json en la raíz
```

Por cada cliente, el comando:
1. Recoge PDFs existentes en la carpeta del cliente
2. Une imágenes de cédula (`CC1`, `CC2`) en `CEDULA_<cliente>.pdf`
3. Convierte el resto de imágenes a PDFs individuales
4. Crea la carpeta en Drive (si no existe) y sube todo

### Estructura esperada en tu computador

```
Semana 8/
├── JUAN PEREZ/
│   ├── CC1.jpg
│   ├── CC2.jpg
│   └── instalacion.jpg
├── MARIA LOPEZ/
│   ├── CC1.png
│   ├── CC2.png
│   ├── contrato.pdf
│   └── router.jpg
```

### Resultado en Google Drive

```
Carpeta destino/
├── JUAN PEREZ/
│   ├── CEDULA_JUAN PEREZ.pdf
│   └── instalacion.pdf
├── MARIA LOPEZ/
│   ├── CEDULA_MARIA LOPEZ.pdf
│   ├── contrato.pdf
│   └── router.pdf
```

---

### Subir contratos corregidos a Drive

Sube PDFs de una carpeta local a sus subcarpetas en Drive según el código de 6 dígitos en el nombre del archivo.

```bash
python -m contratos.cli.subir_contratos <carpeta_local> <FOLDER_ID>
```

**Ejemplo:**
```bash
python -m contratos.cli.subir_contratos "C:\Contratos\corregidos" 1BxiMVs0XRA5nFMdKvBd
```

---

### Pipeline completo

Ejecuta en orden: **1) corregir PDFs → 2) subir a Drive → 3) limpiar duplicados**.

```bash
python -m contratos.cli.pipeline <carpeta_local> <FOLDER_ID>
```

**Ejecutar solo algunos pasos:**
```bash
# Solo corregir (paso 1)
python -m contratos.cli.pipeline <carpeta_local> <FOLDER_ID> --pasos 1

# Solo subir y limpiar (pasos 2 y 3)
python -m contratos.cli.pipeline <carpeta_local> <FOLDER_ID> --pasos 2 3
```

Los PDFs corregidos se guardan en `<carpeta_local>/contratos_corregidos/`.

---

### Limpiar duplicados en Drive

Busca archivos `Contrato Nº ...` duplicados, muestra cuáles conservar y cuáles eliminar, y pide confirmación antes de mover a la papelera.

```bash
python -m contratos.cli.limpiar <FOLDER_ID>
```

---

### Explorar árbol de carpetas en Drive

Muestra la estructura de carpetas y la cantidad de archivos por carpeta.

```bash
python -m contratos.cli.explorar <FOLDER_ID>
```

---

## Configurar Google Drive API (solo una vez)

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto o seleccionar uno existente
3. **APIs y Servicios → Biblioteca** → buscar **Google Drive API** → Habilitar
4. **APIs y Servicios → Credenciales → Crear credenciales → ID de cliente OAuth**
5. Pantalla de consentimiento: tipo **Externo**, scope `https://www.googleapis.com/auth/drive`, agregarte como usuario de prueba
6. Tipo de aplicación: **Aplicación de escritorio**
7. Descargar el JSON → renombrarlo a `credentials.json` → colocarlo en la raíz del proyecto

---

## Estructura del proyecto

```
contratos/
├── exceptions.py          # ContratosError, DriveAuthError, DriveUploadError, PdfProcessingError
├── logger.py              # get_logger() centralizado
├── core/
│   ├── drive_client.py    # autenticación y operaciones de Drive
│   ├── pdf_converter.py   # conversión de imágenes a PDF
│   ├── pdf_corrector.py   # corrección de texto en PDFs con PyMuPDF
│   └── duplicates.py      # detección de duplicados en Drive
└── cli/
    ├── subir_contratos.py
    ├── subir_semana.py
    ├── pipeline.py
    ├── limpiar.py
    └── explorar.py

gui.py                     # interfaz gráfica (tkinter)
tests/                     # 59 tests automatizados
credentials.json           # NO subir a git
token.json                 # NO subir a git
```

---

## Tests

```bash
python -m pytest tests/ -v
```
