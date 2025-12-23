#!/usr/bin/env python3
"""
Odoo 18 Payroll Rules Extractor - IMPROVED VERSION
Extracts all payroll rules with complete fields and proper XML ID references.
"""

import xmlrpc.client
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import sys
import re


def connect_odoo(url, db, username, password):
    """Establish connection to Odoo via XML-RPC."""
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')

    try:
        uid = common.authenticate(db, username, password, {})
        if not uid:
            raise Exception("Authentication failed. Check credentials.")

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        return uid, models
    except Exception as e:
        raise Exception(f"Connection error: {e}")


def get_salary_rule_categories(models, db, uid, password):
    """Fetch all salary rule categories."""
    categories = models.execute_kw(
        db, uid, password,
        'hr.salary.rule.category', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'code', 'parent_id']}
    )
    return {cat['id']: cat for cat in categories}


def get_payroll_structures(models, db, uid, password):
    """Fetch all payroll structures."""
    try:
        structures = models.execute_kw(
            db, uid, password,
            'hr.payroll.structure', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'code', 'rule_ids']}
        )
        return {struct['id']: struct for struct in structures}
    except Exception:
        return {}


def get_salary_rules(models, db, uid, password, structure_id=None):
    """Fetch salary rules with ALL available fields."""
    # Lista de campos validados para Odoo 18 hr.salary.rule
    fields = [
        'id', 'name', 'code', 'sequence', 'category_id',
        'condition_select', 'condition_python', 'condition_range',
        'condition_range_min', 'condition_range_max',
        'amount_select', 'amount_fix', 'amount_percentage',
        'amount_python_compute', 'amount_percentage_base',
        'quantity', 'appears_on_payslip', 'active',
        'note', 'struct_id', 'company_id'
    ]

    domain = []
    if structure_id:
        domain = [('struct_id', '=', structure_id)]

    try:
        rules = models.execute_kw(
            db, uid, password,
            'hr.salary.rule', 'search_read',
            [domain],
            {'fields': fields, 'order': 'sequence, id'}
        )
        return rules
    except Exception as e:
        # Si algunos campos fallan, intentar con campos básicos
        print(f"Warning: Some fields not available, using basic fields. Error: {e}")
        basic_fields = [
            'id', 'name', 'code', 'sequence', 'category_id',
            'condition_select', 'condition_python',
            'amount_select', 'amount_python_compute',
            'appears_on_payslip', 'active', 'struct_id'
        ]
        rules = models.execute_kw(
            db, uid, password,
            'hr.salary.rule', 'search_read',
            [domain],
            {'fields': basic_fields, 'order': 'sequence, id'}
        )
        return rules


def get_external_id(models, db, uid, password, model, record_id):
    """Get external ID (XML ID) for a record if it exists."""
    try:
        ir_model_data = models.execute_kw(
            db, uid, password,
            'ir.model.data', 'search_read',
            [[('model', '=', model), ('res_id', '=', record_id)]],
            {'fields': ['module', 'name'], 'limit': 1}
        )
        if ir_model_data:
            return f"{ir_model_data[0]['module']}.{ir_model_data[0]['name']}"
        return None
    except:
        return None


def sanitize_xml_id(name, code=None, prefix=''):
    """Generate a valid XML ID from name/code."""
    base = code if code else name
    # Convertir a minúsculas y reemplazar caracteres especiales
    xml_id = base.lower()
    # Reemplazar espacios y caracteres especiales con guiones bajos
    xml_id = re.sub(r'[^a-z0-9_]', '_', xml_id)
    # Eliminar guiones bajos consecutivos
    xml_id = re.sub(r'_+', '_', xml_id)
    # Eliminar guiones bajos al inicio y final
    xml_id = xml_id.strip('_')
    
    if prefix:
        return f"{prefix}_{xml_id}"
    return xml_id


