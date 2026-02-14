# List Pods

> Returns a list of Pods.

## OpenAPI

````yaml GET /pods
paths:
  path: /pods
  method: get
  servers:
    - url: https://rest.runpod.io/v1
  request:
    security:
      - title: ApiKey
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
          cookie: {}
    parameters:
      path: {}
      query:
        computeType:
          schema:
            - type: enum<string>
              enum:
                - GPU
                - CPU
              description: Filter to only GPU or only CPU Pods.
              example: CPU
        cpuFlavorId:
          schema:
            - type: array
              items:
                allOf:
                  - type: string
              description: Filter to CPU Pods with any of the listed CPU flavors.
              example:
                - cpu3c
                - cpu5g
        dataCenterId:
          schema:
            - type: array
              items:
                allOf:
                  - type: string
              description: >-
                Filter to Pods located in any of the provided Runpod data
                centers.
              example:
                - EU-RO-1
        desiredStatus:
          schema:
            - type: enum<string>
              enum:
                - RUNNING
                - EXITED
                - TERMINATED
              description: Filter to Pods currently in the provided state.
              example: RUNNING
        endpointId:
          schema:
            - type: string
              required: false
              description: >-
                Filter to workers on the provided Serverless endpoint (note that
                endpoint workers are not included in the response by default,
                set includeWorkers to true to include them).
              maxLength: 191
        gpuTypeId:
          schema:
            - type: array
              items:
                allOf:
                  - type: string
              description: Filter to Pods with any of the listed GPU types attached.
              example:
                - NVIDIA GeForce RTX 4090
                - NVIDIA RTX A5000
        id:
          schema:
            - type: string
              required: false
              description: Filter to a specific Pod.
              example: xedezhzb9la3ye
        imageName:
          schema:
            - type: string
              required: false
              description: Filter to Pods created with the provided image.
              example: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
        includeMachine:
          schema:
            - type: boolean
              description: Include information about the machine the Pod is running on.
              default: false
              example: true
        includeNetworkVolume:
          schema:
            - type: boolean
              description: >-
                Include information about the network volume attached to the
                returned Pod, if any.
              default: false
              example: true
        includeSavingsPlans:
          schema:
            - type: boolean
              description: Include information about the savings plans applied to the Pod.
              default: false
              example: true
        includeTemplate:
          schema:
            - type: boolean
              description: Include information about the template the Pod uses, if any.
              default: false
              example: true
        includeWorkers:
          schema:
            - type: boolean
              description: Set to true to also list Pods which are Serverless workers.
              default: false
              example: true
        name:
          schema:
            - type: string
              required: false
              description: Filter to Pods with the provided name.
              maxLength: 191
        networkVolumeId:
          schema:
            - type: string
              description: Filter to Pods with the provided network volume attached.
              example: agv6w2qcg7
        templateId:
          schema:
            - type: string
              required: false
              description: Filter to Pods created from the provided template.
              example: 30zmvf89kd
      header: {}
      cookie: {}
    body: {}
  response:
    '200':
      application/json:
        schemaArray:
          - type: array
            items:
              allOf:
                - $ref: '#/components/schemas/Pod'
            refIdentifier: '#/components/schemas/Pods'
        examples:
          example:
            value:
              - adjustedCostPerHr: 0.69
                aiApiId: null
                consumerUserId: user_2PyTJrLzeuwfZilRZ7JhCQDuSqo
                containerDiskInGb: 50
                containerRegistryAuthId: clzdaifot0001l90809257ynb
                costPerHr: '0.74'
                cpuFlavorId: cpu3c
                desiredStatus: RUNNING
                dockerEntrypoint:
                  - <string>
                dockerStartCmd:
                  - <string>
                endpointId: null
                env:
                  ENV_VAR: value
                gpu:
                  id: <string>
                  count: 1
                  displayName: <string>
                  securePrice: 123
                  communityPrice: 123
                  oneMonthPrice: 123
                  threeMonthPrice: 123
                  sixMonthPrice: 123
                  oneWeekPrice: 123
                  communitySpotPrice: 123
                  secureSpotPrice: 123
                id: xedezhzb9la3ye
                image: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
                interruptible: false
                lastStartedAt: '2024-07-12T19:14:40.144Z'
                lastStatusChange: >-
                  Rented by User: Fri Jul 12 2024 15:14:40 GMT-0400 (Eastern
                  Daylight Time)
                locked: false
                machine:
                  minPodGpuCount: 123
                  gpuTypeId: <string>
                  gpuType:
                    id: <string>
                    count: 1
                    displayName: <string>
                    securePrice: 123
                    communityPrice: 123
                    oneMonthPrice: 123
                    threeMonthPrice: 123
                    sixMonthPrice: 123
                    oneWeekPrice: 123
                    communitySpotPrice: 123
                    secureSpotPrice: 123
                  cpuCount: 123
                  cpuTypeId: <string>
                  cpuType:
                    id: <string>
                    displayName: <string>
                    cores: 123
                    threadsPerCore: 123
                    groupId: <string>
                  location: <string>
                  dataCenterId: <string>
                  diskThroughputMBps: 123
                  maxDownloadSpeedMbps: 123
                  maxUploadSpeedMbps: 123
                  supportPublicIp: true
                  secureCloud: true
                  maintenanceStart: <string>
                  maintenanceEnd: <string>
                  maintenanceNote: <string>
                  note: <string>
                  costPerHr: 123
                  currentPricePerGpu: 123
                  gpuAvailable: 123
                  gpuDisplayName: <string>
                machineId: s194cr8pls2z
                memoryInGb: 62
                name: <string>
                networkVolume:
                  id: agv6w2qcg7
                  name: my network volume
                  size: 50
                  dataCenterId: EU-RO-1
                portMappings:
                  '22': 10341
                ports:
                  - 8888/http
                  - 22/tcp
                publicIp: 100.65.0.119
                savingsPlans:
                  - costPerHr: 0.21
                    endTime: '2024-07-12T19:14:40.144Z'
                    gpuTypeId: NVIDIA GeForce RTX 4090
                    id: clkrb4qci0000mb09c7sualzo
                    podId: xedezhzb9la3ye
                    startTime: '2024-05-12T19:14:40.144Z'
                slsVersion: 0
                templateId: null
                vcpuCount: 24
                volumeEncrypted: false
                volumeInGb: 20
                volumeMountPath: /workspace
        description: Successful operation.
    '400':
      _mintlify/placeholder:
        schemaArray:
          - type: any
            description: Invalid ID supplied.
        examples: {}
        description: Invalid ID supplied.
    '404':
      _mintlify/placeholder:
        schemaArray:
          - type: any
            description: Pod not found.
        examples: {}
        description: Pod not found.
  deprecated: false
  type: path
