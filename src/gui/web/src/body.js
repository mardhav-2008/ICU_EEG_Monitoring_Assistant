import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { clone as cloneSkinned } from "three/addons/utils/SkeletonUtils.js";

// -----------------------------------------------------------------------------
// DOM and Three.js scene
// -----------------------------------------------------------------------------

const mount = document.getElementById("stage");
const hint = document.getElementById("hint");

if (!mount) throw new Error("Missing #stage element in index.html");

function setHint(message) {
    if (hint) hint.textContent = message;
}

const scene = new THREE.Scene();
// Keep the scene transparent so the layered dark-glass CSS backdrop is visible.
scene.background = null;
scene.fog = new THREE.FogExp2(0x0b171b, 0.025);

const camera = new THREE.PerspectiveCamera(
    35,
    Math.max(1, mount.clientWidth) / Math.max(1, mount.clientHeight),
    0.1,
    100
);
camera.position.set(0, 0, 6);

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
});
renderer.setClearColor(0x000000, 0);
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
mount.appendChild(renderer.domElement);

// Soft sage and cool fill lighting for the glass-like environment.
scene.add(new THREE.HemisphereLight(0xd9eee0, 0x14201e, 1.65));

const keyLight = new THREE.DirectionalLight(0xe5f5e8, 2.0);
keyLight.position.set(4, 6, 5);
scene.add(keyLight);

const fillLight = new THREE.PointLight(0x8bb99d, 8, 20);
fillLight.position.set(-4, 1, -3);
scene.add(fillLight);

// Shared rotation root.
const worldRoot = new THREE.Group();
scene.add(worldRoot);

const anatomyRoot = new THREE.Group();
anatomyRoot.name = "AnatomicalMuscleDisplay";
worldRoot.add(anatomyRoot);

const anatomyReferenceRoot = new THREE.Group();
anatomyReferenceRoot.name = "InvisibleAnatomicalSelectionReference";
worldRoot.add(anatomyReferenceRoot);

const hologramRoot = new THREE.Group();
hologramRoot.name = "HologramDisplay";
worldRoot.add(hologramRoot);

// -----------------------------------------------------------------------------
// State
// -----------------------------------------------------------------------------

const loader = new GLTFLoader();
loader.setMeshoptDecoder(MeshoptDecoder);

let bridge = null;
let patientSex = "male";
let visualStyle = "hologram";
let anatomyReferenceMeshes = [];

let hologramModels = { male: null, female: null };
let activeDisplayModel = null;
let dragging = false;
let dragged = false;
let pointerStart = { x: 0, y: 0 };
let previousPointer = { x: 0, y: 0 };

// -----------------------------------------------------------------------------
// Model helpers
// -----------------------------------------------------------------------------

function normalizeModel(root, targetHeight = 3.0) {
    root.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(root);
    if (bounds.isEmpty()) throw new Error(`Cannot normalize empty model: ${root.name}`);

    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z);
    if (!Number.isFinite(maxDimension) || maxDimension <= 0) {
        throw new Error(`Invalid dimensions for model: ${root.name}`);
    }

    root.position.sub(center);
    root.scale.setScalar(targetHeight / maxDimension);
    root.updateMatrixWorld(true);
}

function frameModel(root) {
    if (!root) return;
    root.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(root);
    if (bounds.isEmpty()) return;

    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    const verticalFov = THREE.MathUtils.degToRad(camera.fov);
    const horizontalFov = 2 * Math.atan(
        Math.tan(verticalFov / 2) * camera.aspect
    );
    const verticalDistance = size.y / (2 * Math.tan(verticalFov / 2));
    const horizontalDistance = size.x / (2 * Math.tan(horizontalFov / 2));
    const distance = Math.max(verticalDistance, horizontalDistance, size.z) * 2.0;

    camera.position.set(center.x, center.y, center.z + Math.max(4, distance));
    camera.lookAt(center);
}

function findNamedNode(root, names) {
    const wantedNames = new Set(names.map(name => name.trim().toLowerCase()));
    let result = null;
    root.traverse(object => {
        if (!result && object.name && wantedNames.has(object.name.trim().toLowerCase())) {
            result = object;
        }
    });
    return result;
}

function findStructureName(mesh, modelRoot) {
    let current = mesh;
    while (current && current !== modelRoot) {
        if (current.name && !/^mesh(?:[_\s-]?\d+)?$/i.test(current.name)) return current.name;
        current = current.parent;
    }
    return mesh.name || "Unknown structure";
}