def escape_xml_content(text):
    """Properly escape text for XML content, handling CDATA when needed."""
    if not text:
        return ""
    
    text = str(text)
    
    # Si el texto contiene caracteres especiales de XML, usar CDATA
    if any(char in text for char in ['<', '>', '&']) and not text.strip().startswith('<![CDATA['):
        # Verificar si ya tiene CDATA
        if '<![CDATA[' not in text:
            return f"<![CDATA[{text}]]>"
    
    return text


def create_field_element(parent, field_name, value, **attrs):
    """Create a field element with proper formatting."""
    field = ET.SubElement(parent, 'field', {'name': field_name, **attrs})
    
    # Si el valor contiene XML especial, manejar apropiadamente
    if isinstance(value, str) and any(char in value for char in ['<', '>', '&']):
        # ElementTree maneja esto automáticamente, pero aseguramos el formato
        field.text = value
    else:
        field.text = str(value) if value is not None else ""
    
    return field


def create_xml_output(rules, categories, structures, models, db, uid, password, 
                     generate_xmlids=True, module_prefix='l10n_do_hr_payroll'):
    """Generate Odoo-compatible XML data file with proper XML IDs and all fields."""
    
    # Mapa de XML IDs para referencias
    category_xmlids = {}
    structure_xmlids = {}
    rule_xmlids = {}
    
    # Obtener XML IDs existentes si es posible
    if generate_xmlids:
        print("Fetching existing XML IDs...")
        for cat_id, cat in categories.items():
            ext_id = get_external_id(models, db, uid, password, 'hr.salary.rule.category', cat_id)
            if ext_id:
                category_xmlids[cat_id] = ext_id
            else:
                # Generar uno nuevo
                xml_id = sanitize_xml_id(cat['name'], cat['code'])
                category_xmlids[cat_id] = f"{module_prefix}.aginc_{xml_id.upper()}"
        
        for struct_id, struct in structures.items():
            ext_id = get_external_id(models, db, uid, password, 'hr.payroll.structure', struct_id)
            if ext_id:
                structure_xmlids[struct_id] = ext_id
            else:
                xml_id = sanitize_xml_id(struct['name'], struct.get('code'))
                structure_xmlids[struct_id] = f"{module_prefix}.aginc_structure_{xml_id}"
        
        for rule in rules:
            ext_id = get_external_id(models, db, uid, password, 'hr.salary.rule', rule['id'])
            if ext_id:
                rule_xmlids[rule['id']] = ext_id
            else:
                xml_id = sanitize_xml_id(rule['name'], rule['code'])
                rule_xmlids[rule['id']] = f"{module_prefix}.aginc_hr_salary_rule_{xml_id}"
    
    # Create root element
    root = ET.Element('odoo')
    
    # Add comment for salary rules section
    comment = ET.Comment(' Reglas salariales para la estructura de Nomina Regular (Quincenal y con retenciones en ambas quincenas) ')
    root.append(comment)
    
    # Add salary rules
    for rule in rules:
        # Determinar el XML ID para este registro
        if generate_xmlids and rule['id'] in rule_xmlids:
            record_xmlid = rule_xmlids[rule['id']].split('.')[-1]  # Solo la parte después del módulo
        else:
            record_xmlid = sanitize_xml_id(rule['name'], rule['code'], 'aginc_hr_salary_rule')
        
        record = ET.SubElement(root, 'record', {
            'id': record_xmlid,
            'model': 'hr.salary.rule'
        })
        
        # Campo: name
        create_field_element(record, 'name', rule['name'])
        
        # Campo: category_id (con ref)
        if rule.get('category_id'):
            cat_id = rule['category_id'][0]
            if cat_id in category_xmlids:
                ref_id = category_xmlids[cat_id]
            else:
                cat = categories.get(cat_id)
                if cat:
                    ref_id = f"hr_payroll.{sanitize_xml_id(cat['name'], cat['code']).upper()}"
                else:
                    ref_id = None
            
            if ref_id:
                ET.SubElement(record, 'field', {
                    'name': 'category_id',
                    'ref': ref_id
                })
        
        # Campo: struct_id (con ref)
        if rule.get('struct_id'):
            struct_id = rule['struct_id'][0]
            if struct_id in structure_xmlids:
                ref_id = structure_xmlids[struct_id]
            else:
                struct = structures.get(struct_id)
                if struct:
                    ref_id = sanitize_xml_id(struct['name'], struct.get('code'), module_prefix)
                else:
                    ref_id = None
            
            if ref_id:
                ET.SubElement(record, 'field', {
                    'name': 'struct_id',
                    'ref': ref_id
                })
        
        # Campo: code
        if rule.get('code'):
            create_field_element(record, 'code', rule['code'])
        
        # Campo: sequence
        create_field_element(record, 'sequence', rule.get('sequence', 0))
        
        # Campo: appears_on_payslip
        if 'appears_on_payslip' in rule:
            create_field_element(record, 'appears_on_payslip', 
                               str(rule['appears_on_payslip']))
        
        # Campo: condition_select
        condition_select = rule.get('condition_select', 'none')
        create_field_element(record, 'condition_select', condition_select)
        
        # Campo: condition_python (si aplica)
        if condition_select == 'python' and rule.get('condition_python'):
            field = ET.SubElement(record, 'field', {'name': 'condition_python'})
            field.text = escape_xml_content(rule['condition_python'])
        
        # Campos de condition_range
        if condition_select == 'range':
            if rule.get('condition_range'):
                create_field_element(record, 'condition_range', rule['condition_range'])
            if rule.get('condition_range_min') is not None:
                create_field_element(record, 'condition_range_min', 
                                   rule['condition_range_min'])
            if rule.get('condition_range_max') is not None:
                create_field_element(record, 'condition_range_max', 
                                   rule['condition_range_max'])
        
        # Campo: amount_select
        amount_select = rule.get('amount_select', 'fix')
        create_field_element(record, 'amount_select', amount_select)
        
        # Campo: amount_python_compute (si aplica)
        if amount_select == 'code' and rule.get('amount_python_compute'):
            field = ET.SubElement(record, 'field', {'name': 'amount_python_compute'})
            field.text = escape_xml_content(rule['amount_python_compute'])
        
        # Campo: amount_fix
        if amount_select == 'fix' and rule.get('amount_fix') is not None:
            create_field_element(record, 'amount_fix', rule['amount_fix'])
        
        # Campo: amount_percentage
        if amount_select == 'percentage':
            if rule.get('amount_percentage') is not None:
                create_field_element(record, 'amount_percentage', 
                                   rule['amount_percentage'])
            if rule.get('amount_percentage_base'):
                create_field_element(record, 'amount_percentage_base', 
                                   rule['amount_percentage_base'])
        
        # Campo: quantity
        if rule.get('quantity'):
            create_field_element(record, 'quantity', rule['quantity'])
        
        # Campo: active
        if 'active' in rule:
            create_field_element(record, 'active', str(rule['active']))
        
        # Campo: note
        if rule.get('note'):
            field = ET.SubElement(record, 'field', {'name': 'note'})
            field.text = escape_xml_content(rule['note'])
    
    return root


