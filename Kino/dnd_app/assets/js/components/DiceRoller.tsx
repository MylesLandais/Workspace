import React, { useMemo, useRef, useState, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Physics, useBox, usePlane, Triplet, useConvexPolyhedron } from '@react-three/cannon';
import * as THREE from 'three';
import { OrbitControls, Html } from '@react-three/drei';
import { createDiceTexture, DiceSkin, DICE_SKINS } from '../lib/diceTexture';

// Map standard D6 faces: 1, 6, 2, 5, 3, 4
const D6_FACES = [
    { n: 1, pos: [0.55, 0, 0], rot: [0, Math.PI / 2, 0] },
    { n: 6, pos: [-0.55, 0, 0], rot: [0, -Math.PI / 2, 0] },
    { n: 2, pos: [0, 0.55, 0], rot: [-Math.PI / 2, 0, 0] },
    { n: 5, pos: [0, -0.55, 0], rot: [Math.PI / 2, 0, 0] },
    { n: 3, pos: [0, 0, 0.55], rot: [0, 0, 0] },
    { n: 4, pos: [0, 0, -0.55], rot: [Math.PI, 0, Math.PI] }
];

const DiceFace = ({ number, position, rotation, skin = 'premium-gold' }: { number: number, position: number[], rotation: number[], skin?: DiceSkin }) => {
    const textureUrl = useMemo(() => createDiceTexture(number, skin), [number, skin]);
    const texture = useMemo(() => {
        const loader = new THREE.TextureLoader();
        return loader.load(textureUrl || "");
    }, [textureUrl]);

    return (
        <mesh position={new THREE.Vector3(...position)} rotation={new THREE.Euler(...rotation)}>
            <planeGeometry args={[0.42, 0.42]} />
            <meshBasicMaterial map={texture} transparent opacity={1} depthWrite={false} toneMapped={false} />
        </mesh>
    );
};

