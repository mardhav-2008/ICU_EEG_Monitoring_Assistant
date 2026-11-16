
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { clone as cloneSkinned } from "three/addons/utils/SkeletonUtils.js";

// -----------------------------------------------------------------------------
// DOM and Three.js scene
// -----------------------------------------------------------------------------

const mount = document.getElementById("stage");
const hint = document.getElementById("hint");

if (!mount) {
    throw new Error("Missing #stage element in index.html");
}

function setHint(message) {
    if (hint) hint.textContent = message;
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07131a);
scene.fog = new THREE.Fog(0x07131a, 12, 38);

const camera = new THREE.PerspectiveCamera(
    35,
    Math.max(1, mount.clientWidth) / Math.max(1, mount.clientHeight),
    0.1,
    100
);
camera.position.set(0, 0, 6);

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: false
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
mount.appendChild(renderer.domElement);

// Lighting for original anatomical materials.
scene.add(new THREE.HemisphereLight(0xd9fff8, 0x14252c, 1.8));

const keyLight = new THREE.DirectionalLight(0xffffff, 2.0);
keyLight.position.set(4, 6, 5);
scene.add(keyLight);

const fillLight = new THREE.PointLight(0x31d9c8, 10, 20);
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

let hologramModels = {
    male: null,
    female: null
};

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

    if (bounds.isEmpty()) {
        throw new Error(`Cannot normalize empty model: ${root.name}`);
    }

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

    if (bounds.isEmpty()) {
        console.warn("[CAMERA] Cannot frame an empty model.");
        return;
    }

    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());

    const verticalFov = THREE.MathUtils.degToRad(camera.fov);

    const horizontalFov = 2 * Math.atan(
        Math.tan(verticalFov / 2) * camera.aspect
    );

    const verticalDistance =
        size.y / (2 * Math.tan(verticalFov / 2));

    const horizontalDistance =
        size.x / (2 * Math.tan(horizontalFov / 2));

    // Extra breathing room for different male/female proportions.
    const distance = Math.max(
        verticalDistance,
        horizontalDistance,
        size.z
    ) * 2.0;

    camera.position.set(
        center.x,
        center.y,
        center.z + Math.max(4, distance)
    );

    camera.lookAt(center);

    console.log("[CAMERA] Model framed:", {
        width: size.x,
        height: size.y,
        depth: size.z,
        distance
    });
}

function findNamedNode(root, names) {
    const wantedNames = new Set(
        names.map(name => name.trim().toLowerCase())
    );

    let result = null;

    root.traverse(object => {
        if (
            !result &&
            object.name &&
            wantedNames.has(object.name.trim().toLowerCase())
        ) {
            result = object;
        }
    });

    return result;
}

function findStructureName(mesh, modelRoot) {
    let current = mesh;

    while (current && current !== modelRoot) {
        if (
            current.name &&
            !/^mesh(?:[_\s-]?\d+)?$/i.test(current.name)
        ) {
            return current.name;
        }

        current = current.parent;
    }

    return mesh.name || "Unknown structure";
}

// -----------------------------------------------------------------------------
// Anatomical model: show ONLY the original muscle layer
// -----------------------------------------------------------------------------

function isolateMuscleLayer(model) {
    const musclesGroup = findNamedNode(model, ["muscles"]);

    if (!musclesGroup) {
        console.error(
            "[ANATOMY] Could not find a group named 'muscles'."
        );

        console.error("[ANATOMY] Named nodes in this file:");

        model.traverse(object => {
            if (object.name) {
                console.log(
                    `[ANATOMY NODE] ${object.name} (${object.type})`
                );
            }
        });

        throw new Error(
            "The anatomical GLB does not contain a 'muscles' group."
        );
    }

    // Hide everything first.
    model.traverse(object => {
        object.visible = false;
    });

    // Make the muscle group's ancestors visible.
    let ancestor = musclesGroup;

    while (ancestor) {
        ancestor.visible = true;

        if (ancestor === model) break;

        ancestor = ancestor.parent;
    }

    // Restore visibility inside the muscle group only.
    musclesGroup.traverse(object => {
        object.visible = true;
    });

    console.log("[ANATOMY] Showing original muscle meshes only.");
}

function showFullAnatomy(model) {
    // Restore visibility of every anatomical structure,
    // including skin, muscles, skeleton, organs, vessels and nerves.
    model.traverse(object => {
        object.visible = true;
    });

    console.log("[ANATOMY] Full anatomical model with skin enabled.");
}