def prettify_xml(elem):
    """Return a pretty-printed XML string with proper formatting."""
    # Convertir a string
    rough_string = ET.tostring(elem, encoding='unicode', method='xml')
    
    # Parsear con minidom para pretty print
    try:
        reparsed = minidom.parseString(rough_string)
        pretty = reparsed.toprettyxml(indent="    ", encoding=None)
        
        # Limpiar líneas vacías extras
        lines = [line for line in pretty.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    except Exception as e:
        print(f"Warning: Could not prettify XML: {e}")
        return rough_string


def sanitize_filename(name):
    """Convert structure name to a safe filename."""
    safe_name = name.lower().replace(' ', '_').replace('-', '_')
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in safe_name)
    while '__' in safe_name:
        safe_name = safe_name.replace('__', '_')
    return safe_name.strip('_')


def list_structures(models, db, uid, password):
    """List all available payroll structures."""
    structures = get_payroll_structures(models, db, uid, password)
    if not structures:
        print("No payroll structures found.")
        return

    print("\nAvailable Payroll Structures:")
    print("-" * 70)
    print(f"{'ID':<6} {'Code':<25} {'Name'}")
    print("-" * 70)
    for struct_id, struct in sorted(structures.items()):
        code = struct.get('code', '') or ''
        name = struct.get('name', '')
        print(f"{struct_id:<6} {code:<25} {name}")
    print("-" * 70)
    print(f"Total: {len(structures)} structures")


