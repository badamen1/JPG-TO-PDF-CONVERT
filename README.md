# 📁 Gestión Documental de Instalaciones de Internet

Conjunto de herramientas en Python para automatizar la conversión de imágenes a PDF y la subida de documentación de clientes a Google Drive.

---

## 🗂️ Herramientas disponibles

| Herramienta | Descripción |
|---|---|
| `convert_images_to_pdf.py` | Convierte imágenes (PNG/JPG/JPEG) a PDF desde la terminal |
| `subir_semana.py` | Sube una semana completa de clientes a Google Drive |
| `gui.py` | Interfaz gráfica para convertir imágenes a PDF |

---

## ⚙️ Instalación

1. Crear y activar el entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

---

## 🚀 Subir semana completa a Google Drive

Comando principal del proyecto. Procesa todas las carpetas de clientes de una semana y las sube automáticamente a una carpeta ya existente en Drive.

```bash
python subir_semana.py --ruta_local "C:/Proyecto/Yoro/Semana 8" --drive_folder_id "ID_DE_CARPETA"
```

### ¿Qué hace por cada cliente?

1. **Recoge PDFs existentes** en la carpeta del cliente (se suben tal cual)
2. **Une imágenes de cédula** (archivos con `CC1` o `CC2` en el nombre) en un único `CEDULA_<cliente>.pdf`
3. **Convierte el resto de imágenes** a PDFs individuales
4. **Verifica en Drive** si la carpeta del cliente ya existe → si existe la omite, si no existe la crea y sube todo
5. **Muestra un resumen** con el estado de cada cliente

### Estructura esperada en tu computador

```
Semana 8/
├── JUAN PEREZ/
│   ├── CC1.jpg          ← cédula frontal
│   ├── CC2.jpg          ← cédula trasera
│   └── instalacion.jpg
├── MARIA LOPEZ/
│   ├── CC1.png
│   ├── CC2.png
│   ├── contrato.pdf     ← PDF existente, se sube directo
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

### Opciones

| Opción | Descripción |
|---|---|
| `--ruta_local` | Ruta local a la carpeta de la semana |
| `--drive_folder_id` | ID de la carpeta destino en Drive (ya debe existir) |
| `--credentials` | Ruta al `credentials.json` (default: `credentials.json`) |

### Resumen de consola

```
============================================================
  📊 RESUMEN FINAL
============================================================
  ⏱  Tiempo total: 45.2 segundos
  👥 Clientes encontrados: 5
  ✅ Subidos: 4
  ⏭  Omitidos (ya en Drive): 1
  📄 Total archivos procesados: 18

  Cliente                          Archivos      Estado
  ────────────────────────────── ────────── ──────────
  JUAN PEREZ                            3          ✅
  MARIA LOPEZ                           4          ✅
  CARLOS GARCIA (ya subido)             3          ⏭
============================================================
```

---

## 🔐 Configurar Google Drive API (solo una vez)

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto nuevo o seleccionar uno existente
3. **APIs y Servicios → Biblioteca** → buscar **Google Drive API** → Habilitar
4. **APIs y Servicios → Credenciales → Crear credenciales → ID de cliente OAuth**
5. Configurar pantalla de consentimiento: tipo **Externo**, agregar scope `https://www.googleapis.com/auth/drive`, agregarte como usuario de prueba
6. Tipo de aplicación: **Aplicación de escritorio**
7. Descargar el JSON → renombrarlo a `credentials.json` → colocarlo en la raíz del proyecto

> En la primera ejecución se abrirá el navegador para autorizar. El token se guarda en `token.json` automáticamente para usos futuros.

---

## 🖼️ Convertir imágenes a PDF (CLI)

Convierte imágenes individuales o carpetas enteras a PDF.

```bash
# Un PDF por imagen
python convert_images_to_pdf.py imagen1.jpg imagen2.png

# Todas las imágenes de una carpeta
python convert_images_to_pdf.py C:\ruta\carpeta\

# Combinar varias imágenes en un solo PDF
python convert_images_to_pdf.py imagen1.jpg imagen2.jpg -m -n documento_final

# Guardar PDFs en una carpeta específica
python convert_images_to_pdf.py *.jpg -o C:\salida\
```

### Opciones

| Opción | Descripción |
|---|---|
| `-o`, `--out` | Directorio de salida |
| `-m`, `--merge` | Combinar todas las imágenes en un solo PDF |
| `-n`, `--name` | Nombre del PDF combinado (solo con `--merge`) |
| `-d`, `--delete-original` | Eliminar imágenes originales tras conversión exitosa |

---

## 🖥️ Interfaz gráfica

```bash
python gui.py
```

---

## 📦 Archivos del proyecto

```
JPG TO PDF CONVERT/
├── subir_semana.py          ← subida a Drive
├── drive_uploader.py        ← módulo Drive API
├── convert_images_to_pdf.py ← conversión de imágenes
├── gui.py                   ← interfaz gráfica
├── requirements.txt
├── credentials.json         ← NO subir a git
└── token.json               ← NO subir a git
```
