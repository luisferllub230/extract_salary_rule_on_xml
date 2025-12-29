# Odoo Payroll Rules Extractor

Herramienta para extraer reglas de nomina desde Odoo 18 y exportarlas a formato XML compatible con modulos Odoo.

## Requisitos

- Python 3.6+
- Acceso a un servidor Odoo 18 con el modulo de nomina instalado (`hr_payroll`)
- Credenciales de usuario con permisos de lectura en los modelos de nomina

## Scripts Disponibles

### 1. `odoo_payroll_extractor_improved.py`

Script principal para extraer reglas salariales y exportarlas a XML.

#### Uso Basico

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_base_datos \
    --user admin \
    --password mi_password
```

#### Opciones Disponibles

| Opcion | Descripcion |
|--------|-------------|
| `--url` | URL del servidor Odoo (requerido) |
| `--db` | Nombre de la base de datos (requerido) |
| `--user` | Nombre de usuario (requerido) |
| `--password` | Contrasena o API key (requerido) |
| `--output` | Archivo de salida XML (opcional, se genera automaticamente) |
| `--list-structures` | Lista todas las estructuras de nomina disponibles |
| `--structure-id` | Extrae solo las reglas de una estructura especifica |
| `--module-prefix` | Prefijo para XML IDs (default: `l10n_do_hr_payroll`) |
| `--no-xmlid-lookup` | Omite la busqueda de XML IDs existentes (mas rapido) |
| `--include-without-xmlid` | Incluye reglas sin xmlid (genera xmlid automatico). Por defecto se omiten |
| `--log-file` | Ruta del archivo de log (se genera automaticamente si no se especifica) |

## Manejo de Reglas sin XML ID

Por defecto, el script **omite las reglas que no tienen un XML ID** registrado en Odoo (`ir.model.data`). Esto previene la creacion de duplicados al importar el XML en otro sistema.

### Comportamiento por defecto (omitir reglas sin xmlid)

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret
```

Las reglas sin xmlid:
- No se incluyen en el archivo XML generado
- Se registran en el archivo de log con nivel WARNING
- Se muestran en el resumen final de la ejecucion

### Incluir todas las reglas (opcional)

Si deseas incluir las reglas sin xmlid (generando un xmlid automatico), usa la opcion `--include-without-xmlid`:

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --include-without-xmlid
```

**Advertencia:** Usar esta opcion puede causar duplicados si importas el XML en un sistema donde esas reglas ya existen con otro xmlid.

## Sistema de Logging

El script genera automaticamente un archivo de log con el formato `payroll_extractor_YYYYMMDD_HHMMSS.log` que contiene:

- Informacion de reglas omitidas (sin xmlid)
- Informacion de reglas incluidas con xmlid generado (cuando se usa `--include-without-xmlid`)
- Resumen de la extraccion

### Especificar archivo de log personalizado

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --log-file mi_log_personalizado.log
```

## Ejemplos de Uso

### Listar estructuras de nomina disponibles

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --list-structures
```

### Extraer reglas de una estructura especifica

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --structure-id 5 \
    --output reglas_estructura_5.xml
```

### Extraer todas las reglas con prefijo personalizado

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --module-prefix mi_modulo_nomina \
    --output todas_las_reglas.xml
```

### Extraer incluyendo reglas sin xmlid

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --include-without-xmlid \
    --log-file extraccion_completa.log
```

## Ejemplo de Salida del Script

```
Connecting to Odoo at http://localhost:8069...
Connected successfully (uid: 2)
Fetching salary rule categories...
Found 15 categories
Fetching payroll structures...
Found 3 structures
Fetching salary rules...
Found 50 rules
Fetching rule parameters...
Found 10 rule parameters
Fetching parameter values...
Found 25 parameter values
Fetching salary rule inputs...
Found 5 inputs
Fetching existing XML IDs...
Generating XML with complete fields and proper references...

======================================================================
RESULTADO DE LA EXTRACCION
======================================================================
XML exportado a: payroll_rules_complete.xml
Total reglas encontradas: 50
Reglas exportadas: 47
Reglas omitidas (sin xmlid): 3
Parametros de reglas exportados: 10
Valores de parametros exportados: 25
Inputs exportados: 5

======================================================================
REGLAS OMITIDAS (SIN XMLID)
======================================================================
ID       Codigo               Nombre
----------------------------------------------------------------------
123      TEST_RULE            Regla de prueba
456      CUSTOM_1             Regla personalizada 1
789      TEMP_CALC            Calculo temporal
----------------------------------------------------------------------
ADVERTENCIA: 3 regla(s) fueron omitidas por no tener xmlid.
Estas reglas no fueron incluidas en el XML para evitar duplicados.

Log guardado en: payroll_extractor_20251229_143022.log
======================================================================
```