components:
  schemas:
    Pod:
      type: object
      properties:
        adjustedCostPerHr:
          type: number
          example: 0.69
          description: >-
            The effective cost in Runpod credits per hour of running a Pod,
            adjusted by active Savings Plans.
        aiApiId:
          type: string
          example: null
          description: Synonym for endpointId (legacy name).
        consumerUserId:
          type: string
          example: user_2PyTJrLzeuwfZilRZ7JhCQDuSqo
          description: A unique string identifying the Runpod user who rents a Pod.
        containerDiskInGb:
          type: integer
          example: 50
          description: >-
            The amount of disk space, in gigabytes (GB), to allocate on the
            container disk for a Pod. The data on the container disk is wiped
            when the Pod restarts. To persist data across Pod restarts, set
            volumeInGb to configure the Pod network volume.
        containerRegistryAuthId:
          type: string
          example: clzdaifot0001l90809257ynb
          description: >-
            If a Pod is created with a container registry auth, the unique
            string identifying that container registry auth.
        costPerHr:
          type: number
          example: '0.74'
          format: currency
          description: >-
            The cost in Runpod credits per hour of running a Pod. Note that the
            actual cost may be lower if Savings Plans are applied.
        cpuFlavorId:
          type: string
          example: cpu3c
          description: >-
            If the Pod is a CPU Pod, the unique string identifying the CPU
            flavor the Pod is running on.
        desiredStatus:
          type: string
          enum:
            - RUNNING
            - EXITED
            - TERMINATED
          description: The current expected status of a Pod.
        dockerEntrypoint:
          type: array
          items:
            type: string
          description: >-
            If specified, overrides the ENTRYPOINT for the Docker image run on
            the created Pod. If [], uses the ENTRYPOINT defined in the image.
        dockerStartCmd:
          type: array
          items:
            type: string
          description: >-
            If specified, overrides the start CMD for the Docker image run on
            the created Pod. If [], uses the start CMD defined in the image.
        endpointId:
          type: string
          example: null
          description: >-
            If the Pod is a Serverless worker, a unique string identifying the
            associated endpoint.
        env:
          type: object
          items:
            type: string
          example:
            ENV_VAR: value
          default: {}
        gpu:
          type: object
          properties:
            id:
              type: string
            count:
              type: integer
              example: 1
              description: The number of GPUs attached to a Pod.
            displayName:
              type: string
            securePrice:
              type: number
            communityPrice:
              type: number
            oneMonthPrice:
              type: number
            threeMonthPrice:
              type: number
            sixMonthPrice:
              type: number
            oneWeekPrice:
              type: number
            communitySpotPrice:
              type: number
            secureSpotPrice:
              type: number
        id:
          type: string
          example: xedezhzb9la3ye
          description: A unique string identifying a [Pod](#/components/schema/Pod).
        image:
          type: string
          example: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
          description: The image tag for the container run on a Pod.
        interruptible:
          type: boolean
          example: false
          description: >-
            Describes how a Pod is rented. An interruptible Pod can be rented at
            a lower cost but can be stopped at any time to free up resources for
            another Pod. A reserved Pod is rented at a higher cost but runs
            until it exits or is manually stopped.
        lastStartedAt:
          type: string
          example: '2024-07-12T19:14:40.144Z'
          description: The UTC timestamp when a Pod was last started.
        lastStatusChange:
          type: string
          example: >-
            Rented by User: Fri Jul 12 2024 15:14:40 GMT-0400 (Eastern Daylight
            Time)
          description: A string describing the last lifecycle event on a Pod.
        locked:
          type: boolean
          example: false
          description: >-
            Set to true to lock a Pod. Locking a Pod disables stopping or
            resetting the Pod.
        machine:
          type: object
          properties:
            minPodGpuCount:
              type: integer
            gpuTypeId:
              type: string
            gpuType:
              type: object
              properties:
                id:
                  type: string
                count:
                  type: integer
                  example: 1
                  description: The number of GPUs attached to a Pod.
                displayName:
                  type: string
                securePrice:
                  type: number
                communityPrice:
                  type: number
                oneMonthPrice:
                  type: number
                threeMonthPrice:
                  type: number
                sixMonthPrice:
                  type: number
                oneWeekPrice:
                  type: number
                communitySpotPrice:
                  type: number
                secureSpotPrice:
                  type: number
            cpuCount:
              type: integer
            cpuTypeId:
              type: string
            cpuType:
              type: object
              properties:
                id:
                  type: string
                displayName:
                  type: string
                cores:
                  type: number
                threadsPerCore:
                  type: number
                groupId:
                  type: string
            location:
              type: string
            dataCenterId:
              type: string
            diskThroughputMBps:
              type: integer
            maxDownloadSpeedMbps:
              type: integer
            maxUploadSpeedMbps:
              type: integer
            supportPublicIp:
              type: boolean
            secureCloud:
              type: boolean
            maintenanceStart:
              type: string
            maintenanceEnd:
              type: string
            maintenanceNote:
              type: string
            note:
              type: string
            costPerHr:
              type: number
            currentPricePerGpu:
              type: number
            gpuAvailable:
              type: integer
            gpuDisplayName:
              type: string
          description: >-
            Information about the machine a Pod is running on (see
            [Machine](#/components/schemas/Machine)).
        machineId:
          type: string
          example: s194cr8pls2z
          description: A unique string identifying the host machine a Pod is running on.
        memoryInGb:
          type: number
          example: 62
          description: The amount of RAM, in gigabytes (GB), attached to a Pod.
        name:
          type: string
          maxLength: 191
          description: >-
            A user-defined name for the created Pod. The name does not need to
            be unique.
        networkVolume:
          type: object
          properties:
            id:
              type: string
              example: agv6w2qcg7
              description: A unique string identifying a network volume.
            name:
              type: string
              example: my network volume
              description: >-
                A user-defined name for a network volume. The name does not need
                to be unique.
            size:
              type: integer
              example: 50
              description: >-
                The amount of disk space, in gigabytes (GB), allocated to a
                network volume.
            dataCenterId:
              type: string
              example: EU-RO-1
              description: The Runpod data center ID where a network volume is located.
          description: >-
            If a network volume is attached to a Pod, information about the
            network volume (see [network volume
            schema](#/components/schemas/NetworkVolume)).
        portMappings:
          type: object
          items:
            type: integer
          example:
            '22': 10341
          description: >-
            A mapping of internal ports to public ports on a Pod. For example, {
            "22": 10341 } means that port 22 on the Pod is mapped to port 10341
            and is publicly accessible at [public ip]:10341. If the Pod is still
            initializing, this mapping is not yet determined and will be empty.
        ports:
          type: array
          items:
            type: string
          example:
            - 8888/http
            - 22/tcp
          description: >-
            A list of ports exposed on a Pod. Each port is formatted as [port
            number]/[protocol]. Protocol can be either http or tcp.
        publicIp:
          type: string
          example: 100.65.0.119
          format: ipv4
          nullable: true
          description: >-
            The public IP address of a Pod. If the Pod is still initializing,
            this IP is not yet determined and will be empty.
        savingsPlans:
          type: array
          items:
            $ref: '#/components/schemas/SavingsPlan'
          description: >-
            The list of active Savings Plans applied to a Pod (see [Savings
            Plans](#/components/schemas/SavingsPlan)). If none are applied, the
            list is empty.
        slsVersion:
          type: integer
          example: 0
          description: >-
            If the Pod is a Serverless worker, the version of the associated
            endpoint (see [Endpoint
            Version](#/components/schemas/Endpoint/version)).
        templateId:
          type: string
          example: null
          description: >-
            If a Pod is created with a template, the unique string identifying
            that template.
        vcpuCount:
          type: number
          example: 24
          description: The number of virtual CPUs attached to a Pod.
        volumeEncrypted:
          type: boolean
          example: false
          description: >-
            Set to true if the local network volume of a Pod is encrypted. Can
            only be set when creating a Pod.
        volumeInGb:
          type: integer
          example: 20
          description: >-
            The amount of disk space, in gigabytes (GB), to allocate on the Pod
            volume for a Pod. The data on the Pod volume is persisted across Pod
            restarts. To persist data so that future Pods can access it, create
            a network volume and set networkVolumeId to attach it to the Pod.
        volumeMountPath:
          type: string
          example: /workspace
          description: >-
            If either a Pod volume or a network volume is attached to a Pod, the
            absolute path where the network volume is mounted in the filesystem.
    SavingsPlan:
      type: object
      properties:
        costPerHr:
          type: number
          example: 0.21
        endTime:
          type: string
          example: '2024-07-12T19:14:40.144Z'
        gpuTypeId:
          type: string
          example: NVIDIA GeForce RTX 4090
        id:
          type: string
          example: clkrb4qci0000mb09c7sualzo
        podId:
          type: string
          example: xedezhzb9la3ye
        startTime:
          type: string
          example: '2024-05-12T19:14:40.144Z'

````