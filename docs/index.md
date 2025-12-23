# Welcome to Harnice

**Harnice** is a powerful Python framework for electrical system design and harness management that transforms how engineers define, validate, and document complex electrical systems. By providing a single source of truth for system connectivity and enabling automated generation of all downstream artifacts, Harnice empowers designers to focus on engineering excellence rather than manual documentation.

## What is an Electrical System?

An **electrical system** is any collection of interconnected electrical components—circuit boards, electrical boxes, devices, and subsystems—that communicate and interact through wires, cables, or harnesses.

Electrical systems are everywhere:

- **Consumer Electronics**: Smartphones, laptops, IoT devices
- **Industrial Systems**: Commercial power distribution, manufacturing control systems
- **Transportation**: Automotive, aerospace, and marine control systems
- **Entertainment**: Professional audio systems, concert sound systems
- **Infrastructure**: City power distribution networks, building automation

## The Challenge: Why Harnice Exists

Modern electrical system design faces critical challenges that traditional tools fail to address:

### The Single Source of Truth Problem

Electrical systems require precise documentation of every device, connection, and design rule. Without a centralized system definition, designers struggle with:

- **Conflicting documentation** across multiple files, spreadsheets, and drawings
- **Broken traceability** between design intent and final artifacts
- **Manual synchronization** of changes across documentation, BOMs, and drawings
- **Error-prone processes** that scale poorly with system complexity

### The Automation Gap

Traditional workflows force engineers to manually compile, validate, and document system designs, consuming valuable engineering time on repetitive tasks rather than design innovation.

## The Harnice Solution

Harnice addresses these challenges through three core principles:

### 1. **Single Source of Truth**

Harnice maintains one authoritative system definition that describes all devices, their connections, and design rules. Every artifact generated from this definition is directly traceable to the source, ensuring consistency and eliminating conflicting documentation.

### 2. **Machine-Readable Design Rules**

Designers define standards, rules, and processes in a clear, concise format that is both human-readable and machine-executable. Harnice uses these rules to automatically build, validate, simulate, and generate artifacts from your system definition.

### 3. **Unlimited Automated Outputs**

From a single system definition, Harnice generates all downstream documentation automatically:

- **Complete Bill of Materials** (BOMs) with devices, harnesses, parts, cable lengths, consumables, and more
- **Version control and release management** with part numbers per reference designator
- **Production documentation** including harness build drawings, formboards, and wirelists in PDF and CSV formats
- **Electrical simulation** capabilities for steady-state and transient analysis
- **Custom artifacts** through extensible Python scripting

## How Harnice Works

Harnice is a Python package that processes netlists and transforms them into comprehensive system documentation and artifacts.

### The Workflow

1. **Define Your System**: Create a block diagram using KiCad or Altium
   - Components represent devices
   - Nets represent harnesses and connections

2. **Process the Netlist**: Harnice analyzes your netlist to:
   - Determine harness requirements
   - Build channel maps
   - Generate System Instances Lists (comprehensive part and connection inventories)

3. **Apply Design Rules**: The harness editor:
   - Locates harnesses within the system
   - Applies standard build rules
   - Adds required parts automatically

4. **Generate Artifacts**: Export build drawings, BOMs, wirelists, and other documentation instantaneously

### Minimum Input Requirements

Harnice operates efficiently with minimal input:

- **Fully defined devices** with all signals, channels, and connectors accounted for
- **Complete electrical behavior definitions** for each device
- **System block diagram** with all devices and harness connections specified
- **Design rules** expressed as:
  - Channel mapping preferences
  - Part selection trees
  - Length, size, count, and attribute requirements
  - Any custom rule your system requires
- **Physical routing information** (imported or manually defined)

## Unprecedented Flexibility

Harnice represents a fundamental departure from traditional eCAD packages by offering complete extensibility:

**You define your own vocabulary, relationships, and instance types.**

As long as an item can be defined as an "instance," it can be part of your electrical system. Whether you're tracking cables, connectors, mechanical fasteners, or custom components, Harnice adapts to your needs rather than forcing you into predefined categories.

This flexibility enables:
- Custom part types and classifications
- Domain-specific terminology
- Unique relationship definitions
- Integration with any component or material in your system

## Current Limitations

Harnice focuses on electrical system connectivity and harness management. The following areas are currently outside scope:

- **Internal device design**: Harnice tracks how devices interact with the outside world, not their internal circuitry or software configuration
- **Non-electrical properties**: Physical dimensions, weight, thermal characteristics, environmental compliance, and mechanical mounting are not currently tracked
- **As-built tracking**: ERP/MES functionality for manufacturing execution is not yet provided

## The State of the Industry

### Existing Commercial Solutions

Traditional eCAD packages (Zuken, E-plan, Altium Harnessing) offer comprehensive features but come with significant drawbacks:

- **High cost**: Enterprise licensing that limits accessibility
- **Steep learning curve**: Training-intensive interfaces
- **Limited customization**: Rigid workflows that don't adapt to unique requirements
- **Poor user experience**: Complex interfaces that hinder productivity

### Manual Alternatives

Many teams resort to manual documentation methods:

- Hand-drawn schematics on paper
- Generic drawing tools (Visio, PowerPoint, Excel, MS Paint, WireViz) that produce attractive visuals but lack metadata
- **No design rule checking**: Manual validation is error-prone and time-consuming
- **Multiple sources of truth**: Documentation scattered across files, leading to inconsistencies

## Why Harnice is Different

Harnice transforms the design workflow by automating the tedious work while preserving complete control and flexibility:

**Without Harnice**: Engineers manually compile information from design guides, industry standards, and various sources, documenting results throughout the design process. This approach suffers from poor traceability, broken links to source information, and results that scale linearly with design time.

**With Harnice**: Engineers document design inputs (standards, rules, processes) in a machine-readable format. Python handles the repetitive work—generating documentation, validating connections, applying rules—while designers focus on engineering decisions and innovation.

The result? Faster design cycles, fewer errors, complete traceability, and the freedom to customize every aspect of your workflow.
