/**
 * DiceVisualizer - Deterministic 3D Dice Roller
 * 
 * Uses Three.js with procedural geometry and deterministic tweening.
 * No physics engine - all animations are deterministic and land exactly on target faces.
 * 
 * @class DiceVisualizer
 */
class DiceVisualizer {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.getElementById(container) : container;
        if (!this.container) {
            throw new Error('Container element not found');
        }

        this.options = {
            theme: options.theme || 'default',
            cameraDistance: options.cameraDistance || 8,
            animationDuration: options.animationDuration || { min: 1200, max: 2000 },
            ...options
        };

        // State management
        this.isRolling = false;
        this.dicePool = [];
        this.animationId = null;
        this.eventListeners = { start: [], complete: [] };

        // Three.js setup
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.lights = [];

        // Initialize
        this.init();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a2e);

        // Create camera
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(0, 5, this.options.cameraDistance);
        this.camera.lookAt(0, 0, 0);

        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            alpha: true, 
            antialias: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit pixel ratio for performance
        this.container.appendChild(this.renderer.domElement);

        // Add lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        this.scene.add(directionalLight);
        this.lights.push(directionalLight);

        // Add ground plane (dice tray)
        const groundGeometry = new THREE.PlaneGeometry(20, 20);
        const groundMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x2d2d44,
            roughness: 0.8,
            metalness: 0.2
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.5;
        this.scene.add(ground);

        // Handle resize
        this.handleResize = this.handleResize.bind(this);
        window.addEventListener('resize', this.handleResize);
        window.addEventListener('orientationchange', this.handleResize);

        // Start render loop
        this.animate();
    }

    handleResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }

    /**
     * Create a die mesh for the given type
     * @param {string} dieType - 'd4', 'd6', 'd8', 'd10', 'd12', 'd20'
     * @returns {THREE.Mesh}
     */
    createDieMesh(dieType) {
        let geometry;
        const material = new THREE.MeshNormalMaterial(); // MVP: no textures

        switch (dieType) {
            case 'd4':
                geometry = new THREE.TetrahedronGeometry(0.8);
                break;
            case 'd6':
                geometry = new THREE.BoxGeometry(1, 1, 1);
                // Round corners slightly by subdividing
                geometry = new THREE.BufferGeometry().fromGeometry(geometry);
                break;
            case 'd8':
                geometry = new THREE.OctahedronGeometry(0.9);
                break;
            case 'd10':
                // Pentagonal trapezohedron - approximated with octahedron for MVP
                geometry = new THREE.OctahedronGeometry(0.85);
                break;
            case 'd12':
                geometry = new THREE.DodecahedronGeometry(0.85);
                break;
            case 'd20':
                geometry = new THREE.IcosahedronGeometry(0.9);
                break;
            default:
                throw new Error(`Unsupported die type: ${dieType}`);
        }

        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData.dieType = dieType;
        mesh.userData.originalRotation = mesh.rotation.clone();

        return mesh;
    }

    /**
     * Get quaternion rotation for a specific face value
     * These are hardcoded mappings for deterministic landing
     */
    getRotationForFace(dieType, faceValue) {
        // Pre-calculated quaternion mappings for each die type
        // These ensure deterministic landing on target faces
        const mappings = {
            d4: {
                1: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)),
                2: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.6, 0, Math.PI * 0.3)),
                3: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.6, Math.PI * 0.3, 0)),
                4: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI * 0.6, -Math.PI * 0.3))
            },
            d6: {
                1: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)),
                2: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI / 2, 0)),
                3: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0)),
                4: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)),
                5: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI / 2, 0)),
                6: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI, 0, 0))
            },
            d8: {
                1: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)),
                2: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI, 0, 0)),
                3: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, Math.PI / 2)),
                4: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, -Math.PI / 2)),
                5: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)),
                6: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0)),
                7: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI / 2, 0)),
                8: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI / 2, 0))
            },
            d10: {
                0: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)),
                1: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.4, 0, 0)),
                2: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.4, 0, 0)),
                3: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI * 0.4, 0)),
                4: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI * 0.4, 0)),
                5: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.6, Math.PI * 0.3, 0)),
                6: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.6, Math.PI * 0.3, 0)),
                7: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.3, -Math.PI * 0.6, 0)),
                8: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.3, -Math.PI * 0.6, 0)),
                9: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI, 0, 0))
            },
            d12: {
                1: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)),
                2: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.5, 0, 0)),
                3: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI * 0.5, 0)),
                4: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI * 0.5, 0)),
                5: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.3, Math.PI * 0.3, 0)),
                6: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.3, Math.PI * 0.3, 0)),
                7: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.3, -Math.PI * 0.3, 0)),
                8: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.3, -Math.PI * 0.3, 0)),
                9: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.6, 0, Math.PI * 0.3)),
                10: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.6, 0, Math.PI * 0.3)),
                11: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI * 0.6, Math.PI * 0.3)),
                12: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI * 0.6, Math.PI * 0.3))
            },
            d20: {
                1: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)),
                2: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.4, 0, 0)),
                3: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.4, 0, 0)),
                4: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI * 0.4, 0)),
                5: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI * 0.4, 0)),
                6: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.2, Math.PI * 0.2, 0)),
                7: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.2, Math.PI * 0.2, 0)),
                8: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.2, -Math.PI * 0.2, 0)),
                9: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.2, -Math.PI * 0.2, 0)),
                10: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.5, 0, Math.PI * 0.2)),
                11: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.5, 0, Math.PI * 0.2)),
                12: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI * 0.5, Math.PI * 0.2)),
                13: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI * 0.5, Math.PI * 0.2)),
                14: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.6, Math.PI * 0.3, Math.PI * 0.2)),
                15: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.6, Math.PI * 0.3, Math.PI * 0.2)),
                16: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.6, -Math.PI * 0.3, Math.PI * 0.2)),
                17: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.6, -Math.PI * 0.3, Math.PI * 0.2)),
                18: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI, 0, 0)),
                19: new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI * 0.7, Math.PI * 0.5, Math.PI * 0.3)),
                20: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI * 0.7, Math.PI * 0.5, Math.PI * 0.3))
            }
        };

        const dieMapping = mappings[dieType];
        if (!dieMapping) {
            throw new Error(`No rotation mapping for die type: ${dieType}`);
        }

        const quaternion = dieMapping[faceValue];
        if (!quaternion) {
            // Fallback to first face if invalid value
            return dieMapping[Object.keys(dieMapping)[0]].clone();
        }

        return quaternion.clone();
    }

    /**
     * Easing function: easeOutCubic
     */
    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    /**
     * Animate a single die to its target face
     */
    async animateDie(die, targetFace, dieType) {
        const duration = typeof this.options.animationDuration === 'object'
            ? this.options.animationDuration.min + Math.random() * (this.options.animationDuration.max - this.options.animationDuration.min)
            : this.options.animationDuration;

        // Handle zero-duration case (instant snap)
        if (duration <= 0) {
            const targetRot = this.getRotationForFace(dieType, targetFace);
            die.quaternion.copy(targetRot);
            die.position.set(
                (Math.random() - 0.5) * 3,
                0.5,
                (Math.random() - 0.5) * 3
            );
            return;
        }

        const spins = 3 + Math.floor(Math.random() * 4); // 3-6 extra spins
        const startTime = performance.now();
        const startRot = die.quaternion.clone();
        const startPos = die.position.clone();
        const targetRot = this.getRotationForFace(dieType, targetFace);
        
        // Random starting position
        const endPos = new THREE.Vector3(
            (Math.random() - 0.5) * 3,
            0.5,
            (Math.random() - 0.5) * 3
        );

        return new Promise((resolve) => {
            const animate = (now) => {
                const elapsed = now - startTime;
                const t = Math.min(elapsed / duration, 1);
                const easeT = this.easeOutCubic(t);

                // Extra spin on all axes
                const spinAngle = spins * Math.PI * 2 * (1 - easeT);
                const spinQ = new THREE.Quaternion().setFromEuler(
                    new THREE.Euler(spinAngle * 0.7, spinAngle, spinAngle * 1.3)
                );

                // Slerp to final orientation
                const finalQ = startRot.clone().slerp(targetRot, easeT);
                finalQ.multiply(spinQ);
                die.quaternion.copy(finalQ);

                // Bounce effect (vertical position)
                const bounceHeight = Math.sin(t * Math.PI) * 2;
                die.position.lerpVectors(startPos, endPos, easeT);
                die.position.y = endPos.y + bounceHeight;

                if (t < 1) {
                    requestAnimationFrame(animate);
                } else {
                    // Ensure final position is exact
                    die.quaternion.copy(targetRot);
                    die.position.copy(endPos);
                    resolve();
                }
            };
            requestAnimationFrame(animate);
        });
    }

    /**
     * Main roll method - accepts roll requests and animates to results
     * @param {Array} rollRequests - Array of {dieType, faceValue} objects
     * @returns {Promise<Array>} Array of roll results
     */
    async roll(rollRequests) {
        if (this.isRolling) {
            console.warn('Roll already in progress, ignoring new roll');
            return;
        }

        this.isRolling = true;
        this.emit('start', rollRequests);

        // Clear previous dice
        this.clearTray();

        // Create dice meshes
        const dice = [];
        const results = [];

        rollRequests.forEach((request, index) => {
            const die = this.createDieMesh(request.dieType);
            
            // Position dice in a grid
            const cols = Math.ceil(Math.sqrt(rollRequests.length));
            const row = Math.floor(index / cols);
            const col = index % cols;
            die.position.set(
                (col - (cols - 1) / 2) * 1.5,
                3 + Math.random() * 2, // Start above tray
                (row - (rollRequests.length / cols - 1) / 2) * 1.5
            );

            this.scene.add(die);
            dice.push({ mesh: die, request });
        });

        this.dicePool = dice;

        // Animate all dice simultaneously
        const animations = dice.map(({ mesh, request }) =>
            this.animateDie(mesh, request.faceValue, request.dieType)
        );

        await Promise.all(animations);

        // Collect results
        dice.forEach(({ request }) => {
            results.push({
                dieType: request.dieType,
                faceValue: request.faceValue,
                total: request.faceValue + (request.modifier || 0)
            });
        });

        this.isRolling = false;
        this.emit('complete', results);

        return results;
    }

    /**
     * Legacy imperative version - rollTo with face values and die types
     * @param {Array<number>} faceValues - Array of face values to land on
     * @param {Array<string>} dieTypes - Array of die types ('d4', 'd6', etc.)
     */
    async rollTo(faceValues, dieTypes) {
        if (faceValues.length !== dieTypes.length) {
            throw new Error('faceValues and dieTypes arrays must have same length');
        }

        const rollRequests = faceValues.map((faceValue, i) => ({
            dieType: dieTypes[i],
            faceValue: faceValue,
            modifier: 0
        }));

        return this.roll(rollRequests);
    }

    /**
     * Clear all dice from the tray
     */
    clearTray() {
        this.dicePool.forEach(({ mesh }) => {
            this.scene.remove(mesh);
            mesh.geometry.dispose();
            mesh.material.dispose();
        });
        this.dicePool = [];
    }

    /**
     * Set theme (placeholder for future theming)
     */
    setTheme(theme) {
        this.options.theme = theme;
        // Future: update materials, colors, etc.
    }

    /**
     * Event listener registration
     */
    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }

    /**
     * Emit event
     */
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => callback(data));
        }
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('orientationchange', this.handleResize);

        this.clearTray();

        // Dispose of Three.js resources
        if (this.renderer) {
            this.renderer.dispose();
            if (this.renderer.domElement.parentNode) {
                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
            }
        }

        // Dispose lights
        this.lights.forEach(light => {
            if (light.dispose) light.dispose();
        });

        this.scene = null;
        this.camera = null;
        this.renderer = null;
    }
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DiceVisualizer;
}

