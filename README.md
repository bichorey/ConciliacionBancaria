```markdown
# Conciliación Bancaria

Aplicación web desarrollada en Streamlit para realizar conciliación bancaria automatizada entre registros del Mayor y extractos bancarios.

## Características

- **Conciliación automática**: Algoritmo MVP que realiza matching one-to-one y many-to-one entre registros
- **Tolerancia de fechas**: Configurable hasta 30 días de diferencia
- **Agrupación inteligente**: Permite agrupar múltiples movimientos del Mayor contra uno del Banco
- **Resultado previo**: Soporta cargar archivos de conciliación anteriores para procesar solo pendientes
- **Export Excel**: Genera archivo con formato, colores por estado, filtros y columnas autoajustadas
- **Interfaz intuitiva**: Sidebar con parámetros, carga de archivos drag & drop, visualización de resultados

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/TU_USUARIO/ConciliacionBancaria.git
cd ConciliacionBancaria
```

2. Crear entorno virtual:
```bash
python -m venv .venv
```

3. Activar entorno virtual:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecutar la aplicación:
```bash
streamlit run app.py
```

2. Abrir navegador en `http://localhost:8501`

3. **Configurar parámetros** (sidebar):
   - Tolerancia de días: diferencia máxima permitida entre fechas
   - Máx. items por grupo: cantidad de registros del Mayor que pueden agruparse contra uno del Banco
   - Dirección agrupación: MAYOR→BANCO o BANCO→MAYOR

4. **Cargar archivos**:
   - **Mayor**: archivo Excel/CSV con columnas estándar del libro mayor
   - **Banco**: archivo Excel/CSV con extracto bancario
   - **Resultado previo**: opcionalmente, cargar un Excel generado previamente para procesar solo pendientes

5. **Procesar**: hacer clic en "Conciliar"

6. **Descargar**: botón para exportar Excel con detalle y resumen

## Formato de archivos

### Mayor (columnas esperadas)
- Código, Cuenta, Fecha, Tipo, Nro. Comp, Subcuenta
- Detalle, CUIT, Razon Social, Débito, Crédito, Saldo, Importe

### Banco (columnas esperadas)
- NUM, FECHA, COMBTE, DESCRIPCION
- DEBITO, CREDITO, SALDO, IMPORTE

### Fechas e importes
- **Fechas**: formato dd/mm/yyyy
- **Importes**: separador de miles (.) y decimales (,) - ejemplo: 1.234,56

## Estados de conciliación

- **Conciliado exacto**: mismo importe y fecha
- **Conciliado por tolerancia**: mismo importe, fecha dentro de tolerancia
- **Conciliado por agrupación**: suma de varios registros Mayor = un registro Banco
- **Solo en Mayor**: registro sin match en Banco
- **Solo en Banco**: registro sin match en Mayor

## Archivos del proyecto

- `app.py`: interfaz Streamlit y lógica principal
- `reconciliacion.py`: algoritmos de conciliación y procesamiento
- `requirements.txt`: dependencias Python

## Notas importantes

- No subir archivos con datos sensibles al repositorio
- Los archivos Excel de ejemplo están incluidos solo para testing
- La aplicación maneja automáticamente duplicados de columnas y variaciones en nombres
- Soporta CSV con detección automática de separadores

## Desarrollo

Para contribuir o modificar:

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m "descripción"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## Licencia

Proyecto de uso interno. No redistribuir sin autorización.
```