// -----------------------------------------------------------------------------
// Anatomical model
// -----------------------------------------------------------------------------

function showFullAnatomy(model) {
    model.traverse(object => { object.visible = true; });
}

function makeInvisibleRaycastReference(model) {
    model.traverse(object => {
        if (!object.isMesh) return;
        const makeInvisibleMaterial = material => {
            const invisible = material.clone();
            invisible.transparent = true;
            invisible.opacity = 0;
            invisible.colorWrite = false;
            invisible.depthWrite = false;
            invisible.depthTest = false;
            return invisible;
        };
        object.material = Array.isArray(object.material)
            ? object.material.map(makeInvisibleMaterial)
            : makeInvisibleMaterial(object.material);
        object.visible = true;
        object.userData.isAnatomyReference = true;
    });
}

async function loadAnatomy(sex) {
    setHint(`LOADING ${sex.toUpperCase()} ANATOMICAL MODEL...`);
    const gltf = await loader.loadAsync(`./assets/anatomy-${sex}.glb`);
    const displayModel = gltf.scene;
    const referenceModel = gltf.scene.clone(true);

    showFullAnatomy(displayModel);
    normalizeModel(displayModel);
    normalizeModel(referenceModel);

    anatomyRoot.clear();
    anatomyReferenceRoot.clear();
    anatomyReferenceMeshes = [];
    anatomyRoot.add(displayModel);

    makeInvisibleRaycastReference(referenceModel);
    anatomyReferenceRoot.add(referenceModel);

    referenceModel.traverse(object => {
        if (!object.isMesh) return;
        object.userData.structureKey = findStructureName(object, referenceModel);
        anatomyReferenceMeshes.push(object);
    });

    if (visualStyle === "stylized") setActiveDisplay(anatomyRoot, displayModel);
}

// -----------------------------------------------------------------------------
// Hologram model
// -----------------------------------------------------------------------------

function createHologramMaterial() {
    return new THREE.MeshBasicMaterial({
        color: 0x9ad8b0,
        wireframe: true,
        transparent: true,
        opacity: 0.72,
        depthWrite: false,
        side: THREE.DoubleSide
    });
}

function applyHologramMaterial(root) {
    root.traverse(object => {
        if (!object.isMesh) return;
        object.material = Array.isArray(object.material)
            ? object.material.map(() => createHologramMaterial())
            : createHologramMaterial();
    });
}

async function loadHologramModels() {
    setHint("LOADING MALE/FEMALE HOLOGRAM MODELS...");
    const gltf = await loader.loadAsync("./assets/HumanModels.glb");
    const nodes = gltf.parser.json.nodes || [];
    const maleIndex = nodes.findIndex(node => node.name === "Man (Rig)");
    const femaleIndex = nodes.findIndex(node => node.name === "Woman (Rig)");
    if (maleIndex === -1 || femaleIndex === -1) {
        throw new Error("Rigged character nodes are missing from GLB metadata.");
    }

    const [maleNode, femaleNode] = await Promise.all([
        gltf.parser.getDependency("node", maleIndex),
        gltf.parser.getDependency("node", femaleIndex)
    ]);
    if (!maleNode || !femaleNode) throw new Error("Could not resolve rigged GLB nodes.");

    hologramRoot.clear();
    function prepareCharacter(node, sex) {
        const character = cloneSkinned(node);
        character.name = `${sex}Hologram`;
        applyHologramMaterial(character);
        normalizeModel(character);
        return character;
    }

    hologramModels.male = prepareCharacter(maleNode, "Male");
    hologramModels.female = prepareCharacter(femaleNode, "Female");
    hologramRoot.add(hologramModels.male, hologramModels.female);
    selectHologramSex();
}

function selectHologramSex() {
    for (const [sex, model] of Object.entries(hologramModels)) {
        if (model) model.visible = sex === patientSex;
    }
}

function setActiveDisplay(root, modelToFrame) {
    anatomyRoot.visible = root === anatomyRoot;
    hologramRoot.visible = root === hologramRoot;
    anatomyReferenceRoot.visible = true;
    activeDisplayModel = modelToFrame || null;
    if (activeDisplayModel) frameModel(activeDisplayModel);
}

