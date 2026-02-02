"""
D38999 MIL-DTL-38999 Series III and IV Part Number Builder
Constructs part numbers and returns specifications per MIL-DTL-38999
"""
import math

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


# Example usage
if __name__ == "__main__":
    # Example 1: Series III Plug with SVG generation
    print("\nExample 1: Series III Environmental Plug")
    connector1 = D38999PartNumber(
        series_code='26',
        class_code='W',
        shell_code='A',
        insert_arrangement='A35',
        contact_type='P',
        polarization='N'
    )
    connector1.print_properties()
    
    # Generate SVG
    svg_output = connector1.generate_svg('d38999_connector.svg')
    print("SVG Preview (first 500 chars):")
    print(svg_output[:500] + "...")
    
    # Example 2: Series III Receptacle with more contacts
    print("\n" + "="*70)
    print("\nExample 2: Series III Jam-nut Receptacle")
    connector2 = D38999PartNumber(
        series_code='24',
        class_code='F',
        shell_code='B',
        insert_arrangement='B35',
        contact_type='S',
        polarization='A'
    )
    connector2.print_properties()
    
    # Example 3: Series IV Plug
    print("\n" + "="*70)
    print("\nExample 3: Series IV Plug")
    connector3 = D38999PartNumber(
        series_code='47',
        class_code='W',
        shell_code='D',
        insert_arrangement='E26',
        contact_type='P',
        polarization='N'
    )
    connector3.print_properties()
    
    # Get contact specifications table
    print("\n" + "="*70)
    print("\nContact Size Specifications:")
    print("-" * 70)
    print(f"{'Size':<8} {'Wire AWG':<15} {'Env Current':<15} {'Hermetic Current':<15}")
    print("-" * 70)
    for size, spec in D38999PartNumber.CONTACT_SPECS.items():
        if 'wire_awg' in spec:
            print(f"#{size:<7} {spec['wire_awg']:<15} {spec['env_current']} Amp{'':<10} {spec['hermetic_current']} Amp")
    
    # Available insert arrangements summary
    print("\n" + "="*70)
    print("\nAvailable Insert Arrangements (Sample):")
    print("-" * 70)
    print(f"{'Arrangement':<15} {'Contacts':<10} {'Size':<10} {'Rating':<10}")
    print("-" * 70)
    for arr, info in list(D38999PartNumber.INSERT_ARRANGEMENTS.items())[:10]:
        print(f"{arr:<15} {info['contacts']:<10} #{info['size']:<9} {info['service_rating']:<10}")
    print(f"... and {len(D38999PartNumber.INSERT_ARRANGEMENTS) - 10} more arrangements")