const D6 = ({ id, position, velocity, targetResult, onSettle, skin = 'premium-gold' }: { id: number, position: Triplet, velocity: Triplet, targetResult: number, onSettle: (id: number, val: number) => void, skin?: DiceSkin }) => {
    const [ref, api] = useBox(() => ({
        mass: 1,
        position,
        rotation: [Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI],
        velocity,
        args: [1, 1, 1],
        material: { friction: 0.6, restitution: 0.2 },
        linearDamping: 0.2,
        angularDamping: 0.2
    }));

    const velocityRef = useRef([0, 0, 0]);
    const angularVelocityRef = useRef([0, 0, 0]);
    useEffect(() => api.velocity.subscribe((v) => (velocityRef.current = v)), [api.velocity]);
    useEffect(() => api.angularVelocity.subscribe((v) => (angularVelocityRef.current = v)), [api.angularVelocity]);

    const [finished, setFinished] = useState(false);

    const boxFaces = useMemo(() => [
        { normal: new THREE.Vector3(1, 0, 0), n: 1 },
        { normal: new THREE.Vector3(-1, 0, 0), n: 6 },
        { normal: new THREE.Vector3(0, 1, 0), n: 2 },
        { normal: new THREE.Vector3(0, -1, 0), n: 5 },
        { normal: new THREE.Vector3(0, 0, 1), n: 3 },
        { normal: new THREE.Vector3(0, 0, -1), n: 4 }
    ], []);

    useFrame(() => {
        if (!ref.current) return;

        const speed = new THREE.Vector3(...velocityRef.current).length();
        const angSpeed = new THREE.Vector3(...angularVelocityRef.current).length();

        const targetFace = boxFaces.find(f => f.n === targetResult);
        if (targetFace) {
            const currentQ = new THREE.Quaternion();
            ref.current.getWorldQuaternion(currentQ);

            const worldNormal = targetFace.normal.clone().applyQuaternion(currentQ);
            const targetUp = new THREE.Vector3(0, 1, 0);

            const errorQ = new THREE.Quaternion().setFromUnitVectors(worldNormal, targetUp);
            const [x, y, z, w] = [errorQ.x, errorQ.y, errorQ.z, errorQ.w];

            const rollFactor = Math.max(0, 1 - speed / 8);
            const torqueStrength = finished ? 0 : 4 * rollFactor;

            if (torqueStrength > 0) {
                const angle = 2 * Math.acos(Math.min(1, Math.max(-1, w)));
                const sinHalfAngle = Math.sqrt(Math.max(0, 1 - w * w));
                if (sinHalfAngle > 0.01) {
                    const axis = new THREE.Vector3(x, y, z).divideScalar(sinHalfAngle);
                    api.applyTorque(axis.multiplyScalar(angle * torqueStrength).toArray() as Triplet);
                }
            }
        }

        if (speed < 0.1 && angSpeed < 0.1 && !finished) {
            onSettle(id, targetResult);
            setFinished(true);
        } else if (speed > 0.5) {
            if (finished) setFinished(false);
        }
    });

    return (
        <group ref={ref as any}>
            <mesh castShadow receiveShadow>
                <boxGeometry args={[1, 1, 1]} />
                <meshPhysicalMaterial
                    color="#050505"
                    roughness={0.05}
                    metalness={0.2}
                    clearcoat={1}
                    clearcoatRoughness={0.1}
                    reflectivity={1}
                    emissive="#110022"
                    emissiveIntensity={0.2}
                />
            </mesh>
            {D6_FACES.map(f => (
                <DiceFace key={f.n} number={f.n} position={f.pos} rotation={f.rot} skin={skin} />
            ))}
            {finished && (
                <Html position={[0, 1.5, 0]} center>
                    <div className="bg-black/95 text-yellow-400 px-4 py-1 rounded border-2 border-yellow-400 font-bold text-2xl drop-shadow-[0_0_10px_rgba(255,215,0,0.5)] flex flex-col items-center">
                        <span className="text-[8px] opacity-60 uppercase tracking-widest">Result</span>
                        {targetResult}
                    </div>
                </Html>
            )}
        </group>
    );
};

