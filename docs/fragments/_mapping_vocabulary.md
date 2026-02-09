??? note "Mapping vocabulary"

    ![Vocabulary graphic](fragments_images/terminology.png)

    **Net:**

    - Requirement that a harness must exist to connect some connectors together.

    **Harness:**

    - A harness is an assembly of connectors, cables, and other electrical components that connect multiple devices together. It is the physical item that is built and installed in a system.



    **Channel:**

    - A channel is a set of signals that transmit or receive one piece of information, power, etc. They have "channel_types" which define their attributes and compatibility with other channels, and contain a list of required signals (pos, neg)



    **Signal:**

    - A signal is a physical conductive part inside a connector of a device that facilitiates electrical interface with the outside world. A signal must be part of a channel and live inside a connector.



    **Circuit:**

    - A circuit is the requirement that there must exist an electrical path between two signals of connected devices. You can assign conductors or other electrical elements along it. Instances assigned along the circuit have "circuit ids" which represent the order in which the circuit passes through them.



    **Conductor:**

    - A piece of copper, sometimes contained in a cable. Has as many properties, appearances, as you need



    **Cable:**

    - A cable is a COTS or custom physical item, purchased by length, that contains electrical conductors, and are physically installed inside harnesses.



    ## Less important terms

    - **Contact:**

        - The metal parts of a connector that does the actual mating with the other connector, allows for termination to a wire. Can be pins, sockets, studs, terminals, etc.



    - **Cavity:**

        - The hole in a connector that physically holds a contact

