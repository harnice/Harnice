import yaml
import json
import csv
import fileio
from collections import defaultdict

def load_yaml_data():
    with open(fileio.path('harness yaml'), 'r') as file:
        return yaml.safe_load(file)

def append_instance_row(row):
    with open(fileio.path('instances list'), 'a', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(row)

def make_new_list():
    with open(fileio.path('instances list'), 'w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow([
            'instance_name',
            'bom_line_number',
            'mpn',
            'item_type',
            'parent_instance',
            'supplier',
            'length',
            'diameter',
            'translate_formboard',
            'translate_bs'
        ])

def add_connectors():
    yaml_data_parsed = load_yaml_data()
    connectors = yaml_data_parsed.get('connectors', {})

    for instance_name, connector in connectors.items():
        mpn = connector.get('mpn', '')
        supplier = connector.get('supplier', '')
        component_instances = []

        for component in connector.get('additional_components', []):
            component_mpn = component.get('mpn', '')
            component_type = component.get('type', '')
            component_supplier = component.get('supplier', '')

            suffix = 'bs' if component_type.lower() == 'backshell' else component_type.lower()
            component_instance_name = f'{instance_name}.{suffix}'
            component_instances.append(component_instance_name)

            append_instance_row([
                component_instance_name,
                '',
                component_mpn,
                component_type,
                instance_name,
                component_supplier,
                '', '', '', ''
            ])

        append_instance_row([
            instance_name,
            '',
            mpn,
            'Connector',
            '',
            supplier,
            '', '', '', ''
        ])

def add_cables():
    yaml_data_parsed = load_yaml_data()
    cables = yaml_data_parsed.get('cables', {})

    for cable_name, cable in cables.items():
        mpn = cable.get('mpn', '')
        supplier = cable.get('supplier', '')

        append_instance_row([
            cable_name,
            '',
            mpn,
            'Cable',
            '',
            supplier,
            '', '', '', ''
        ])

def add_formboard_segments():
    with open(fileio.path('formboard graph definition'), 'r') as f:
        formboard_data = yaml.safe_load(f)

    for segment_name, segment in formboard_data.items():
        append_instance_row([
            segment_name,
            '',
            '',
            'Segment',
            '',
            '',
            segment.get('length', ''),
            segment.get('diameter', ''),
            '', ''
        ])

def add_cable_lengths():
    with open(fileio.path('connections to graph'), 'r') as json_file:
        graph_data = json.load(json_file)

    tsv_path = fileio.path('instances list')
    with open(tsv_path, newline='') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if 'length' not in fieldnames:
        fieldnames.append('length')

    for row in rows:
        if row.get('item_type') == 'Cable':
            instance = row.get('instance_name')
            row['length'] = graph_data.get(instance, {}).get('wirelength', '')
        else:
            row['length'] = row.get('length', '')

    with open(tsv_path, 'w', newline='') as tsv_file:
        writer = csv.DictWriter(tsv_file, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def convert_to_bom():
    mpn_groups = defaultdict(lambda: {
        'qty': 0,
        'item_type': '',
        'supplier': '',
        'total_length': 0.0
    })

    with open(fileio.path('instances list'), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            mpn = row.get('mpn', '').strip()
            if not mpn:
                continue

            item_type = row.get('item_type', '').strip()
            supplier = row.get('supplier', '').strip()
            length_str = row.get('length', '').strip()

            mpn_data = mpn_groups[mpn]
            mpn_data['qty'] += 1
            mpn_data['item_type'] = item_type
            mpn_data['supplier'] = supplier

            if item_type.lower() == 'cable' and length_str:
                try:
                    mpn_data['total_length'] += float(length_str)
                except ValueError:
                    pass

    bom_rows = []
    for i, (mpn, data) in enumerate(mpn_groups.items(), start=1):
        row = {
            'bom_line_number': i,
            'mpn': mpn,
            'item_type': data['item_type'],
            'qty': data['qty'],
            'supplier': data['supplier']
        }
        if data['item_type'].lower() == 'cable':
            row['total_length_exact'] = f"{data['total_length']:.2f}"
        bom_rows.append(row)

    fieldnames = ['bom_line_number', 'mpn', 'item_type', 'qty', 'supplier', 'total_length_exact']
    with open(fileio.path('harness bom'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(bom_rows)

    return fileio.path('harness bom')

def add_bom_line_numbers():
    mpn_to_bom_line = {}
    with open(fileio.path('harness bom'), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            mpn = row.get('mpn', '').strip()
            bom_line = row.get('bom_line_number', '').strip()
            if mpn and bom_line:
                mpn_to_bom_line[mpn] = bom_line

    with open(fileio.path('instances list'), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames or []
        if 'bom_line_number' not in fieldnames:
            fieldnames.append('bom_line_number')

    for row in rows:
        mpn = row.get('mpn', '').strip()
        row['bom_line_number'] = mpn_to_bom_line.get(mpn, '')

    with open(fileio.path('instances list'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

    return fileio.path('instances list')