// Keep the full anatomical model invisible but raycastable.
// Do not set visible=false because Three.js raycasting skips invisible objects.
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
    setHint(`LOADING ${sex.toUpperCase()} MUSCLE MODEL...`);

    const url = `./assets/anatomy-${sex}.glb`;

    console.log(`[ANATOMY] Loading ${url}`);

    const gltf = await loader.loadAsync(url);

    console.log("========== HUMAN MODELS GLB ==========");

    gltf.scene.traverse(object => {
        if (object.name) {
            console.log(
                `[GLB] ${object.name} | ${object.type} | ` +
                `Mesh: ${object.isMesh} | ` +
                `Skinned: ${object.isSkinnedMesh}`
            );
        }
    });

    console.log("======================================");

    // Separate clones for display and anatomical selection.
    const displayModel = gltf.scene;
    const referenceModel = gltf.scene.clone(true);

    // isolateMuscleLayer(displayModel);
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

        object.userData.structureKey = findStructureName(
            object,
            referenceModel
        );

        anatomyReferenceMeshes.push(object);
    });

    console.log(
        `[ANATOMY] ${sex} model loaded. ` +
        `${anatomyReferenceMeshes.length} reference meshes available.`
    );

    if (visualStyle === "stylized") {
        setActiveDisplay(anatomyRoot, displayModel);
    }
}

// -----------------------------------------------------------------------------
// Hologram model: rigged male/female GLB
// -----------------------------------------------------------------------------