const PHI = (1 + Math.sqrt(5)) / 2;
const vertices: Triplet[] = [
    [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
    [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
    [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1]
];

const faceIndices = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
];

const D20_FACE_NUMBERS = [
    20, 2, 8, 14, 1, 19, 13, 7, 3, 18, 12, 6, 4, 17, 11, 5, 9, 16, 10, 15
];

const D20 = ({ id, position, velocity, targetResult, onSettle, skin = 'premium-gold' }: { id: number, position: Triplet, velocity: Triplet, targetResult: number, onSettle: (id: number, val: number) => void, skin?: DiceSkin }) => {
    const { d20Vertices, d20Faces, d20Normals } = useMemo(() => {
        const v: Triplet[] = vertices;
        const f: number[][] = faceIndices;
        const n: Triplet[] = f.map(indices => {
            const v0 = new THREE.Vector3(...v[indices[0]]);
            const v1 = new THREE.Vector3(...v[indices[1]]);
            const v2 = new THREE.Vector3(...v[indices[2]]);
            const cross = new THREE.Vector3().crossVectors(
                new THREE.Vector3().subVectors(v1, v0),
                new THREE.Vector3().subVectors(v2, v0)
            ).normalize();
            return [cross.x, cross.y, cross.z] as Triplet;
        });
        return { d20Vertices: v, d20Faces: f, d20Normals: n };
    }, []);

    const [ref, api] = useConvexPolyhedron(() => ({
        mass: 1,
        position,
        velocity,
        angularVelocity: [(Math.random() - 0.5) * 40, (Math.random() - 0.5) * 40, (Math.random() - 0.5) * 40] as Triplet,
        args: [d20Vertices, d20Faces, d20Normals, []],
        material: { friction: 0.8, restitution: 0.1 },
        allowSleep: true,
        sleepSpeedLimit: 0.1,
    }));

    const velocityRef = useRef<number[]>([0, 0, 0]);
    const angularVelocityRef = useRef<number[]>([0, 0, 0]);
    useEffect(() => api.velocity.subscribe(v => (velocityRef.current = v)), [api.velocity]);
    useEffect(() => api.angularVelocity.subscribe(v => (angularVelocityRef.current = v)), [api.angularVelocity]);

    const [finished, setFinished] = useState(false);

    const faces = useMemo(() => {
        return d20Faces.map((indices, i) => {
            const v0 = new THREE.Vector3(...d20Vertices[indices[0]]);
            const v1 = new THREE.Vector3(...d20Vertices[indices[1]]);
            const v2 = new THREE.Vector3(...d20Vertices[indices[2]]);
            const center = new THREE.Vector3().add(v0).add(v1).add(v2).divideScalar(3);
            const normal = new THREE.Vector3(...d20Normals[i]);
            const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
            const rot = new THREE.Euler().setFromQuaternion(q);
            return { normal, rot, pos: center.multiplyScalar(1.02), n: D20_FACE_NUMBERS[i] };
        });
    }, [d20Vertices, d20Faces, d20Normals]);

    useFrame(() => {
        if (!ref.current) return;
        const speed = new THREE.Vector3(...velocityRef.current).length();
        const angSpeed = new THREE.Vector3(...angularVelocityRef.current).length();

        const targetFace = faces.find(f => f.n === targetResult);
        if (targetFace && !finished && speed < 8) {
            const currentQ = new THREE.Quaternion();
            ref.current.getWorldQuaternion(currentQ);
            const worldNormal = targetFace.normal.clone().applyQuaternion(currentQ);
            const targetUp = new THREE.Vector3(0, 1, 0);
            const errorQ = new THREE.Quaternion().setFromUnitVectors(worldNormal, targetUp);
            const [x, y, z, w] = [errorQ.x, errorQ.y, errorQ.z, errorQ.w];
            const rollFactor = Math.max(0, 1 - speed / 12);
            const strength = 60 * rollFactor;
            const angle = 2 * Math.acos(Math.min(1, Math.max(-1, w)));
            const sinHalfAngle = Math.sqrt(Math.max(0, 1 - w * w));
            if (sinHalfAngle > 0.01) {
                const axis = new THREE.Vector3(x, y, z).divideScalar(sinHalfAngle);
                api.applyTorque(axis.multiplyScalar(angle * strength).toArray() as Triplet);
            }
        }

        if (speed < 0.01 && angSpeed < 0.01 && !finished) {
            onSettle(id, targetResult);
            setFinished(true);
        } else if (speed > 0.5) {
            if (finished) setFinished(false);
        }
    });

    return (
        <group ref={ref as any}>
            <mesh castShadow receiveShadow>
                <bufferGeometry>
                    <bufferAttribute
                        attach="attributes-position"
                        args={[new Float32Array(d20Faces.flat().flatMap(i => d20Vertices[i])), 3]}
                    />
                </bufferGeometry>
                <meshPhysicalMaterial
                    color="#050505"
                    roughness={0.03}
                    metalness={0.4}
                    clearcoat={1}
                    clearcoatRoughness={0.02}
                    transmission={0.1}
                    thickness={0.5}
                    ior={1.5}
                    reflectivity={1}
                    emissive="#1a0033"
                    emissiveIntensity={0.8}
                />
            </mesh>
            {faces.map((f, i) => (
                <DiceFace key={i} number={f.n} position={f.pos.toArray()} rotation={[f.rot.x, f.rot.y, f.rot.z]} skin={skin} />
            ))}
            {finished && (
                <Html position={[0, 1.8, 0]} center>
                    <div className="bg-black/95 text-yellow-400 px-5 py-2 rounded-lg border-2 border-yellow-400 font-bold text-4xl drop-shadow-[0_0_20px_rgba(255,215,0,0.6)] flex flex-col items-center">
                        <span className="text-[10px] opacity-60 uppercase tracking-[0.2em] mb-1">Result</span>
                        {targetResult}
                    </div>
                </Html>
            )}
        </group>
    );
};

const Plane = () => {
    const [ref] = usePlane(() => ({ rotation: [-Math.PI / 2, 0, 0], material: { friction: 1.0, restitution: 0.1 } }));
    return (
        <mesh ref={ref as any} receiveShadow>
            <planeGeometry args={[100, 100]} />
            <meshStandardMaterial color="#0a0a0a" />
        </mesh>
    );
};

const Walls = () => {
    usePlane(() => ({ position: [0, 0, -10], rotation: [0, 0, 0] }));
    usePlane(() => ({ position: [0, 0, 10], rotation: [0, -Math.PI, 0] }));
    usePlane(() => ({ position: [-10, 0, 0], rotation: [0, Math.PI / 2, 0] }));
    usePlane(() => ({ position: [10, 0, 0], rotation: [0, -Math.PI / 2, 0] }));
    return null;
}

// Phoenix LiveView component interface
interface DiceRollerProps {
    pushEvent?: (event: string, payload: any) => void;
    diceType?: 'D6' | 'D20';
    diceCount?: number;
    skin?: DiceSkin;
    showSkinSelector?: boolean;
}

export const DiceRoller = ({ 
    pushEvent, 
    diceType: initialDiceType = 'D20', 
    diceCount: initialDiceCount = 1,
    skin: initialSkin = 'premium-gold',
    showSkinSelector = true
}: DiceRollerProps) => {
    const [diceType, setDiceType] = useState<'D6' | 'D20'>(initialDiceType);
    const [diceCount, setDiceCount] = useState(initialDiceCount);
    const [diceSkin, setDiceSkin] = useState<DiceSkin>(initialSkin);
    const [rolls, setRolls] = useState<{ id: number, type: string, pos: Triplet, vel: Triplet, target: number }[]>([]);
    const [settled, setSettled] = useState<Record<number, number>>({});

    useEffect(() => {
        if (rolls.length > 0 && Object.keys(settled).length === rolls.length) {
            const sum = Object.values(settled).reduce((a, b) => (a as number) + (b as number), 0) as number;
            if (pushEvent) {
                pushEvent('dice-rolled', { result: sum, diceType, diceCount, individualRolls: Object.values(settled) });
            }
        }
    }, [settled, rolls.length, pushEvent, diceType, diceCount]);

    const throwDice = (e: React.MouseEvent | React.TouchEvent) => {
        let entropyX = 0;
        let entropyY = 0;

        if ('clientX' in e) {
            entropyX = (e.clientX % 100) / 100;
            entropyY = (e.clientY % 100) / 100;
        }

        const newRolls = [];
        setSettled({});
        for (let i = 0; i < diceCount; i++) {
            const r1 = Math.random();
            const r2 = Math.random();
            const factorX = (r1 + entropyX) % 1;
            const factorZ = (r2 + entropyY) % 1;

            const offsetX = (factorX - 0.5) * 2;
            const offsetZ = (factorZ - 0.5) * 2;

            const target = diceType === 'D20' ? Math.ceil(Math.random() * 20) : Math.ceil(Math.random() * 6);

            newRolls.push({
                id: Date.now() + i + Math.random(),
                type: diceType,
                pos: [offsetX * 6, 12 + i, offsetZ * 6] as Triplet,
                vel: [-offsetX * 15, -20, -offsetZ * 15] as Triplet,
                target
            });
        }
        setRolls(newRolls);
    };

    const skinColors: Record<DiceSkin, string> = {
        'premium-gold': '#FFD700',
        'classic-red': '#E00000',
        'obsidian': '#1C1C1C',
        'emerald': '#50C878',
        'sapphire': '#4169E1',
        'custom': '#808080',
    };

    return (
        <div className="w-full h-full relative group">
            <div className="absolute top-4 left-4 z-10 bg-black/60 p-4 rounded backdrop-blur border border-yellow-400/20 text-white pointer-events-auto transition-opacity opacity-20 group-hover:opacity-100 hover:opacity-100">
                <div className="flex gap-2 mb-2">
                    <button onClick={() => setDiceType('D6')} className={`px-3 py-1 rounded border ${diceType === 'D6' ? 'bg-red-600' : 'border-gray-600'}`}>D6</button>
                    <button onClick={() => setDiceType('D20')} className={`px-3 py-1 rounded border ${diceType === 'D20' ? 'bg-red-600' : 'border-gray-600'}`}>D20</button>
                </div>
                {showSkinSelector && (
                    <div className="mb-2">
                        <div className="text-xs text-gray-400 mb-1">Dice Skin</div>
                        <div className="flex gap-1 flex-wrap">
                            {(Object.keys(DICE_SKINS) as DiceSkin[]).filter(s => s !== 'custom').map(skin => (
                                <button
                                    key={skin}
                                    onClick={() => setDiceSkin(skin)}
                                    className={`w-6 h-6 rounded border-2 ${
                                        diceSkin === skin 
                                            ? 'border-yellow-400 scale-110' 
                                            : 'border-gray-600'
                                    }`}
                                    style={{ backgroundColor: skinColors[skin] }}
                                    title={skin.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                />
                            ))}
                        </div>
                    </div>
                )}
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs">Count:</span>
                    <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map(n => (
                            <button
                                key={n}
                                onClick={() => setDiceCount(n)}
                                className={`w-6 h-6 text-xs rounded border ${diceCount === n ? 'bg-yellow-400 text-black' : 'border-gray-600'}`}
                            >
                                {n}
                            </button>
                        ))}
                    </div>
                </div>
                <button
                    onClick={throwDice}
                    className="w-full py-2 bg-yellow-400 text-black font-bold rounded hover:bg-yellow-600 transition-colors mb-2"
                >
                    THROW
                </button>
                {rolls.length > 0 && (
                    <div className="text-center p-2 bg-black/40 rounded border border-yellow-400/30">
                        <div className="text-[10px] uppercase opacity-60">Status</div>
                        <div className="text-xl font-bold text-yellow-400">
                            {Object.keys(settled).length === rolls.length
                                ? `Total: ${Object.values(settled).reduce((a, b) => (a as number) + (b as number), 0)}`
                                : `Rolling... (${Object.keys(settled).length}/${rolls.length})`}
                        </div>
                    </div>
                )}
            </div>

            <Canvas shadows camera={{ position: [15, 15, 15], fov: 40 }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.7} />
                    <spotLight position={[20, 40, 20]} angle={0.4} penumbra={1} castShadow intensity={400} />
                    <pointLight position={[-10, 10, -10]} color="#6666ff" intensity={100} />
                    <Physics gravity={[0, -70, 0]}>
                        <Plane />
                        <Walls />
                        {rolls.map((roll: any) => (
                            roll.type === 'D20'
                                ? <D20 key={roll.id} id={roll.id} position={roll.pos} velocity={roll.vel} targetResult={roll.target} onSettle={(id, val) => setSettled(p => ({ ...p, [id]: val }))} skin={diceSkin} />
                                : <D6 key={roll.id} id={roll.id} position={roll.pos} velocity={roll.vel} targetResult={roll.target} onSettle={(id, val) => setSettled(p => ({ ...p, [id]: val }))} skin={diceSkin} />
                        ))}
                    </Physics>
                </Suspense>
                <OrbitControls />
            </Canvas>
        </div>
    );
};

// Export to window.Components for phoenix_live_react
if (typeof window !== 'undefined') {
    (window as any).Components = (window as any).Components || {};
    (window as any).Components.DiceRoller = DiceRoller;
}

