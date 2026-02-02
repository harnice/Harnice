"""
D38999 MIL-DTL-38999 Series III and IV Part Number Builder
Constructs part numbers and returns specifications per MIL-DTL-38999
"""
import math
import os
import itertools
import json
from pathlib import Path

# Configuration constants
REVISION = 1
RELEASE_STATUS = None  # None, 'Draft', 'Review', 'Released', 'Obsolete'

class D38999PartNumber:
    # Series definitions
    SERIES_III = {
        '26': 'Plug with accessory threads',
        '24': 'Jam-nut mount receptacle',
        '20': 'Wall mount receptacle',
        '21': 'Box mount receptacle (hermetic)',
        '25': 'Solder mount receptacle (hermetic)',
        '23': 'Jam-nut mount receptacle (hermetic)',
        '27': 'Weld mount receptacle (hermetic)'
    }
    
    SERIES_IV = {
        '46': 'Plug without EMI ground spring',
        '47': 'Plug with EMI ground spring',
        '40': 'Wall mount receptacle',
        '42': 'Box mount receptacle',
        '44': 'Jam-nut mount receptacle',
        '49': 'In-line receptacle',
        '41': 'Box mount receptacle (hermetic)',
        '43': 'Jam-nut mount receptacle (hermetic)',
        '45': 'Solder mount receptacle (hermetic)',
        '48': 'Weld mount receptacle (hermetic)'
    }
    
    # Environmental classes (Series III and IV)
    ENV_CLASSES = {
        'F': {'name': 'Electroless Nickel', 'material': 'Aluminum', 
              'temp_range': '-65°C to +200°C', 'salt_spray': '48 hour', 'conductive': True},
        'G': {'name': 'Space-Grade Electroless Nickel', 'material': 'Aluminum', 
              'temp_range': '-65°C to +200°C', 'salt_spray': '48 hour', 'conductive': True, 'space_grade': True},
        'W': {'name': 'Cadmium Olive Drab over Electroless Nickel', 'material': 'Aluminum', 
              'temp_range': '-65°C to +175°C', 'salt_spray': '500 hour', 'conductive': True},
        'T': {'name': 'Nickel-PTFE', 'material': 'Aluminum', 
              'temp_range': '-65°C to +175°C', 'conductive': True},
        'J': {'name': 'Cadmium Olive Drab (Composite)', 'material': 'Composite', 
              'temp_range': '-65°C to +175°C', 'salt_spray': '500 hour', 'conductive': True},
        'M': {'name': 'Electroless Nickel (Composite)', 'material': 'Composite', 
              'temp_range': '-65°C to +200°C', 'salt_spray': '500 hour', 'conductive': True},
        'K': {'name': 'Passivate (Stainless)', 'material': 'Stainless Steel', 
              'conductive': True},
        'S': {'name': 'Electrodeposited Nickel (Stainless)', 'material': 'Stainless Steel', 
              'conductive': True},
        'V': {'name': 'Tin-Zinc over Electroless Nickel', 'material': 'Aluminum', 
              'conductive': True},
        'Z': {'name': 'Zinc Nickel Black', 'material': 'Aluminum', 
              'conductive': True},
        'AA': {'name': 'Tri-Nickel Alloy', 'material': 'Aluminum', 
               'conductive': True}
    }
    
    # Hermetic classes
    HERMETIC_CLASSES = {
        'Y': {'name': 'Passivate (Hermetic)', 'material': 'Stainless Steel', 
              'conductive': True},
        'N': {'name': 'Electrodeposited Nickel (Hermetic)', 'material': 'Stainless Steel', 
              'salt_spray': '500 hour', 'conductive': True},
        'H': {'name': 'Passivate Space-Grade (Hermetic)', 'material': 'Stainless Steel', 
              'conductive': True, 'space_grade': True}
    }
    
    # Shell sizes
    SHELL_SIZES = {
        'A': {'size': 9, 'thread_size': 'M12'},
        'B': {'size': 11, 'thread_size': 'M15'},
        'C': {'size': 13, 'thread_size': 'M18'},
        'D': {'size': 15, 'thread_size': 'M22'},
        'E': {'size': 17, 'thread_size': 'M25'},
        'F': {'size': 19, 'thread_size': 'M28'},
        'G': {'size': 21, 'thread_size': 'M31'},
        'H': {'size': 23, 'thread_size': 'M34'},
        'J': {'size': 25, 'thread_size': 'M37'}
    }
    
    # Contact types
    CONTACT_TYPES = {
        'P': {'type': 'Pin', 'cycles': 500},
        'S': {'type': 'Socket', 'cycles': 500},
        'H': {'type': 'Pin', 'cycles': 1500},
        'J': {'type': 'Socket', 'cycles': 1500},
        'A': {'type': 'Pin insert, less standard contacts'},
        'B': {'type': 'Socket insert, less standard contacts'}
    }
    
    # Contact sizes and specifications
    CONTACT_SPECS = {
        '22D': {'wire_awg': '#22-#28', 'env_current': 5, 'hermetic_current': 3},
        '20': {'wire_awg': '#20-#24', 'env_current': 7.5, 'hermetic_current': 5},
        '16': {'wire_awg': '#16-#20', 'env_current': 13, 'hermetic_current': 10},
        '12': {'wire_awg': '#12-#14', 'env_current': 23, 'hermetic_current': 17},
        '8': {'type': 'Coax/Twinax', 'env_current': 1, 'hermetic_current': 1},
        '23': {'type': 'High-Density', 'wire_awg': '#22-#26', 'env_current': 5, 'hermetic_current': 5}
    }
    
    # Polarization options
    POLARIZATIONS = {
        'N': 'Normal (Master key)',
        'A': 'Alternate A',
        'B': 'Alternate B',
        'C': 'Alternate C',
        'D': 'Alternate D',
        'E': 'Alternate E',
        'K': 'Alternate K (Series IV)',
        'L': 'Alternate L (Series IV)',
        'M': 'Alternate M (Series IV)',
        'R': 'Alternate R (Series IV)'
    }
    
    # Insert arrangements with contact positions and counts
    INSERT_ARRANGEMENTS = {
        # Size 22D contacts
        'A35': {'contacts': 6, 'size': '22D', 'service_rating': 'M',
                'positions': [{'label': 'A', 'angle': 0, 'radius': 0},
                             {'label': 'B', 'angle': 60, 'radius': 2.5},
                             {'label': 'C', 'angle': 120, 'radius': 2.5},
                             {'label': 'D', 'angle': 180, 'radius': 2.5},
                             {'label': 'E', 'angle': 240, 'radius': 2.5},
                             {'label': 'F', 'angle': 300, 'radius': 2.5}]},
        'B35': {'contacts': 13, 'size': '22D', 'service_rating': 'M',
                'positions': [{'label': 'A', 'angle': 0, 'radius': 0}] +
                            [{'label': chr(66+i), 'angle': i*60, 'radius': 2.5} for i in range(6)] +
                            [{'label': chr(72+i), 'angle': 30+i*60, 'radius': 4.5} for i in range(6)]},
        'C35': {'contacts': 22, 'size': '22D', 'service_rating': 'M'},
        'D35': {'contacts': 37, 'size': '22D', 'service_rating': 'M'},
        'E35': {'contacts': 55, 'size': '22D', 'service_rating': 'M'},
        'F35': {'contacts': 66, 'size': '22D', 'service_rating': 'M'},
        'F45': {'contacts': 67, 'size': '22D', 'service_rating': 'M'},
        'G35': {'contacts': 79, 'size': '22D', 'service_rating': 'M'},
        'H35': {'contacts': 100, 'size': '22D', 'service_rating': 'M'},
        'J35': {'contacts': 128, 'size': '22D', 'service_rating': 'M'},
        
        # Size 20 contacts
        'A98': {'contacts': 3, 'size': '20', 'service_rating': 'I'},
        'B4': {'contacts': 4, 'size': '20', 'service_rating': 'I'},
        'B5': {'contacts': 5, 'size': '20', 'service_rating': 'I'},
        'B98': {'contacts': 6, 'size': '20', 'service_rating': 'I'},
        'B99': {'contacts': 7, 'size': '20', 'service_rating': 'I'},
        'C8': {'contacts': 8, 'size': '20', 'service_rating': 'I'},
        'C98': {'contacts': 10, 'size': '20', 'service_rating': 'I'},
        'D18': {'contacts': 18, 'size': '20', 'service_rating': 'I'},
        'D19': {'contacts': 19, 'size': '20', 'service_rating': 'I'},
        'E26': {'contacts': 26, 'size': '20', 'service_rating': 'I'},
        'F32': {'contacts': 32, 'size': '20', 'service_rating': 'I'},
        'G24': {'contacts': 24, 'size': '20', 'service_rating': 'I'},
        'G25': {'contacts': 25, 'size': '20', 'service_rating': 'I'},
        'G27': {'contacts': 27, 'size': '20', 'service_rating': 'I'},
        'G41': {'contacts': 41, 'size': '20', 'service_rating': 'I'},
        'H32': {'contacts': 32, 'size': '20', 'service_rating': 'I'},
        'H34': {'contacts': 34, 'size': '20', 'service_rating': 'I'},
        'H36': {'contacts': 36, 'size': '20', 'service_rating': 'I'},
        'H53': {'contacts': 53, 'size': '20', 'service_rating': 'I'},
        'H55': {'contacts': 55, 'size': '20', 'service_rating': 'I'},
        'J61': {'contacts': 61, 'size': '20', 'service_rating': 'I'},
        
        # Size 16 contacts
        'B2': {'contacts': 2, 'size': '16', 'service_rating': 'I'},
        'C4': {'contacts': 4, 'size': '16', 'service_rating': 'I'},
        'D5': {'contacts': 5, 'size': '16', 'service_rating': 'II'},
        'E8': {'contacts': 8, 'size': '16', 'service_rating': 'II'},
        'F11': {'contacts': 11, 'size': '16', 'service_rating': 'II'},
        'G16': {'contacts': 16, 'size': '16', 'service_rating': 'II'},
        'H21': {'contacts': 21, 'size': '16', 'service_rating': 'II'},
        'H97': {'contacts': 16, 'size': '16', 'service_rating': 'I'},
        'H99': {'contacts': 11, 'size': '16', 'service_rating': 'II'},
        'J29': {'contacts': 29, 'size': '16', 'service_rating': 'I'},
        'J37': {'contacts': 37, 'size': '16', 'service_rating': 'II'},
        
        # Size 12 contacts
        'E6': {'contacts': 6, 'size': '12', 'service_rating': 'I'},
        'G11': {'contacts': 11, 'size': '12', 'service_rating': 'I'},
        'J19': {'contacts': 19, 'size': '12', 'service_rating': 'I'},
    }
    
    # Dimensions for Series III connectors
    SERIES_III_DIMENSIONS = {
        'A': {'shell_dia': 0.858, 'coupling_dia': 0.732, 'thread': 'M12', 'panel_cutout': 0.693},
        'B': {'shell_dia': 0.984, 'coupling_dia': 0.839, 'thread': 'M15', 'panel_cutout': 0.825},
        'C': {'shell_dia': 1.157, 'coupling_dia': 1.008, 'thread': 'M18', 'panel_cutout': 1.010},
        'D': {'shell_dia': 1.280, 'coupling_dia': 1.138, 'thread': 'M22', 'panel_cutout': 1.135},
        'E': {'shell_dia': 1.406, 'coupling_dia': 1.276, 'thread': 'M25', 'panel_cutout': 1.260},
        'F': {'shell_dia': 1.516, 'coupling_dia': 1.382, 'thread': 'M28', 'panel_cutout': 1.385},
        'G': {'shell_dia': 1.642, 'coupling_dia': 1.508, 'thread': 'M31', 'panel_cutout': 1.510},
        'H': {'shell_dia': 1.768, 'coupling_dia': 1.626, 'thread': 'M34', 'panel_cutout': 1.635},
        'J': {'shell_dia': 1.890, 'coupling_dia': 1.752, 'thread': 'M37', 'panel_cutout': 1.760}
    }
    
    # Dimensions for Series IV connectors
    SERIES_IV_DIMENSIONS = {
        'B': {'shell_dia': 0.781, 'thread': 'M15', 'panel_cutout_wall': 0.625, 'panel_cutout_jam': 0.825},
        'C': {'shell_dia': 0.921, 'thread': 'M18', 'panel_cutout_wall': 0.750, 'panel_cutout_jam': 1.010},
        'D': {'shell_dia': 1.047, 'thread': 'M22', 'panel_cutout_wall': 0.906, 'panel_cutout_jam': 1.135},
        'E': {'shell_dia': 1.218, 'thread': 'M25', 'panel_cutout_wall': 1.016, 'panel_cutout_jam': 1.260},
        'F': {'shell_dia': 1.296, 'thread': 'M28', 'panel_cutout_wall': 1.142, 'panel_cutout_jam': 1.385},
        'G': {'shell_dia': 1.421, 'thread': 'M31', 'panel_cutout_wall': 1.266, 'panel_cutout_jam': 1.510},
        'H': {'shell_dia': 1.546, 'thread': 'M34', 'panel_cutout_wall': 1.375, 'panel_cutout_jam': 1.635},
        'J': {'shell_dia': 1.672, 'thread': 'M37', 'panel_cutout_wall': 1.484, 'panel_cutout_jam': 1.760}
    }
    
    # Crimp tooling requirements
    CRIMP_TOOLS = {
        '22D': {
            'crimper': 'M22520/2-01 (Glenair 809-015)',
            'positioner_pin': 'M22520/2-09 (K42 Daniels)',
            'positioner_socket': 'M22520/2-07 (K40 Daniels)',
            'insertion_tool': 'M81969/14-01 (Glenair 859-020)',
            'extraction_tool': 'M81969/14-01 (Glenair 859-020)'
        },
        '20': {
            'crimper': 'M22520/2-01 (Glenair 809-015)',
            'positioner': 'M22520/2-10 (K43 Daniels)',
            'insertion_tool': 'M81969/14-10 (Glenair 809-207)',
            'extraction_tool': 'M81969/14-10 (Glenair 809-207)'
        },
        '16': {
            'crimper': 'M22520/1-01 (Glenair 809-136)',
            'positioner': 'M22520/1-04 (Glenair 809-137)',
            'insertion_tool': 'M81969/14-03 (Glenair 809-131)',
            'extraction_tool': 'M81969/14-03 (Glenair 809-131)'
        },
        '12': {
            'crimper': 'M22520/1-01 (Glenair 809-136)',
            'positioner': 'M22520/1-04 (Glenair 809-137)',
            'insertion_tool': 'M81969/14-04 (Glenair 809-132)',
            'extraction_tool': 'M81969/14-04 (Glenair 809-132)'
        },
        '8_COAX': {
            'crimper': 'M22520/2-01 (Glenair 809-015)',
            'positioner': 'M22520/2-31 (K-406 Daniels)',
            'shield_crimper': 'M22520/5-01 (Glenair 809-129)',
            'shield_die': 'M22520/5-05 (Glenair 859-051)'
        },
        '12_COAX': {
            'crimper': 'M22520/2-01 (Glenair 809-015)',
            'positioner': 'M22520/2-34 (K-323 Daniels)',
            'shield_crimper': 'M22520/31-01 (Glenair 809-133)',
            'shield_positioner': 'M22520/31-02 (Glenair 809-134)'
        }
    }
    
    def __init__(self, series_code, class_code, shell_code, insert_arrangement, 
                 contact_type, polarization='N'):
        self.series_code = series_code
        self.class_code = class_code.upper()
        self.shell_code = shell_code.upper()
        self.insert_arrangement = insert_arrangement.upper()
        self.contact_type = contact_type.upper()
        self.polarization = polarization.upper()
        
        # Determine if Series III or IV
        if series_code in self.SERIES_III:
            self.series = 'III'
            self.series_desc = self.SERIES_III[series_code]
        elif series_code in self.SERIES_IV:
            self.series = 'IV'
            self.series_desc = self.SERIES_IV[series_code]
        else:
            raise ValueError(f"Invalid series code: {series_code}")
    
    def build_part_number(self):
        """Construct the full D38999 part number"""
        return f"D38999/{self.series_code}{self.class_code}{self.shell_code}{self.insert_arrangement}{self.contact_type}{self.polarization}"
    
    def get_properties(self):
        """Return all properties of the connector"""
        props = {
            'part_number': self.build_part_number(),
            'series': self.series,
            'series_description': self.series_desc,
            'specification': 'MIL-DTL-38999',
        }
        
        # Add class/finish information
        all_classes = {**self.ENV_CLASSES, **self.HERMETIC_CLASSES}
        if self.class_code in all_classes:
            class_info = all_classes[self.class_code]
            props['class'] = self.class_code
            props['finish'] = class_info['name']
            props['material'] = class_info['material']
            props['temperature_range'] = class_info.get('temp_range', 'N/A')
            props['salt_spray'] = class_info.get('salt_spray', 'N/A')
            props['conductive'] = class_info.get('conductive', False)
            props['space_grade'] = class_info.get('space_grade', False)
        
        # Add shell size information
        if self.shell_code in self.SHELL_SIZES:
            shell_info = self.SHELL_SIZES[self.shell_code]
            props['shell_code'] = self.shell_code
            props['shell_size'] = shell_info['size']
            props['thread_size'] = shell_info['thread_size']
        
        # Add insert arrangement
        props['insert_arrangement'] = self.insert_arrangement
        
        # Add insert arrangement details
        if self.insert_arrangement in self.INSERT_ARRANGEMENTS:
            insert_info = self.INSERT_ARRANGEMENTS[self.insert_arrangement]
            props['contact_count'] = insert_info['contacts']
            props['contact_size'] = insert_info['size']
            props['service_rating'] = insert_info['service_rating']
            if 'positions' in insert_info:
                props['contact_positions'] = insert_info['positions']
        
        # Add contact type
        if self.contact_type in self.CONTACT_TYPES:
            contact_info = self.CONTACT_TYPES[self.contact_type]
            props['contact_gender'] = contact_info['type']
            if 'cycles' in contact_info:
                props['mating_cycles'] = contact_info['cycles']
        
        # Add polarization
        if self.polarization in self.POLARIZATIONS:
            props['polarization'] = self.POLARIZATIONS[self.polarization]
        
        # Threading type
        if self.series == 'III':
            props['coupling_type'] = 'Triple-start thread'
        elif self.series == 'IV':
            props['coupling_type'] = '90° breech-lock'
        
        # EMC performance
        props['shielding'] = '65dB minimum at 10 GHz'
        props['sealing'] = 'IP67'
        
        # Add dimensions
        if self.series == 'III' and self.shell_code in self.SERIES_III_DIMENSIONS:
            props['dimensions'] = self.SERIES_III_DIMENSIONS[self.shell_code]
        elif self.series == 'IV' and self.shell_code in self.SERIES_IV_DIMENSIONS:
            props['dimensions'] = self.SERIES_IV_DIMENSIONS[self.shell_code]
        
        # Add tooling requirements
        if self.insert_arrangement in self.INSERT_ARRANGEMENTS:
            contact_size = self.INSERT_ARRANGEMENTS[self.insert_arrangement]['size']
            if contact_size in self.CRIMP_TOOLS:
                props['tooling'] = self.CRIMP_TOOLS[contact_size]
        
        return props
    
    def get_contact_specs(self, contact_size):
        """Get specifications for a specific contact size"""
        if contact_size in self.CONTACT_SPECS:
            return self.CONTACT_SPECS[contact_size]
        return None
    
    def print_properties(self):
        """Print formatted properties"""
        props = self.get_properties()
        print(f"\n{'='*70}")
        print(f"D38999 CONNECTOR SPECIFICATIONS")
        print(f"{'='*70}")
        print(f"Part Number: {props['part_number']}")
        print(f"Specification: {props['specification']}")
        print(f"Series: {props['series']}")
        print(f"Description: {props['series_description']}")
        print(f"\n{'-'*70}")
        print(f"FINISH AND MATERIAL")
        print(f"{'-'*70}")
        print(f"Class: {props.get('class', 'N/A')}")
        print(f"Finish: {props.get('finish', 'N/A')}")
        print(f"Material: {props.get('material', 'N/A')}")
        print(f"Temperature Range: {props.get('temperature_range', 'N/A')}")
        print(f"Salt Spray: {props.get('salt_spray', 'N/A')}")
        print(f"Conductive: {props.get('conductive', False)}")
        print(f"Space Grade: {props.get('space_grade', False)}")
        print(f"\n{'-'*70}")
        print(f"MECHANICAL")
        print(f"{'-'*70}")
        print(f"Shell Code: {props.get('shell_code', 'N/A')}")
        print(f"Shell Size: {props.get('shell_size', 'N/A')}")
        print(f"Thread Size: {props.get('thread_size', 'N/A')}")
        print(f"Coupling Type: {props.get('coupling_type', 'N/A')}")
        
        if 'dimensions' in props:
            dims = props['dimensions']
            print(f"\nDimensions (inches):")
            for key, val in dims.items():
                print(f"  {key.replace('_', ' ').title()}: {val}")
        
        print(f"\n{'-'*70}")
        print(f"CONTACTS")
        print(f"{'-'*70}")
        print(f"Insert Arrangement: {props.get('insert_arrangement', 'N/A')}")
        print(f"Contact Count: {props.get('contact_count', 'N/A')}")
        print(f"Contact Size: #{props.get('contact_size', 'N/A')}")
        print(f"Service Rating: {props.get('service_rating', 'N/A')}")
        print(f"Contact Gender: {props.get('contact_gender', 'N/A')}")
        print(f"Mating Cycles: {props.get('mating_cycles', 'N/A')}")
        print(f"Polarization: {props.get('polarization', 'N/A')}")
        
        # Print contact positions if available
        if 'contact_positions' in props:
            print(f"\nContact Positions:")
            for pos in props['contact_positions']:
                print(f"  {pos['label']}: Angle={pos['angle']}°, Radius={pos['radius']}mm")
        
        print(f"\n{'-'*70}")
        print(f"TOOLING REQUIREMENTS")
        print(f"{'-'*70}")
        if 'tooling' in props:
            for tool, part in props['tooling'].items():
                print(f"{tool.replace('_', ' ').title()}: {part}")
        else:
            print("No tooling data available")
        
        print(f"\n{'-'*70}")
        print(f"PERFORMANCE")
        print(f"{'-'*70}")
        print(f"Shielding: {props.get('shielding', 'N/A')}")
        print(f"Sealing: {props.get('sealing', 'N/A')}")
        print(f"{'='*70}\n")
    
    def generate_svg(self, filename=None):
        """Generate SVG representation of connector face"""
        props = self.get_properties()
        
        if 'contact_positions' not in props:
            return "SVG generation requires contact position data"
        
        # SVG parameters
        width = 400
        height = 400
        center_x = width / 2
        center_y = height / 2
        scale = 20  # pixels per mm
        
        # Contact sizes in mm
        contact_diameters = {
            '22D': 1.3,
            '20': 1.5,
            '16': 2.0,
            '12': 2.8
        }
        
        contact_size = props.get('contact_size', '20')
        contact_dia = contact_diameters.get(contact_size, 1.5) * scale
        
        # Shell diameter from dimensions
        shell_radius = 50  # default
        if 'dimensions' in props:
            shell_dia_inches = props['dimensions'].get('shell_dia', 1.0)
            shell_radius = (shell_dia_inches * 25.4 / 2) * scale  # convert to mm then pixels
        
        # Build SVG
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .shell {{ fill: #cccccc; stroke: #333333; stroke-width: 2; }}
      .contact {{ fill: #ffd700; stroke: #333333; stroke-width: 1; }}
      .label {{ font-family: Arial; font-size: 10px; fill: #000000; text-anchor: middle; }}
      .title {{ font-family: Arial; font-size: 14px; font-weight: bold; fill: #000000; }}
      .keyway {{ fill: #666666; }}
    </style>
  </defs>
  
  <!-- Title -->
  <text x="{center_x}" y="20" class="title" text-anchor="middle">{props['part_number']}</text>
  <text x="{center_x}" y="35" class="label" text-anchor="middle">
    {props.get('contact_count', 0)} contacts, Size #{contact_size}
  </text>
  
  <!-- Shell outline -->
  <circle cx="{center_x}" cy="{center_y}" r="{shell_radius}" class="shell"/>
  
  <!-- Master keyway (at 0 degrees) -->
  <rect x="{center_x - 3}" y="{center_y - shell_radius}" width="6" height="15" class="keyway"/>
  
  <!-- Contacts -->
'''
        
        for pos in props['contact_positions']:
            angle_rad = (pos['angle'] - 90) * 3.14159 / 180  # -90 to start at top
            radius_pixels = pos['radius'] * scale
            x = center_x + radius_pixels * math.cos(angle_rad)
            y = center_y + radius_pixels * math.sin(angle_rad)
            
            svg += f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{contact_dia/2:.1f}" class="contact"/>\n'
            
            # Label
            label_offset = contact_dia / 2 + 8
            label_x = x
            label_y = y + 3  # slight offset for better centering
            svg += f'  <text x="{label_x:.1f}" y="{label_y:.1f}" class="label">{pos["label"]}</text>\n'
        
        svg += '''
  <!-- Legend -->
  <text x="10" y="380" class="label" text-anchor="start">● Pin Contact</text>
  <text x="10" y="395" class="label" text-anchor="start">▮ Master Keyway</text>
</svg>'''
        
        if filename:
            with open(filename, 'w') as f:
                f.write(svg)
            print(f"SVG saved to {filename}")
        
        return svg


class D38999PartNumberGenerator:
    """Generate multiple D38999 part numbers from ranges and perform batch operations"""
    
    def __init__(self, base_dir='.', revision=REVISION, release_status=RELEASE_STATUS):
        self.base_dir = Path(base_dir)
        self.generated_parts = []
        self.revision = revision
        self.release_status = release_status
    
    def generate_part_numbers(self, series_codes, class_codes, shell_codes, 
                             insert_arrangements, contact_types, polarizations):
        """
        Generate all combinations of part numbers from the given ranges.
        
        Args:
            series_codes: List of series codes (e.g., ['24', '26'])
            class_codes: List of class codes (e.g., ['F', 'W', 'K', 'Z'])
            shell_codes: List of shell codes (e.g., ['A', 'B', 'C'])
            insert_arrangements: List of insert arrangements (e.g., ['35', 'A35', 'B35'])
            contact_types: List of contact types (e.g., ['P', 'S'])
            polarizations: List of polarizations (e.g., ['N', 'A', 'B'])
        
        Returns:
            List of D38999PartNumber objects
        """
        self.generated_parts = []
        invalid_parts = []
        
        # Generate all combinations
        combinations = itertools.product(
            series_codes,
            class_codes,
            shell_codes,
            insert_arrangements,
            contact_types,
            polarizations
        )
        
        for series, cls, shell, insert, contact, polar in combinations:
            try:
                part = D38999PartNumber(series, cls, shell, insert, contact, polar)
                self.generated_parts.append(part)
            except ValueError as e:
                invalid_parts.append({
                    'series': series,
                    'class': cls,
                    'shell': shell,
                    'insert': insert,
                    'contact': contact,
                    'polarization': polar,
                    'error': str(e)
                })
        
        print(f"\nGenerated {len(self.generated_parts)} valid part numbers")
        if invalid_parts:
            print(f"Skipped {len(invalid_parts)} invalid combinations")
        
        return self.generated_parts
    
    def create_directories(self, root_dir=None, include_subdirs=False):
        """
        Create directory structure for all generated part numbers.
        
        Args:
            root_dir: Root directory name. If None, creates directories at current level
            include_subdirs: If True, create subdirectories for docs, drawings, etc.
        
        Returns:
            Dictionary with statistics about created directories
        """
        if not self.generated_parts:
            print("No part numbers generated. Run generate_part_numbers() first.")
            return None
        
        # If root_dir is None, use current directory
        if root_dir is None:
            base_path = self.base_dir
        else:
            base_path = self.base_dir / root_dir
            base_path.mkdir(exist_ok=True)
        
        stats = {
            'created': 0,
            'already_existed': 0,
            'failed': 0,
            'total': len(self.generated_parts)
        }
        
        subdirs = []
        if include_subdirs:
            subdirs = ['drawings', 'specifications', 'test_reports', 'tooling', 'assembly']
        
        for part in self.generated_parts:
            part_number = part.build_part_number()
            # Clean part number for directory name (replace / with -)
            dir_name = part_number.replace('/', '-')
            part_dir = base_path / dir_name
            
            # Create revision directory inside part directory
            rev_dir_name = f"{dir_name}-{self.revision}"
            rev_dir = part_dir / rev_dir_name
            
            try:
                if part_dir.exists() and rev_dir.exists():
                    stats['already_existed'] += 1
                else:
                    # Create main part directory
                    part_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create revision directory
                    rev_dir.mkdir(parents=True, exist_ok=True)
                    stats['created'] += 1
                    
                    # Create subdirectories if requested (in revision directory)
                    for subdir in subdirs:
                        (rev_dir / subdir).mkdir(exist_ok=True)
                    
                    # Create attributes JSON file
                    self._create_attributes_json(part, rev_dir, dir_name)
                    
                    # Create placeholder SVG file
                    self._create_placeholder_svg(rev_dir, dir_name)
                    
                    # Create a README in the main part directory
                    self._create_readme(part, part_dir)
                    
            except Exception as e:
                stats['failed'] += 1
                print(f"Failed to create directory for {part_number}: {e}")
        
        print(f"\nDirectory Creation Summary:")
        if root_dir:
            print(f"  Root directory: {base_path.absolute()}")
        else:
            print(f"  Location: Current directory ({base_path.absolute()})")
        print(f"  Revision: {self.revision}")
        print(f"  Release Status: {self.release_status if self.release_status else 'Not Set'}")
        print(f"  Total part numbers: {stats['total']}")
        print(f"  Directories created: {stats['created']}")
        print(f"  Already existed: {stats['already_existed']}")
        print(f"  Failed: {stats['failed']}")
        
        return stats
    
    def _create_attributes_json(self, part, directory, dir_name):
        """Create JSON file with comprehensive part attributes"""
        props = part.get_properties()
        
        # Build comprehensive attributes dictionary
        attributes = {
            'metadata': {
                'part_number': props['part_number'],
                'revision': self.revision,
                'release_status': self.release_status,
                'specification': props['specification'],
                'created_date': None,  # Can be populated with actual date
                'modified_date': None,
                'created_by': None,
                'approved_by': None
            },
            'identification': {
                'series': props['series'],
                'series_code': part.series_code,
                'series_description': props['series_description'],
                'manufacturer': 'Glenair / Various QPL',
                'mil_spec': 'MIL-DTL-38999'
            },
            'finish_and_material': {
                'class_code': props.get('class', 'N/A'),
                'finish_name': props.get('finish', 'N/A'),
                'material': props.get('material', 'N/A'),
                'temperature_range': props.get('temperature_range', 'N/A'),
                'salt_spray_rating': props.get('salt_spray', 'N/A'),
                'conductive': props.get('conductive', False),
                'space_grade': props.get('space_grade', False)
            },
            'mechanical': {
                'shell_code': props.get('shell_code', 'N/A'),
                'shell_size': props.get('shell_size', 'N/A'),
                'thread_size': props.get('thread_size', 'N/A'),
                'coupling_type': props.get('coupling_type', 'N/A'),
                'dimensions': props.get('dimensions', {})
            },
            'contacts': {
                'insert_arrangement': props.get('insert_arrangement', 'N/A'),
                'contact_count': props.get('contact_count', 'N/A'),
                'contact_size': props.get('contact_size', 'N/A'),
                'service_rating': props.get('service_rating', 'N/A'),
                'contact_gender': props.get('contact_gender', 'N/A'),
                'contact_type_code': part.contact_type,
                'mating_cycles': props.get('mating_cycles', 'N/A'),
                'contact_positions': props.get('contact_positions', [])
            },
            'polarization': {
                'polarization_code': part.polarization,
                'polarization_description': props.get('polarization', 'N/A')
            },
            'electrical': {
                'shielding': props.get('shielding', 'N/A'),
                'voltage_rating': None,  # Can be derived from service rating
                'current_rating': None,  # Depends on contact size
                'dielectric_withstanding_voltage': None,
                'insulation_resistance': None
            },
            'environmental': {
                'sealing_class': props.get('sealing', 'N/A'),
                'ip_rating': 'IP67',
                'operating_temperature_min': props.get('temperature_range', '').split(' to ')[0] if ' to ' in props.get('temperature_range', '') else None,
                'operating_temperature_max': props.get('temperature_range', '').split(' to ')[1] if ' to ' in props.get('temperature_range', '') else None,
                'altitude_rating': '70,000 ft',
                'vibration_rating': 'Per MIL-DTL-38999',
                'shock_rating': 'Per MIL-DTL-38999'
            },
            'tooling': props.get('tooling', {}),
            'standards_compliance': {
                'mil_dtl_38999': True,
                'mil_std_1560': True,
                'rohs_compliant': None,
                'reach_compliant': None,
                'dfars_compliant': True
            },
            'procurement': {
                'cage_code': '06324',  # Glenair CAGE code
                'lead_time_weeks': None,
                'minimum_order_quantity': None,
                'unit_price': None,
                'availability': None
            },
            'quality': {
                'qpl_listed': True,
                'test_reports_available': False,
                'certificate_of_conformance': False,
                'inspection_level': None
            },
            'notes': {
                'general': f"D38999 Series {props['series']} connector per MIL-DTL-38999",
                'assembly': "Requires appropriate crimp contacts and tooling",
                'mating': f"Mates with corresponding {props['series']} series connector",
                'warnings': []
            }
        }
        
        # Write JSON file
        json_file = directory / f"{dir_name}-{self.revision}-attributes.json"
        with open(json_file, 'w') as f:
            json.dump(attributes, f, indent=2)
    
    def _create_placeholder_svg(self, directory, dir_name):
        """Create placeholder SVG file for future drawing"""
        svg_file = directory / f"{dir_name}-{self.revision}-drawing.svg"
        
        placeholder_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .placeholder {{ fill: #f0f0f0; stroke: #999999; stroke-width: 2; stroke-dasharray: 5,5; }}
      .text {{ font-family: Arial; font-size: 14px; fill: #666666; text-anchor: middle; }}
    </style>
  </defs>
  
  <rect x="10" y="10" width="380" height="380" class="placeholder"/>
  <text x="200" y="190" class="text">{dir_name}</text>
  <text x="200" y="210" class="text">Revision {self.revision}</text>
  <text x="200" y="230" class="text">Drawing Placeholder</text>
</svg>'''
        
        with open(svg_file, 'w') as f:
            f.write(placeholder_svg)
    
    def _create_readme(self, part, directory):
        """Create a README file with part specifications"""
        readme_path = directory / 'README.txt'
        props = part.get_properties()
        
        with open(readme_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write(f"D38999 CONNECTOR SPECIFICATIONS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Part Number: {props['part_number']}\n")
            f.write(f"Specification: {props['specification']}\n")
            f.write(f"Series: {props['series']}\n")
            f.write(f"Description: {props['series_description']}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("FINISH AND MATERIAL\n")
            f.write("-" * 70 + "\n")
            f.write(f"Class: {props.get('class', 'N/A')}\n")
            f.write(f"Finish: {props.get('finish', 'N/A')}\n")
            f.write(f"Material: {props.get('material', 'N/A')}\n")
            f.write(f"Temperature Range: {props.get('temperature_range', 'N/A')}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("MECHANICAL\n")
            f.write("-" * 70 + "\n")
            f.write(f"Shell Size: {props.get('shell_size', 'N/A')}\n")
            f.write(f"Thread Size: {props.get('thread_size', 'N/A')}\n")
            f.write(f"Coupling Type: {props.get('coupling_type', 'N/A')}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("CONTACTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Insert Arrangement: {props.get('insert_arrangement', 'N/A')}\n")
            f.write(f"Contact Count: {props.get('contact_count', 'N/A')}\n")
            f.write(f"Contact Size: #{props.get('contact_size', 'N/A')}\n")
            f.write(f"Contact Gender: {props.get('contact_gender', 'N/A')}\n")
            f.write(f"Mating Cycles: {props.get('mating_cycles', 'N/A')}\n\n")
            
            f.write("=" * 70 + "\n")
    
    def generate_svgs(self, output_dir=None, populate_drawings=False):
        """
        Generate SVG drawings for all part numbers that have position data.
        
        Args:
            output_dir: Directory where part number folders are located. 
                       If None, uses current directory.
            populate_drawings: If True, replace placeholder SVGs with actual drawings
        """
        if output_dir is None:
            output_path = self.base_dir
        else:
            output_path = self.base_dir / output_dir
            
        generated = 0
        skipped = 0
        
        for part in self.generated_parts:
            part_number = part.build_part_number()
            dir_name = part_number.replace('/', '-')
            rev_dir_name = f"{dir_name}-{self.revision}"
            
            # Check if this part has position data
            props = part.get_properties()
            if 'contact_positions' in props and populate_drawings:
                try:
                    # Generate actual SVG with contact positions
                    svg_file = output_path / dir_name / rev_dir_name / f"{dir_name}-{self.revision}-drawing.svg"
                    part.generate_svg(str(svg_file))
                    generated += 1
                except Exception as e:
                    print(f"Failed to generate SVG for {part_number}: {e}")
                    skipped += 1
            else:
                if not populate_drawings:
                    # Placeholder already created
                    pass
                else:
                    skipped += 1
        
        if populate_drawings:
            print(f"\nSVG Generation Summary:")
            print(f"  SVGs generated: {generated}")
            print(f"  Skipped (no position data): {skipped}")
        else:
            print(f"\nPlaceholder SVGs created for all parts")
            print(f"  Use populate_drawings=True to generate actual drawings")
    
    def export_catalog(self, filename='part_catalog.csv'):
        """
        Export all generated part numbers to a CSV catalog.
        
        Args:
            filename: Output CSV filename
        """
        if not self.generated_parts:
            print("No part numbers to export.")
            return
        
        output_path = self.base_dir / filename
        
        with open(output_path, 'w') as f:
            # Header
            f.write("Part Number,Series,Description,Class,Finish,Shell Size,")
            f.write("Insert Arrangement,Contact Count,Contact Size,Contact Type,")
            f.write("Polarization,Thread Size,Temperature Range\n")
            
            # Data rows
            for part in self.generated_parts:
                props = part.get_properties()
                f.write(f"{props['part_number']},")
                f.write(f"{props['series']},")
                f.write(f"\"{props['series_description']}\",")
                f.write(f"{props.get('class', '')},")
                f.write(f"\"{props.get('finish', '')}\",")
                f.write(f"{props.get('shell_size', '')},")
                f.write(f"{props.get('insert_arrangement', '')},")
                f.write(f"{props.get('contact_count', '')},")
                f.write(f"{props.get('contact_size', '')},")
                f.write(f"\"{props.get('contact_gender', '')}\",")
                f.write(f"{props.get('polarization', '')},")
                f.write(f"{props.get('thread_size', '')},")
                f.write(f"\"{props.get('temperature_range', '')}\"\n")
        
        print(f"\nCatalog exported to: {output_path.absolute()}")
        print(f"Total parts: {len(self.generated_parts)}")
    
    def filter_parts(self, **criteria):
        """
        Filter generated parts by criteria.
        
        Args:
            **criteria: Key-value pairs to filter by (e.g., shell_size=11, contact_count=13)
        
        Returns:
            List of matching D38999PartNumber objects
        """
        matching = []
        
        for part in self.generated_parts:
            props = part.get_properties()
            match = True
            
            for key, value in criteria.items():
                if props.get(key) != value:
                    match = False
                    break
            
            if match:
                matching.append(part)
        
        return matching
    
    def get_summary(self):
        """Get summary statistics of generated part numbers"""
        if not self.generated_parts:
            return "No part numbers generated."
        
        summary = {
            'total_parts': len(self.generated_parts),
            'series': {},
            'classes': {},
            'shell_sizes': {},
            'contact_types': {}
        }
        
        for part in self.generated_parts:
            props = part.get_properties()
            
            # Count by series
            series = props['series']
            summary['series'][series] = summary['series'].get(series, 0) + 1
            
            # Count by class
            cls = props.get('class', 'Unknown')
            summary['classes'][cls] = summary['classes'].get(cls, 0) + 1
            
            # Count by shell size
            shell = props.get('shell_size', 'Unknown')
            summary['shell_sizes'][shell] = summary['shell_sizes'].get(shell, 0) + 1
            
            # Count by contact type
            contact = props.get('contact_gender', 'Unknown')
            summary['contact_types'][contact] = summary['contact_types'].get(contact, 0) + 1
        
        return summary
    
    def print_summary(self):
        """Print formatted summary statistics"""
        summary = self.get_summary()
        
        if isinstance(summary, str):
            print(summary)
            return
        
        print(f"\n{'='*70}")
        print("PART NUMBER GENERATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total Part Numbers: {summary['total_parts']}")
        
        print(f"\nBy Series:")
        for series, count in sorted(summary['series'].items()):
            print(f"  Series {series}: {count}")
        
        print(f"\nBy Class:")
        for cls, count in sorted(summary['classes'].items()):
            print(f"  Class {cls}: {count}")
        
        print(f"\nBy Shell Size:")
        for size, count in sorted(summary['shell_sizes'].items()):
            print(f"  Size {size}: {count}")
        
        print(f"\nBy Contact Type:")
        for contact, count in sorted(summary['contact_types'].items()):
            print(f"  {contact}: {count}")
        
        print(f"{'='*70}\n")


# Example usage
if __name__ == "__main__":
    print("\n" + "="*70)
    print("D38999 CONNECTOR DIRECTORY GENERATOR")
    print(f"Revision: {REVISION}")
    print(f"Release Status: {RELEASE_STATUS if RELEASE_STATUS else 'Not Set'}")
    print("="*70)
    
    # Create generator instance
    generator = D38999PartNumberGenerator(revision=REVISION, release_status=RELEASE_STATUS)
    
    # Define ranges for batch generation
    series_codes = ['24', '26']  # Jam-nut receptacle and Plug
    class_codes = ['F', 'W', 'K', 'Z']  # Different finishes
    shell_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']  # All shell sizes
    insert_arrangements = ['A35', 'B35', 'C35']  # Sample arrangements
    contact_types = ['P', 'S']  # Pin and Socket
    polarizations = ['N', 'A', 'B', 'C']  # Normal and alternates
    
    # Generate all combinations
    print("\nGenerating part numbers from ranges...")
    print(f"  Series: {series_codes}")
    print(f"  Classes: {class_codes}")
    print(f"  Shell Codes: {shell_codes}")
    print(f"  Insert Arrangements: {insert_arrangements}")
    print(f"  Contact Types: {contact_types}")
    print(f"  Polarizations: {polarizations}")
    
    parts = generator.generate_part_numbers(
        series_codes=series_codes,
        class_codes=class_codes,
        shell_codes=shell_codes,
        insert_arrangements=insert_arrangements,
        contact_types=contact_types,
        polarizations=polarizations
    )
    
    # Print summary
    generator.print_summary()
    
    # Create directories at the same level as the script (no nesting)
    print("\n" + "="*70)
    print("CREATING CONNECTOR DIRECTORIES")
    print("="*70)
    print("Creating directories at current level...")
    print(f"Structure: PartNumber/PartNumber-Rev{REVISION}/")
    stats = generator.create_directories(
        root_dir=None,  # None = create at current level, no nesting
        include_subdirs=True
    )
    
    # Export catalog
    print("\n" + "="*70)
    print("EXPORTING CATALOG")
    print("="*70)
    generator.export_catalog('d38999_catalog.csv')
    
    # Note about SVG generation
    print("\n" + "="*70)
    print("SVG DRAWINGS")
    print("="*70)
    print("Placeholder SVG files created for all parts")
    print("To populate with actual drawings, call:")
    print("  generator.generate_svgs(populate_drawings=True)")
    
    # Example: Filter parts
    print("\n" + "="*70)
    print("FILTERING EXAMPLE")
    print("="*70)
    print("\nFinding all Size 11 shell connectors with 13 contacts...")
    filtered = generator.filter_parts(shell_size=11, contact_count=13)
    print(f"Found {len(filtered)} matching parts:")
    for part in filtered[:5]:  # Show first 5
        props = part.get_properties()
        print(f"  {props['part_number']} - {props['series_description']}")
    if len(filtered) > 5:
        print(f"  ... and {len(filtered) - 5} more")
    
    print("\n" + "="*70)
    print("OPERATION COMPLETE")
    print("="*70)
    print(f"\nAll connector directories created at:")
    print(f"  {Path.cwd()}")
    print(f"\nDirectory structure:")
    print(f"  PartNumber/")
    print(f"    ├── PartNumber-{REVISION}/")
    print(f"    │   ├── PartNumber-{REVISION}-attributes.json")
    print(f"    │   ├── PartNumber-{REVISION}-drawing.svg (placeholder)")
    print(f"    │   ├── drawings/")
    print(f"    │   ├── specifications/")
    print(f"    │   ├── test_reports/")
    print(f"    │   ├── tooling/")
    print(f"    │   └── assembly/")
    print(f"    └── README.txt")
    print(f"\nTotal directories: {stats['created'] + stats['already_existed']}")
    print(f"Catalog exported to: d38999_catalog.csv")