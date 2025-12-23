# Odoo Payroll Rules Extractor

Herramienta para extraer reglas de nómina desde Odoo 18 y exportarlas a formato XML compatible con módulos Odoo.

## Requisitos

- Python 3.6+
- Acceso a un servidor Odoo 18 con el módulo de nómina instalado (`hr_payroll`)
- Credenciales de usuario con permisos de lectura en los modelos de nómina

## Scripts Disponibles

### 1. `odoo_payroll_extractor_improved.py`

Script principal para extraer reglas salariales y exportarlas a XML.

#### Uso Básico

```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_base_datos \
    --user admin \
    --password mi_password
```

#### Opciones Disponibles

| Opción | Descripción |
|--------|-------------|
| `--url` | URL del servidor Odoo (requerido) |
| `--db` | Nombre de la base de datos (requerido) |
| `--user` | Nombre de usuario (requerido) |
| `--password` | Contraseña o API key (requerido) |
| `--output` | Archivo de salida XML (opcional, se genera automáticamente) |
| `--list-structures` | Lista todas las estructuras de nómina disponibles |
| `--structure-id` | Extrae solo las reglas de una estructura específica |
| `--module-prefix` | Prefijo para XML IDs (default: `l10n_do_hr_payroll`) |
| `--no-xmlid-lookup` | Omite la búsqueda de XML IDs existentes (más rápido) |

#### Ejemplos

**Listar estructuras de nómina disponibles:**
```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --list-structures
```

**Extraer reglas de una estructura específica:**
```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --structure-id 5 \
    --output reglas_estructura_5.xml
```

**Extraer todas las reglas con prefijo personalizado:**
```bash
python odoo_payroll_extractor_improved.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --module-prefix mi_modulo_nomina \
    --output todas_las_reglas.xml
```

### 2. `inspect_odoo_fields.py`

Script auxiliar para inspeccionar los campos disponibles en el modelo `hr.salary.rule`.

#### Uso

```bash
python inspect_odoo_fields.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret
```

#### Opciones

| Opción | Descripción |
|--------|-------------|
| `--url` | URL del servidor Odoo (requerido) |
| `--db` | Nombre de la base de datos (requerido) |
| `--user` | Nombre de usuario (requerido) |
| `--password` | Contraseña o API key (requerido) |
| `--model` | Modelo a inspeccionar (default: `hr.salary.rule`) |
| `--export` | Exporta los nombres de campos en formato Python |

#### Ejemplo con exportación de campos

```bash
python inspect_odoo_fields.py \
    --url http://localhost:8069 \
    --db mi_db \
    --user admin \
    --password secret \
    --export
```

## Formato de Salida XML

El script genera archivos XML compatibles con Odoo que incluyen:

- Referencias XML ID correctas para categorías y estructuras
- Todos los campos relevantes de las reglas salariales:
  - `name`, `code`, `sequence`
  - `category_id`, `struct_id`
  - `condition_select`, `condition_python`
  - `amount_select`, `amount_python_compute`, `amount_fix`, `amount_percentage`
  - `appears_on_payslip`, `active`, `note`

### Ejemplo de salida

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <!-- Reglas salariales -->
    <record id="aginc_hr_salary_rule_salario_base" model="hr.salary.rule">
        <field name="name">Salario Base</field>
        <field name="category_id" ref="hr_payroll.BASIC"/>
        <field name="struct_id" ref="l10n_do_hr_payroll.estructura_nomina"/>
        <field name="code">BASIC</field>
        <field name="sequence">1</field>
        <field name="amount_select">code</field>
        <field name="amount_python_compute">result = contract.wage</field>
    </record>
</odoo>
```

## Notas

- El script utiliza XML-RPC para comunicarse con Odoo
- Se recomienda usar API keys en lugar de contraseñas para mayor seguridad
- Los XML IDs generados siguen el formato `{module_prefix}.aginc_hr_salary_rule_{code}`