function switchVisualStyle(style) {
    visualStyle = style === "stylized" ? "stylized" : "hologram";
    if (visualStyle === "stylized") {
        const model = anatomyRoot.children[0];
        if (model) {
            setActiveDisplay(anatomyRoot, model);
            setHint("ANATOMICAL MODEL READY · SELECT A STRUCTURE");
        } else setHint("ANATOMICAL MODEL NOT READY");
        return;
    }

    selectHologramSex();
    const selectedModel = hologramModels[patientSex];
    if (selectedModel) {
        setActiveDisplay(hologramRoot, selectedModel);
        setHint("HOLOGRAM READY · SELECT THE BRAIN");
    } else setHint("HOLOGRAM MODEL NOT READY");
}

window.setVisualStyle = switchVisualStyle;
window.setPatientSex = async sex => {
    const nextSex = sex === "female" ? "female" : "male";
    if (nextSex === patientSex) return;
    patientSex = nextSex;
    try {
        await loadAnatomy(patientSex);
        selectHologramSex();
        switchVisualStyle(visualStyle);
    } catch (error) {
        console.error("[PATIENT] Model switch failed:", error);
        setHint("PATIENT MODEL SWITCH FAILED · CHECK CONSOLE");
    }
};

// -----------------------------------------------------------------------------
// Qt bridge
// -----------------------------------------------------------------------------

if (window.qt && window.QWebChannel) {
    new QWebChannel(qt.webChannelTransport, channel => {
        bridge = channel.objects.backend;
        console.log("[WEB] Python bridge connected.");
    });
}

// -----------------------------------------------------------------------------
// Anatomical picking
// -----------------------------------------------------------------------------

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const brainStructures = new Set(["brain", "cerebellum", "brainstem", "cranial_nerves"]);

function selectAtPointer(event) {
    if (!anatomyReferenceMeshes.length) return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);

    const intersections = raycaster.intersectObjects(anatomyReferenceMeshes, false);
    if (!intersections.length) return;

    const brainHit = intersections.find(hit => {
        const key = (hit.object.userData.structureKey || "").toLowerCase();
        return brainStructures.has(key);
    });
    const selectedHit = brainHit || intersections[0];
    const structure = selectedHit.object.userData.structureKey || "Unknown structure";
    const isBrain = brainStructures.has(structure.toLowerCase());

    if (isBrain) {
        setHint("BRAIN SELECTED · EEG MONITORING AVAILABLE");
        if (bridge) bridge.selectRegion("brain");
    } else {
        setHint(`SELECTED: ${structure.toUpperCase()}`);
        if (bridge) bridge.selectRegion(structure);
    }
}

renderer.domElement.addEventListener("pointerdown", event => {
    dragging = true;
    dragged = false;
    pointerStart = { x: event.clientX, y: event.clientY };
    previousPointer = { x: event.clientX, y: event.clientY };
    renderer.domElement.setPointerCapture(event.pointerId);
});

renderer.domElement.addEventListener("pointermove", event => {
    if (!dragging) return;
    const deltaX = event.clientX - previousPointer.x;
    const deltaY = event.clientY - previousPointer.y;
    const totalMovement = Math.abs(event.clientX - pointerStart.x) +
        Math.abs(event.clientY - pointerStart.y);
    if (totalMovement > 4) dragged = true;
    worldRoot.rotation.y += deltaX * 0.006;
    worldRoot.rotation.x = THREE.MathUtils.clamp(
        worldRoot.rotation.x + deltaY * 0.003, -0.25, 0.25
    );
    previousPointer = { x: event.clientX, y: event.clientY };
});

renderer.domElement.addEventListener("pointerup", event => {
    dragging = false;
    if (!dragged) selectAtPointer(event);
});
renderer.domElement.addEventListener("pointercancel", () => { dragging = false; });

// -----------------------------------------------------------------------------
// Resize and render
// -----------------------------------------------------------------------------

function resizeRenderer() {
    const width = Math.max(1, mount.clientWidth);
    const height = Math.max(1, mount.clientHeight);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
    if (activeDisplayModel) frameModel(activeDisplayModel);
}
new ResizeObserver(resizeRenderer).observe(mount);

function animate() {
    requestAnimationFrame(animate);
    if (!dragging) worldRoot.rotation.y += 0.0006;
    renderer.render(scene, camera);
}
resizeRenderer();
animate();

async function initializeModels() {
    setHint("LOADING ANATOMY AND HOLOGRAM MODELS...");
    try {
        await Promise.all([loadAnatomy(patientSex), loadHologramModels()]);
        switchVisualStyle(visualStyle);
        setHint("3D MODELS READY · SELECT THE BRAIN");
    } catch (error) {
        console.error("[3D] Model initialization failed:", error);
        setHint("MODEL LOADING FAILED · CHECK WEB CONSOLE");
    }
}
initializeModels();
