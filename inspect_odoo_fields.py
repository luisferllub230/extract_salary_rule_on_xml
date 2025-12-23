#!/usr/bin/env python3
"""
Odoo Fields Inspector
Verifica qué campos están disponibles en el modelo hr.salary.rule
"""

import xmlrpc.client
import argparse
import sys


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


def get_model_fields(models, db, uid, password, model_name='hr.salary.rule'):
    """Get all available fields for a model."""
    try:
        # Obtener información de campos usando fields_get
        fields_info = models.execute_kw(
            db, uid, password,
            model_name, 'fields_get',
            [],
            {'attributes': ['string', 'type', 'required', 'readonly']}
        )
        return fields_info
    except Exception as e:
        print(f"Error getting fields: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description='Inspect available fields in Odoo hr.salary.rule model'
    )
    parser.add_argument('--url', required=True, help='Odoo server URL')
    parser.add_argument('--db', required=True, help='Database name')
    parser.add_argument('--user', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password or API key')
    parser.add_argument('--model', default='hr.salary.rule', help='Model to inspect')
    parser.add_argument('--export', action='store_true', help='Export field names for script')

    args = parser.parse_args()

    print(f"Connecting to Odoo at {args.url}...")
    try:
        uid, models = connect_odoo(args.url, args.db, args.user, args.password)
        print(f"Connected successfully (uid: {uid})\n")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Inspecting model: {args.model}\n")
    fields_info = get_model_fields(models, args.db, uid, args.password, args.model)

    if not fields_info:
        print("No fields found or error occurred.")
        sys.exit(1)

    # Categorizar campos
    basic_fields = []
    relation_fields = []
    computed_fields = []
    other_fields = []

    for field_name, field_data in sorted(fields_info.items()):
        field_type = field_data.get('type', 'unknown')
        
        if field_type in ['many2one', 'one2many', 'many2many']:
            relation_fields.append(field_name)
        elif field_data.get('readonly', False) and field_type not in ['char', 'text', 'float', 'integer']:
            computed_fields.append(field_name)
        elif field_name in ['id', 'create_uid', 'create_date', 'write_uid', 'write_date']:
            other_fields.append(field_name)
        else:
            basic_fields.append(field_name)

    # Mostrar resultados
    print("=" * 70)
    print("AVAILABLE FIELDS IN hr.salary.rule")
    print("=" * 70)
    print()

    if basic_fields:
        print("BASIC FIELDS (Recommended for extraction):")
        print("-" * 70)
        for field in basic_fields:
            field_data = fields_info[field]
            print(f"  • {field:<30} ({field_data['type']:<15}) - {field_data.get('string', '')}")
        print()

    if relation_fields:
        print("RELATION FIELDS:")
        print("-" * 70)
        for field in relation_fields:
            field_data = fields_info[field]
            print(f"  • {field:<30} ({field_data['type']:<15}) - {field_data.get('string', '')}")
        print()

    if computed_fields:
        print("COMPUTED/READONLY FIELDS:")
        print("-" * 70)
        for field in computed_fields:
            field_data = fields_info[field]
            print(f"  • {field:<30} ({field_data['type']:<15}) - {field_data.get('string', '')}")
        print()

    print(f"Total fields: {len(fields_info)}")
    print()

    # Exportar lista de campos si se solicita
    if args.export:
        print("=" * 70)
        print("PYTHON CODE FOR SCRIPT:")
        print("=" * 70)
        print()
        print("# Copy this to your extraction script:")
        print("fields = [")
        
        # Campos recomendados para extracción
        recommended = basic_fields + relation_fields
        for field in sorted(recommended):
            if field not in ['__last_update', 'display_name']:
                print(f"    '{field}',")
        
        print("]")
        print()
        
        print("# Alternative - All fields:")
        print("fields = [")
        for field in sorted(fields_info.keys()):
            if field not in ['__last_update', 'display_name']:
                print(f"    '{field}',  # {fields_info[field].get('string', '')}")
        print("]")


if __name__ == '__main__':
    main()