def main():
    parser = argparse.ArgumentParser(
        description='Extract payroll rules from Odoo 18 to XML with complete fields and proper references'
    )
    parser.add_argument('--url', required=True, 
                       help='Odoo server URL (e.g., http://localhost:8069)')
    parser.add_argument('--db', required=True, help='Database name')
    parser.add_argument('--user', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password or API key')
    parser.add_argument('--output', default=None, 
                       help='Output XML file (auto-generated from structure name if not specified)')
    parser.add_argument('--list-structures', action='store_true', 
                       help='List all available payroll structures and exit')
    parser.add_argument('--structure-id', type=int, 
                       help='Extract rules only for the specified structure ID')
    parser.add_argument('--module-prefix', default='l10n_do_hr_payroll',
                       help='Module prefix for XML IDs (default: l10n_do_hr_payroll)')
    parser.add_argument('--no-xmlid-lookup', action='store_true',
                       help='Skip looking up existing XML IDs (faster but may generate inconsistent IDs)')

    args = parser.parse_args()

    print(f"Connecting to Odoo at {args.url}...")
    try:
        uid, models = connect_odoo(args.url, args.db, args.user, args.password)
        print(f"Connected successfully (uid: {uid})")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # List structures mode
    if args.list_structures:
        list_structures(models, args.db, uid, args.password)
        sys.exit(0)

    print("Fetching salary rule categories...")
    categories = get_salary_rule_categories(models, args.db, uid, args.password)
    print(f"Found {len(categories)} categories")

    print("Fetching payroll structures...")
    structures = get_payroll_structures(models, args.db, uid, args.password)
    print(f"Found {len(structures)} structures")

    # Validate structure_id if provided
    selected_structure = None
    if args.structure_id:
        if args.structure_id not in structures:
            print(f"Error: Structure ID {args.structure_id} not found.", file=sys.stderr)
            print("Use --list-structures to see available structures.", file=sys.stderr)
            sys.exit(1)
        selected_structure = structures[args.structure_id]
        print(f"Filtering by structure: {selected_structure['name']} (ID: {args.structure_id})")

    print("Fetching salary rules...")
    rules = get_salary_rules(models, args.db, uid, args.password, 
                            structure_id=args.structure_id)
    print(f"Found {len(rules)} rules")

    if not rules:
        print("No rules found for the specified criteria.")
        sys.exit(0)

    print("Generating XML with complete fields and proper references...")
    xml_root = create_xml_output(
        rules, categories, structures, models, args.db, uid, args.password,
        generate_xmlids=not args.no_xmlid_lookup,
        module_prefix=args.module_prefix
    )
    
    xml_string = prettify_xml(xml_root)
    
    # Asegurar declaración XML correcta
    if not xml_string.startswith('<?xml'):
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string

    # Determine output filename
    if args.output:
        output_file = args.output
    elif selected_structure:
        structure_name = sanitize_filename(selected_structure['name'])
        output_file = f"payroll_rules_{structure_name}.xml"
    else:
        output_file = 'payroll_rules_complete.xml'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_string)

    print(f"\n✓ XML exported successfully to: {output_file}")
    print(f"✓ Total rules exported: {len(rules)}")
    print(f"✓ All fields included with proper XML ID references")


if __name__ == '__main__':
    main()
