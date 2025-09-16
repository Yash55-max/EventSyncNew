/**
 * Virtual Events Client - Revolutionary Event Management Platform
 * WebGL/WebXR powered immersive virtual events with VR/AR support
 */

class VirtualEventsClient {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.options = {
            enableVR: true,
            enableAR: true,
            enableSpatialAudio: true,
            quality: 'high',
            ...options
        };
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        this.virtualEventId = null;
        this.userId = null;
        this.avatar = null;
        this.participants = new Map();
        
        this.socketManager = null;
        this.audioManager = null;
        this.interactionManager = null;
        this.pollManager = null;
        this.streamManager = null;
        
        this.deviceCapabilities = {};
        this.vrSession = null;
        this.arSession = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Initialize Three.js scene
            await this.initializeScene();
            
            // Detect device capabilities
            this.detectCapabilities();
            
            // Initialize managers
            this.initializeManagers();
            
            // Setup event listeners
            this.setupEventListeners();
            
            console.log('Virtual Events Client initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize Virtual Events Client:', error);
        }
    }
    
    async initializeScene() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.Fog(0x404040, 10, 1000);
        
        // Setup camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 1.6, 5); // Human height
        
        // Setup renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            powerPreference: 'high-performance'
        });
        
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1;
        
        // Enable XR
        if (this.options.enableVR || this.options.enableAR) {
            this.renderer.xr.enabled = true;
        }
        
        // Setup controls
        this.controls = new THREE.PointerLockControls(this.camera, this.renderer.domElement);
        this.scene.add(this.controls.getObject());
        
        // Setup lighting
        this.setupLighting();
        
        // Setup physics
        await this.initializePhysics();
        
        // Start render loop
        this.startRenderLoop();
    }
    
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        
        // Directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -20;
        directionalLight.shadow.camera.right = 20;
        directionalLight.shadow.camera.top = 20;
        directionalLight.shadow.camera.bottom = -20;
        this.scene.add(directionalLight);
        
        // Point lights for atmosphere
        const pointLight1 = new THREE.PointLight(0x4080ff, 0.5, 30);
        pointLight1.position.set(-10, 5, -10);
        this.scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xff8040, 0.5, 30);
        pointLight2.position.set(10, 5, 10);
        this.scene.add(pointLight2);
    }
    
    async initializePhysics() {
        // Initialize Cannon.js physics world
        this.world = new CANNON.World();
        this.world.gravity.set(0, -9.82, 0);
        this.world.broadphase = new CANNON.NaiveBroadphase();
        this.world.solver.iterations = 10;
        
        // Ground physics body
        const groundShape = new CANNON.Plane();
        const groundBody = new CANNON.Body({ mass: 0 });
        groundBody.addShape(groundShape);
        groundBody.quaternion.setFromAxisAngle(new CANNON.Vec3(1, 0, 0), -Math.PI / 2);
        this.world.add(groundBody);
    }
    
    detectCapabilities() {
        this.deviceCapabilities = {
            webxr: 'xr' in navigator,
            webgl: this.renderer.capabilities.isWebGL2,
            vr: false,
            ar: false,
            spatialAudio: 'AudioContext' in window,
            gamepad: 'getGamepads' in navigator,
            deviceMotion: 'DeviceMotionEvent' in window,
            camera: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices
        };
        
        // Check WebXR support
        if (this.deviceCapabilities.webxr) {
            if ('requestSession' in navigator.xr) {
                navigator.xr.isSessionSupported('immersive-vr').then(supported => {
                    this.deviceCapabilities.vr = supported;
                });
                
                navigator.xr.isSessionSupported('immersive-ar').then(supported => {
                    this.deviceCapabilities.ar = supported;
                });
            }
        }
        
        console.log('Device capabilities:', this.deviceCapabilities);
    }
    
    initializeManagers() {
        // Socket manager for real-time communication
        this.socketManager = new VirtualSocketManager(this);
        
        // Audio manager for spatial audio
        this.audioManager = new SpatialAudioManager(this);
        
        // Interaction manager for UI elements
        this.interactionManager = new InteractionManager(this);
        
        // Poll manager for interactive polls
        this.pollManager = new PollManager(this);
        
        // Stream manager for live streaming
        this.streamManager = new StreamManager(this);
    }
    
    setupEventListeners() {
        // Resize handler
        window.addEventListener('resize', () => this.handleResize());
        
        // Keyboard controls
        document.addEventListener('keydown', (event) => this.handleKeyDown(event));
        document.addEventListener('keyup', (event) => this.handleKeyUp(event));
        
        // Mouse controls
        this.canvas.addEventListener('click', () => {
            if (!this.controls.isLocked) {
                this.controls.lock();
            }
        });
        
        // Touch controls for mobile
        this.setupTouchControls();
        
        // VR/AR button handlers
        this.setupXRButtons();
    }
    
    setupTouchControls() {
        let touchStartX, touchStartY;
        
        this.canvas.addEventListener('touchstart', (event) => {
            if (event.touches.length === 1) {
                touchStartX = event.touches[0].clientX;
                touchStartY = event.touches[0].clientY;
            }
        });
        
        this.canvas.addEventListener('touchmove', (event) => {
            event.preventDefault();
            
            if (event.touches.length === 1) {
                const deltaX = event.touches[0].clientX - touchStartX;
                const deltaY = event.touches[0].clientY - touchStartY;
                
                this.camera.rotation.y -= deltaX * 0.01;
                this.camera.rotation.x -= deltaY * 0.01;
                this.camera.rotation.x = Math.max(-Math.PI/2, Math.min(Math.PI/2, this.camera.rotation.x));
                
                touchStartX = event.touches[0].clientX;
                touchStartY = event.touches[0].clientY;
            }
        });
    }
    
    setupXRButtons() {
        const vrButton = document.getElementById('vr-button');
        const arButton = document.getElementById('ar-button');
        
        if (vrButton && this.deviceCapabilities.vr) {
            vrButton.style.display = 'block';
            vrButton.addEventListener('click', () => this.enterVR());
        }
        
        if (arButton && this.deviceCapabilities.ar) {
            arButton.style.display = 'block';
            arButton.addEventListener('click', () => this.enterAR());
        }
    }
    
    startRenderLoop() {
        const animate = () => {
            this.renderer.setAnimationLoop(animate);
            
            // Update physics
            this.world.step(1/60);
            
            // Update managers
            this.updateManagers();
            
            // Update avatar animation
            this.updateAvatar();
            
            // Update participants
            this.updateParticipants();
            
            // Render scene
            this.renderer.render(this.scene, this.camera);
        };
        
        animate();
    }
    
    updateManagers() {
        if (this.audioManager) this.audioManager.update();
        if (this.interactionManager) this.interactionManager.update();
        if (this.pollManager) this.pollManager.update();
        if (this.streamManager) this.streamManager.update();
    }
    
    async joinVirtualEvent(virtualEventId, userId, deviceInfo) {
        try {
            this.virtualEventId = virtualEventId;
            this.userId = userId;
            
            // Connect to socket
            await this.socketManager.connect(virtualEventId, userId);
            
            // Request to join virtual event
            const response = await fetch(`/api/virtual-events/${virtualEventId}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_info: deviceInfo || this.getDeviceInfo()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Load environment
                await this.loadEnvironment(data.environment);
                
                // Create avatar
                this.avatar = await this.createAvatar(data.avatar);
                
                // Initialize audio
                await this.audioManager.initialize();
                
                // Load initial state
                this.loadInitialState(data.initial_state);
                
                console.log('Successfully joined virtual event');
                return true;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Failed to join virtual event:', error);
            return false;
        }
    }
    
    async loadEnvironment(environmentConfig) {
        // Clear existing environment
        this.clearScene();
        
        const envType = environmentConfig.type;
        
        switch (envType) {
            case 'conference_hall':
                await this.loadConferenceHall(environmentConfig);
                break;
            case 'vr_world':
                await this.loadVRWorld(environmentConfig);
                break;
            case 'hackathon_space':
                await this.loadHackathonSpace(environmentConfig);
                break;
            default:
                await this.loadDefaultEnvironment(environmentConfig);
        }
        
        // Setup interactive elements
        this.setupInteractiveElements(environmentConfig.interactive_elements);
        
        // Apply lighting configuration
        this.applyLightingConfig(environmentConfig.lighting_config);
        
        // Setup audio zones
        this.audioManager.setupAudioZones(environmentConfig.audio_zones);
    }
    
    async loadConferenceHall(config) {
        // Create stage
        const stageGeometry = new THREE.BoxGeometry(10, 0.5, 5);
        const stageMaterial = new THREE.MeshLambertMaterial({ color: 0x8B4513 });
        const stage = new THREE.Mesh(stageGeometry, stageMaterial);
        stage.position.set(0, 0.25, -5);
        stage.castShadow = true;
        stage.receiveShadow = true;
        this.scene.add(stage);
        
        // Create seats
        await this.createSeatingArrangement(config.assets.seats);
        
        // Create screens
        await this.createScreens(config.assets.screens);
        
        // Create floor
        const floorGeometry = new THREE.PlaneGeometry(50, 50);
        const floorMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x999999,
            transparent: true,
            opacity: 0.8
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.scene.add(floor);
        
        // Add walls
        await this.createWalls();
    }
    
    async loadVRWorld(config) {
        // Create floating stage
        const stageGeometry = new THREE.CylinderGeometry(4, 4, 0.2, 16);
        const stageMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4444ff,
            metalness: 0.3,
            roughness: 0.4,
            emissive: 0x001122
        });
        const stage = new THREE.Mesh(stageGeometry, stageMaterial);
        stage.position.set(0, 5, 0);
        stage.castShadow = true;
        this.scene.add(stage);
        
        // Create holograms
        await this.createHolograms(config.assets.holograms);
        
        // Create portal gates
        await this.createPortals(config.assets.portal_gates);
        
        // Add particle effects
        this.createParticleEffects();
        
        // Create floating platforms
        await this.createFloatingPlatforms();
    }
    
    async loadHackathonSpace(config) {
        // Create team pods
        await this.createTeamPods(config.assets.team_pods);
        
        // Create code walls
        await this.createCodeWalls(config.assets.code_walls);
        
        // Create mentor stations
        await this.createMentorStations(config.assets.mentor_stations);
        
        // Add ambient tech lighting
        this.createTechLighting();
        
        // Create submission areas
        await this.createSubmissionAreas();
    }
    
    async createAvatar(avatarConfig) {
        const avatar = new Avatar(avatarConfig);
        await avatar.load();
        
        avatar.position.copy(this.camera.position);
        this.scene.add(avatar.mesh);
        
        return avatar;
    }
    
    setupInteractiveElements(elements) {
        elements.forEach(element => {
            const interactive = this.interactionManager.createElement(element);
            this.scene.add(interactive);
        });
    }
    
    applyLightingConfig(lightingConfig) {
        // Update existing lights based on configuration
        this.scene.traverse((object) => {
            if (object.isLight) {
                if (lightingConfig.ambient && object.isAmbientLight) {
                    object.color.setHex(lightingConfig.ambient.color.replace('#', '0x'));
                    object.intensity = lightingConfig.ambient.intensity;
                }
            }
        });
        
        // Add custom lighting
        if (lightingConfig.stage) {
            const stageLight = new THREE.SpotLight(
                lightingConfig.stage.color.replace('#', '0x'),
                lightingConfig.stage.intensity,
                30,
                Math.PI / 6
            );
            stageLight.position.set(0, 10, -5);
            stageLight.target.position.set(0, 0, -5);
            stageLight.castShadow = true;
            this.scene.add(stageLight);
            this.scene.add(stageLight.target);
        }
    }
    
    async enterVR() {
        if (!this.deviceCapabilities.vr) {
            console.warn('VR not supported on this device');
            return;
        }
        
        try {
            const session = await navigator.xr.requestSession('immersive-vr', {
                requiredFeatures: ['local-floor'],
                optionalFeatures: ['hand-tracking', 'bounded-floor']
            });
            
            this.vrSession = session;
            this.renderer.xr.setSession(session);
            
            // Setup VR controllers
            this.setupVRControllers();
            
            console.log('Entered VR mode');
            
        } catch (error) {
            console.error('Failed to enter VR:', error);
        }
    }
    
    async enterAR() {
        if (!this.deviceCapabilities.ar) {
            console.warn('AR not supported on this device');
            return;
        }
        
        try {
            const session = await navigator.xr.requestSession('immersive-ar', {
                requiredFeatures: ['local'],
                optionalFeatures: ['hit-test', 'plane-detection']
            });
            
            this.arSession = session;
            this.renderer.xr.setSession(session);
            
            // Setup AR features
            this.setupARFeatures();
            
            console.log('Entered AR mode');
            
        } catch (error) {
            console.error('Failed to enter AR:', error);
        }
    }
    
    setupVRControllers() {
        const controller1 = this.renderer.xr.getController(0);
        const controller2 = this.renderer.xr.getController(1);
        
        // Add controller models
        const controllerModelFactory = new THREE.XRControllerModelFactory();
        
        const controllerGrip1 = this.renderer.xr.getControllerGrip(0);
        controllerGrip1.add(controllerModelFactory.createControllerModel(controllerGrip1));
        this.scene.add(controllerGrip1);
        
        const controllerGrip2 = this.renderer.xr.getControllerGrip(1);
        controllerGrip2.add(controllerModelFactory.createControllerModel(controllerGrip2));
        this.scene.add(controllerGrip2);
        
        // Add interaction rays
        const geometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(0, 0, -1)
        ]);
        
        const line1 = new THREE.Line(geometry, new THREE.LineBasicMaterial({color: 0xff0000}));
        line1.name = 'controller-ray';
        line1.scale.z = 10;
        controller1.add(line1.clone());
        
        const line2 = new THREE.Line(geometry, new THREE.LineBasicMaterial({color: 0x0000ff}));
        line2.name = 'controller-ray';
        line2.scale.z = 10;
        controller2.add(line2.clone());
        
        this.scene.add(controller1);
        this.scene.add(controller2);
        
        // Setup controller event listeners
        controller1.addEventListener('selectstart', () => this.onControllerSelect(controller1));
        controller2.addEventListener('selectstart', () => this.onControllerSelect(controller2));
    }
    
    onControllerSelect(controller) {
        // Handle VR controller interactions
        const intersections = this.interactionManager.getControllerIntersections(controller);
        
        if (intersections.length > 0) {
            const intersection = intersections[0];
            this.interactionManager.handleControllerInteraction(intersection);
        }
    }
    
    updateAvatar() {
        if (this.avatar) {
            // Update avatar position based on camera
            const cameraWorldPosition = new THREE.Vector3();
            this.camera.getWorldPosition(cameraWorldPosition);
            
            this.avatar.updatePosition(cameraWorldPosition);
            this.avatar.updateAnimation();
            
            // Send position update to server
            if (this.socketManager) {
                this.socketManager.sendPositionUpdate(
                    cameraWorldPosition.toArray(),
                    [this.camera.rotation.x, this.camera.rotation.y, this.camera.rotation.z]
                );
            }
        }
    }
    
    updateParticipants() {
        this.participants.forEach((participant, userId) => {
            participant.update();
        });
    }
    
    addParticipant(participantData) {
        const participant = new RemoteParticipant(participantData);
        this.participants.set(participantData.user_id, participant);
        this.scene.add(participant.mesh);
        
        console.log(`Added participant: ${participantData.username}`);
    }
    
    removeParticipant(userId) {
        const participant = this.participants.get(userId);
        if (participant) {
            this.scene.remove(participant.mesh);
            participant.dispose();
            this.participants.delete(userId);
            
            console.log(`Removed participant: ${userId}`);
        }
    }
    
    updateParticipantPosition(userId, position, rotation) {
        const participant = this.participants.get(userId);
        if (participant) {
            participant.updatePosition(position);
            participant.updateRotation(rotation);
        }
    }
    
    handleResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    handleKeyDown(event) {
        switch (event.code) {
            case 'KeyW':
            case 'ArrowUp':
                this.moveForward = true;
                break;
            case 'KeyS':
            case 'ArrowDown':
                this.moveBackward = true;
                break;
            case 'KeyA':
            case 'ArrowLeft':
                this.moveLeft = true;
                break;
            case 'KeyD':
            case 'ArrowRight':
                this.moveRight = true;
                break;
            case 'Space':
                this.jump();
                event.preventDefault();
                break;
        }
    }
    
    handleKeyUp(event) {
        switch (event.code) {
            case 'KeyW':
            case 'ArrowUp':
                this.moveForward = false;
                break;
            case 'KeyS':
            case 'ArrowDown':
                this.moveBackward = false;
                break;
            case 'KeyA':
            case 'ArrowLeft':
                this.moveLeft = false;
                break;
            case 'KeyD':
            case 'ArrowRight':
                this.moveRight = false;
                break;
        }
    }
    
    jump() {
        if (this.canJump) {
            this.velocity.y += 10;
            this.canJump = false;
        }
    }
    
    getDeviceInfo() {
        return {
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            device_pixel_ratio: window.devicePixelRatio,
            webgl_version: this.renderer.capabilities.isWebGL2 ? '2.0' : '1.0',
            max_texture_size: this.renderer.capabilities.maxTextureSize,
            capabilities: this.deviceCapabilities
        };
    }
    
    clearScene() {
        // Remove all non-essential objects from scene
        const objectsToRemove = [];
        
        this.scene.traverse((object) => {
            if (object !== this.camera && !object.isLight) {
                objectsToRemove.push(object);
            }
        });
        
        objectsToRemove.forEach(object => {
            this.scene.remove(object);
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(material => material.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });
    }
    
    dispose() {
        // Clean up resources
        this.clearScene();
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.socketManager) {
            this.socketManager.disconnect();
        }
        
        if (this.audioManager) {
            this.audioManager.dispose();
        }
        
        if (this.vrSession) {
            this.vrSession.end();
        }
        
        if (this.arSession) {
            this.arSession.end();
        }
    }
}

// Export for use in other modules
window.VirtualEventsClient = VirtualEventsClient;