## Formato de Salida XML

El script genera archivos XML compatibles con Odoo que incluyen:

### Reglas Salariales (`hr.salary.rule`)
- Referencias XML ID correctas para categorias y estructuras
- Todos los campos relevantes:
  - `name`, `code`, `sequence`
  - `category_id`, `struct_id`
  - `condition_select`, `condition_python`, `condition_range`, `condition_range_min`, `condition_range_max`
  - `amount_select`, `amount_python_compute`, `amount_fix`, `amount_percentage`, `amount_percentage_base`
  - `quantity`, `appears_on_payslip`, `active`, `note`

### Parametros de Reglas (`hr.rule.parameter`)
- Parametros configurables de nomina
- Valores historicos (`hr.rule.parameter.value`) con sus fechas

### Tipos de Input (`hr.payslip.input.type`)
- Tipos de inputs para nomina
- Referencias a estructuras asociadas

### Ejemplo de salida XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <!-- Reglas salariales para la estructura de Nomina Regular -->
    <record id="l10n_do_hr_payroll.aginc_hr_salary_rule_salario_base" model="hr.salary.rule">
        <field name="name">Salario Base</field>
        <field name="category_id" ref="l10n_do_hr_payroll.aginc_BASIC"/>
        <field name="struct_id" ref="l10n_do_hr_payroll.aginc_structure_nomina_regular"/>
        <field name="code">BASIC</field>
        <field name="sequence">1</field>
        <field name="appears_on_payslip">True</field>
        <field name="condition_select">none</field>
        <field name="amount_select">code</field>
        <field name="amount_python_compute">result = contract.wage</field>
        <field name="active">True</field>
    </record>

    <!-- Parametros de Reglas Salariales -->
    <!-- TOPE_TSS -->
    <record id="l10n_do_hr_payroll.aginc_rule_parameter_tope_tss" model="hr.rule.parameter">
        <field name="name">Tope TSS</field>
        <field name="code">TOPE_TSS</field>
    </record>
    <record id="l10n_do_hr_payroll.aginc_rule_parameter_value_tope_tss_2024_01_01" model="hr.rule.parameter.value">
        <field name="rule_parameter_id" ref="l10n_do_hr_payroll.aginc_rule_parameter_tope_tss"/>
        <field name="date_from">2024-01-01</field>
        <field name="parameter_value">235000.00</field>
    </record>

    <!-- Tipos de Inputs para Nomina -->
    <record id="l10n_do_hr_payroll.aginc_payslip_input_type_horas_extra" model="hr.payslip.input.type">
        <field name="name">Horas Extra</field>
        <field name="code">HE</field>
    </record>
</odoo>
```

## Script Auxiliar: `inspect_odoo_fields.py`

Script para inspeccionar los campos disponibles en modelos de Odoo.

### Uso

```bash
python inspect_odoo_fields.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret
```

### Opciones

| Opcion | Descripcion |
|--------|-------------|
| `--url` | URL del servidor Odoo (requerido) |
| `--db` | Nombre de la base de datos (requerido) |
| `--user` | Nombre de usuario (requerido) |
| `--password` | Contrasena o API key (requerido) |
| `--model` | Modelo a inspeccionar (default: `hr.salary.rule`) |
| `--export` | Exporta los nombres de campos en formato Python |

### Ejemplo con exportacion de campos

```bash
python inspect_odoo_fields.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --model hr.rule.parameter \
    --export
```

## Notas Importantes

- El script utiliza XML-RPC para comunicarse con Odoo
- Se recomienda usar API keys en lugar de contrasenas para mayor seguridad
- Los XML IDs existentes se preservan tal como estan en Odoo
- Los XML IDs generados automaticamente siguen el formato `aginc_hr_salary_rule_{code}`
- Las reglas sin xmlid se omiten por defecto para evitar duplicados
- Siempre revisa el log generado para verificar que reglas fueron omitidas

## Archivos Generados

| Archivo | Descripcion |
|---------|-------------|
| `payroll_rules_*.xml` | Archivo XML con las reglas extraidas |
| `payroll_extractor_*.log` | Archivo de log con detalles de la extraccion |

## Troubleshooting

### Error de conexion
Verifica que la URL, base de datos, usuario y contrasena sean correctos.

### Reglas no encontradas
Usa `--list-structures` para verificar las estructuras disponibles y `--structure-id` para filtrar.

### Muchas reglas omitidas
Si muchas reglas no tienen xmlid, pueden ser reglas creadas manualmente. Usa `--include-without-xmlid` para incluirlas.
