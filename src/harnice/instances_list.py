import yaml
import json
import csv
from collections import defaultdict
import fileio

INSTANCES_LIST_COLUMNS = [
    'instance_name',
    'bom_line_number',
    'mpn',
    'item_type',
    'parent_instance',
    'parent_csys',
    'supplier',
    'library_rev',
    'length',
    'diameter',
    'translate_x',
    'translate_y',
    'rotate_csys'
]

def load_yaml_data():
    with open(fileio.path('harness yaml'), 'r') as file:
        return yaml.safe_load(file)

def read_instance_rows():
    with open(fileio.path('instances list'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def write_instance_rows(rows):
    with open(fileio.path('instances list'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def append_instance_row(data_dict):
    with open(fileio.path('instances list'), 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter='\t')
        writer.writerow({key: data_dict.get(key, '') for key in INSTANCES_LIST_COLUMNS})

def make_new_list():
    write_instance_rows([])

def add_connectors():
    yaml_data = load_yaml_data()
    for instance_name, connector in yaml_data.get('connectors', {}).items():
        for component in connector.get('additional_components', []):
            suffix = 'bs' if component.get('type', '').lower() == 'backshell' else component.get('type', '').lower()
            component_instance = f"{instance_name}.{suffix}"
            append_instance_row({
                'instance_name': component_instance,
                'mpn': component.get('mpn', ''),
                'item_type': component.get('type', ''),
                'parent_instance': instance_name,
                'parent_csys': 'PULL FROM CONNECTOR LIBRARY',
                'supplier': component.get('supplier', '')
            })

        append_instance_row({
            'instance_name': instance_name,
            'mpn': connector.get('mpn', ''),
            'item_type': 'Connector',
            'parent_csys': 'PULL FROM CONNECTOR LIBRARY',
            'supplier': connector.get('supplier', '')
        })

def add_cables():
    yaml_data = load_yaml_data()
    for cable_name, cable in yaml_data.get('cables', {}).items():
        append_instance_row({
            'instance_name': cable_name,
            'mpn': cable.get('mpn', ''),
            'item_type': 'Cable',
            'supplier': cable.get('supplier', '')
        })

def add_formboard_segments():
    with open(fileio.path('formboard graph definition'), 'r') as f:
        segments = yaml.safe_load(f)
    for seg_name, seg in segments.items():
        append_instance_row({
            'instance_name': seg_name,
            'item_type': 'Segment',
            'length': seg.get('length', ''),
            'diameter': seg.get('diameter', '')
        })

def add_cable_lengths():
    with open(fileio.path('connections to graph'), 'r') as json_file:
        graph_data = json.load(json_file)

    rows = read_instance_rows()
    for row in rows:
        if row.get('item_type', '').lower() == 'cable':
            row['length'] = graph_data.get(row['instance_name'], {}).get('wirelength', '')

    write_instance_rows(rows)

def convert_to_bom():
    rows = read_instance_rows()
    mpn_groups = defaultdict(lambda: {'qty': 0, 'item_type': '', 'supplier': '', 'total_length': 0.0})

    for row in rows:
        mpn = row.get('mpn', '').strip()
        if not mpn:
            continue
        group = mpn_groups[mpn]
        group['qty'] += 1
        group['item_type'] = row.get('item_type', '')
        group['supplier'] = row.get('supplier', '')
        if group['item_type'].lower() == 'cable':
            try:
                group['total_length'] += float(row.get('length', '') or 0)
            except ValueError:
                pass

    output = []
    for i, (mpn, group) in enumerate(mpn_groups.items(), 1):
        row = {
            'bom_line_number': i,
            'mpn': mpn,
            'item_type': group['item_type'],
            'qty': group['qty'],
            'supplier': group['supplier']
        }
        if group['item_type'].lower() == 'cable':
            row['total_length_exact'] = f"{group['total_length']:.2f}"
        output.append(row)

    fieldnames = ['bom_line_number', 'mpn', 'item_type', 'qty', 'supplier', 'total_length_exact']
    with open(fileio.path('harness bom'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(output)

    return fileio.path('harness bom')

def add_bom_line_numbers():
    with open(fileio.path('harness bom'), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        mpn_map = {row['mpn']: row['bom_line_number'] for row in reader if row.get('mpn')}

    rows = read_instance_rows()
    for row in rows:
        row['bom_line_number'] = mpn_map.get(row.get('mpn', ''), '')

    write_instance_rows(rows)
    return fileio.path('instances list')

def add_nodes():
    with open(fileio.path('formboard graph definition'), 'r') as f:
        graph = yaml.safe_load(f)

    node_set = set()
    for seg in graph.values():
        node_set.update([seg.get('segment_end_a'), seg.get('segment_end_b')])

    for node in sorted(filter(None, node_set)):
        append_instance_row({
            'instance_name': f'{node}.node',
            'item_type': 'Node',
            'parent_instance': node
        })