function createHologramMaterial() {
    return new THREE.MeshBasicMaterial({
        color: 0x62ffe5,
        wireframe: true,
        transparent: true,
        opacity: 0.78,
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

function isolateCharacterScene(sceneClone, characterNodeName) {
    const characterNode = findNamedNode(
        sceneClone,
        [characterNodeName]
    );

    if (!characterNode) {
        throw new Error(
            `Could not find character node '${characterNodeName}'`
        );
    }

    // Hide all nodes first.
    sceneClone.traverse(object => {
        object.visible = false;
    });

    // Show the target node's parent chain.
    let ancestor = characterNode;

    while (ancestor) {
        ancestor.visible = true;

        if (ancestor === sceneClone) break;

        ancestor = ancestor.parent;
    }

    // Show descendants of the selected character.
    characterNode.traverse(object => {
        object.visible = true;
    });

    return characterNode;
}

async function loadHologramModels() {
    setHint("LOADING MALE/FEMALE HOLOGRAM MODELS...");

    const url = "./assets/HumanModels.glb";
    console.log(`[HOLOGRAM] Loading ${url}`);

    const gltf = await loader.loadAsync(url);

    // Read the original glTF JSON metadata.
    const nodes = gltf.parser.json.nodes || [];

    console.log(`[HOLOGRAM] GLB contains ${nodes.length} nodes.`);

    // Find the exact node indices from the GLB metadata.
    const maleIndex = nodes.findIndex(
        node => node.name === "Man (Rig)"
    );

    const femaleIndex = nodes.findIndex(
        node => node.name === "Woman (Rig)"
    );

    console.log("[HOLOGRAM] Male node index:", maleIndex);
    console.log("[HOLOGRAM] Female node index:", femaleIndex);

    if (maleIndex === -1 || femaleIndex === -1) {
        console.error("[HOLOGRAM] Available character nodes:");

        nodes.forEach((node, index) => {
            if (node.name) {
                console.log(`[GLB NODE ${index}] ${node.name}`);
            }
        });

        throw new Error("Rigged character nodes are missing from GLB metadata.");
    }

    // Resolve the nodes directly through GLTFLoader's parser.
    const [maleNode, femaleNode] = await Promise.all([
        gltf.parser.getDependency("node", maleIndex),
        gltf.parser.getDependency("node", femaleIndex)
    ]);

    if (!maleNode || !femaleNode) {
        throw new Error("Three.js could not resolve the rigged GLB nodes.");
    }

    console.log("[HOLOGRAM] Male object:", maleNode.name);
    console.log("[HOLOGRAM] Female object:", femaleNode.name);

    hologramRoot.clear();

    function prepareCharacter(node, sex) {
        // Preserve the skeleton and skinned mesh relationships.
        const character = cloneSkinned(node);

        character.name = `${sex}Hologram`;

        applyHologramMaterial(character);
        normalizeModel(character);

        return character;
    }

    hologramModels.male = prepareCharacter(maleNode, "Male");
    hologramModels.female = prepareCharacter(femaleNode, "Female");

    hologramRoot.add(
        hologramModels.male,
        hologramModels.female
    );

    selectHologramSex();

    console.log("[HOLOGRAM] Both rigged models loaded successfully.");
}

// -----------------------------------------------------------------------------
// Mode and patient selection
// -----------------------------------------------------------------------------

function selectHologramSex() {
    for (const [sex, model] of Object.entries(hologramModels)) {
        if (model) {
            model.visible = sex === patientSex;
        }
    }
}

function setActiveDisplay(root, modelToFrame) {
    anatomyRoot.visible = root === anatomyRoot;
    hologramRoot.visible = root === hologramRoot;

    // Keep the anatomical selection reference available.
    anatomyReferenceRoot.visible = true;

    activeDisplayModel = modelToFrame || null;

    if (activeDisplayModel) {
        frameModel(activeDisplayModel);
    }
}

function switchVisualStyle(style) {
    visualStyle = style === "stylized" ? "stylized" : "hologram";

    if (visualStyle === "stylized") {
        const model = anatomyRoot.children[0];

        if (model) {
            setActiveDisplay(anatomyRoot, model);
            setHint("MUSCLE LAYER READY · SELECT A STRUCTURE");
        } else {
            setHint("MUSCLE MODEL NOT READY");
        }

        return;
    }

    selectHologramSex();

    const selectedModel = hologramModels[patientSex];

    if (selectedModel) {
        setActiveDisplay(hologramRoot, selectedModel);
        setHint("HOLOGRAM READY · SELECT THE BRAIN");
    } else {
        setHint("HOLOGRAM MODEL NOT READY");
    }
}

window.setVisualStyle = switchVisualStyle;

window.setPatientSex = async sex => {
    const nextSex = sex === "female" ? "female" : "male";

    if (nextSex === patientSex) return;

    patientSex = nextSex;

    console.log(`[PATIENT] Switching model to ${patientSex}.`);

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
// Python / Qt WebChannel bridge
// -----------------------------------------------------------------------------

if (window.qt && window.QWebChannel) {
    new QWebChannel(qt.webChannelTransport, channel => {
        bridge = channel.objects.backend;

        console.log("[WEB] Python bridge connected.");
    });
}

// -----------------------------------------------------------------------------
// Click selection: invisible anatomical reference in either mode
// -----------------------------------------------------------------------------

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const brainStructures = new Set([
    "brain",
    "cerebellum",
    "brainstem",
    "cranial_nerves"
]);

function selectAtPointer(event) {
    if (!anatomyReferenceMeshes.length) return;

    const rect = renderer.domElement.getBoundingClientRect();

    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;

    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(pointer, camera);

    const intersections = raycaster.intersectObjects(
        anatomyReferenceMeshes,
        false
    );

    if (!intersections.length) return;

    // Prefer brain structures even if the skull is in front.
    const brainHit = intersections.find(hit => {
        const key = (
            hit.object.userData.structureKey || ""
        ).toLowerCase();

        return brainStructures.has(key);
    });

    const selectedHit = brainHit || intersections[0];

    const structure =
        selectedHit.object.userData.structureKey || "Unknown structure";

    const isBrain = brainStructures.has(structure.toLowerCase());

    if (isBrain) {
        setHint("BRAIN SELECTED · EEG MONITORING AVAILABLE");

        if (bridge) {
            bridge.selectRegion("brain");
        }
    } else {
        setHint(`SELECTED: ${structure.toUpperCase()}`);

        if (bridge) {
            bridge.selectRegion(structure);
        }
    }

    console.log(`[ANATOMY] Selected: ${structure}`);
}

renderer.domElement.addEventListener("pointerdown", event => {
    dragging = true;
    dragged = false;

    pointerStart = {
        x: event.clientX,
        y: event.clientY
    };

    previousPointer = {
        x: event.clientX,
        y: event.clientY
    };

    renderer.domElement.setPointerCapture(event.pointerId);
});

renderer.domElement.addEventListener("pointermove", event => {
    if (!dragging) return;

    const deltaX = event.clientX - previousPointer.x;
    const deltaY = event.clientY - previousPointer.y;

    const totalMovement =
        Math.abs(event.clientX - pointerStart.x) +
        Math.abs(event.clientY - pointerStart.y);

    if (totalMovement > 4) {
        dragged = true;
    }

    worldRoot.rotation.y += deltaX * 0.006;

    worldRoot.rotation.x = THREE.MathUtils.clamp(
        worldRoot.rotation.x + deltaY * 0.003,
        -0.25,
        0.25
    );

    previousPointer = {
        x: event.clientX,
        y: event.clientY
    };
});

renderer.domElement.addEventListener("pointerup", event => {
    dragging = false;

    if (!dragged) {
        selectAtPointer(event);
    }
});

renderer.domElement.addEventListener("pointercancel", () => {
    dragging = false;
});

// -----------------------------------------------------------------------------
// Resize and render loop
// -----------------------------------------------------------------------------

function resizeRenderer() {
    const width = Math.max(1, mount.clientWidth);
    const height = Math.max(1, mount.clientHeight);

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);

    if (activeDisplayModel) {
        frameModel(activeDisplayModel);
    }
}

new ResizeObserver(resizeRenderer).observe(mount);

function animate() {
    requestAnimationFrame(animate);

    if (!dragging) {
        worldRoot.rotation.y += 0.0006;
    }

    renderer.render(scene, camera);
}

resizeRenderer();
animate();

// -----------------------------------------------------------------------------
// Initial loading
// -----------------------------------------------------------------------------

async function initializeModels() {
    setHint("LOADING ANATOMY AND HOLOGRAM MODELS...");

    try {
        await Promise.all([
            loadAnatomy(patientSex),
            loadHologramModels()
        ]);

        switchVisualStyle(visualStyle);

        setHint("3D MODELS READY · SELECT THE BRAIN");

        console.log("[3D] All models initialized successfully.");
    } catch (error) {
        console.error("[3D] Model initialization failed:", error);

        setHint("MODEL LOADING FAILED · CHECK WEB CONSOLE");
    }
}

initializeModels();
